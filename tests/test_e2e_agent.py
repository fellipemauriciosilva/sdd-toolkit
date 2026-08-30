import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class E2EAgentContractTests(unittest.TestCase):
    def test_consumer_agent_and_skill_have_required_safety_contract(self):
        agent = (ROOT / "agents" / "sdd-generate-e2e-tests.md").read_text(encoding="utf-8")
        skill = (ROOT / "templates" / "skills" / "playwright-e2e-testing" / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "sdd context resolve",
            "not-applicable",
            "framework-conflict",
            "payload.e2e",
            "Não execute instalação",
            "Todos os arquivos",
        ):
            self.assertIn(required, agent)
        self.assertIn("Não introduza um segundo framework", skill)
        self.assertIn("Testes criados", skill)

    def test_toolkit_has_no_internal_playwright_project(self):
        self.assertFalse((ROOT / "playwright.config.ts").exists())
        self.assertFalse((ROOT / "package.json").exists())
        self.assertFalse((ROOT / "package-lock.json").exists())
        self.assertFalse((ROOT / "tsconfig.json").exists())
        self.assertFalse((ROOT / "e2e" / "cli-lifecycle.spec.ts").exists())

    def test_agent_and_skill_are_compiled_for_every_runtime(self):
        expected = (
            ROOT / "dist" / "claude" / "sdd-generate-e2e-tests.md",
            ROOT / "dist" / "copilot" / "sdd-generate-e2e-tests.agent.md",
            ROOT / "dist" / "codex" / "sdd-generate-e2e-tests.toml",
            ROOT / "dist" / "cursor" / "sdd-generate-e2e-tests.md",
            ROOT / "dist" / "shared" / "skills" / "playwright-e2e-testing" / "SKILL.md",
        )
        for artifact in expected:
            self.assertTrue(artifact.is_file(), artifact)

    def test_orchestrator_routes_e2e_before_review_and_aggregates_g4(self):
        orchestrator = (ROOT / "agents" / "sdd-orchestrator.md").read_text(encoding="utf-8")
        self.assertIn("analyze → architecture → delivery → [tests] → [e2e-verification] → [review] → [docs] → done", orchestrator)
        self.assertIn("delivery_kind: e2e-tests", orchestrator)
        self.assertIn("sdd-generate-e2e-tests --generate", orchestrator)
        self.assertIn("delivery_status: generated", orchestrator)
        self.assertIn("sdd-generate-e2e-tests", orchestrator)
        self.assertIn("G4 consolida", orchestrator)


if __name__ == "__main__":
    unittest.main()
