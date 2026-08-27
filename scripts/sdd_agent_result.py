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
    "project_discovery", "review", "scaffold", "unit", "workspace",
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
    unknown = set(value).difference(REQUIRED | OPTIONAL)
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
    return value


def load(path: str) -> Dict[str, Any]:
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))
