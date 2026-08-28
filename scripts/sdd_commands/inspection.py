"""Read-only inspection: runtimes, contracts and the semantic linter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

import sdd_runtime as RUNTIME
import sdd_discovery as DISCOVERY
import sdd_delivery as DELIVERY
import sdd_architecture as ARCHITECTURE
import sdd_lint as LINT
import sdd_user_state as STATE

from .common import ROOT, emit, profile_path_arg, redact_paths


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


def contract_lint(args: argparse.Namespace) -> int:
    """Run the semantic contract linter over a toolkit source tree."""
    root = Path(args.kit_root).expanduser().resolve(strict=False)
    if not (root / "agents").is_dir():
        raise STATE.StateError(f"not a toolkit source tree: {root}")
    report = LINT.lint(root)
    emit(report, args.json)
    return 0 if report["status"] == "clean" else 1


def register_runtime(sub) -> None:
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


def register_delivery(sub) -> None:
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


def register_architecture(sub) -> None:
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


def register_lint(sub) -> None:
    lint_parser = sub.add_parser("lint", help="Lint agent contracts, compiled artifacts and evals")
    lint_parser.add_argument("--kit-root", default=str(ROOT))
    lint_parser.add_argument("--json", action="store_true")
    lint_parser.set_defaults(handler=contract_lint)
