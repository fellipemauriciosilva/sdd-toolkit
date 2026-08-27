#!/usr/bin/env python3
"""Resolve and validate the delivery contract used by SDD demands."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Union


DELIVERY_AGENTS = {
    "application": "sdd-implement-spec",
    "refactor": "sdd-refactor-code",
    "unit-tests": "sdd-generate-tests",
    "integration-tests": "sdd-generate-integration-tests",
    "e2e-tests": "sdd-generate-e2e-tests",
    "migration": "sdd-analyze-migration",
}
TYPE_DEFAULTS = {
    "feature": ("application", ["unit"]),
    "bugfix": ("application", ["unit"]),
    "refactor": ("refactor", ["unit"]),
    "migration": ("migration", ["integration"]),
    "test-e2e": ("e2e-tests", ["e2e"]),
}
TYPE_ALIASES = {"e2e": "test-e2e", "playwright": "test-e2e"}
SAFE_TEXT = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
TABLE_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$")


def normalize_type(value: str) -> str:
    normalized = value.strip().lower()
    normalized = TYPE_ALIASES.get(normalized, normalized)
    if normalized not in TYPE_DEFAULTS:
        raise ValueError(f"unsupported demand type: {value}")
    return normalized


def propose(type_name: str, description: str = "") -> Dict[str, Any]:
    demand_type = normalize_type(type_name)
    delivery_kind, verification = TYPE_DEFAULTS[demand_type]
    text = SAFE_TEXT.sub(" ", description or "").strip()
    rationale = f"Default for demand type '{demand_type}'."
    if demand_type in {"feature", "bugfix"} and re.search(r"\b(browser|web|ui|frontend|jornada|tela)\b", text, re.I):
        verification = ["unit", "e2e"]
        rationale = "Application delivery with E2E verification because the description indicates a user-facing web journey."
    if demand_type == "test-e2e":
        rationale = "The demand explicitly delivers an E2E suite; Playwright generation is the implementation, not only verification."
    return {
        "schema_version": 1,
        "contract_version": "1.0",
        "delivery_kind": delivery_kind,
        "verification": verification,
        "rationale": rationale,
        "owner": "sdd-analyze-demand",
        "expected_evidence": ["payload.delivery", *[f"payload.{item}" for item in verification if item != "none"]],
        "commands": [],
    }


def validate(contract: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(contract, dict):
        raise ValueError("delivery contract must be an object")
    required = {"schema_version", "contract_version", "delivery_kind", "verification", "rationale", "owner", "expected_evidence"}
    missing = required.difference(contract)
    if missing:
        raise ValueError(f"delivery contract missing: {', '.join(sorted(missing))}")
    if contract["schema_version"] != 1 or contract["owner"] != "sdd-analyze-demand":
        raise ValueError("unsupported delivery contract version or owner")
    if not isinstance(contract["contract_version"], str) or not re.fullmatch(r"\d+\.\d+", contract["contract_version"]):
        raise ValueError("unsupported delivery contract version")
    delivery = contract["delivery_kind"]
    if delivery not in DELIVERY_AGENTS:
        raise ValueError(f"unsupported delivery_kind: {delivery}")
    verification = contract["verification"]
    if not isinstance(verification, list) or len(verification) != len(set(verification)):
        raise ValueError("verification must be a list without duplicates")
    if not verification or any(item not in {"none", "unit", "integration", "e2e"} for item in verification):
        raise ValueError("verification contains an unsupported value")
    if "none" in verification and len(verification) != 1:
        raise ValueError("none cannot be combined with another verification")
    if delivery == "e2e-tests" and "e2e" not in verification:
        raise ValueError("e2e-tests delivery requires e2e verification")
    if not isinstance(contract["rationale"], str) or not contract["rationale"].strip():
        raise ValueError("rationale is required")
    if not isinstance(contract["expected_evidence"], list) or not contract["expected_evidence"]:
        raise ValueError("expected_evidence is required")
    return {**contract, "delivery_agent": DELIVERY_AGENTS[delivery]}


def extract_task_contract(task_path: Union[str, Path]) -> Dict[str, Any]:
    """Read the machine-checkable Delivery Strategy table from task.md."""
    path = Path(task_path)
    content = path.read_text(encoding="utf-8")
    match = re.search(
        r"^##\s+Delivery Strategy\s*$([\s\S]*?)(?=^##\s+|\Z)",
        content,
        flags=re.MULTILINE,
    )
    if not match:
        raise ValueError("task.md does not contain a Delivery Strategy section")
    values: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        row = TABLE_ROW.match(line.strip())
        if row and row.group(1).lower() not in {"field", "-------"}:
            values[row.group(1).strip().lower()] = row.group(2).strip()
    required = {"delivery_contract_version", "delivery_kind", "verification", "rationale", "owner", "expected_evidence"}
    missing = required.difference(values)
    if missing:
        raise ValueError(f"task.md delivery strategy missing: {', '.join(sorted(missing))}")
    verification_text = values["verification"].strip().strip("`")
    verification = [item.strip() for item in re.split(r"[, ]+", verification_text.strip("[]")) if item.strip()]
    evidence_text = values["expected_evidence"].strip().strip("`")
    expected_evidence = [item.strip() for item in re.split(r"[,;]+", evidence_text.strip("[]")) if item.strip()]
    try:
        schema_version = int(values.get("schema_version", "1"))
    except ValueError as exc:
        raise ValueError("task.md schema_version must be an integer") from exc
    contract = {
        "schema_version": schema_version,
        "contract_version": values["delivery_contract_version"],
        "delivery_kind": values["delivery_kind"].strip("`"),
        "verification": verification,
        "rationale": values["rationale"],
        "owner": values["owner"].strip("`"),
        "expected_evidence": expected_evidence,
    }
    return validate(contract)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve SDD delivery contracts")
    sub = parser.add_subparsers(dest="command", required=True)
    propose_parser = sub.add_parser("propose")
    propose_parser.add_argument("--type", required=True)
    propose_parser.add_argument("--description", default="")
    validate_parser = sub.add_parser("validate")
    source = validate_parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file")
    source.add_argument("--task")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "propose":
            value = validate(propose(args.type, args.description))
        else:
            if args.task:
                value = extract_task_contract(args.task)
            else:
                value = validate(json.loads(Path(args.file).read_text(encoding="utf-8")))
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "code": "invalid_delivery_contract", "detail": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
