"""AGENT_RESULT envelope: schema, validator and CLI must agree and fail closed."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "sdd.py"
sys.path.insert(0, str(ROOT / "scripts"))

import sdd_agent_result as ENVELOPE  # noqa: E402

VALID = {
    "schema_version": 1,
    "agent": "sdd-implement-spec",
    "agent_version": "4.0.0",
    "runtime": "claude",
    "status": "completed",
    "summary": "Critérios cobertos com validação local.",
    "changes": [{"path": "src/example", "action": "modified"}],
    "evidence": [{"kind": "command", "source": "comando de teste do projeto", "outcome": "passed"}],
    "decisions": [{"statement": "Framework existente reutilizado.", "confidence": "confirmed", "evidence_refs": [0]}],
    "preexisting_failures": ["suite legada: 2 falhas anteriores à demanda"],
    "residual_risks": [],
    "blocked_on": [],
    "next_agent": "sdd-bootstrap",
    "payload": {"delivery": {"files": 1}},
}


def schema_validator():
    document = json.loads((ROOT / "schemas" / "agent-result.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(document)
    return Draft202012Validator(document)


def without(field):
    value = copy.deepcopy(VALID)
    value.pop(field)
    return value


def mutated(**changes):
    value = copy.deepcopy(VALID)
    value.update(changes)
    return value


class EnvelopeAcceptanceTests(unittest.TestCase):
    def test_schema_and_validator_accept_a_complete_result(self):
        schema_validator().validate(VALID)
        self.assertEqual(VALID, ENVELOPE.validate(copy.deepcopy(VALID)))

    def test_not_run_evidence_is_representable(self):
        value = mutated(
            status="blocked",
            evidence=[{"kind": "test", "source": "suite e2e", "outcome": "not-run"}],
            blocked_on=["ambiente e2e não autorizado"],
        )
        schema_validator().validate(value)
        ENVELOPE.validate(copy.deepcopy(value))

    def test_every_agent_payload_key_is_accepted(self):
        for key in sorted(ENVELOPE.PAYLOAD_KEYS):
            payload = {} if key != "context_request" else {
                "resource": "src/auth.py",
                "reason": "Contrato de sessão é necessário.",
                "acceptance_criterion": "Validar sessão.",
                "requested_tokens": 400,
            }
            value = mutated(payload={key: payload})
            schema_validator().validate(value)
            ENVELOPE.validate(copy.deepcopy(value))


class EnvelopeRejectionTests(unittest.TestCase):
    def test_preexisting_failures_is_mandatory(self):
        value = without("preexisting_failures")
        self.assertTrue(list(schema_validator().iter_errors(value)))
        with self.assertRaises(ValueError):
            ENVELOPE.validate(value)

    def test_every_required_field_is_enforced_by_both_layers(self):
        for field in sorted(ENVELOPE.REQUIRED):
            value = without(field)
            self.assertTrue(list(schema_validator().iter_errors(value)), field)
            with self.assertRaises(ValueError, msg=field):
                ENVELOPE.validate(value)

    def test_unknown_top_level_field_is_rejected(self):
        value = mutated(gate="G4 passed")
        self.assertTrue(list(schema_validator().iter_errors(value)))
        with self.assertRaises(ValueError):
            ENVELOPE.validate(value)

    def test_legacy_result_block_is_not_a_valid_field(self):
        value = mutated(REVIEW_RESULT={"findings": []})
        self.assertTrue(list(schema_validator().iter_errors(value)))
        with self.assertRaises(ValueError):
            ENVELOPE.validate(value)

    def test_unknown_payload_key_is_rejected(self):
        value = mutated(payload={"gate_approval": {}})
        self.assertTrue(list(schema_validator().iter_errors(value)))
        with self.assertRaises(ValueError):
            ENVELOPE.validate(value)

    def test_blocked_result_must_declare_what_blocks_it(self):
        with self.assertRaises(ValueError):
            ENVELOPE.validate(mutated(status="blocked"))

    def test_unsupported_runtime_and_status_are_rejected(self):
        for value in (mutated(runtime="github-copilot"), mutated(status="approved")):
            self.assertTrue(list(schema_validator().iter_errors(value)))
            with self.assertRaises(ValueError):
                ENVELOPE.validate(value)

    def test_unsupported_evidence_outcome_is_rejected(self):
        value = mutated(evidence=[{"kind": "test", "source": "suite", "outcome": "assumed"}])
        self.assertTrue(list(schema_validator().iter_errors(value)))
        with self.assertRaises(ValueError):
            ENVELOPE.validate(value)

    def test_nested_delivery_contract_is_revalidated(self):
        value = mutated(payload={"delivery": {
            "schema_version": 1,
            "contract_version": "1.0",
            "delivery_kind": "not-a-kind",
            "verification": ["unit"],
            "rationale": "x",
            "owner": "sdd-analyze-demand",
            "expected_evidence": ["comando"],
        }})
        with self.assertRaises(ValueError):
            ENVELOPE.validate(value)


class EnvelopeCliTests(unittest.TestCase):
    def run_cli(self, value):
        with tempfile.TemporaryDirectory(prefix="sdd-envelope-") as temporary:
            path = Path(temporary) / "result.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(CLI), "result", "validate", "--file", str(path), "--json"],
                capture_output=True, text=True, check=False,
            )

    def test_cli_accepts_a_valid_envelope(self):
        completed = self.run_cli(VALID)
        self.assertEqual(0, completed.returncode, msg=completed.stderr)
        self.assertEqual("valid", json.loads(completed.stdout)["status"])

    def test_cli_fails_closed_on_an_incomplete_envelope(self):
        completed = self.run_cli(without("evidence"))
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("evidence", completed.stderr)


if __name__ == "__main__":
    unittest.main()
