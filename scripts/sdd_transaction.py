#!/usr/bin/env python3
"""Persistent user-scope transaction journal for SDD Toolkit lifecycle operations."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


SCHEMA_VERSION = 1
OWNER = "sdd-toolkit"
PHASES = ["planned", "staged", "assets", "shim", "path", "manifest", "verified", "committed"]
TERMINAL_STATUSES = {"committed", "rolled_back"}


class TransactionError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_document_bytes(value: Dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def atomic_write(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        os.chmod(path.parent, 0o700)
    payload = json_document_bytes(value)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
        if os.name != "nt":
            os.chmod(path, 0o600)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def compute_plan_id(plan: Dict[str, Any]) -> str:
    content = json.loads(canonical_json({key: value for key, value in plan.items() if key not in {"plan_id", "created_at"}}))
    for action in content.get("actions", []):
        if action.get("kind") == "manifest":
            action["after_sha256"] = None
    return sha256_bytes(canonical_json(content).encode("utf-8"))


def build_plan(
    operation: str,
    profile_root: Path,
    actions: Iterable[Dict[str, Any]],
    allowed_roots: Iterable[Path],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    normalized_actions = sorted((dict(item) for item in actions), key=lambda item: (item["target"], item["id"]))
    plan: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "operation": operation,
        "scope": "user",
        "profile_root": str(profile_root.resolve(strict=False)),
        "created_at": utc_now(),
        "allowed_roots": sorted({str(Path(item).resolve(strict=False)) for item in allowed_roots}),
        "actions": normalized_actions,
        "smoke_checks": ["owned-hashes", "manifest-consistency"],
        "metadata": metadata or {},
    }
    plan["plan_id"] = compute_plan_id(plan)
    return plan


def transactions_root(state_root: Path) -> Path:
    return state_root.resolve(strict=False) / "user" / "transactions"


def lock_path(state_root: Path) -> Path:
    return state_root.resolve(strict=False) / "user" / "transaction.lock"


def process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
            process_query_limited_information = 0x1000
            still_active = 259
            handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, pid)
            if not handle:
                return False
            exit_code = ctypes.c_ulong()
            try:
                if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    return False
                return exit_code.value == still_active
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except (AttributeError, OSError):
            return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


class OperationLock:
    def __init__(self, state_root: Path, timeout: float = 10.0) -> None:
        self.path = lock_path(state_root)
        self.timeout = timeout
        self.acquired = False

    def __enter__(self) -> "OperationLock":
        deadline = time.monotonic() + self.timeout
        while True:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            try:
                descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    json.dump({"pid": os.getpid(), "created_at": utc_now()}, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                self.acquired = True
                return self
            except FileExistsError:
                try:
                    record = json.loads(self.path.read_text(encoding="utf-8"))
                    owner_pid = int(record.get("pid", -1))
                except (OSError, ValueError, json.JSONDecodeError):
                    owner_pid = -1
                if not process_is_alive(owner_pid):
                    try:
                        self.path.unlink()
                    except FileNotFoundError:
                        pass
                    continue
                if time.monotonic() >= deadline:
                    raise TransactionError(f"Timed out waiting for user transaction lock: {self.path}")
                time.sleep(0.1)

    def __exit__(self, *_: object) -> None:
        if self.acquired:
            self.path.unlink(missing_ok=True)


def journal_hash(journal: Dict[str, Any]) -> str:
    content = {key: value for key, value in journal.items() if key != "journal_hash"}
    return sha256_bytes(canonical_json(content).encode("utf-8"))


def validate_plan(plan: Dict[str, Any]) -> None:
    if plan.get("schema_version") != SCHEMA_VERSION or plan.get("scope") != "user":
        raise TransactionError("Unsupported transaction plan")
    if plan.get("plan_id") != compute_plan_id(plan):
        raise TransactionError("Transaction plan hash does not match its content")
    if not isinstance(plan.get("actions"), list) or not isinstance(plan.get("allowed_roots"), list):
        raise TransactionError("Transaction plan actions or roots are invalid")
    action_ids = [item.get("id") for item in plan["actions"] if isinstance(item, dict)]
    if len(action_ids) != len(plan["actions"]) or len(action_ids) != len(set(action_ids)):
        raise TransactionError("Transaction action IDs must be unique")


def validate_journal(journal: Dict[str, Any]) -> None:
    if journal.get("schema_version") != SCHEMA_VERSION:
        raise TransactionError("Unsupported transaction journal")
    if journal.get("journal_hash") != journal_hash(journal):
        raise TransactionError("Transaction journal integrity check failed")
    validate_plan(journal.get("plan", {}))
    if journal.get("plan_id") != journal["plan"]["plan_id"]:
        raise TransactionError("Transaction journal references another plan")


def is_within(target: Path, root: Path) -> bool:
    try:
        target.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def validate_target(plan: Dict[str, Any], target: Path, action_id: str) -> Dict[str, Any]:
    action = next((item for item in plan["actions"] if item.get("id") == action_id), None)
    if action is None or Path(action.get("target", "")).resolve(strict=False) != target.resolve(strict=False):
        raise TransactionError(f"Target is not authorized by transaction plan: {target}")
    if not any(is_within(target, Path(root)) for root in plan["allowed_roots"]):
        raise TransactionError(f"Target escapes transaction roots: {target}")
    current = target
    allowed = [Path(root).resolve(strict=False) for root in plan["allowed_roots"]]
    while not any(current == root for root in allowed) and current.parent != current:
        if current.is_symlink():
            raise TransactionError(f"Target contains a symbolic link: {target}")
        current = current.parent
    return action


def windows_path_entry_present(entry: str) -> bool:
    if os.name != "nt":
        raise TransactionError("Windows PATH action cannot run on this platform")
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ) as key:
        try:
            current, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current = ""
    normalized = entry.rstrip("\\/").casefold()
    return any(item.rstrip("\\/").casefold() == normalized for item in str(current).split(";") if item)


def set_windows_path_entry(entry: str, present: bool) -> None:
    if os.name != "nt":
        raise TransactionError("Windows PATH action cannot run on this platform")
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
        try:
            current, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current, kind = "", winreg.REG_EXPAND_SZ
        values = [item for item in str(current).split(";") if item]
        normalized = entry.rstrip("\\/").casefold()
        filtered = [item for item in values if item.rstrip("\\/").casefold() != normalized]
        if present:
            filtered.append(entry)
        winreg.SetValueEx(key, "Path", 0, kind, ";".join(filtered))


def read_journal(path: Path) -> Dict[str, Any]:
    try:
        journal = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TransactionError(f"Cannot read transaction journal {path}: {exc}") from exc
    if not isinstance(journal, dict):
        raise TransactionError(f"Invalid transaction journal: {path}")
    validate_journal(journal)
    return journal


def list_journals(state_root: Path) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    root = transactions_root(state_root)
    if not root.is_dir():
        return result
    for path in sorted(root.glob("*/journal.json")):
        journal = read_journal(path)
        result.append({
            "plan_id": journal["plan_id"],
            "operation": journal["plan"]["operation"],
            "phase": journal["phase"],
            "status": journal["status"],
            "created_at": journal["created_at"],
            "updated_at": journal["updated_at"],
            "journal_path": str(path),
        })
    return result


def incomplete_journals(state_root: Path) -> List[Dict[str, Any]]:
    return [item for item in list_journals(state_root) if item["status"] not in TERMINAL_STATUSES]


class Transaction:
    def __init__(self, state_root: Path, journal_path: Path, journal: Dict[str, Any]) -> None:
        self.state_root = state_root.resolve(strict=False)
        self.journal_path = journal_path
        self.root = journal_path.parent
        self.backup_root = self.root / "backups"
        self.journal = journal

    @classmethod
    def start(cls, state_root: Path, plan: Dict[str, Any]) -> "Transaction":
        validate_plan(plan)
        root = transactions_root(state_root) / plan["plan_id"]
        journal_path = root / "journal.json"
        if journal_path.exists():
            existing = read_journal(journal_path)
            if existing["status"] not in TERMINAL_STATUSES:
                raise TransactionError(f"Transaction already requires recovery: {plan['plan_id']}")
            if existing["status"] == "committed":
                raise TransactionError(f"Transaction plan was already applied: {plan['plan_id']}")
            archived = root / f"journal.rolled-back.{time.time_ns()}.json"
            os.replace(journal_path, archived)
        else:
            root.mkdir(parents=True, exist_ok=False)
        journal: Dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "plan_id": plan["plan_id"],
            "status": "active",
            "phase": "planned",
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "plan": plan,
            "backups": [],
            "events": [{"phase": "planned", "at": utc_now()}],
            "conflicts": [],
        }
        journal["journal_hash"] = journal_hash(journal)
        atomic_write(journal_path, journal)
        return cls(state_root, journal_path, journal)

    def write(self) -> None:
        self.journal["updated_at"] = utc_now()
        self.journal["journal_hash"] = journal_hash(self.journal)
        atomic_write(self.journal_path, self.journal)

    def phase(self, phase: str) -> None:
        if phase not in PHASES:
            raise TransactionError(f"Unknown transaction phase: {phase}")
        if PHASES.index(phase) < PHASES.index(self.journal["phase"]):
            raise TransactionError("Transaction phase cannot move backwards")
        self.journal["phase"] = phase
        self.journal["events"].append({"phase": phase, "at": utc_now()})
        self.write()

    def track_file(self, action_id: str) -> None:
        action = next((item for item in self.journal["plan"]["actions"] if item["id"] == action_id), None)
        if action is None:
            raise TransactionError(f"Unknown transaction action: {action_id}")
        target = Path(action["target"])
        validate_target(self.journal["plan"], target, action_id)
        if any(item["action_id"] == action_id for item in self.journal["backups"]):
            raise TransactionError(f"Transaction action already tracked: {action_id}")
        if target.exists() and (target.is_symlink() or not target.is_file()):
            raise TransactionError(f"Transaction target is not a regular file: {target}")
        existed = target.is_file()
        before_sha256 = sha256_file(target) if existed else None
        if action.get("before_sha256") != before_sha256:
            raise TransactionError(f"Transaction target changed since preview: {target}")
        backup_name: Optional[str] = None
        if existed:
            self.backup_root.mkdir(parents=True, exist_ok=True)
            backup_name = f"{len(self.journal['backups']):04d}.backup"
            shutil.copy2(target, self.backup_root / backup_name)
        self.journal["backups"].append({
            "record_type": "file",
            "action_id": action_id,
            "target": str(target),
            "existed": existed,
            "before_sha256": before_sha256,
            "after_sha256": action.get("after_sha256"),
            "backup": backup_name,
        })
        self.write()

    def track_windows_path(self, action_id: str) -> None:
        action = next((item for item in self.journal["plan"]["actions"] if item["id"] == action_id), None)
        if action is None or action.get("kind") != "path" or action.get("strategy") != "windows-user-env":
            raise TransactionError(f"Unknown Windows PATH action: {action_id}")
        if any(item["action_id"] == action_id for item in self.journal["backups"]):
            raise TransactionError(f"Transaction action already tracked: {action_id}")
        entry = action.get("entry")
        if not isinstance(entry, str) or not entry:
            raise TransactionError("Windows PATH transaction entry is invalid")
        current = windows_path_entry_present(entry)
        if current != action.get("before_present"):
            raise TransactionError("Windows PATH changed since preview")
        self.journal["backups"].append({
            "record_type": "windows-path",
            "action_id": action_id,
            "target": "windows-user-env",
            "existed": current,
            "before_sha256": None,
            "after_sha256": None,
            "backup": None,
        })
        self.write()

    def commit(self) -> None:
        self.phase("committed")
        self.journal["status"] = "committed"
        self.write()
        if self.backup_root.exists():
            shutil.rmtree(self.backup_root)

    def rollback(self) -> Dict[str, Any]:
        return recover_journal(self.journal_path, apply=True)


def recover_journal(path: Path, apply: bool) -> Dict[str, Any]:
    journal = read_journal(path)
    if journal["status"] in TERMINAL_STATUSES:
        return {"plan_id": journal["plan_id"], "status": journal["status"], "actions": [], "conflicts": []}
    planned: List[Dict[str, str]] = []
    conflicts: List[str] = []
    for record in reversed(journal["backups"]):
        action_record = next((item for item in journal["plan"]["actions"] if item.get("id") == record["action_id"]), None)
        if action_record is None:
            raise TransactionError(f"Journal action is not present in plan: {record['action_id']}")
        if record.get("record_type") == "windows-path":
            if action_record.get("kind") != "path" or action_record.get("strategy") != "windows-user-env":
                raise TransactionError("Journal Windows PATH action does not match its plan")
            entry = action_record.get("entry")
            if not isinstance(entry, str) or not entry:
                raise TransactionError("Journal Windows PATH entry is invalid")
            current_present = windows_path_entry_present(entry)
            if current_present == action_record.get("before_present"):
                path_action = "already-restored"
            elif current_present == action_record.get("after_present"):
                path_action = "restore-path-entry"
            else:
                path_action = "preserve-conflict"
                conflicts.append("windows-user-env")
            planned.append({"target": "windows-user-env", "action": path_action})
            continue
        target = Path(record["target"])
        validate_target(journal["plan"], target, record["action_id"])
        before_hash = record.get("before_sha256")
        after_hash = record.get("after_sha256")
        current_hash = sha256_file(target) if target.is_file() and not target.is_symlink() else None
        if record["existed"]:
            if current_hash == before_hash:
                action = "already-restored"
            elif (after_hash is not None and current_hash == after_hash) or (after_hash is None and not target.exists()):
                action = "restore"
            else:
                action = "preserve-conflict"
                conflicts.append(str(target))
        else:
            if not target.exists():
                action = "already-removed"
            elif after_hash is not None and current_hash == after_hash:
                action = "remove-created"
            else:
                action = "preserve-conflict"
                conflicts.append(str(target))
        planned.append({"target": str(target), "action": action})
    if not apply:
        return {"plan_id": journal["plan_id"], "status": "recovery-ready" if not conflicts else "recovery-blocked", "actions": planned, "conflicts": conflicts}
    if conflicts:
        journal["status"] = "recovery-blocked"
        journal["conflicts"] = conflicts
        journal["updated_at"] = utc_now()
        journal["journal_hash"] = journal_hash(journal)
        atomic_write(path, journal)
        return {"plan_id": journal["plan_id"], "status": "recovery-blocked", "actions": planned, "conflicts": conflicts}
    for record, item in zip(reversed(journal["backups"]), planned):
        if record.get("record_type") == "windows-path":
            if item["action"] == "restore-path-entry":
                action_record = next(action for action in journal["plan"]["actions"] if action["id"] == record["action_id"])
                set_windows_path_entry(action_record["entry"], bool(action_record["before_present"]))
            continue
        target = Path(record["target"])
        if item["action"] == "restore":
            backup = path.parent / "backups" / record["backup"]
            if not backup.is_file() or sha256_file(backup) != record["before_sha256"]:
                raise TransactionError(f"Transaction backup is missing or corrupt: {backup}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, target)
        elif item["action"] == "remove-created":
            target.unlink()
    journal["status"] = "rolled_back"
    journal["phase"] = "planned"
    journal["events"].append({"phase": "recovered", "at": utc_now()})
    journal["updated_at"] = utc_now()
    journal["journal_hash"] = journal_hash(journal)
    atomic_write(path, journal)
    backup_root = path.parent / "backups"
    if backup_root.exists():
        shutil.rmtree(backup_root)
    return {"plan_id": journal["plan_id"], "status": "rolled_back", "actions": planned, "conflicts": []}


def recover_transactions(state_root: Path, plan_id: str = "", apply: bool = False) -> Dict[str, Any]:
    journals = incomplete_journals(state_root)
    if plan_id:
        journals = [item for item in journals if item["plan_id"] == plan_id]
        if not journals:
            return {
                "schema_version": SCHEMA_VERSION,
                "scope": "user",
                "mode": "apply" if apply else "preview",
                "status": "not-found",
                "transactions": [],
            }
    results = [recover_journal(Path(item["journal_path"]), apply=apply) for item in journals]
    blocked = any(item["status"] == "recovery-blocked" for item in results)
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": "user",
        "mode": "apply" if apply else "preview",
        "status": "blocked" if blocked else ("recovered" if apply and results else "ready"),
        "transactions": results,
    }


def fault(point: str) -> None:
    if os.environ.get("SDD_TOOLKIT_TEST_MODE") == "1" and os.environ.get("SDD_TOOLKIT_FAULT_AT") == point:
        os._exit(97)
