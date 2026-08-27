import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import sdd_lint  # noqa: E402

DEMAND_AGENTS = sdd_lint.DEMAND_AGENTS
SUPPORT_AGENTS = sdd_lint.SUPPORT_AGENTS


class AgentContractTests(unittest.TestCase):
    def test_sources_use_the_v4_contract_and_no_legacy_demand_files(self):
        toolkit_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        agents = sorted((ROOT / "agents").glob("*.md"))
        self.assertEqual(17, len(agents))
        for path in agents:
            text = path.read_text(encoding="utf-8")
            self.assertIn(f'version: "{toolkit_version}"', text, path.name)
            self.assertIn("AGENT_RESULT", text, path.name)
            self.assertEqual([], sdd_lint.legacy_hits(text), path.name)
            self.assertNotIn("sdd-fill-project-context", text, path.name)
            self.assertNotIn("--profile=yolo", text, path.name)
            if path.stem in DEMAND_AGENTS:
                self.assertIn("sdd context resolve", text, path.name)
                for variable in sdd_lint.CANONICAL_VARIABLES:
                    self.assertIn(variable, text, f"{path.name}: {variable}")

    def test_demand_and_support_agents_cover_the_whole_catalog(self):
        names = {path.stem for path in (ROOT / "agents").glob("*.md")}
        self.assertEqual(names, DEMAND_AGENTS | SUPPORT_AGENTS)
        self.assertEqual(set(), DEMAND_AGENTS & SUPPORT_AGENTS)

    def test_support_agents_that_resolve_context_still_scope_to_the_spec(self):
        for name in sorted(SUPPORT_AGENTS):
            text = (ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8")
            if "sdd context resolve" in text:
                self.assertIn("SPEC_PATH", text, name)

    def test_only_bootstrap_owns_orchestration_state(self):
        for path in sorted((ROOT / "agents").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            if path.stem == "sdd-bootstrap":
                self.assertIn("proprietário de `session-state.md`", text)
            else:
                self.assertNotIn("proprietário de `session-state.md`", text, path.name)
                self.assertNotIn("Atualize `{SPEC_PATH}session-state.md`", text, path.name)

    def test_every_agent_declares_its_payload_key(self):
        for path in sorted((ROOT / "agents").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            expected = sdd_lint.PAYLOAD_BY_AGENT[path.stem]
            self.assertTrue(
                any(f"payload.{key}" in text for key in expected),
                f"{path.name}: esperado um de {sorted(expected)}",
            )

    def test_contract_document_defines_canonical_context_and_result(self):
        contract = (ROOT / "docs" / "AGENT-CONTRACT.md").read_text(encoding="utf-8")
        for required in (
            "PROJECT_PATH", "SDD_WORKSPACE", "SPEC_PATH", "RUNTIME", "AGENT_RESULT",
            "confirmed", "inferred", "unknown", "payload", "preexisting_failures",
            "templates/agent-policy.md", "sdd_lint.py",
        ):
            self.assertIn(required, contract)

    def test_contract_document_lists_every_agent_payload(self):
        contract = (ROOT / "docs" / "AGENT-CONTRACT.md").read_text(encoding="utf-8")
        for agent, keys in sdd_lint.PAYLOAD_BY_AGENT.items():
            self.assertIn(f"`{agent}`", contract, agent)
            for key in keys:
                self.assertIn(f"`{key}`", contract, f"{agent}: {key}")


if __name__ == "__main__":
    unittest.main()
