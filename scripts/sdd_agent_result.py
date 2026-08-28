#!/usr/bin/env python3
"""Validate portable SDD agent result envelopes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict


RUNTIMES = {"copilot", "claude", "codex", "cursor"}
STATUSES = {"completed", "blocked", "failed", "not-applicable"}
CONFIDENCE = {"confirmed", "inferred", "unknown"}
OUTCOMES = {"passed", "failed", "observed", "not-run"}
ACTIONS = {"created", "modified", "deleted", "none"}
KINDS = {"command", "file", "test", "observation"}
PAYLOAD_KEYS = {
    "analysis", "architecture", "delivery", "document", "documentation", "e2e", "install",
    "integration", "investigation", "migration_analysis", "orchestration",
    "project_discovery", "review", "scaffold", "unit", "workspace", "context_request",
}
REQUIRED = {
    "schema_version", "agent", "agent_version", "runtime", "status", "summary",
    "changes", "evidence", "decisions", "preexisting_failures",
    "residual_risks", "blocked_on", "next_agent",
}
OPTIONAL = {"payload"}


def _validate_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    unknown = set(payload).difference(PAYLOAD_KEYS)
    if unknown:
        raise ValueError(f"unsupported payload keys: {', '.join(sorted(unknown))}")
    for key, value in payload.items():
        if not isinstance(value, dict):
            raise ValueError(f"payload.{key} must be an object")
    if "delivery" in payload:
        _validate_nested("sdd_delivery", payload["delivery"], "payload.delivery")
    if "architecture" in payload:
        _validate_nested("sdd_architecture", payload["architecture"], "payload.architecture")
    if "context_request" in payload:
        request = payload["context_request"]
        required = {"resource", "reason", "acceptance_criterion", "requested_tokens"}
        if required.difference(request) or not isinstance(request["resource"], str) or not isinstance(request["reason"], str):
            raise ValueError("payload.context_request is incomplete")
        if not isinstance(request["acceptance_criterion"], str) or not isinstance(request["requested_tokens"], int):
            raise ValueError("payload.context_request has invalid values")
        if request["requested_tokens"] < 1 or request["requested_tokens"] > 10000:
            raise ValueError("payload.context_request requested_tokens is out of range")


def _validate_nested(module_name: str, contract: Dict[str, Any], label: str) -> None:
    """Reuse the dedicated contract validators when the payload carries one."""
    if "schema_version" not in contract:
        return
    try:
        module = __import__(module_name)
    except ImportError:
        return
    try:
        module.validate(contract)
    except ValueError as exc:
        raise ValueError(f"{label}: {exc}") from exc


def validate(value: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("agent result must be an object")
    missing = REQUIRED.difference(value)
    if missing:
        raise ValueError(f"agent result missing: {', '.join(sorted(missing))}")
    optional = OPTIONAL | {"context"}
    unknown = set(value).difference(REQUIRED | optional)
    if unknown:
        raise ValueError(f"agent result has unsupported fields: {', '.join(sorted(unknown))}")
    if value["schema_version"] != 1:
        raise ValueError("unsupported agent result schema_version")
    if not isinstance(value["agent"], str) or not re.fullmatch(r"sdd-[a-z0-9-]+", value["agent"]):
        raise ValueError("agent must be a canonical sdd agent name")
    if not isinstance(value["agent_version"], str) or not re.fullmatch(r"\d+\.\d+\.\d+", value["agent_version"]):
        raise ValueError("agent_version must be semantic version text")
    if value["runtime"] not in RUNTIMES or value["status"] not in STATUSES:
        raise ValueError("runtime or status is unsupported")
    if not isinstance(value["summary"], str) or not value["summary"].strip():
        raise ValueError("summary is required")
    for field in ("changes", "evidence", "decisions", "preexisting_failures", "residual_risks", "blocked_on"):
        if not isinstance(value[field], list):
            raise ValueError(f"{field} must be a list")
    for field in ("preexisting_failures", "residual_risks", "blocked_on"):
        if any(not isinstance(item, str) for item in value[field]):
            raise ValueError(f"{field} must contain only text entries")
    if not isinstance(value["next_agent"], str):
        raise ValueError("next_agent must be a string")
    for item in value["changes"]:
        if not isinstance(item, dict) or item.get("action") not in ACTIONS or not isinstance(item.get("path"), str):
            raise ValueError("invalid change entry")
    for item in value["evidence"]:
        if not isinstance(item, dict) or item.get("kind") not in KINDS or item.get("outcome") not in OUTCOMES or not isinstance(item.get("source"), str):
            raise ValueError("invalid evidence entry")
    for item in value["decisions"]:
        if not isinstance(item, dict) or item.get("confidence") not in CONFIDENCE or not isinstance(item.get("statement"), str) or not isinstance(item.get("evidence_refs"), list):
            raise ValueError("invalid decision entry")
    if value["status"] == "blocked" and not value["blocked_on"]:
        raise ValueError("a blocked result must declare blocked_on")
    if "payload" in value:
        _validate_payload(value["payload"])
    if "context" in value:
        context = value["context"]
        expected = {"context_id", "digest", "ticket", "project_id"}
        if not isinstance(context, dict) or set(context) != expected:
            raise ValueError("context must contain context_id, digest, ticket and project_id")
        if not re.fullmatch(r"ctx-[0-9a-f]{16}", str(context["context_id"])):
            raise ValueError("context.context_id is invalid")
        if not re.fullmatch(r"[0-9a-f]{64}", str(context["digest"])):
            raise ValueError("context.digest is invalid")
        if not isinstance(context["ticket"], str) or not context["ticket"]:
            raise ValueError("context.ticket is invalid")
        if not re.fullmatch(r"[0-9a-f]{64}", str(context["project_id"])):
            raise ValueError("context.project_id is invalid")
    return value


def load(path: str) -> Dict[str, Any]:
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))
