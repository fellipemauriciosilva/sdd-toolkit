"""The semantic linter must be clean here and must actually catch regressions."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "sdd.py"
sys.path.insert(0, str(ROOT / "scripts"))

import sdd_lint  # noqa: E402

COPIED = ("agents", "dist", "templates", "evals", "schemas", "metadata", "runtimes", "scripts")


class LintCleanTests(unittest.TestCase):
    def test_repository_has_no_contract_findings(self):
        report = sdd_lint.lint(ROOT)
        self.assertEqual([], report["findings"])
        self.assertEqual("clean", report["status"])

    def test_cli_exposes_lint_and_reports_json(self):
        completed = subprocess.run(
            [sys.executable, str(CLI), "lint", "--json"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, completed.returncode, msg=completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("clean", payload["status"])
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), payload["toolkit_version"])


class LintRegressionTests(unittest.TestCase):
    """Each case mutates a copy of the kit and asserts the linter fails closed."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="sdd-lint-")
        self.kit = Path(self.directory.name) / "kit"
        self.kit.mkdir()
        for name in COPIED:
            shutil.copytree(ROOT / name, self.kit / name, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(ROOT / "VERSION", self.kit / "VERSION")
        self.addCleanup(self.directory.cleanup)

    def messages(self):
        return [item["message"] for item in sdd_lint.lint(self.kit)["findings"]]

    def patch(self, relative, old, new, count=1):
        path = self.kit / relative
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, relative)
        path.write_text(text.replace(old, new, count), encoding="utf-8", newline="\n")

    def test_detects_a_legacy_demand_file(self):
        self.patch("agents/sdd-create-spec.md", "Crie `SPEC_PATH`", "Crie `tasks.md` e `SPEC_PATH`")
        self.assertIn("referência legada: tasks.md", self.messages())

    def test_detects_a_missing_canonical_variable(self):
        self.patch("agents/sdd-review-code.md", "PROJECT_PATH", "o-projeto", count=-1)
        self.assertTrue(any("variáveis canônicas ausentes" in message for message in self.messages()))

    def test_detects_a_command_without_the_terminal_capability(self):
        self.patch("agents/sdd-review-code.md", 'capabilities: "read,terminal"', 'capabilities: "read"')
        self.assertIn("instrui executar comando sem declarar terminal", self.messages())

    def test_detects_state_ownership_leaking_out_of_the_bootstrap(self):
        self.patch(
            "agents/sdd-implement-spec.md",
            "Não atualize `session-state.md`.",
            "Atualize `session-state.md` ao final.",
        )
        self.assertIn("agente de execução não atualiza session-state.md", self.messages())

    def test_detects_a_result_outside_the_envelope(self):
        self.patch(
            "agents/sdd-review-code.md",
            "Retorne `AGENT_RESULT` com `payload.review`",
            "Retorne `REVIEW_RESULT`",
        )
        self.assertTrue(any("resultado fora do envelope" in message for message in self.messages()))

    def test_detects_a_payload_outside_the_contract(self):
        self.patch("agents/sdd-review-code.md", "`payload.review`", "`payload.delivery`")
        self.assertTrue(any("payload fora do contrato" in message for message in self.messages()))

    def test_detects_stack_coupling(self):
        self.patch(
            "agents/sdd-implement-spec.md",
            "2. Descubra linguagem, build, testes e padrões existentes. Não presuma\n"
            "   stack, ferramenta de build, mensageria ou framework de teste.",
            "2. Use Maven e Spring Boot como padrão do projeto.",
        )
        self.assertTrue(any("acoplamento de stack" in message for message in self.messages()))

    def test_detects_a_destructive_git_instruction(self):
        self.patch(
            "agents/sdd-refactor-code.md",
            "4. Execute testes relevantes",
            "4. Ao falhar, rode git stash e recomece. Execute testes relevantes",
        )
        self.assertTrue(any("operação destrutiva" in message for message in self.messages()))

    def test_detects_a_version_drift_between_agent_and_toolkit(self):
        self.patch("agents/sdd-architect.md", 'version: "4.0.0"', 'version: "3.9.0"')
        self.assertTrue(any("difere do VERSION" in message for message in self.messages()))

    def test_detects_a_stale_dist_artifact(self):
        path = self.kit / "dist" / "cursor" / "sdd-review-code.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("## Política comum SDD", "## Notas"),
            encoding="utf-8", newline="\n",
        )
        messages = self.messages()
        self.assertTrue(any("política não injetada" in message for message in messages))
        self.assertTrue(any("corpo divergente entre runtimes" in message for message in messages))

    def test_detects_a_missing_shared_policy(self):
        (self.kit / "templates" / "agent-policy.md").unlink()
        self.assertIn("política comum ausente", self.messages())

    def test_detects_an_agent_without_evals(self):
        shutil.rmtree(self.kit / "evals" / "sdd-refactor-code")
        self.assertIn("agente sem evals", self.messages())

    def test_detects_an_agent_without_an_adversarial_eval(self):
        shutil.rmtree(self.kit / "evals" / "sdd-refactor-code" / "case-03")
        self.assertIn("sem caso adversarial", self.messages())


if __name__ == "__main__":
    unittest.main()
