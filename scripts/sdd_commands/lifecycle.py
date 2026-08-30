"""Transactional lifecycle: install, update, uninstall, doctor and transactions."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import sdd_transaction as TXN
import sdd_runtime as RUNTIME
import sdd_discovery as DISCOVERY
import sdd_user_state as STATE

from .common import ROOT, emit, profile_path_arg, redact_paths
from .source import load_user_installation, local_source_metadata, source_install, source_state_path, user_install_sources, user_installation_path
from .inspection import detect_harnesses


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
    # A source that disappears (agent renamed or removed) leaves its old asset
    # behind unless we schedule it for removal here. We only ever remove an
    # asset whose on-disk hash still matches what we recorded — if it drifted,
    # someone else touched it, and we treat that the same as any other asset
    # conflict: block and let the user resolve it, never delete silently.
    obsolete: List[tuple[Path, Dict[str, Any]]] = []
    retained_previous: List[Dict[str, Any]] = []
    for item in previous.get("managed_files", []):
        if not isinstance(item, dict):
            continue
        previous_path = item.get("path")
        if not isinstance(previous_path, str):
            retained_previous.append(item)
            continue
        if previous_path in current_paths:
            # Still produced today: `managed`/`preserved` below already carry
            # a fresh record for this path. Keeping it here too would double
            # every current asset in the manifest on every install/update.
            continue
        if item.get("owner") != "sdd-toolkit":
            retained_previous.append(item)
            continue
        try:
            obsolete_target = STATE.safe_lexical_path(profile, previous_path, "User installation target")
        except STATE.StateError:
            conflicts.append(previous_path)
            retained_previous.append(item)
            continue
        if not obsolete_target.exists() and not obsolete_target.is_symlink():
            continue  # already gone; drop it from the manifest without a conflict
        if obsolete_target.is_symlink() or not obsolete_target.is_file() or STATE.sha256_file(obsolete_target) != item.get("sha256"):
            conflicts.append(previous_path)
            retained_previous.append(item)
            continue
        obsolete.append((obsolete_target, item))
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
    obsolete_ids: Dict[str, str] = {}
    for index, (obsolete_target, item) in enumerate(obsolete):
        action_id = f"obsolete-{index:04d}"
        obsolete_ids[str(obsolete_target)] = action_id
        transaction_actions.append({
            "id": action_id,
            "kind": "asset",
            "operation": "remove",
            "target": str(obsolete_target),
            "before_sha256": item.get("sha256"),
            "after_sha256": None,
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
    obsolete_runtimes = {
        runtime
        for _, item in obsolete
        for runtime in (item.get("runtimes") or ([item["runtime"]] if item.get("runtime") else []))
    }
    allowed_roots = [state_path.parent]
    for runtime in {runtime for item in files for runtime in item["runtimes"]} | obsolete_runtimes:
        adapter = RUNTIME.load_adapters(kit).get(runtime)
        if adapter is not None:
            allowed_roots.append(profile / adapter.user_profile)
            allowed_roots.append(profile / adapter.skill_dir)
    allowed_roots.extend(obsolete_target.parent for obsolete_target, _ in obsolete)
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
        # Assets a previous install created that no current source produces
        # anymore (an agent renamed or removed). Reported separately from
        # `files` because they have no source to diff against — they only
        # ever go away.
        "obsolete": [{"path": item.get("path"), "action": "remove"} for _, item in obsolete],
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
                for obsolete_target, _ in obsolete:
                    transaction.track_file(obsolete_ids[str(obsolete_target)])
                    obsolete_target.unlink()
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
                    target = Path(item["target"])
                    if item["after_sha256"] is None:
                        if target.exists() or target.is_symlink():
                            raise TXN.TransactionError(f"Transaction removal smoke check failed: {target}")
                        continue
                    if not target.is_file() or target.is_symlink() or STATE.sha256_file(target) != item["after_sha256"]:
                        raise TXN.TransactionError(f"Transaction smoke check failed: {target}")
                transaction.phase("verified")
                TXN.fault("after-verified")
                transaction.commit()
                report["status"] = "installed"
                report["transaction_status"] = "committed"
                for directory in sorted({obsolete_target.parent for obsolete_target, _ in obsolete}, key=lambda item: len(item.parts), reverse=True):
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


def register_install(sub) -> None:
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


def register_user_cli_command(sub) -> None:
    register_cli_parser = sub.add_parser("register-user-cli", help=argparse.SUPPRESS)
    register_cli_parser.add_argument("--shim-path", required=True)
    register_cli_parser.add_argument("--path-strategy", choices=["windows-user-env", "unix-profile-block", "none"], default="none")
    register_cli_parser.add_argument("--path-entry", default="")
    register_cli_parser.add_argument("--path-target", default="")
    register_cli_parser.add_argument("--json", action="store_true")
    register_cli_parser.set_defaults(handler=register_user_cli)


def register_transaction(sub) -> None:
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


def register_doctor(sub) -> None:
    doctor_parser = sub.add_parser("doctor", help="Inspect the user-scoped installation and runtime profiles")
    doctor_parser.add_argument("--scope", choices=["user"], default="user")
    doctor_parser.add_argument("--profile-root", default="")
    doctor_parser.add_argument("--runtime", default="all", help="all, one runtime, or a comma-separated runtime list")
    doctor_parser.add_argument("--discovery-mode", choices=["quick", "full"], default="quick")
    doctor_parser.add_argument("--redact-paths", action="store_true")
    doctor_parser.add_argument("--json", action="store_true")
    doctor_parser.set_defaults(handler=user_doctor)


def register_update_uninstall(sub) -> None:
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
