import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "sdd.py"


def result_document():
    return {
        "schema_version": 1,
        "agent": "sdd-analyze-demand",
        "agent_version": "4.0.0",
        "runtime": "codex",
        "status": "completed",
        "summary": "Demanda analisada com critérios de aceite.",
        "changes": [{"path": "task.md", "action": "modified"}],
        "evidence": [{"kind": "file", "source": "task.md", "outcome": "observed"}],
        "decisions": [{"statement": "A entrega exige implementação.", "confidence": "confirmed", "evidence_refs": [0]}],
        "preexisting_failures": [],
        "residual_risks": [],
        "blocked_on": [],
        "next_agent": "sdd-architect",
        "payload": {"analysis": {}},
    }


class ContextPackCliTests(unittest.TestCase):
    def run_cli(self, env, *args):
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def test_pack_is_immutable_and_result_is_recorded_transactionally(self):
        with tempfile.TemporaryDirectory(prefix="sdd-context-") as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            state = root / "state"
            history = root / "history"
            env = {**os.environ, "SDD_TOOLKIT_STATE_DIR": str(state), "SDD_TOOLKIT_HISTORY_DIR": str(history)}
            activation = self.run_cli(env, "activate", "--project-path", str(project), "--json")
            self.assertEqual(0, activation.returncode, activation.stderr)
            workspace = Path(json.loads(activation.stdout)["activation"]["workspace"])
            spec = workspace / "ABC-1"
            spec.mkdir(parents=True)
            (spec / "task.md").write_text("# Login seguro\n\n## Critérios de aceite\n\n- Validar sessão.\n", encoding="utf-8")

            preview = self.run_cli(env, "context", "pack", "--project-path", str(project), "--ticket", "ABC-1", "--agent", "sdd-analyze-demand", "--json")
            self.assertEqual(0, preview.returncode, preview.stderr)
            preview_body = json.loads(preview.stdout)
            self.assertEqual("preview", preview_body["mode"])
            self.assertFalse((spec / "contexts").exists())

            applied = self.run_cli(env, "context", "pack", "--project-path", str(project), "--ticket", "ABC-1", "--agent", "sdd-analyze-demand", "--apply", "--json")
            self.assertEqual(0, applied.returncode, applied.stderr)
            pack_body = json.loads(applied.stdout)
            pack_path = Path(pack_body["context_path"])
            self.assertTrue(pack_path.is_file())
            self.assertTrue(pack_body["context"]["context_id"].startswith("ctx-"))
            self.assertEqual("Login seguro", pack_body["context"]["objective"])

            validated = self.run_cli(env, "context", "validate", "--file", str(pack_path), "--json")
            self.assertEqual(0, validated.returncode, validated.stderr)
            self.assertEqual("valid", json.loads(validated.stdout)["status"])

            result_path = root / "agent-result.json"
            agent_result = result_document()
            agent_result["payload"]["context_request"] = {
                "resource": "technical-design.md",
                "reason": "O contrato técnico é necessário.",
                "acceptance_criterion": "Validar sessão.",
                "requested_tokens": 400,
            }
            (spec / "technical-design.md").write_text("# Design\n\nContrato de sessão.\n", encoding="utf-8")
            result_path.write_text(json.dumps(agent_result), encoding="utf-8")
            expanded = self.run_cli(env, "context", "expand", "--project-path", str(project), "--ticket", "ABC-1", "--parent-file", str(pack_path), "--request-file", str(result_path), "--apply", "--json")
            self.assertEqual(0, expanded.returncode, expanded.stderr)
            expanded_body = json.loads(expanded.stdout)
            self.assertEqual(pack_body["context"]["context_id"], expanded_body["context"]["parent_context_id"])
            self.assertTrue(any(item["path"] == "technical-design.md" for item in expanded_body["context"]["references"]))
            recorded = self.run_cli(env, "result", "record", "--project-path", str(project), "--ticket", "ABC-1", "--file", str(result_path), "--context-file", str(pack_path), "--apply", "--json")
            self.assertEqual(0, recorded.returncode, recorded.stderr)
            record = json.loads(recorded.stdout)
            self.assertEqual("recorded", record["status"])
            self.assertTrue(Path(record["result_path"]).is_file())
            self.assertTrue((spec / "state.json").is_file())
            self.assertTrue((spec / "events.ndjson").is_file())
            self.assertTrue((spec / "context-summary.md").is_file())

            state_view = self.run_cli(env, "context", "state", "--project-path", str(project), "--ticket", "ABC-1", "--json")
            self.assertEqual(0, state_view.returncode, state_view.stderr)
            self.assertEqual("sdd-architect", json.loads(state_view.stdout)["state"]["next_agent"])

    def test_pack_schema_accepts_emitted_document(self):
        schema = json.loads((ROOT / "schemas" / "context-pack.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        with tempfile.TemporaryDirectory(prefix="sdd-context-schema-") as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            env = {
                **os.environ,
                "SDD_TOOLKIT_STATE_DIR": str(root / "state"),
                "SDD_TOOLKIT_HISTORY_DIR": str(root / "history"),
            }
            self.assertEqual(0, self.run_cli(env, "activate", "--project-path", str(project), "--json").returncode)
            emitted = self.run_cli(env, "context", "pack", "--project-path", str(project), "--ticket", "ABC-2", "--agent", "sdd-bootstrap", "--json")
            self.assertEqual(0, emitted.returncode, emitted.stderr)
            Draft202012Validator(schema).validate(json.loads(emitted.stdout)["context"])


if __name__ == "__main__":
    unittest.main()
