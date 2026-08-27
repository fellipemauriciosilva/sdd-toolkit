import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REMOVED_AGENTS = {
    "sdd-inspect-infra",
    "sdd-sharepoint-migration-analyst",
    "sdd-java-legacy-analyst",
    "sdd-migrate-kustomize-to-helm",
}
EXPECTED_ATTRIBUTION = {
    "author": "Felipe Maurício da Silva",
    "author_email": "fellipemauriciosilva@gmail.com",
    "author_linkedin": "https://www.linkedin.com/in/felipe-mauricio-06685735/",
}


class AgentInventoryTests(unittest.TestCase):
    def test_every_agent_has_canonical_author_and_compiled_attribution(self):
        sources = sorted((ROOT / "agents").glob("*.md"))
        self.assertEqual(17, len(sources))
        for source in sources:
            lines = source.read_text(encoding="utf-8-sig").splitlines()
            end = lines.index("---", 1)
            frontmatter = {}
            for line in lines[1:end]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip().strip('"').strip("'")
            for key, expected in EXPECTED_ATTRIBUTION.items():
                self.assertEqual(expected, frontmatter.get(key), f"{source.name}: {key}")

            compiled = {
                "claude": ROOT / "dist" / "claude" / f"{source.stem}.md",
                "copilot": ROOT / "dist" / "copilot" / f"{source.stem}.agent.md",
                "codex": ROOT / "dist" / "codex" / f"{source.stem}.toml",
                "cursor": ROOT / "dist" / "cursor" / f"{source.stem}.md",
            }
            for runtime, artifact in compiled.items():
                text = artifact.read_text(encoding="utf-8")
                for expected in EXPECTED_ATTRIBUTION.values():
                    self.assertIn(expected, text, f"{runtime}: {source.name}")
                self.assertNotIn('author: "SDD Toolkit Maintainers"', text, f"{runtime}: {source.name}")

    def test_removed_agents_are_absent_from_sources_and_runtime_outputs(self):
        source_names = {path.stem for path in (ROOT / "agents").glob("*.md")}
        self.assertEqual(17, len(source_names))
        self.assertTrue(REMOVED_AGENTS.isdisjoint(source_names))

        patterns = {
            "claude": "*.md",
            "copilot": "*.agent.md",
            "codex": "*.toml",
            "cursor": "*.md",
        }
        for runtime, pattern in patterns.items():
            artifacts = list((ROOT / "dist" / runtime).glob(pattern))
            self.assertEqual(17, len(artifacts), runtime)
            for removed in REMOVED_AGENTS:
                self.assertFalse(any(path.name.startswith(removed + ".") for path in artifacts))

    def test_active_routing_and_installation_contracts_do_not_reference_removed_agents(self):
        files = [
            ROOT / "README.md",
            ROOT / "install.ps1",
            ROOT / "install.sh",
            ROOT / "scripts" / "sdd_user_state.py",
            ROOT / ".github" / "workflows" / "ci.yml",
            *(ROOT / "agents").glob("*.md"),
        ]
        combined = "\n".join(path.read_text(encoding="utf-8-sig") for path in files)
        for removed in REMOVED_AGENTS:
            self.assertNotIn(removed, combined)


if __name__ == "__main__":
    unittest.main()
