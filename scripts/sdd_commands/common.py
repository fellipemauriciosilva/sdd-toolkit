"""Shared CLI primitives: output, public identity and path arguments."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict

import sdd_user_state as STATE

ROOT = Path(__file__).resolve().parents[2]
ACTIVATION_SCHEMA_VERSION = 2
TICKET_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def emit(value: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return
    for key, item in value.items():
        print(f"{key}: {json.dumps(item, ensure_ascii=False) if isinstance(item, (dict, list)) else item}")


def public_identity() -> Dict[str, str]:
    path = ROOT / "metadata" / "project-identity.json"
    try:
        maintainer = json.loads(path.read_text(encoding="utf-8"))["maintainer"]
        identity = {
            "name": str(maintainer["name"]),
            "email": str(maintainer["email"]),
            "linkedin": str(maintainer["linkedin"]),
        }
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise STATE.StateError(f"Invalid public project identity: {path}") from exc
    if not all(identity.values()):
        raise STATE.StateError(f"Invalid public project identity: {path}")
    return identity


def about(args: argparse.Namespace) -> int:
    result = {
        "schema_version": 1,
        "project": "SDD Toolkit",
        "toolkit_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "maintainer": public_identity(),
    }
    emit(result, args.json)
    return 0


def project_path_arg(value: str) -> Path:
    project = Path(value).expanduser().resolve(strict=False)
    if not project.is_dir():
        raise STATE.StateError(f"Project directory does not exist: {project}")
    return project


def profile_path_arg(value: str) -> Path:
    profile = Path(value).expanduser().resolve(strict=False)
    if profile.parent == profile:
        raise STATE.StateError("User profile root cannot be the filesystem root")
    return profile


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


def register_about(sub) -> None:
    about_parser = sub.add_parser("about", help="Show public toolkit identity and version")
    about_parser.add_argument("--json", action="store_true")
    about_parser.set_defaults(handler=about)
