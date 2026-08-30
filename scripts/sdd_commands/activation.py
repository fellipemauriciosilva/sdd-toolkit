"""Project activation, personal workspace and the daily ticket handoff."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import sdd_runtime as RUNTIME
import sdd_user_state as STATE

from .common import ACTIVATION_SCHEMA_VERSION, ROOT, TICKET_PATTERN, emit, project_path_arg
from .source import user_installation_path


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
        "agent": "sdd-orchestrator",
        "handoff": f"Use sdd-orchestrator to {action} ticket {ticket} in the current project.",
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


def register_activate(sub) -> None:
    activate_parser = sub.add_parser("activate", help="Activate the current project for user-scoped SDD work")
    activate_parser.add_argument("--project-path", default=".", help="Override the current project directory")
    activate_parser.add_argument("--kit-root", default="", help=argparse.SUPPRESS)
    activate_parser.add_argument("--runtime", choices=["auto", *RUNTIME.runtime_choices(ROOT)], default="auto", help="Optional runtime hint")
    activate_parser.add_argument("--dry-run", action="store_true", help="Preview without updating the local activation registry")
    activate_parser.add_argument("--apply", action="store_true", help=argparse.SUPPRESS)
    activate_parser.add_argument("--json", action="store_true")
    activate_parser.set_defaults(handler=activate_user)


def register_status(sub) -> None:
    status_parser = sub.add_parser("status", help="Show the current project's activation and SDD work")
    status_parser.add_argument("--project-path", default=".")
    status_parser.add_argument("--json", action="store_true")
    status_parser.set_defaults(handler=user_status)


def register_daily(sub) -> None:
    for daily_name, daily_help in (("start", "Prepare a ticket for the SDD orchestrator"), ("resume", "Prepare a ticket to resume with the SDD orchestrator")):
        daily_parser = sub.add_parser(daily_name, help=daily_help)
        daily_parser.add_argument("ticket", nargs="?", default="")
        daily_parser.add_argument("--project-path", default=".")
        daily_parser.add_argument("--runtime", choices=["auto", *RUNTIME.runtime_choices(ROOT)], default="auto")
        daily_parser.add_argument("--yes", action="store_true", help="Activate the current project locally when needed")
        daily_parser.add_argument("--json", action="store_true")
        daily_parser.set_defaults(handler=lambda args, action=daily_name: daily_handoff(args, action))


def register_activation(sub) -> None:
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
