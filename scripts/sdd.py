#!/usr/bin/env python3
"""Public SDD Toolkit command line interface.

The platform installers are thin wrappers around the user-scoped lifecycle so
that Windows, Linux and macOS expose the same vocabulary and exit codes.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import sdd_transaction as TXN
import sdd_runtime as RUNTIME
import sdd_discovery as DISCOVERY
import sdd_delivery as DELIVERY
import sdd_architecture as ARCHITECTURE
import sdd_user_state as STATE


ROOT = Path(__file__).resolve().parents[1]
ACTIVATION_SCHEMA_VERSION = 2
TICKET_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def emit(value: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return
    for key, item in value.items():
        print(f"{key}: {json.dumps(item, ensure_ascii=False) if isinstance(item, (dict, list)) else item}")


def user_activation_path() -> Path:
    return STATE.state_dir() / "user" / "activations.json"


def default_user_workspace(project: Path, project_id: str) -> tuple[Path, Path]:
    history_root = os.environ.get("SDD_TOOLKIT_HISTORY_DIR")
    if history_root:
        base = Path(history_root).expanduser().resolve(strict=False)
        if base == Path.home() or base.parent == base:
            raise STATE.StateError("SDD_TOOLKIT_HISTORY_DIR must point to a dedicated history directory")
    else:
        base = Path.home() / "sdd-history-implementations"
    namespace = base / f"{project.name}-{project_id[:12]}"
    return namespace, namespace / project.name / "specs"


def load_user_activations() -> Dict[str, Any]:
    path = user_activation_path()
    if not path.exists():
        return {"schema_version": ACTIVATION_SCHEMA_VERSION, "activations": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise STATE.StateError(f"Cannot read user activation state {path}: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") not in {1, ACTIVATION_SCHEMA_VERSION}:
        raise STATE.StateError(f"Unsupported or invalid user activation schema: {path}")
    activations = value.get("activations")
    if not isinstance(activations, list):
        raise STATE.StateError(f"Invalid user activation list: {path}")
    normalized: List[Dict[str, Any]] = []
    for item in activations:
        if (
            not isinstance(item, dict)
            or item.get("schema_version") not in {1, ACTIVATION_SCHEMA_VERSION}
            or item.get("scope") != "user"
            or not isinstance(item.get("project_id"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", item["project_id"])
            or not isinstance(item.get("project_path"), str)
            or not Path(item["project_path"]).is_absolute()
            or not isinstance(item.get("workspace_root"), str)
            or not Path(item["workspace_root"]).is_absolute()
            or not isinstance(item.get("workspace"), str)
            or not Path(item["workspace"]).is_absolute()
        ):
            raise STATE.StateError(f"Invalid user activation entry: {path}")
        record = dict(item)
        legacy_runtime = record.pop("runtime", None)
        hints = record.get("runtime_hints", [])
        if not isinstance(hints, list) or not all(isinstance(hint, str) for hint in hints):
            raise STATE.StateError(f"Invalid runtime hints in activation entry: {path}")
        if isinstance(legacy_runtime, str) and legacy_runtime not in {"", "all", "auto"} and legacy_runtime not in hints:
            hints.append(legacy_runtime)
        record["runtime_hints"] = sorted(set(hints))
        record["schema_version"] = ACTIVATION_SCHEMA_VERSION
        normalized.append(record)
    return {"schema_version": ACTIVATION_SCHEMA_VERSION, "activations": normalized}


def project_path_arg(value: str) -> Path:
    project = Path(value).expanduser().resolve(strict=False)
    if not project.is_dir():
        raise STATE.StateError(f"Project directory does not exist: {project}")
    return project


def activation_project_path(value: str) -> Path:
    """Resolve the current project without requiring users to know its root."""
    project = project_path_arg(value)
    try:
        completed = subprocess.run(
            ["git", "-C", str(project), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=3, check=False,
        )
        root = Path(completed.stdout.strip()).resolve(strict=False)
        if completed.returncode == 0 and root.is_dir():
            return root
    except (OSError, subprocess.TimeoutExpired):
        pass
    return project


def activation_kit_root(value: str) -> Path:
    if value:
        kit = Path(value).expanduser().resolve(strict=False)
    else:
        kit = ROOT
        installation = user_installation_path()
        if installation.is_file():
            try:
                candidate = json.loads(installation.read_text(encoding="utf-8")).get("kit_root")
                if isinstance(candidate, str) and candidate:
                    kit = Path(candidate).expanduser().resolve(strict=False)
            except (OSError, json.JSONDecodeError):
                pass
    if not kit.is_dir() or not (kit / "VERSION").is_file():
        raise STATE.StateError("Toolkit source is unavailable; run the global installer or use --kit-root for a development checkout")
    return kit


def activation_record(project: Path, kit: Path, runtime: str, previous: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    project_id = STATE.installation_id(project)
    workspace_root, workspace = default_user_workspace(project, project_id)
    now = STATE.utc_now()
    return {
        "schema_version": ACTIVATION_SCHEMA_VERSION,
        "scope": "user",
        "profile": "default",
        "runtime_hints": sorted(set(
            list((previous or {}).get("runtime_hints", []))
            + ([] if runtime in {"", "all", "auto"} else [runtime])
        )),
        "project_id": project_id,
        "project_name": project.name,
        "project_path": str(project),
        "workspace_root": str(workspace_root),
        "workspace": str(workspace),
        "kit_root": str(kit),
        "toolkit_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "created_at": (previous or {}).get("created_at", now),
        "updated_at": (previous or {}).get("updated_at", now),
    }


def save_activation(record: Dict[str, Any]) -> Dict[str, Any]:
    path = user_activation_path()
    with STATE.RegistryLock(path.with_suffix(path.suffix + ".lock")):
        current = load_user_activations()
        entries = [item for item in current["activations"] if item.get("project_id") != record["project_id"]]
        previous = next((item for item in current["activations"] if item.get("project_id") == record["project_id"]), None)
        if previous:
            record["created_at"] = previous.get("created_at", record["created_at"])
            record["updated_at"] = previous.get("updated_at", record["updated_at"])
        entries.append(record)
        current["activations"] = sorted(entries, key=lambda item: item["project_path"].lower())
        STATE.atomic_write(path, current, backup=True)
    Path(record["workspace"]).mkdir(parents=True, exist_ok=True)
    return record


def activate_user(args: argparse.Namespace) -> int:
    project = activation_project_path(args.project_path)
    kit = activation_kit_root(args.kit_root)
    current = load_user_activations()
    existing = next((item for item in current["activations"] if item.get("project_id") == STATE.installation_id(project)), None)
    record = activation_record(project, kit, args.runtime, existing)
    apply = not getattr(args, "dry_run", False)
    result = {
        "schema_version": ACTIVATION_SCHEMA_VERSION,
        "mode": "apply" if apply else "preview",
        "status": "already-active" if existing else ("activated" if apply else "ready"),
        "scope": "user",
        "action": "update" if existing else "create",
        "activation": record,
        "state_path": str(user_activation_path()),
        "writes_project": False,
        "creates_workspace": bool(apply and not existing),
        "next": "sdd start <TICKET>",
    }
    if apply:
        record = save_activation(record)
        result["activation"] = record
    emit(result, args.json)
    return 0


def resolve_context(args: argparse.Namespace) -> int:
    project = activation_project_path(args.project_path)
    project_id = STATE.installation_id(project)
    activations = load_user_activations().get("activations", [])
    activation = next((item for item in activations if item.get("project_id") == project_id), None)
    source = "user-activation"
    effective_scope = "user"
    status = "ready"
    if activation:
        workspace = Path(activation["workspace"])
        runtime = args.runtime
        profile = activation["profile"]
    else:
        _, workspace = default_user_workspace(project, project_id)
        runtime = args.runtime
        profile = "default"
        source = "default"
        status = "unactivated"
    result: Dict[str, Any] = {
        "schema_version": 1,
        "status": status,
        "scope": effective_scope,
        "source": source,
        "profile": profile,
        "runtime": runtime,
        "runtime_hints": activation.get("runtime_hints", []) if activation else [],
        "project": {
            "name": project.name,
            "path": str(project),
            "project_id": project_id,
        },
        "workspace": str(workspace),
        "activation_state": str(user_activation_path()),
        "writes_project": False,
    }
    if args.ticket:
        if not TICKET_PATTERN.fullmatch(args.ticket):
            raise STATE.StateError("Ticket must contain only letters, numbers, '.', '_' or '-' and be at most 128 characters")
        result["ticket"] = args.ticket
        result["spec_path"] = str(workspace / args.ticket)
    emit(result, args.json)
    return 0


def activation_for(project: Path) -> Optional[Dict[str, Any]]:
    project_id = STATE.installation_id(project)
    return next((item for item in load_user_activations()["activations"] if item.get("project_id") == project_id), None)


def user_status(args: argparse.Namespace) -> int:
    project = activation_project_path(args.project_path)
    activation = activation_for(project)
    result: Dict[str, Any] = {
        "schema_version": ACTIVATION_SCHEMA_VERSION,
        "scope": "user",
        "project": str(project),
        "status": "active" if activation else "unactivated",
        "activation": activation,
        "next": "sdd start <TICKET>" if activation else "sdd activate",
    }
    if activation:
        specs = Path(activation["workspace"])
        result["workspace"] = str(specs)
        result["tickets"] = sorted(
            item.name for item in specs.iterdir()
            if item.is_dir() and TICKET_PATTERN.fullmatch(item.name)
        ) if specs.is_dir() else []
    emit(result, args.json)
    return 0


def activate_for_start(project: Path, runtime: str) -> Dict[str, Any]:
    kit = activation_kit_root("")
    record = activation_record(project, kit, runtime, activation_for(project))
    return save_activation(record)


def daily_handoff(args: argparse.Namespace, action: str) -> int:
    project = activation_project_path(args.project_path)
    ticket = getattr(args, "ticket", "")
    activation = activation_for(project)
    if action == "resume" and not ticket and activation:
        workspace = Path(activation["workspace"])
        candidates = sorted(
            item.name for item in workspace.iterdir()
            if item.is_dir() and (item / "session-state.md").is_file()
        ) if workspace.is_dir() else []
        if len(candidates) == 1:
            ticket = candidates[0]
        elif len(candidates) > 1:
            raise STATE.StateError("Multiple resumable tickets found; run 'sdd resume <TICKET>'")
        else:
            raise STATE.StateError("No resumable ticket found; run 'sdd start <TICKET>'")
    if not TICKET_PATTERN.fullmatch(ticket):
        raise STATE.StateError("Ticket must contain only letters, numbers, '.', '_' or '-' and be at most 128 characters")
    if not activation:
        if not getattr(args, "yes", False):
            result = {
                "schema_version": ACTIVATION_SCHEMA_VERSION,
                "status": "activation-required",
                "project": str(project),
                "ticket": ticket,
                "next": "Run 'sdd activate' first, or repeat with --yes to activate this project locally.",
                "writes_project": False,
            }
            emit(result, args.json)
            return 2
        activation = activate_for_start(project, getattr(args, "runtime", "auto"))
    workspace = Path(activation["workspace"])
    result = {
        "schema_version": ACTIVATION_SCHEMA_VERSION,
        "status": "ready",
        "action": action,
        "project": str(project),
        "ticket": ticket,
        "workspace": str(workspace),
        "spec_path": str(workspace / ticket),
        "runtime": getattr(args, "runtime", "auto"),
        "agent": "sdd-bootstrap",
        "handoff": f"Use sdd-bootstrap to {action} ticket {ticket} in the current project.",
        "writes_project": False,
    }
    emit(result, args.json)
    return 0


def activation_lifecycle(args: argparse.Namespace) -> int:
    current = load_user_activations()
    if args.activation_command == "list":
        emit({"schema_version": ACTIVATION_SCHEMA_VERSION, "scope": "user", "activations": current["activations"]}, args.json)
        return 0
    project = activation_project_path(args.project_path)
    record = activation_for(project)
    if args.activation_command == "show":
        emit({"schema_version": ACTIVATION_SCHEMA_VERSION, "scope": "user", "status": "active" if record else "unactivated", "activation": record}, args.json)
        return 0
    if not record:
        emit({"schema_version": ACTIVATION_SCHEMA_VERSION, "scope": "user", "status": "unactivated", "project": str(project)}, args.json)
        return 0
    result = {"schema_version": ACTIVATION_SCHEMA_VERSION, "scope": "user", "status": "preview" if not args.apply else "deactivated", "activation": record, "writes_project": False}
    if args.apply:
        path = user_activation_path()
        with STATE.RegistryLock(path.with_suffix(path.suffix + ".lock")):
            latest = load_user_activations()
            latest["activations"] = [item for item in latest["activations"] if item.get("project_id") != record["project_id"]]
            STATE.atomic_write(path, latest, backup=True)
    emit(result, args.json)
    return 0


def user_installation_path() -> Path:
    return STATE.state_dir() / "user" / "installation.json"


def load_user_installation() -> Dict[str, Any]:
    path = user_installation_path()
    if not path.exists():
        return {"schema_version": 2, "scope": "user", "managed_files": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise STATE.StateError(f"Cannot read user installation state {path}: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") not in {1, 2} or value.get("scope") != "user" or not isinstance(value.get("managed_files"), list):
        raise STATE.StateError(f"Unsupported or invalid user installation state: {path}")
    normalized: List[Dict[str, Any]] = []
    for item in value["managed_files"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise STATE.StateError(f"Invalid managed file record: {path}")
        runtimes = item.get("runtimes")
        if not isinstance(runtimes, list):
            runtimes = [item.get("runtime")] if isinstance(item.get("runtime"), str) else []
        if not runtimes or not all(isinstance(runtime, str) for runtime in runtimes):
            raise STATE.StateError(f"Invalid managed file runtimes: {path}")
        record = dict(item)
        record["runtimes"] = list(dict.fromkeys(runtimes))
        record.setdefault("runtime", record["runtimes"][0])
        normalized.append(record)
    value["managed_files"] = normalized
    value["schema_version"] = 2
    return value


def profile_path_arg(value: str) -> Path:
    profile = Path(value).expanduser().resolve(strict=False)
    if profile.parent == profile:
        raise STATE.StateError("User profile root cannot be the filesystem root")
    return profile


def user_install_sources(kit: Path, runtime: str, profile: Path) -> List[Dict[str, Any]]:
    targets: List[Dict[str, Any]] = []
    adapters = RUNTIME.load_adapters(kit)
    try:
        runtimes = RUNTIME.selected_runtimes(runtime, adapters)
    except ValueError as exc:
        raise STATE.StateError(str(exc)) from exc
    by_relative: Dict[str, Dict[str, Any]] = {}
    for target in runtimes:
        adapter = adapters[target]
        source_root = kit / adapter.output_dir
        pattern = "*.toml" if adapter.renderer == "codex-toml" else "*.agent.md" if target == "copilot" else "*.md"
        for source in sorted(source_root.glob(pattern)):
            relative = str(Path(adapter.user_agent_dir) / source.name)
            entry = by_relative.setdefault(relative, {"runtime": target, "runtimes": [], "source": str(source), "relative": relative})
            if target not in entry["runtimes"]:
                entry["runtimes"].append(target)
        if target in {"codex", "cursor"}:
            shared_root = kit / "dist" / "shared" / "skills"
            shared_sources = list(sorted(shared_root.glob("*/SKILL.md"))) if shared_root.is_dir() else []
            shared_sources.extend(sorted((kit / "templates" / "skills").glob("*/SKILL.md")))
        else:
            shared_sources = sorted((kit / "templates" / "skills").glob("*/SKILL.md"))
        for skill in shared_sources:
            relative = str(Path(adapter.skill_dir) / skill.parent.name / "SKILL.md")
            entry = by_relative.setdefault(relative, {"runtime": target, "runtimes": [], "source": str(skill), "relative": relative})
            if target not in entry["runtimes"]:
                entry["runtimes"].append(target)
    targets = list(by_relative.values())
    if not targets:
        raise STATE.StateError(f"No compiled assets found for runtime '{runtime}' in {kit}")
    return targets


def local_source_metadata(kit: Path) -> Dict[str, str]:
    commit = "0000000"
    remote = "local"
    try:
        completed = subprocess.run(["git", "-C", str(kit), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5, check=False)
        if completed.returncode == 0 and re.fullmatch(r"[0-9a-f]{7,64}", completed.stdout.strip()):
            commit = completed.stdout.strip()
        remote_result = subprocess.run(["git", "-C", str(kit), "config", "--get", "remote.origin.url"], capture_output=True, text=True, timeout=5, check=False)
        if remote_result.returncode == 0 and remote_result.stdout.strip():
            remote = remote_result.stdout.strip()
            if "@" in remote and "://" in remote:
                scheme, remainder = remote.split("://", 1)
                remote = f"{scheme}://{remainder.split('@', 1)[-1]}"
    except (OSError, subprocess.TimeoutExpired):
        pass
    version = (kit / "VERSION").read_text(encoding="utf-8").strip()
    return {
        "source_type": "local",
        "repository_url": remote or "local",
        "channel": "explicit",
        "requested_ref": "local",
        "resolved_ref": version,
        "commit": commit,
    }


def source_state_path() -> Path:
    return STATE.state_dir() / "user" / "source.json"


def validate_kit_root(kit: Path) -> None:
    required = (
        kit / "VERSION", kit / "scripts" / "sdd.py", kit / "scripts" / "sdd_user_state.py",
        kit / "dist", kit / "templates" / "skills", kit / "schemas",
    )
    missing = [str(item) for item in required if not item.exists()]
    if missing:
        raise STATE.StateError(f"Toolkit source is incomplete; missing: {', '.join(missing)}")


def git_command(arguments: List[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(["git", *arguments], capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise STATE.StateError(f"Git command failed: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[:500]
        raise STATE.StateError(f"Git command failed: {detail or 'unknown error'}")
    return completed


def validate_repository_url(value: str) -> str:
    url = value.strip()
    if not url:
        raise STATE.StateError("repository URL is required")
    if "://" in url:
        scheme, remainder = url.split("://", 1)
        if scheme not in {"https", "ssh", "file"}:
            raise STATE.StateError("repository URL must use HTTPS, SSH or an explicit local file URL")
        if "@" in remainder:
            user = remainder.split("@", 1)[0]
            if scheme != "ssh" or user != "git":
                raise STATE.StateError("repository URL must not contain embedded credentials")
    elif not re.fullmatch(r"(?:git@[^:/]+):.+", url):
        raise STATE.StateError("repository URL must use HTTPS, SSH or an explicit local file URL")
    return url


def remote_ref(url: str, channel: str, requested: str) -> str:
    if requested:
        return requested
    if channel == "main":
        return "main"
    output = git_command(["ls-remote", "--refs", "--tags", url, "v*"], timeout=30).stdout
    tags: List[tuple[tuple[int, int, int], int, str]] = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        tag = parts[1].removeprefix("refs/tags/")
        if tag.endswith("^{}"):
            continue
        match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(-([0-9A-Za-z.-]+))?", tag)
        if not match:
            continue
        prerelease = 1 if match.group(5) else 0
        if channel == "stable" and prerelease:
            continue
        if channel == "beta" and not prerelease:
            continue
        tags.append(((int(match.group(1)), int(match.group(2)), int(match.group(3))), prerelease, tag))
    if not tags:
        raise STATE.StateError(f"No valid {channel} tag found in repository")
    tags.sort(key=lambda item: (item[0], item[1], item[2]))
    return tags[-1][2]


def toolkit_version(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?", value.strip())
    if not match:
        raise STATE.StateError(f"Invalid toolkit version: {value}")
    return tuple(int(part) for part in match.groups())


def source_install(args: argparse.Namespace) -> int:
    incomplete = TXN.incomplete_journals(STATE.state_dir())
    if incomplete:
        result = {
            "schema_version": 1, "scope": "user", "status": "blocked",
            "code": "transaction_recovery_required", "incomplete_transactions": len(incomplete),
            "next_action": "sdd transaction recover --scope user --apply",
        }
        emit(result, args.json)
        return 2
    url = validate_repository_url(args.repository_url)
    root = Path(args.source_root or (STATE.state_dir() / "user" / "kit")).expanduser().resolve(strict=False)
    if root.parent == root or root == Path.home():
        raise STATE.StateError("source root must be a dedicated directory")
    existing = root.exists()
    if existing and not (root / ".git").is_dir():
        raise STATE.StateError(f"source root exists but is not a Git checkout: {root}")
    if getattr(args, "offline", False):
        if not existing or not (root / "VERSION").is_file():
            result = {
                "schema_version": 1, "scope": "user", "mode": "apply" if args.apply else "preview",
                "status": "blocked", "code": "offline_cache_missing", "repository_url": url,
                "source_root": str(root), "cache_path": str(root), "writes_project": False,
            }
            emit(result, args.json)
            return 2
        validate_kit_root(root)
        result = {
            "schema_version": 1, "scope": "user", "mode": "apply" if args.apply else "preview",
            "status": "offline-ready", "action": "reuse-cache", "repository_url": url,
            "resolved_ref": git_command(["-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"], timeout=10).stdout.strip(),
            "version": (root / "VERSION").read_text(encoding="utf-8").strip(),
            "source_root": str(root), "cache_path": str(root), "writes_project": False,
        }
        emit(result, args.json)
        return 0
    ref = remote_ref(url, args.channel, args.ref)
    mode = "update" if existing else "clone"
    result: Dict[str, Any] = {
        "schema_version": 1, "scope": "user", "mode": "apply" if args.apply else "preview",
        "status": "ready", "action": mode, "repository_url": url, "channel": args.channel,
        "requested_ref": args.ref or "", "resolved_ref": ref, "source_root": str(root),
        "writes_project": False,
    }
    if not args.apply:
        emit(result, args.json)
        return 0
    if existing:
        dirty = git_command(["-C", str(root), "status", "--porcelain"], timeout=10).stdout.strip()
        if dirty:
            result["status"] = "blocked"
            result["code"] = "source_dirty"
            result["detail"] = "source checkout has local changes; update was not attempted"
            emit(result, args.json)
            return 2
    staging_parent = Path(tempfile.mkdtemp(prefix="sdd-source-", dir=str(root.parent)))
    staging = staging_parent / "kit"
    previous = root.with_name(f".{root.name}.previous")
    promoted = False
    try:
        git_command(["clone", "--depth", "1", "--branch", ref, url, str(staging)], timeout=120)
        validate_kit_root(staging)
        candidate_version = (staging / "VERSION").read_text(encoding="utf-8").strip()
        if existing and (root / "VERSION").is_file():
            current_version = (root / "VERSION").read_text(encoding="utf-8").strip()
            if toolkit_version(candidate_version) < toolkit_version(current_version) and not getattr(args, "allow_downgrade", False):
                result.update({
                    "status": "blocked",
                    "code": "downgrade_requires_confirmation",
                    "current_version": current_version,
                    "candidate_version": candidate_version,
                    "detail": "re-run with --allow-downgrade to accept a lower toolkit version",
                })
                emit(result, args.json)
                return 2
        if previous.exists():
            raise STATE.StateError(f"source backup already exists: {previous}")
        if existing:
            os.replace(root, previous)
        os.replace(staging, root)
        promoted = True
        commit = git_command(["-C", str(root), "rev-parse", "HEAD"], timeout=10).stdout.strip()
        source = {
            "schema_version": 1, "scope": "user", "source_type": "git",
            "repository_url": url, "channel": args.channel,
            "requested_ref": args.ref or args.channel, "resolved_ref": ref, "commit": commit,
            "source_root": str(root), "updated_at": STATE.utc_now(),
            "cache_path": str(root),
        }
        with STATE.RegistryLock(source_state_path().with_suffix(".json.lock")):
            STATE.atomic_write(source_state_path(), source, backup=True)
        if previous.exists() and not getattr(args, "keep_previous_source", False):
            shutil.rmtree(previous)
        result.update({"status": "updated" if existing else "cloned", "commit": commit})
    except (OSError, STATE.StateError) as exc:
        if previous.exists():
            if root.exists():
                shutil.rmtree(root, ignore_errors=True)
            os.replace(previous, root)
        elif promoted and root.exists():
            shutil.rmtree(root, ignore_errors=True)
        result["status"] = "rolled_back"
        result["error"] = str(exc)
        emit(result, args.json)
        return 2
    finally:
        if staging_parent.exists():
            shutil.rmtree(staging_parent, ignore_errors=True)
    emit(result, args.json)
    return 0


def source_status(args: argparse.Namespace) -> int:
    path = source_state_path()
    if not path.exists():
        result = {"schema_version": 1, "scope": "user", "status": "not-configured", "source_state": str(path)}
        emit(result, args.json)
        return 0
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise STATE.StateError(f"Cannot read source state {path}: {exc}") from exc
    root = Path(source.get("source_root", ""))
    result = dict(source)
    result["status"] = "healthy" if root.is_dir() and (root / "VERSION").is_file() else "missing"
    result["source_state"] = str(path)
    emit(result, args.json)
    return 2 if result["status"] == "missing" else 0


def transaction_status(args: argparse.Namespace) -> int:
    transactions = TXN.list_journals(STATE.state_dir())
    incomplete = [item for item in transactions if item["status"] not in TXN.TERMINAL_STATUSES]
    result = {
        "schema_version": 1,
        "scope": "user",
        "status": "recovery-required" if incomplete else "healthy",
        "incomplete": len(incomplete),
        "transactions": incomplete if args.active_only else transactions,
        "read_only": True,
    }
    emit(redact_paths(result) if args.redact_paths else result, args.json)
    return 2 if incomplete else 0


def transaction_recover(args: argparse.Namespace) -> int:
    with TXN.OperationLock(STATE.state_dir()):
        result = TXN.recover_transactions(STATE.state_dir(), plan_id=args.plan_id, apply=args.apply)
    emit(redact_paths(result) if args.redact_paths else result, args.json)
    return 2 if result["status"] in {"blocked", "not-found"} else 0


def install_user(args: argparse.Namespace) -> int:
    if args.scope != "user":
        result = {
            "schema_version": 1,
            "status": "blocked",
            "scope": args.scope,
            "detail": "organization installation requires a managed provider and approved publication target; use the organization workflow when enabled",
        }
        emit(result, args.json)
        return 2
    kit = Path(args.kit_root or ROOT).expanduser().resolve(strict=False)
    if not kit.is_dir() or not (kit / "VERSION").is_file():
        raise STATE.StateError(f"Toolkit root is invalid: {kit}")
    profile = profile_path_arg(args.profile_root or str(Path.home()))
    discovery = None
    selected_runtime = args.runtime
    if args.runtime == "detected":
        try:
            discovery = DISCOVERY.discover_runtimes(profile, kit, "all", "quick")
        except ValueError as exc:
            raise STATE.StateError(str(exc)) from exc
        detected = [target for target, record in discovery["runtimes"].items() if record["integration_ready"]]
        selected_runtime = ",".join(detected) if detected else ""
    sources = user_install_sources(kit, selected_runtime, profile) if selected_runtime else []
    previous = load_user_installation()
    previous_by_path = {
        item.get("path"): item
        for item in previous.get("managed_files", [])
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    files: List[Dict[str, Any]] = []
    conflicts: List[str] = []
    for item in sources:
        source = Path(item["source"])
        target = STATE.safe_lexical_path(profile, item["relative"], "User installation target")
        source_hash = STATE.sha256_file(source)
        old = previous_by_path.get(item["relative"])
        if not target.exists():
            action = "create"
        elif target.is_symlink() or not target.is_file():
            action = "conflict"
        elif old and old.get("sha256") == STATE.sha256_file(target):
            action = "update"
        elif STATE.sha256_file(target) == source_hash:
            action = "preserve"
        else:
            action = "conflict"
        if action == "conflict":
            conflicts.append(item["relative"])
        files.append({
            "runtime": item["runtime"],
            "runtimes": item["runtimes"],
            "path": item["relative"],
            "sha256": source_hash,
            "action": action,
        })
    state_path = user_installation_path()
    managed = [
        {"path": item["path"], "runtime": item["runtime"], "runtimes": item["runtimes"], "sha256": item["sha256"], "owner": "sdd-toolkit"}
        for item in files
        if item["action"] != "preserve"
    ]
    preserved = [
        {"path": item["path"], "runtime": item["runtime"], "runtimes": item["runtimes"], "sha256": item["sha256"], "owner": "sdd-toolkit"}
        for item in files
        if item["action"] == "preserve"
    ]
    current_paths = {item["path"] for item in files}
    retained_previous = [
        item for item in previous.get("managed_files", [])
        if isinstance(item, dict) and item.get("path") not in current_paths
    ]
    source_metadata = local_source_metadata(kit)
    source_record_path = source_state_path()
    if source_record_path.is_file():
        try:
            candidate_source = json.loads(source_record_path.read_text(encoding="utf-8"))
            if candidate_source.get("source_root") == str(kit):
                source_metadata = candidate_source
        except (OSError, json.JSONDecodeError):
            pass
    proposed_state = {
        "schema_version": 2,
        "scope": "user",
        "profile_root": str(profile),
        "kit_root": str(kit),
        "toolkit_version": (kit / "VERSION").read_text(encoding="utf-8").strip(),
        "updated_at": STATE.utc_now(),
        "managed_files": retained_previous + managed + preserved,
        "source": source_metadata,
    }
    for metadata_field in ("cli", "path_integration"):
        if metadata_field in previous:
            proposed_state[metadata_field] = previous[metadata_field]
    cli_install: Optional[Dict[str, Any]] = None
    path_install: Optional[Dict[str, Any]] = None
    if getattr(args, "with_cli", False):
        install_root = Path(args.install_root).expanduser().resolve(strict=False) if args.install_root else (
            STATE.state_dir().parent / "sdd-toolkit-data"
        ).resolve(strict=False)
        if install_root.parent == install_root or install_root == Path.home():
            conflicts.append("unsafe-install-root")
        bin_dir = Path(args.bin_dir).expanduser().resolve(strict=False) if getattr(args, "bin_dir", "") else install_root / "bin"
        if bin_dir.parent == bin_dir or bin_dir == Path.home():
            conflicts.append("unsafe-bin-dir")
        shim_path = bin_dir / ("sdd.cmd" if os.name == "nt" else "sdd")
        cli_script = kit / "scripts" / "sdd.py"
        if os.name == "nt":
            shim_content = f'@echo off\r\n"{sys.executable}" "{cli_script}" %*\r\n'.encode("utf-8")
        else:
            shim_content = f'#!/usr/bin/env bash\nexec {shlex.quote(sys.executable)} {shlex.quote(str(cli_script))} "$@"\n'.encode("utf-8")
        shim_hash = TXN.sha256_bytes(shim_content)
        previous_cli = previous.get("cli") if isinstance(previous.get("cli"), dict) else None
        if shim_path.exists() and (
            shim_path.is_symlink() or not shim_path.is_file()
            or not previous_cli or previous_cli.get("path") != str(shim_path)
            or previous_cli.get("sha256") != STATE.sha256_file(shim_path)
        ):
            conflicts.append(str(shim_path))
        else:
            cli_install = {
                "path": shim_path,
                "content": shim_content,
                "action": {
                    "id": "shim",
                    "kind": "shim",
                    "operation": "update" if shim_path.is_file() else "create",
                    "target": str(shim_path),
                    "before_sha256": STATE.sha256_file(shim_path) if shim_path.is_file() else None,
                    "after_sha256": shim_hash,
                    "owner": "sdd-toolkit",
                },
            }
            proposed_state["cli"] = {
                "path": str(shim_path), "sha256": shim_hash, "owner": "sdd-toolkit", "registered_at": STATE.utc_now(),
            }
        if getattr(args, "no_path", False):
            proposed_state["path_integration"] = {
                "strategy": "none", "entry": str(bin_dir), "target": "none",
                "marker": "sdd-toolkit", "updated_at": STATE.utc_now(),
            }
        elif os.name == "nt":
            present = TXN.windows_path_entry_present(str(bin_dir))
            previous_path = previous.get("path_integration") if isinstance(previous.get("path_integration"), dict) else None
            owned = bool(previous_path and previous_path.get("strategy") == "windows-user-env" and previous_path.get("entry") == str(bin_dir))
            if present and not owned:
                proposed_state["path_integration"] = {
                    "strategy": "none", "entry": str(bin_dir), "target": "none",
                    "marker": "sdd-toolkit", "updated_at": STATE.utc_now(),
                }
            else:
                if not present:
                    path_install = {
                        "action": {
                            "id": "path", "kind": "path", "operation": "create", "target": "windows-user-env",
                            "before_sha256": None, "after_sha256": None, "owner": "sdd-toolkit",
                            "strategy": "windows-user-env", "entry": str(bin_dir),
                            "before_present": False, "after_present": True,
                        }
                    }
                proposed_state["path_integration"] = {
                    "strategy": "windows-user-env", "entry": str(bin_dir), "target": "windows-user-env",
                    "marker": "sdd-toolkit", "updated_at": STATE.utc_now(),
                }
        else:
            shell_name = Path(os.environ.get("SHELL", "sh")).name
            profile_file = profile / (".bashrc" if shell_name == "bash" else ".zshrc" if shell_name == "zsh" else ".profile")
            original = profile_file.read_text(encoding="utf-8") if profile_file.is_file() and not profile_file.is_symlink() else ""
            marker_start = "# >>> sdd-toolkit PATH >>>"
            marker_end = "# <<< sdd-toolkit PATH <<<"
            expected_line = f'export PATH="{bin_dir}:$PATH"'
            previous_path = previous.get("path_integration") if isinstance(previous.get("path_integration"), dict) else None
            owned = bool(previous_path and previous_path.get("strategy") == "unix-profile-block" and previous_path.get("target") == str(profile_file))
            if marker_start in original or marker_end in original:
                if marker_start not in original or marker_end not in original or expected_line not in original or not owned:
                    conflicts.append(str(profile_file))
            else:
                updated_profile = original.rstrip("\n") + ("\n" if original else "") + f"{marker_start}\n{expected_line}\n{marker_end}\n"
                path_install = {
                    "content": updated_profile.encode("utf-8"),
                    "action": {
                        "id": "path", "kind": "path", "operation": "update" if profile_file.is_file() else "create",
                        "target": str(profile_file),
                        "before_sha256": STATE.sha256_file(profile_file) if profile_file.is_file() else None,
                        "after_sha256": TXN.sha256_bytes(updated_profile.encode("utf-8")), "owner": "sdd-toolkit",
                        "strategy": "unix-profile-block", "entry": str(bin_dir),
                    },
                }
            proposed_state["path_integration"] = {
                "strategy": "unix-profile-block", "entry": str(bin_dir), "target": str(profile_file),
                "marker": "sdd-toolkit", "updated_at": STATE.utc_now(),
            }
    transaction_actions: List[Dict[str, Any]] = []
    action_ids: Dict[str, str] = {}
    for index, item in enumerate(files):
        if item["action"] == "preserve":
            continue
        target = STATE.safe_lexical_path(profile, item["path"], "User installation target")
        action_id = f"asset-{index:04d}"
        action_ids[item["path"]] = action_id
        transaction_actions.append({
            "id": action_id,
            "kind": "asset",
            "operation": item["action"],
            "target": str(target),
            "before_sha256": STATE.sha256_file(target) if target.is_file() and not target.is_symlink() else None,
            "after_sha256": item["sha256"],
            "owner": "sdd-toolkit",
        })
    transaction_actions.append({
        "id": "manifest",
        "kind": "manifest",
        "operation": "update" if state_path.is_file() else "create",
        "target": str(state_path),
        "before_sha256": STATE.sha256_file(state_path) if state_path.is_file() else None,
        "after_sha256": TXN.sha256_bytes(TXN.json_document_bytes(proposed_state)),
        "owner": "sdd-toolkit",
    })
    if cli_install is not None:
        transaction_actions.append(cli_install["action"])
        allowed_cli_root = cli_install["path"].parent
    else:
        allowed_cli_root = None
    if path_install is not None:
        transaction_actions.append(path_install["action"])
    allowed_roots = [state_path.parent]
    for runtime in {runtime for item in files for runtime in item["runtimes"]}:
        adapter = RUNTIME.load_adapters(kit).get(runtime)
        if adapter is not None:
            allowed_roots.append(profile / adapter.user_profile)
            allowed_roots.append(profile / adapter.skill_dir)
    if allowed_cli_root is not None:
        allowed_roots.append(allowed_cli_root)
    if path_install is not None and path_install["action"].get("strategy") == "unix-profile-block":
        allowed_roots.append(Path(path_install["action"]["target"]).parent)
    plan = TXN.build_plan(
        "update" if state_path.exists() else "install",
        profile,
        transaction_actions,
        allowed_roots,
        {"runtime": args.runtime, "selected_runtimes": selected_runtime.split(",") if selected_runtime else [], "toolkit_version": proposed_state["toolkit_version"]},
    )
    requested_plan_id = getattr(args, "plan_id", "")
    if requested_plan_id and requested_plan_id != plan["plan_id"]:
        conflicts.append("transaction-plan-drift")
    incomplete = TXN.incomplete_journals(STATE.state_dir())
    if incomplete:
        conflicts.append("transaction-recovery-required")
    report: Dict[str, Any] = {
        "schema_version": 1,
        "mode": "apply" if args.apply else "preview",
        "status": "blocked" if conflicts else "ready",
        "scope": "user",
        "runtime": args.runtime,
        "selected_runtimes": selected_runtime.split(",") if selected_runtime else [],
        "discovery": discovery,
        "profile_root": str(profile),
        "state_path": str(user_installation_path()),
        "files": files,
        "conflicts": conflicts,
        "writes_project": False,
        "plan_id": plan["plan_id"],
        "transaction_status": "recovery-required" if incomplete else "ready",
    }
    if args.apply and not conflicts:
        with TXN.OperationLock(STATE.state_dir()):
            transaction = TXN.Transaction.start(STATE.state_dir(), plan)
            try:
                transaction.phase("staged")
                TXN.fault("after-staged")
                TXN.fault("before-assets")
                for item in files:
                    if item["action"] == "preserve":
                        continue
                    source = next(Path(candidate["source"]) for candidate in sources if candidate["relative"] == item["path"])
                    target = STATE.safe_lexical_path(profile, item["path"], "User installation target")
                    transaction.track_file(action_ids[item["path"]])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                transaction.phase("assets")
                TXN.fault("after-assets")
                if cli_install is not None:
                    transaction.track_file("shim")
                    cli_install["path"].parent.mkdir(parents=True, exist_ok=True)
                    cli_install["path"].write_bytes(cli_install["content"])
                    if os.name != "nt":
                        os.chmod(cli_install["path"], 0o755)
                transaction.phase("shim")
                TXN.fault("after-shim")
                if path_install is not None:
                    if path_install["action"].get("strategy") == "windows-user-env":
                        transaction.track_windows_path("path")
                        TXN.set_windows_path_entry(path_install["action"]["entry"], True)
                    else:
                        transaction.track_file("path")
                        path_target = Path(path_install["action"]["target"])
                        path_target.parent.mkdir(parents=True, exist_ok=True)
                        path_target.write_bytes(path_install["content"])
                transaction.phase("path")
                TXN.fault("after-path")
                transaction.track_file("manifest")
                TXN.fault("before-manifest")
                STATE.atomic_write(state_path, proposed_state, backup=True)
                transaction.phase("manifest")
                TXN.fault("after-manifest")
                for item in transaction_actions:
                    if item.get("strategy") == "windows-user-env":
                        if TXN.windows_path_entry_present(item["entry"]) != item["after_present"]:
                            raise TXN.TransactionError("Windows PATH smoke check failed")
                        continue
                    if item["after_sha256"] is None:
                        continue
                    target = Path(item["target"])
                    if not target.is_file() or target.is_symlink() or STATE.sha256_file(target) != item["after_sha256"]:
                        raise TXN.TransactionError(f"Transaction smoke check failed: {target}")
                transaction.phase("verified")
                TXN.fault("after-verified")
                transaction.commit()
                report["status"] = "installed"
                report["transaction_status"] = "committed"
            except (OSError, STATE.StateError, TXN.TransactionError) as exc:
                recovery = transaction.rollback()
                report["status"] = "rolled_back" if recovery["status"] == "rolled_back" else "rollback-blocked"
                report["transaction_status"] = recovery["status"]
                report["error"] = str(exc)
                report["recovery"] = recovery
                emit(report, args.json)
                return 2
    emit(report, args.json)
    return 2 if report["status"] == "blocked" else 0


def detect_harnesses(profile: Path, kit_root: Optional[Path] = None, runtime: str = "all", mode: str = "full") -> Dict[str, Any]:
    """Compatibility view over the versioned, evidence-based discovery service."""
    root = kit_root if kit_root and kit_root.is_dir() else ROOT
    try:
        return DISCOVERY.discover_runtimes(profile, root, runtime, mode)["runtimes"]
    except ValueError as exc:
        raise STATE.StateError(str(exc)) from exc


def runtime_detect(args: argparse.Namespace) -> int:
    profile = profile_path_arg(args.profile_root or Path.home())
    try:
        result = DISCOVERY.discover_runtimes(
            profile,
            ROOT,
            args.runtime,
            args.mode,
            [Path(value) for value in args.extensions_dir],
            [Path(value) for value in args.portable_root],
            args.cache,
        )
    except ValueError as exc:
        raise STATE.StateError(str(exc)) from exc
    emit(redact_paths(result) if args.redact_paths else result, args.json)
    return 0


def runtime_inspect(args: argparse.Namespace) -> int:
    try:
        adapters = RUNTIME.load_adapters(ROOT)
        requested = getattr(args, "runtime", "")
        selected = [RUNTIME.canonical_runtime(requested, adapters)] if requested else list(adapters)
    except ValueError as exc:
        raise STATE.StateError(str(exc)) from exc
    result = {
        "schema_version": 1,
        "status": "ready",
        "runtimes": [
            {
                "target": adapters[target].target,
                "adapter_schema_version": adapters[target].adapter_schema_version,
                "min_version": adapters[target].min_version,
                "aliases": list(adapters[target].aliases),
                "commands": list(adapters[target].commands),
                "version_args": list(adapters[target].version_args),
                "scopes": list(adapters[target].scopes),
                "capabilities": list(adapters[target].capabilities),
                "project_agent_dir": adapters[target].project_agent_dir,
                "user_agent_dir": adapters[target].user_agent_dir,
                "skill_dir": adapters[target].skill_dir,
                "output_dir": adapters[target].output_dir,
                "renderer": adapters[target].renderer,
                "section": adapters[target].section,
            }
            for target in selected
        ],
        "read_only": True,
    }
    emit(result, args.json)
    return 0


def delivery_inspect(args: argparse.Namespace) -> int:
    """Expose the deterministic delivery contract for agents and tooling."""
    try:
        if args.delivery_command == "propose":
            result = DELIVERY.validate(DELIVERY.propose(args.type, args.description))
        elif args.task:
            result = DELIVERY.extract_task_contract(args.task)
        else:
            result = DELIVERY.validate(json.loads(Path(args.file).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise STATE.StateError(str(exc)) from exc
    emit(result, args.json)
    return 0


def architecture_inspect(args: argparse.Namespace) -> int:
    """Expose the deterministic architectural contract for agents and tooling."""
    try:
        if args.architecture_command == "propose":
            result = ARCHITECTURE.validate(
                ARCHITECTURE.propose(args.type, args.description, args.delivery_kind)
            )
        elif args.task:
            result = ARCHITECTURE.extract_task_contract(args.task)
        else:
            result = ARCHITECTURE.validate(json.loads(Path(args.file).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise STATE.StateError(str(exc)) from exc
    emit(result, args.json)
    return 0


def redact_paths(value: Any) -> Any:
    sensitive_keys = {
        "path", "project_path", "profile_root", "kit_root", "state_path", "source_state",
        "source_root", "workspace", "spec_path", "activation_state", "executable", "entry", "target", "agents", "skills",
    }
    if isinstance(value, dict):
        return {key: ("<redacted>" if key in sensitive_keys and isinstance(item, str) else redact_paths(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_paths(item) for item in value]
    return value


def user_doctor(args: argparse.Namespace) -> int:
    state_path = user_installation_path()
    issues: List[Dict[str, str]] = []
    if not state_path.exists():
        try:
            incomplete = TXN.incomplete_journals(STATE.state_dir())
        except TXN.TransactionError as exc:
            incomplete = []
            issues.append({"severity": "error", "code": "transaction_journal_invalid", "detail": str(exc)})
        if incomplete:
            issues.append({
                "severity": "error", "code": "transaction_recovery_required",
                "detail": f"{len(incomplete)} incomplete transaction(s)",
            })
        result = {
            "schema_version": 1, "scope": "user", "status": "blocked" if issues else "uninstalled",
            "state_path": str(state_path), "issues": issues,
            "incomplete_transactions": len(incomplete),
            "harnesses": detect_harnesses(Path(args.profile_root or Path.home()), ROOT, getattr(args, "runtime", "all"), getattr(args, "discovery_mode", "full")),
        }
        emit(redact_paths(result) if args.redact_paths else result, args.json)
        return 2 if issues else 0
    state = load_user_installation()
    profile = profile_path_arg(args.profile_root or state.get("profile_root", str(Path.home())))
    kit = Path(state.get("kit_root", "")).expanduser().resolve(strict=False)
    if not kit.is_dir() or not (kit / "VERSION").is_file():
        issues.append({"severity": "error", "code": "kit_missing", "detail": str(kit)})
    if not profile.is_dir():
        issues.append({"severity": "error", "code": "profile_missing", "detail": str(profile)})
    files: List[Dict[str, Any]] = []
    for item in state.get("managed_files", []):
        relative = item.get("path") if isinstance(item, dict) else None
        if not isinstance(relative, str):
            issues.append({"severity": "error", "code": "manifest_invalid_path", "detail": "managed_files"})
            continue
        try:
            target = STATE.safe_lexical_path(profile, relative, "User installation target")
        except STATE.StateError as exc:
            issues.append({"severity": "error", "code": "unsafe_target", "detail": str(exc)})
            continue
        expected = item.get("sha256")
        if target.is_symlink():
            status = "symlink"
            issues.append({"severity": "error", "code": "target_symlink", "detail": relative})
        elif not target.exists():
            status = "missing"
            issues.append({"severity": "error", "code": "asset_missing", "detail": relative})
        elif not target.is_file():
            status = "not-file"
            issues.append({"severity": "error", "code": "target_not_file", "detail": relative})
        else:
            actual = STATE.sha256_file(target)
            status = "healthy" if actual == expected else "modified"
            if status == "modified":
                issues.append({"severity": "warning", "code": "asset_modified", "detail": relative})
        files.append({"path": relative, "runtime": item.get("runtime"), "status": status})
    cli = state.get("cli")
    if isinstance(cli, dict) and isinstance(cli.get("path"), str):
        shim = Path(cli["path"])
        if shim.is_symlink() or not shim.is_file():
            issues.append({"severity": "error", "code": "cli_shim_missing", "detail": str(shim)})
            files.append({"path": str(shim), "status": "missing"})
        elif cli.get("owner") != "sdd-toolkit" or STATE.sha256_file(shim) != cli.get("sha256"):
            issues.append({"severity": "warning", "code": "cli_shim_modified", "detail": str(shim)})
            files.append({"path": str(shim), "status": "modified"})
        else:
            files.append({"path": str(shim), "status": "healthy"})
    path_integration = state.get("path_integration")
    if isinstance(path_integration, dict):
        strategy = path_integration.get("strategy")
        entry = path_integration.get("entry")
        target = path_integration.get("target")
        if not isinstance(entry, str) or not entry:
            issues.append({"severity": "error", "code": "path_record_invalid", "detail": "path_integration.entry"})
        elif strategy == "unix-profile-block":
            profile_file = Path(target) if isinstance(target, str) else None
            if profile_file is None or not profile_file.is_file():
                issues.append({"severity": "warning", "code": "path_profile_missing", "detail": "PATH profile"})
            else:
                profile_text = profile_file.read_text(encoding="utf-8")
                marker_count = profile_text.count("# >>> sdd-toolkit PATH >>>")
                expected = f'export PATH="{entry}:$PATH"'
                if marker_count != 1 or expected not in profile_text:
                    issues.append({"severity": "warning", "code": "path_block_modified", "detail": "PATH profile block"})
        elif strategy == "windows-user-env":
            if os.name != "nt":
                issues.append({"severity": "warning", "code": "path_platform_mismatch", "detail": "windows-user-env"})
            else:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ) as key:
                    try:
                        current, _ = winreg.QueryValueEx(key, "Path")
                    except FileNotFoundError:
                        current = ""
                values = [item for item in str(current).split(";") if item]
                normalized = entry.rstrip("\\/").casefold()
                count = sum(item.rstrip("\\/").casefold() == normalized for item in values)
                if count == 0:
                    issues.append({"severity": "warning", "code": "path_entry_missing", "detail": "user PATH"})
                elif count > 1:
                    issues.append({"severity": "warning", "code": "path_entry_duplicated", "detail": "user PATH"})
        elif strategy != "none":
            issues.append({"severity": "error", "code": "path_strategy_unsupported", "detail": str(strategy)})
    try:
        incomplete_transactions = TXN.incomplete_journals(STATE.state_dir())
    except TXN.TransactionError as exc:
        incomplete_transactions = []
        issues.append({"severity": "error", "code": "transaction_journal_invalid", "detail": str(exc)})
    if incomplete_transactions:
        issues.append({
            "severity": "error", "code": "transaction_recovery_required",
            "detail": f"{len(incomplete_transactions)} incomplete transaction(s)",
        })
    harnesses = detect_harnesses(profile, kit, getattr(args, "runtime", "all"), getattr(args, "discovery_mode", "full"))
    status = "blocked" if any(item["severity"] == "error" for item in issues) else ("warning" if issues else "healthy")
    result = {
        "schema_version": 1,
        "scope": "user",
        "status": status,
        "state_path": str(state_path),
        "profile_root": str(profile),
        "kit_root": str(kit),
        "toolkit_version": state.get("toolkit_version"),
        "files": files,
        "harnesses": harnesses,
        "issues": issues,
        "incomplete_transactions": len(incomplete_transactions),
        "read_only": True,
    }
    emit(redact_paths(result) if args.redact_paths else result, args.json)
    return 2 if status == "blocked" else 0


def user_update(args: argparse.Namespace) -> int:
    incomplete = TXN.incomplete_journals(STATE.state_dir())
    if incomplete:
        result = {
            "schema_version": 1, "scope": "user", "status": "blocked",
            "code": "transaction_recovery_required", "incomplete_transactions": len(incomplete),
            "next_action": "sdd transaction recover --scope user --apply",
        }
        emit(result, args.json)
        return 2
    if not user_installation_path().exists():
        result = {"schema_version": 1, "scope": "user", "status": "blocked", "code": "user_installation_missing", "detail": "run install --scope user first"}
        emit(result, args.json)
        return 2
    state = load_user_installation()
    previous_source_state: Optional[bytes] = None
    if getattr(args, "repository_url", ""):
        source_root = Path(args.source_root or (STATE.state_dir() / "user" / "kit")).expanduser().resolve(strict=False)
        previous_source = source_root.with_name(f".{source_root.name}.previous")
        if source_state_path().is_file():
            previous_source_state = source_state_path().read_bytes()
        args.keep_previous_source = True
        source_result = source_install(args)
        if source_result != 0 or not args.apply:
            return source_result
        source = json.loads(source_state_path().read_text(encoding="utf-8"))
        args.kit_root = source["source_root"]
    args.profile_root = args.profile_root or state.get("profile_root", str(Path.home()))
    args.kit_root = args.kit_root or state.get("kit_root", str(ROOT))
    result = install_user(args)
    if getattr(args, "repository_url", "") and previous_source.exists():
        if result == 0:
            shutil.rmtree(previous_source)
        else:
            current_source = Path(args.kit_root)
            if current_source.exists():
                shutil.rmtree(current_source, ignore_errors=True)
            os.replace(previous_source, current_source)
            if previous_source_state is None:
                source_state_path().unlink(missing_ok=True)
            else:
                source_state_path().write_bytes(previous_source_state)
    return result


def remove_user_path_integration(record: Dict[str, Any]) -> str:
    strategy = record.get("strategy")
    entry = record.get("entry")
    target = record.get("target")
    if strategy in {None, "none"}:
        return "none"
    if not isinstance(entry, str) or not entry:
        raise STATE.StateError("user PATH record is incomplete")
    if strategy == "unix-profile-block":
        profile = Path(target) if isinstance(target, str) and target != "none" else None
        if profile is None or not profile.exists():
            return "missing"
        original = profile.read_text(encoding="utf-8")
        marker_start = "# >>> sdd-toolkit PATH >>>"
        marker_end = "# <<< sdd-toolkit PATH <<<"
        start = original.find(marker_start)
        end = original.find(marker_end, start if start >= 0 else 0)
        if start < 0 or end < 0:
            return "missing"
        end += len(marker_end)
        block = original[start:end]
        expected = f'export PATH="{entry}:$PATH"'
        if expected not in block:
            raise STATE.StateError(f"user shell profile block was modified: {profile}")
        replacement = original[:start].rstrip("\n") + original[end:]
        profile.write_text(replacement.lstrip("\n") + ("\n" if replacement else ""), encoding="utf-8")
        return "removed"
    if strategy == "windows-user-env":
        if os.name != "nt":
            return "unsupported"
        import winreg
        key_path = r"Environment"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            try:
                current, kind = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                return "missing"
            values = [value for value in str(current).split(";") if value]
            normalized = entry.rstrip("\\/").casefold()
            updated = [value for value in values if value.rstrip("\\/").casefold() != normalized]
            if updated == values:
                return "missing"
            winreg.SetValueEx(key, "Path", 0, kind, ";".join(updated))
            return "removed"
    raise STATE.StateError(f"unsupported PATH integration strategy: {strategy}")


def plan_user_path_removal(record: Dict[str, Any]) -> Dict[str, Any]:
    strategy = record.get("strategy")
    entry = record.get("entry")
    target = record.get("target")
    if strategy in {None, "none"}:
        return {"status": "none", "action": None}
    if not isinstance(entry, str) or not entry:
        raise STATE.StateError("user PATH record is incomplete")
    if strategy == "unix-profile-block":
        profile_file = Path(target) if isinstance(target, str) and target != "none" else None
        if profile_file is None or not profile_file.exists():
            return {"status": "missing", "action": None}
        if profile_file.is_symlink() or not profile_file.is_file():
            raise STATE.StateError(f"user shell profile is unsafe: {profile_file}")
        original = profile_file.read_text(encoding="utf-8")
        marker_start = "# >>> sdd-toolkit PATH >>>"
        marker_end = "# <<< sdd-toolkit PATH <<<"
        start = original.find(marker_start)
        end = original.find(marker_end, start if start >= 0 else 0)
        if start < 0 or end < 0:
            return {"status": "missing", "action": None}
        end += len(marker_end)
        block = original[start:end]
        expected = f'export PATH="{entry}:$PATH"'
        if expected not in block:
            raise STATE.StateError(f"user shell profile block was modified: {profile_file}")
        replacement = original[:start].rstrip("\n") + original[end:]
        updated = replacement.lstrip("\n") + ("\n" if replacement else "")
        return {
            "status": "remove",
            "content": updated,
            "action": {
                "id": "path",
                "kind": "path",
                "operation": "update",
                "target": str(profile_file.resolve(strict=False)),
                "before_sha256": STATE.sha256_file(profile_file),
                "after_sha256": TXN.sha256_bytes(updated.encode("utf-8")),
                "owner": "sdd-toolkit",
                "strategy": "unix-profile-block",
                "entry": entry,
            },
        }
    if strategy == "windows-user-env":
        if os.name != "nt":
            return {"status": "unsupported", "action": None}
        present = TXN.windows_path_entry_present(entry)
        if not present:
            return {"status": "missing", "action": None}
        return {
            "status": "remove",
            "action": {
                "id": "path",
                "kind": "path",
                "operation": "remove",
                "target": "windows-user-env",
                "before_sha256": None,
                "after_sha256": None,
                "owner": "sdd-toolkit",
                "strategy": "windows-user-env",
                "entry": entry,
                "before_present": True,
                "after_present": False,
            },
        }
    raise STATE.StateError(f"unsupported PATH integration strategy: {strategy}")


def user_uninstall(args: argparse.Namespace) -> int:
    state_path = user_installation_path()
    if not state_path.exists():
        incomplete = TXN.incomplete_journals(STATE.state_dir())
        result = {
            "schema_version": 1, "scope": "user",
            "status": "blocked" if incomplete else "uninstalled",
            "state_path": str(state_path), "files": [],
            "conflicts": ["transaction-recovery-required"] if incomplete else [],
            "incomplete_transactions": len(incomplete),
        }
        emit(result, args.json)
        return 2 if incomplete else 0
    state = load_user_installation()
    profile = profile_path_arg(args.profile_root or state.get("profile_root", str(Path.home())))
    kit = Path(state.get("kit_root", ROOT)).expanduser().resolve(strict=False)
    adapters = RUNTIME.load_adapters(kit if kit.is_dir() else ROOT)
    try:
        selected_runtimes = set(RUNTIME.selected_runtimes(getattr(args, "runtime", "all"), adapters))
    except ValueError as exc:
        raise STATE.StateError(str(exc)) from exc
    full_uninstall = getattr(args, "runtime", "all") == "all"
    files: List[Dict[str, Any]] = []
    conflicts: List[str] = []
    removable: List[tuple[Path, Dict[str, Any]]] = []
    retained_records: List[Dict[str, Any]] = []
    for item in state.get("managed_files", []):
        relative = item.get("path") if isinstance(item, dict) else None
        if not isinstance(relative, str):
            conflicts.append(str(relative))
            continue
        try:
            target = STATE.safe_lexical_path(profile, relative, "User uninstall target")
        except STATE.StateError:
            conflicts.append(relative)
            files.append({"path": relative, "action": "preserve"})
            continue
        item_runtimes = set(item.get("runtimes") or ([item.get("runtime")] if item.get("runtime") else []))
        affected = item_runtimes & selected_runtimes
        if not affected:
            retained_records.append(dict(item))
            files.append({"path": relative, "runtime": item.get("runtime"), "runtimes": sorted(item_runtimes), "action": "retain"})
            continue
        remaining_runtimes = sorted(item_runtimes - affected)
        if remaining_runtimes and relative.replace("\\", "/").startswith(".agents/skills"):
            retained = dict(item)
            retained["runtimes"] = remaining_runtimes
            retained["runtime"] = remaining_runtimes[0]
            retained_records.append(retained)
            files.append({"path": relative, "runtime": retained["runtime"], "runtimes": remaining_runtimes, "action": "retain-other-runtime"})
            continue
        if not target.exists():
            action = "missing"
        elif target.is_symlink() or not target.is_file():
            action = "preserve"
            conflicts.append(relative)
        elif item.get("owner") != "sdd-toolkit" or STATE.sha256_file(target) != item.get("sha256"):
            action = "preserve"
            conflicts.append(relative)
        else:
            action = "remove"
            removable.append((target, item))
        files.append({"path": relative, "runtime": item.get("runtime"), "runtimes": sorted(item_runtimes), "action": action})
    cli = state.get("cli")
    if full_uninstall and isinstance(cli, dict) and isinstance(cli.get("path"), str):
        shim = Path(cli["path"])
        if shim.is_file() and not shim.is_symlink() and cli.get("owner") == "sdd-toolkit" and STATE.sha256_file(shim) == cli.get("sha256"):
            removable.append((shim, {"path": str(shim), "kind": "cli"}))
            files.append({"path": str(shim), "action": "remove"})
        elif shim.exists():
            conflicts.append(str(shim))
            files.append({"path": str(shim), "action": "preserve"})
    if full_uninstall:
        path_record = state.get("path_integration", {"strategy": "none"})
        try:
            path_plan = plan_user_path_removal(path_record if isinstance(path_record, dict) else {"strategy": "invalid"})
        except STATE.StateError as exc:
            path_plan = {"status": "conflict", "action": None, "detail": str(exc)}
            conflicts.append("path-integration")
        if path_plan["status"] == "unsupported":
            conflicts.append("path-integration-platform")
    else:
        path_plan = {"status": "keep", "action": None}
    remaining = retained_records + [
        item for item in state.get("managed_files", [])
        if isinstance(item, dict) and item.get("path") in conflicts
    ]
    cli_preserved = not full_uninstall or (isinstance(cli, dict) and any(
        item.get("path") == str(cli.get("path")) for item in files if item.get("action") == "preserve"
    ))
    proposed_state = dict(state)
    proposed_state["managed_files"] = remaining
    proposed_state["updated_at"] = STATE.utc_now()
    if not cli_preserved:
        proposed_state.pop("cli", None)
    if path_plan["status"] in {"none", "missing", "remove"}:
        proposed_state.pop("path_integration", None)
    keep_state = bool(remaining or cli_preserved or path_plan["status"] in {"conflict", "unsupported"})
    transaction_actions: List[Dict[str, Any]] = []
    removable_ids: Dict[str, str] = {}
    for index, (target, item) in enumerate(removable):
        action_id = f"remove-{index:04d}"
        removable_ids[str(target)] = action_id
        transaction_actions.append({
            "id": action_id,
            "kind": "shim" if item.get("kind") == "cli" else "asset",
            "operation": "remove",
            "target": str(target.resolve(strict=False)),
            "before_sha256": STATE.sha256_file(target),
            "after_sha256": None,
            "owner": "sdd-toolkit",
        })
    if path_plan.get("action"):
        transaction_actions.append(path_plan["action"])
    transaction_actions.append({
        "id": "manifest",
        "kind": "manifest",
        "operation": "update" if keep_state else "remove",
        "target": str(state_path),
        "before_sha256": STATE.sha256_file(state_path),
        "after_sha256": TXN.sha256_bytes(TXN.json_document_bytes(proposed_state)) if keep_state else None,
        "owner": "sdd-toolkit",
    })
    allowed_roots = [state_path.parent, *[target.parent for target, _ in removable]]
    if path_plan.get("action") and path_plan["action"].get("strategy") == "unix-profile-block":
        allowed_roots.append(Path(path_plan["action"]["target"]).parent)
    plan = TXN.build_plan("uninstall", profile, transaction_actions, allowed_roots, {"preserves_projects_and_specs": True})
    requested_plan_id = getattr(args, "plan_id", "")
    if requested_plan_id and requested_plan_id != plan["plan_id"]:
        conflicts.append("transaction-plan-drift")
    incomplete = TXN.incomplete_journals(STATE.state_dir())
    if incomplete:
        conflicts.append("transaction-recovery-required")
    report: Dict[str, Any] = {
        "schema_version": 2,
        "mode": "apply" if args.apply else "preview",
        "scope": "user",
        "status": "blocked" if conflicts and args.apply else ("warning" if conflicts else "ready"),
        "profile_root": str(profile),
        "state_path": str(state_path),
        "files": files,
        "conflicts": conflicts,
        "preserves_projects_and_specs": True,
        "plan_id": plan["plan_id"],
        "transaction_status": "recovery-required" if incomplete else "ready",
    }
    if args.apply and not conflicts:
        with TXN.OperationLock(STATE.state_dir()):
            transaction = TXN.Transaction.start(STATE.state_dir(), plan)
            try:
                transaction.phase("staged")
                TXN.fault("after-staged")
                for target, _ in removable:
                    transaction.track_file(removable_ids[str(target)])
                    target.unlink()
                transaction.phase("assets")
                TXN.fault("after-assets")
                if path_plan.get("action"):
                    if path_plan["action"].get("strategy") == "windows-user-env":
                        transaction.track_windows_path("path")
                        TXN.set_windows_path_entry(path_plan["action"]["entry"], False)
                    else:
                        transaction.track_file("path")
                        Path(path_plan["action"]["target"]).write_text(path_plan["content"], encoding="utf-8")
                transaction.phase("path")
                TXN.fault("after-path")
                transaction.track_file("manifest")
                if keep_state:
                    STATE.atomic_write(state_path, proposed_state, backup=True)
                else:
                    state_path.unlink()
                transaction.phase("manifest")
                TXN.fault("after-manifest")
                for item in transaction_actions:
                    if item.get("strategy") == "windows-user-env":
                        if TXN.windows_path_entry_present(item["entry"]) != item["after_present"]:
                            raise TXN.TransactionError("Windows PATH smoke check failed")
                        continue
                    target = Path(item["target"])
                    if item["after_sha256"] is None:
                        if target.exists() or target.is_symlink():
                            raise TXN.TransactionError(f"Transaction removal smoke check failed: {target}")
                    elif not target.is_file() or target.is_symlink() or STATE.sha256_file(target) != item["after_sha256"]:
                        raise TXN.TransactionError(f"Transaction smoke check failed: {target}")
                transaction.phase("verified")
                TXN.fault("after-verified")
                transaction.commit()
                report["status"] = "partial" if keep_state else "uninstalled"
                report["transaction_status"] = "committed"
                for directory in sorted({target.parent for target, _ in removable}, key=lambda item: len(item.parts), reverse=True):
                    try:
                        directory.rmdir()
                    except OSError:
                        pass
            except (OSError, STATE.StateError, TXN.TransactionError) as exc:
                recovery = transaction.rollback()
                report["status"] = "rolled_back" if recovery["status"] == "rolled_back" else "rollback-blocked"
                report["transaction_status"] = recovery["status"]
                report["error"] = str(exc)
                report["recovery"] = recovery
                emit(report, args.json)
                return 2
    emit(report, args.json)
    return 2 if report["status"] == "blocked" else 0


def register_user_cli(args: argparse.Namespace) -> int:
    incomplete = TXN.incomplete_journals(STATE.state_dir())
    if incomplete:
        raise TXN.TransactionError("an incomplete user transaction must be recovered before registering the CLI")
    state_path = user_installation_path()
    if not state_path.exists():
        raise STATE.StateError("user installation state does not exist; run install --scope user first")
    shim = Path(args.shim_path).expanduser().resolve(strict=False)
    if not shim.is_file() or shim.is_symlink():
        raise STATE.StateError(f"CLI shim is missing or unsafe: {shim}")
    state = load_user_installation()
    now = STATE.utc_now()
    cli = {
        "path": str(shim),
        "sha256": STATE.sha256_file(shim),
        "owner": "sdd-toolkit",
        "registered_at": now,
    }
    path_integration = {
        "strategy": args.path_strategy,
        "entry": args.path_entry or str(shim.parent),
        "target": args.path_target or "none",
        "marker": "sdd-toolkit",
        "updated_at": now,
    }
    state["cli"] = cli
    state["path_integration"] = path_integration
    state["updated_at"] = now
    with STATE.RegistryLock(state_path.with_suffix(state_path.suffix + ".lock")):
        STATE.atomic_write(state_path, state, backup=True)
    result = {
        "schema_version": 1,
        "scope": "user",
        "status": "registered",
        "state_path": str(state_path),
        "cli": cli,
        "path_integration": path_integration,
    }
    emit(result, args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sdd", description="SDD Toolkit lifecycle CLI")
    parser.add_argument("--version", action="version", version=(ROOT / "VERSION").read_text(encoding="utf-8").strip())
    sub = parser.add_subparsers(dest="command", required=True)

    activate_parser = sub.add_parser("activate", help="Activate the current project for user-scoped SDD work")
    activate_parser.add_argument("--project-path", default=".", help="Override the current project directory")
    activate_parser.add_argument("--kit-root", default="", help=argparse.SUPPRESS)
    activate_parser.add_argument("--runtime", choices=["auto", *RUNTIME.runtime_choices(ROOT)], default="auto", help="Optional runtime hint")
    activate_parser.add_argument("--dry-run", action="store_true", help="Preview without updating the local activation registry")
    activate_parser.add_argument("--apply", action="store_true", help=argparse.SUPPRESS)
    activate_parser.add_argument("--json", action="store_true")
    activate_parser.set_defaults(handler=activate_user)

    user_install_parser = sub.add_parser("install", help="Install compiled agents and skills in a user harness profile")
    user_install_parser.add_argument("--scope", choices=["user", "organization"], default="user")
    user_install_parser.add_argument("--kit-root", default=str(ROOT))
    user_install_parser.add_argument("--profile-root", default="", help="Profile root override for isolated environments")
    user_install_parser.add_argument("--runtime", default="detected", help="detected, all, one runtime, or a comma-separated runtime list")
    user_install_parser.add_argument("--plan-id", default="", help="Apply only if the current plan matches this preview ID")
    user_install_parser.add_argument("--with-cli", action="store_true", help="Install the sdd shim and manage its PATH entry in the same transaction")
    user_install_parser.add_argument("--install-root", default="", help="Dedicated root for the global CLI shim")
    user_install_parser.add_argument("--bin-dir", default="", help="Override the user command directory")
    user_install_parser.add_argument("--no-path", action="store_true", help="Install the shim without changing PATH")
    user_install_parser.add_argument("--apply", action="store_true")
    user_install_parser.add_argument("--json", action="store_true")
    user_install_parser.set_defaults(handler=install_user)

    register_cli_parser = sub.add_parser("register-user-cli", help=argparse.SUPPRESS)
    register_cli_parser.add_argument("--shim-path", required=True)
    register_cli_parser.add_argument("--path-strategy", choices=["windows-user-env", "unix-profile-block", "none"], default="none")
    register_cli_parser.add_argument("--path-entry", default="")
    register_cli_parser.add_argument("--path-target", default="")
    register_cli_parser.add_argument("--json", action="store_true")
    register_cli_parser.set_defaults(handler=register_user_cli)

    runtime_parser = sub.add_parser("runtime", help="Inspect registered harness adapters")
    runtime_sub = runtime_parser.add_subparsers(dest="runtime_command", required=True)
    for runtime_command in ("list", "show"):
        runtime_command_parser = runtime_sub.add_parser(runtime_command, help=f"{runtime_command.capitalize()} runtime adapters")
        if runtime_command == "show":
            runtime_command_parser.add_argument("runtime", choices=RUNTIME.runtime_choices(ROOT)[1:])
        runtime_command_parser.add_argument("--json", action="store_true")
        runtime_command_parser.set_defaults(handler=runtime_inspect)
    runtime_detect_parser = runtime_sub.add_parser("detect", help="Discover installed runtime components and readiness")
    runtime_detect_parser.add_argument("--runtime", default="all", help="all, one runtime, or a comma-separated runtime list")
    runtime_detect_parser.add_argument("--profile-root", default="", help="Profile root override for isolated environments")
    runtime_detect_parser.add_argument("--extensions-dir", action="append", default=[], help="Additional editor extension root; repeatable")
    runtime_detect_parser.add_argument("--portable-root", action="append", default=[], help="VS Code portable root containing data/extensions; repeatable")
    runtime_detect_parser.add_argument("--mode", choices=["quick", "full"], default="quick", help="Quick is passive; full performs bounded local version/package probes")
    runtime_detect_parser.add_argument("--cache", action="store_true", help="Cache a quick scan locally for five minutes with fingerprint invalidation")
    runtime_detect_parser.add_argument("--redact-paths", action="store_true")
    runtime_detect_parser.add_argument("--json", action="store_true")
    runtime_detect_parser.set_defaults(handler=runtime_detect)

    delivery_parser = sub.add_parser("delivery", help="Resolve and validate a demand delivery contract")
    delivery_sub = delivery_parser.add_subparsers(dest="delivery_command", required=True)
    delivery_propose = delivery_sub.add_parser("propose", help="Propose delivery and verification from a demand type")
    delivery_propose.add_argument("--type", required=True)
    delivery_propose.add_argument("--description", default="")
    delivery_propose.add_argument("--json", action="store_true")
    delivery_propose.set_defaults(handler=delivery_inspect)
    delivery_validate = delivery_sub.add_parser("validate", help="Validate a JSON contract or task.md strategy")
    delivery_source = delivery_validate.add_mutually_exclusive_group(required=True)
    delivery_source.add_argument("--file")
    delivery_source.add_argument("--task")
    delivery_validate.add_argument("--json", action="store_true")
    delivery_validate.set_defaults(handler=delivery_inspect)

    architecture_parser = sub.add_parser("architecture", help="Resolve and validate an architectural task contract")
    architecture_sub = architecture_parser.add_subparsers(dest="architecture_command", required=True)
    architecture_propose = architecture_sub.add_parser("propose", help="Propose architectural impact for a demand")
    architecture_propose.add_argument("--type", required=True)
    architecture_propose.add_argument("--description", default="")
    architecture_propose.add_argument("--delivery-kind", default="")
    architecture_propose.add_argument("--json", action="store_true")
    architecture_propose.set_defaults(handler=architecture_inspect)
    architecture_validate = architecture_sub.add_parser("validate", help="Validate a JSON contract or task.md strategy")
    architecture_source = architecture_validate.add_mutually_exclusive_group(required=True)
    architecture_source.add_argument("--file")
    architecture_source.add_argument("--task")
    architecture_validate.add_argument("--json", action="store_true")
    architecture_validate.set_defaults(handler=architecture_inspect)

    source_parser = sub.add_parser("source", help="Manage the user-scoped toolkit source")
    source_sub = source_parser.add_subparsers(dest="source_command", required=True)
    source_status_parser = source_sub.add_parser("status", help="Inspect the configured toolkit source")
    source_status_parser.add_argument("--json", action="store_true")
    source_status_parser.set_defaults(handler=source_status)
    for source_command_name in ("install", "update"):
        source_command = source_sub.add_parser(source_command_name, help=f"{source_command_name.capitalize()} a user-scoped Git source")
        source_command.add_argument("--repository-url", required=True)
        source_command.add_argument("--source-root", default="")
        source_command.add_argument("--channel", choices=["stable", "beta", "main"], default="main")
        source_command.add_argument("--ref", default="")
        source_command.add_argument("--offline", action="store_true", help="Reuse the validated local source cache without network access")
        source_command.add_argument("--allow-downgrade", action="store_true", help="Allow replacing the source with a lower toolkit version")
        source_command.add_argument("--apply", action="store_true")
        source_command.add_argument("--json", action="store_true")
        source_command.set_defaults(handler=source_install)

    context_parser = sub.add_parser("context", help="Resolve the active SDD context for a project")
    context_sub = context_parser.add_subparsers(dest="context_command", required=True)
    resolve_parser = context_sub.add_parser("resolve", help="Resolve workspace, profile and ticket paths")
    resolve_parser.add_argument("--project-path", default=".")
    resolve_parser.add_argument("--runtime", choices=["auto", *RUNTIME.runtime_choices(ROOT)], default="auto")
    resolve_parser.add_argument("--ticket", default="")
    resolve_parser.add_argument("--json", action="store_true")
    resolve_parser.set_defaults(handler=resolve_context)

    transaction_parser = sub.add_parser("transaction", help="Inspect and recover user lifecycle transactions")
    transaction_sub = transaction_parser.add_subparsers(dest="transaction_command", required=True)
    transaction_status_parser = transaction_sub.add_parser("status", help="List transaction journals")
    transaction_status_parser.add_argument("--scope", choices=["user"], default="user")
    transaction_status_parser.add_argument("--active-only", action="store_true")
    transaction_status_parser.add_argument("--redact-paths", action="store_true")
    transaction_status_parser.add_argument("--json", action="store_true")
    transaction_status_parser.set_defaults(handler=transaction_status)
    transaction_recover_parser = transaction_sub.add_parser("recover", help="Preview or recover incomplete transactions")
    transaction_recover_parser.add_argument("--scope", choices=["user"], default="user")
    transaction_recover_parser.add_argument("--plan-id", default="")
    transaction_recover_parser.add_argument("--apply", action="store_true")
    transaction_recover_parser.add_argument("--redact-paths", action="store_true")
    transaction_recover_parser.add_argument("--json", action="store_true")
    transaction_recover_parser.set_defaults(handler=transaction_recover)

    status_parser = sub.add_parser("status", help="Show the current project's activation and SDD work")
    status_parser.add_argument("--project-path", default=".")
    status_parser.add_argument("--json", action="store_true")
    status_parser.set_defaults(handler=user_status)

    doctor_parser = sub.add_parser("doctor", help="Inspect the user-scoped installation and runtime profiles")
    doctor_parser.add_argument("--scope", choices=["user"], default="user")
    doctor_parser.add_argument("--profile-root", default="")
    doctor_parser.add_argument("--runtime", default="all", help="all, one runtime, or a comma-separated runtime list")
    doctor_parser.add_argument("--discovery-mode", choices=["quick", "full"], default="quick")
    doctor_parser.add_argument("--redact-paths", action="store_true")
    doctor_parser.add_argument("--json", action="store_true")
    doctor_parser.set_defaults(handler=user_doctor)

    for name in ("update", "uninstall"):
        command = sub.add_parser(name, help=f"{name.capitalize()} user-scoped toolkit assets")
        command.add_argument("--kit-root", default="")
        command.add_argument("--scope", choices=["user"], default="user")
        command.add_argument("--profile-root", default="")
        if name == "update":
            command.add_argument("--runtime", choices=RUNTIME.runtime_choices(ROOT), default="all")
        command.add_argument("--apply", action="store_true")
        command.add_argument("--json", action="store_true")
        command.add_argument("--no-register", action="store_true")
        if name == "update":
            command.add_argument("--conflict", choices=["keep", "replace", "backup", "skip"], default="keep")
            command.add_argument("--plan-id", default="", help="Apply only if the current plan matches this preview ID")
            command.add_argument("--repository-url", default="")
            command.add_argument("--source-root", default="")
            command.add_argument("--channel", choices=["stable", "beta", "main"], default="main")
            command.add_argument("--ref", default="")
            command.add_argument("--offline", action="store_true", help="Reuse the validated local source cache without network access")
            command.add_argument("--allow-downgrade", action="store_true", help="Allow replacing the source with a lower toolkit version")
            command.set_defaults(handler=user_update)
        elif name == "uninstall":
            command.add_argument("--runtime", choices=RUNTIME.runtime_choices(ROOT), default="all")
            command.add_argument("--plan-id", default="", help="Apply only if the current plan matches this preview ID")
            command.set_defaults(handler=user_uninstall)

    for daily_name, daily_help in (("start", "Prepare a ticket for the SDD bootstrap"), ("resume", "Prepare a ticket to resume with the SDD bootstrap")):
        daily_parser = sub.add_parser(daily_name, help=daily_help)
        daily_parser.add_argument("ticket", nargs="?", default="")
        daily_parser.add_argument("--project-path", default=".")
        daily_parser.add_argument("--runtime", choices=["auto", *RUNTIME.runtime_choices(ROOT)], default="auto")
        daily_parser.add_argument("--yes", action="store_true", help="Activate the current project locally when needed")
        daily_parser.add_argument("--json", action="store_true")
        daily_parser.set_defaults(handler=lambda args, action=daily_name: daily_handoff(args, action))

    activation_parser = sub.add_parser("activation", help="Inspect or remove local project activations")
    activation_sub = activation_parser.add_subparsers(dest="activation_command", required=True)
    activation_list = activation_sub.add_parser("list", help="List local activations")
    activation_list.add_argument("--json", action="store_true")
    activation_list.set_defaults(handler=activation_lifecycle)
    for lifecycle_name in ("show", "deactivate"):
        lifecycle_parser = activation_sub.add_parser(lifecycle_name, help=f"{lifecycle_name.capitalize()} the current project")
        lifecycle_parser.add_argument("--project-path", default=".")
        lifecycle_parser.add_argument("--apply", action="store_true")
        lifecycle_parser.add_argument("--json", action="store_true")
        lifecycle_parser.set_defaults(handler=activation_lifecycle)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (OSError, STATE.StateError, TXN.TransactionError, ValueError) as exc:
        print(f"sdd: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
