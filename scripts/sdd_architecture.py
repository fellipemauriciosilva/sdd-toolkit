#!/usr/bin/env python3
"""Classify and validate the architectural contract of an SDD demand."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Union


ARCHITECTURE_AGENT = "sdd-architect"
IMPACTS = {"low", "medium", "high"}
STATUSES = {"pending", "analyzing", "designed", "blocked", "approved", "superseded"}
MODES = {"design", "review-task"}
TYPE_IMPACTS = {"unit-tests": "low", "integration-tests": "medium", "migration": "high", "test-e2e": "medium"}
HIGH_RISK = re.compile(r"\b(auth|authorization|authentication|database|banco|tabela|schema|migration|event|kafka|queue|breaking|public api|microservice|infra|security|lgpd|payment|pii|encryption|availability)\b|autentica", re.I)
LOW_RISK = re.compile(r"\b(local|isolated|typo|message|validation|unit test|regression test)\b", re.I)
TABLE_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$")


def classify(type_name: str, description: str = "", delivery_kind: str = "") -> str:
    text = f"{type_name} {delivery_kind} {description}".strip()
    if HIGH_RISK.search(text):
        return "high"
    if TYPE_IMPACTS.get(type_name) == "high":
        return "high"
    if TYPE_IMPACTS.get(type_name):
        return TYPE_IMPACTS[type_name]
    if LOW_RISK.search(text) and type_name in {"bugfix", "refactor"}:
        return "low"
    return "medium"


def propose(type_name: str, description: str = "", delivery_kind: str = "") -> Dict[str, Any]:
    impact = classify(type_name.strip().lower(), description, delivery_kind)
    if impact == "low":
        rationale = "A triagem arquitetural curta é suficiente para uma mudança isolada e de baixo acoplamento."
    elif impact == "high":
        rationale = "A demanda pode afetar contratos, dados, segurança, integração ou requisitos não funcionais; exige design completo e decisões explícitas."
    else:
        rationale = "A demanda afeta comportamento ou integração do projeto e requer Technical Design proporcional antes do G2."
    return {
        "schema_version": 1,
        "contract_version": "1.0",
        "architecture_impact": impact,
        "architecture_status": "pending",
        "architecture_agent": ARCHITECTURE_AGENT,
        "architecture_mode": "design",
        "architecture_artifact": "technical-design.md",
        "rationale": rationale,
        "decisions": [],
        "required_evidence": ["ARCHITECTURE_RESULT"],
        "full_design_required": impact != "low",
    }


def validate(contract: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(contract, dict):
        raise ValueError("architecture contract must be an object")
    required = {"schema_version", "contract_version", "architecture_impact", "architecture_status", "architecture_agent", "architecture_mode", "architecture_artifact", "rationale", "required_evidence"}
    missing = required.difference(contract)
    if missing:
        raise ValueError(f"architecture contract missing: {', '.join(sorted(missing))}")
    if contract["schema_version"] != 1 or contract["contract_version"] != "1.0":
        raise ValueError("unsupported architecture contract version")
    if contract["architecture_agent"] != ARCHITECTURE_AGENT:
        raise ValueError("unsupported architecture agent")
    if contract["architecture_impact"] not in IMPACTS or contract["architecture_status"] not in STATUSES or contract["architecture_mode"] not in MODES:
        raise ValueError("unsupported architecture impact, status or mode")
    artifact = contract["architecture_artifact"]
    if not isinstance(artifact, str) or not artifact.strip() or artifact.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", artifact) or ".." in Path(artifact).parts:
        raise ValueError("architecture_artifact must be a relative path inside the spec")
    if not isinstance(contract["rationale"], str) or not contract["rationale"].strip():
        raise ValueError("architecture rationale is required")
    if not isinstance(contract["required_evidence"], list) or not contract["required_evidence"]:
        raise ValueError("required_evidence is required")
    if "decisions" in contract and (not isinstance(contract["decisions"], list) or len(contract["decisions"]) != len(set(contract["decisions"]))):
        raise ValueError("decisions must be a list without duplicates")
    if contract["architecture_impact"] == "low" and contract.get("full_design_required") is True:
        raise ValueError("low impact cannot require full design")
    if contract["architecture_impact"] in {"medium", "high"} and contract.get("full_design_required") is False:
        raise ValueError("medium/high impact requires full design")
    return contract


def extract_task_contract(task_path: Union[str, Path]) -> Dict[str, Any]:
    path = Path(task_path)
    content = path.read_text(encoding="utf-8")
    match = re.search(r"^##\s+Architecture Strategy\s*$([\s\S]*?)(?=^##\s+|\Z)", content, flags=re.MULTILINE)
    if not match:
        raise ValueError("task.md does not contain an Architecture Strategy section")
    values: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        row = TABLE_ROW.match(line.strip())
        if row and row.group(1).lower() not in {"field", "-------"}:
            values[row.group(1).strip().lower()] = row.group(2).strip().strip("`")
    required = {"architecture_contract_version", "architecture_impact", "architecture_status", "architecture_agent", "architecture_mode", "architecture_artifact", "rationale", "required_evidence"}
    missing = required.difference(values)
    if missing:
        raise ValueError(f"task.md architecture strategy missing: {', '.join(sorted(missing))}")
    evidence_text = values["required_evidence"].strip("[]")
    evidence = [item.strip() for item in re.split(r"[,;]+", evidence_text) if item.strip()]
    decisions_text = values.get("decisions", "").strip().strip("[]")
    decisions = [] if decisions_text.lower() in {"", "none", "todo"} else [item.strip() for item in re.split(r"[,;]+", decisions_text) if item.strip()]
    contract = {
        "schema_version": int(values.get("schema_version", "1")),
        "contract_version": values["architecture_contract_version"],
        "architecture_impact": values["architecture_impact"],
        "architecture_status": values["architecture_status"],
        "architecture_agent": values["architecture_agent"],
        "architecture_mode": values["architecture_mode"],
        "architecture_artifact": values["architecture_artifact"],
        "rationale": values["rationale"],
        "decisions": decisions,
        "required_evidence": evidence,
        "full_design_required": values.get("full_design_required", "true").lower() == "true",
    }
    return validate(contract)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve and validate SDD architectural contracts")
    sub = parser.add_subparsers(dest="command", required=True)
    propose_parser = sub.add_parser("propose")
    propose_parser.add_argument("--type", required=True)
    propose_parser.add_argument("--description", default="")
    propose_parser.add_argument("--delivery-kind", default="")
    validate_parser = sub.add_parser("validate")
    source = validate_parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file")
    source.add_argument("--task")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "propose":
            value = validate(propose(args.type, args.description, args.delivery_kind))
        elif args.task:
            value = extract_task_contract(args.task)
        else:
            value = validate(json.loads(Path(args.file).read_text(encoding="utf-8")))
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "blocked", "code": "invalid_architecture_contract", "detail": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
