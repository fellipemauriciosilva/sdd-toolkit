"""Context resolution, immutable packs and the agent result envelope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import sdd_runtime as RUNTIME
import sdd_agent_result as AGENT_RESULT
import sdd_context as CONTEXT
import sdd_user_state as STATE

from .common import ROOT, TICKET_PATTERN, emit
from .activation import activation_project_path, default_user_workspace, load_user_activations, user_activation_path


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


def resolved_context_data(project_path: str, runtime: str, ticket: str) -> Dict[str, Any]:
    project = activation_project_path(project_path)
    project_id = STATE.installation_id(project)
    activation = next((item for item in load_user_activations().get("activations", []) if item.get("project_id") == project_id), None)
    workspace = Path(activation["workspace"]) if activation else default_user_workspace(project, project_id)[1]
    if not TICKET_PATTERN.fullmatch(ticket):
        raise STATE.StateError("Ticket must contain only letters, numbers, '.', '_' or '-' and be at most 128 characters")
    return {
        "ticket": ticket,
        "runtime": runtime,
        "project_id": project_id,
        "spec_path": str(workspace / ticket),
    }


def context_pack(args: argparse.Namespace) -> int:
    resolved = resolved_context_data(args.project_path, args.runtime, args.ticket)
    pack = CONTEXT.build_pack(
        Path(resolved["spec_path"]),
        args.ticket,
        resolved["project_id"],
        args.agent,
        args.stage,
        args.budget,
        args.parent_context_id or None,
    )
    result: Dict[str, Any] = {
        "mode": "apply" if args.apply else "preview",
        "status": "ready",
        "context": pack,
        "writes_project": False,
    }
    if args.apply:
        result["context_path"] = str(CONTEXT.write_pack(Path(resolved["spec_path"]), pack))
    emit(result, args.json)
    return 0


def context_validate(args: argparse.Namespace) -> int:
    try:
        pack = CONTEXT.load_pack(Path(args.file))
    except (OSError, json.JSONDecodeError, CONTEXT.ContextError) as exc:
        raise STATE.StateError(str(exc)) from exc
    emit({"status": "valid", "context": pack}, args.json)
    return 0


def context_explain(args: argparse.Namespace) -> int:
    try:
        pack = CONTEXT.load_pack(Path(args.file))
    except (OSError, json.JSONDecodeError, CONTEXT.ContextError) as exc:
        raise STATE.StateError(str(exc)) from exc
    emit({
        "status": "ready",
        "context_id": pack["context_id"],
        "target_agent": pack["target_agent"],
        "budget": pack["budget"],
        "references": [{
            "path": item["path"],
            "reason": item["reason"],
            "priority": item["priority"],
            "bytes": item["bytes"],
            "included_bytes": item["included_bytes"],
            "omitted_reason": item.get("omitted_reason"),
        } for item in pack["references"]],
        "truncated": pack["truncated"],
        "omitted": pack["omitted"],
    }, args.json)
    return 0


def context_expand(args: argparse.Namespace) -> int:
    resolved = resolved_context_data(args.project_path, args.runtime, args.ticket)
    try:
        parent = CONTEXT.load_pack(Path(args.parent_file))
        result = json.loads(Path(args.request_file).read_text(encoding="utf-8"))
        pack = CONTEXT.expand_pack(Path(resolved["spec_path"]), parent, result)
    except (OSError, json.JSONDecodeError, ValueError, CONTEXT.ContextError) as exc:
        raise STATE.StateError(str(exc)) from exc
    output: Dict[str, Any] = {
        "mode": "apply" if args.apply else "preview",
        "status": "ready",
        "context": pack,
        "writes_project": False,
    }
    if args.apply:
        output["context_path"] = str(CONTEXT.write_pack(Path(resolved["spec_path"]), pack))
    emit(output, args.json)
    return 0


def result_record(args: argparse.Namespace) -> int:
    resolved = resolved_context_data(args.project_path, args.runtime, args.ticket)
    try:
        pack = CONTEXT.load_pack(Path(args.context_file))
        value = json.loads(Path(args.file).read_text(encoding="utf-8"))
        AGENT_RESULT.validate(value)
    except (OSError, json.JSONDecodeError, ValueError, CONTEXT.ContextError) as exc:
        raise STATE.StateError(str(exc)) from exc
    if not args.apply:
        emit({
            "mode": "preview",
            "status": "ready",
            "context_id": pack["context_id"],
            "result_id": "result-" + CONTEXT.digest(value)[:16],
            "writes_project": False,
        }, args.json)
        return 0
    result = CONTEXT.record_result(
        Path(resolved["spec_path"]), args.ticket, resolved["project_id"], pack, value,
    )
    result["mode"] = "apply"
    result["writes_project"] = False
    emit(result, args.json)
    return 0


def context_state(args: argparse.Namespace) -> int:
    resolved = resolved_context_data(args.project_path, args.runtime, args.ticket)
    try:
        result = CONTEXT.inspect_state(Path(resolved["spec_path"]), args.ticket, resolved["project_id"])
    except CONTEXT.ContextError as exc:
        raise STATE.StateError(str(exc)) from exc
    result["writes_project"] = False
    emit(result, args.json)
    return 0


def run_agent(args: argparse.Namespace) -> int:
    resolved = resolved_context_data(args.project_path, args.runtime, args.ticket)
    pack = CONTEXT.build_pack(
        Path(resolved["spec_path"]),
        args.ticket,
        resolved["project_id"],
        args.agent,
        args.stage,
        args.budget,
    )
    result: Dict[str, Any] = {
        "mode": "apply" if args.apply else "preview",
        "status": "prepared",
        "agent": args.agent,
        "ticket": args.ticket,
        "runtime": args.runtime,
        "context": pack,
        "handoff": "Run the selected native agent with the emitted context file, then use sdd result record.",
        "writes_project": False,
    }
    if args.apply:
        result["context_path"] = str(CONTEXT.write_pack(Path(resolved["spec_path"]), pack))
    emit(result, args.json)
    return 0


def agent_result_validate(args: argparse.Namespace) -> int:
    """Validate a portable result emitted by an SDD agent."""
    try:
        result = AGENT_RESULT.load(args.file)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise STATE.StateError(str(exc)) from exc
    emit({"status": "valid", "result": result}, args.json)
    return 0


def register_result(sub) -> None:
    result_parser = sub.add_parser("result", help="Validate a portable agent result envelope")
    result_sub = result_parser.add_subparsers(dest="result_command", required=True)
    result_validate = result_sub.add_parser("validate", help="Validate an AGENT_RESULT JSON document")
    result_validate.add_argument("--file", required=True)
    result_validate.add_argument("--json", action="store_true")
    result_validate.set_defaults(handler=agent_result_validate)
    result_record_parser = result_sub.add_parser("record", help="Validate and transactionally record an agent result")
    result_record_parser.add_argument("--project-path", default=".")
    result_record_parser.add_argument("--runtime", choices=["auto", *RUNTIME.runtime_choices(ROOT)], default="auto")
    result_record_parser.add_argument("--ticket", required=True)
    result_record_parser.add_argument("--file", required=True)
    result_record_parser.add_argument("--context-file", required=True)
    result_record_parser.add_argument("--apply", action="store_true")
    result_record_parser.add_argument("--json", action="store_true")
    result_record_parser.set_defaults(handler=result_record)


def register_context(sub) -> None:
    context_parser = sub.add_parser("context", help="Resolve the active SDD context for a project")
    context_sub = context_parser.add_subparsers(dest="context_command", required=True)
    resolve_parser = context_sub.add_parser("resolve", help="Resolve workspace, profile and ticket paths")
    resolve_parser.add_argument("--project-path", default=".")
    resolve_parser.add_argument("--runtime", choices=["auto", *RUNTIME.runtime_choices(ROOT)], default="auto")
    resolve_parser.add_argument("--ticket", default="")
    resolve_parser.add_argument("--json", action="store_true")
    resolve_parser.set_defaults(handler=resolve_context)
    pack_parser = context_sub.add_parser("pack", help="Build the immutable context pack for an agent")
    pack_parser.add_argument("--project-path", default=".")
    pack_parser.add_argument("--runtime", choices=["auto", *RUNTIME.runtime_choices(ROOT)], default="auto")
    pack_parser.add_argument("--ticket", required=True)
    pack_parser.add_argument("--agent", required=True)
    pack_parser.add_argument("--stage", default="auto")
    pack_parser.add_argument("--budget", type=int, default=4000)
    pack_parser.add_argument("--parent-context-id", default="")
    pack_parser.add_argument("--apply", action="store_true")
    pack_parser.add_argument("--json", action="store_true")
    pack_parser.set_defaults(handler=context_pack)
    context_validate_parser = context_sub.add_parser("validate", help="Validate an immutable context pack")
    context_validate_parser.add_argument("--file", required=True)
    context_validate_parser.add_argument("--json", action="store_true")
    context_validate_parser.set_defaults(handler=context_validate)
    context_explain_parser = context_sub.add_parser("explain", help="Explain context selection without exposing omitted content")
    context_explain_parser.add_argument("--file", required=True)
    context_explain_parser.add_argument("--json", action="store_true")
    context_explain_parser.set_defaults(handler=context_explain)
    context_expand_parser = context_sub.add_parser("expand", help="Create a bounded child context from an agent request")
    context_expand_parser.add_argument("--project-path", default=".")
    context_expand_parser.add_argument("--runtime", choices=["auto", *RUNTIME.runtime_choices(ROOT)], default="auto")
    context_expand_parser.add_argument("--ticket", required=True)
    context_expand_parser.add_argument("--parent-file", required=True)
    context_expand_parser.add_argument("--request-file", required=True)
    context_expand_parser.add_argument("--apply", action="store_true")
    context_expand_parser.add_argument("--json", action="store_true")
    context_expand_parser.set_defaults(handler=context_expand)
    context_state_parser = context_sub.add_parser("state", help="Inspect the canonical state of a demand")
    context_state_parser.add_argument("--project-path", default=".")
    context_state_parser.add_argument("--runtime", choices=["auto", *RUNTIME.runtime_choices(ROOT)], default="auto")
    context_state_parser.add_argument("--ticket", required=True)
    context_state_parser.add_argument("--json", action="store_true")
    context_state_parser.set_defaults(handler=context_state)


def register_run(sub) -> None:
    run_parser = sub.add_parser("run", help="Prepare a standalone agent dispatch using the context-pack protocol")
    run_parser.add_argument("agent")
    run_parser.add_argument("--project-path", default=".")
    run_parser.add_argument("--runtime", choices=["auto", *RUNTIME.runtime_choices(ROOT)], default="auto")
    run_parser.add_argument("--ticket", required=True)
    run_parser.add_argument("--stage", default="standalone")
    run_parser.add_argument("--budget", type=int, default=4000)
    run_parser.add_argument("--apply", action="store_true")
    run_parser.add_argument("--json", action="store_true")
    run_parser.set_defaults(handler=run_agent)
