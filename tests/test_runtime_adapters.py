try:  # tomllib entrou na stdlib no 3.11; tomli tem a mesma API no piso 3.9.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - depende da versao do runner
    import tomli as tomllib
import unittest
import json
import shutil
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator
from scripts import sdd_runtime
from scripts.sdd_compile import compile_agents, compile_shared_skills, filter_sections


ROOT = Path(__file__).resolve().parents[1]


class RuntimeAdapterTests(unittest.TestCase):
    def test_registry_contains_native_runtimes_and_capabilities(self):
        adapters = sdd_runtime.load_adapters(ROOT)
        self.assertEqual(["claude", "codex", "copilot", "cursor"], list(adapters))
        self.assertEqual(["codex", "cursor"], sdd_runtime.selected_runtimes("codex,cursor", adapters))
        self.assertIn("toml-agents", adapters["codex"].capabilities)
        self.assertIn("markdown-agents", adapters["cursor"].capabilities)

    def test_native_artifacts_are_parseable_and_sections_are_filtered(self):
        codex = sorted((ROOT / "dist" / "codex").glob("*.toml"))
        cursor = sorted((ROOT / "dist" / "cursor").glob("*.md"))
        source_count = len(list((ROOT / "agents").glob("*.md")))
        self.assertEqual(source_count, len(codex))
        self.assertEqual(source_count, len(cursor))
        for artifact in codex:
            parsed = tomllib.loads(artifact.read_text(encoding="utf-8"))
            self.assertTrue(parsed["name"])
            self.assertTrue(parsed["developer_instructions"])
        self.assertNotIn("<!-- @claude -->", cursor[0].read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "schemas" / "build-manifest.schema.json").read_text(encoding="utf-8"))
        inventory = json.loads((ROOT / "dist" / "build-manifest.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(inventory)

    def test_section_parser_rejects_unclosed_or_unexpected_blocks(self):
        self.assertEqual("common\ncodex\n", filter_sections("common\n<!-- @codex -->\ncodex\n<!-- @end -->", "codex"))
        with self.assertRaises(ValueError):
            filter_sections("<!-- @codex -->\nmissing end", "codex")
        with self.assertRaises(ValueError):
            filter_sections("<!-- @end -->", "codex")

    def test_compiler_rejects_agent_without_complete_attribution(self):
        with tempfile.TemporaryDirectory() as directory:
            kit_root = Path(directory)
            shutil.copytree(ROOT / "runtimes", kit_root / "runtimes")
            shutil.copytree(ROOT / "metadata", kit_root / "metadata")
            source_root = kit_root / "agents"
            source_root.mkdir()
            (source_root / "missing-author.md").write_text(
                "---\nname: missing-author\ndescription: test\nversion: 1.0.0\ncapabilities: read\n---\nbody\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Missing agent attribution"):
                compile_agents(kit_root, "cursor")

    def test_versioned_capabilities_fail_closed_for_unknown_output(self):
        unknown = sdd_runtime.versioned_capabilities(ROOT, "codex", "development build")
        self.assertEqual("unknown-version", unknown["status"])
        self.assertEqual([], unknown["capabilities"])
        known = sdd_runtime.versioned_capabilities(ROOT, "codex", "codex 1.2.3")
        self.assertEqual("compatible", known["status"])
        self.assertIn("toml-agents", known["capabilities"])

    def test_compiler_prunes_only_stale_managed_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            kit_root = Path(directory)
            shutil.copytree(ROOT / "runtimes", kit_root / "runtimes")
            shutil.copytree(ROOT / "metadata", kit_root / "metadata")
            (kit_root / "agents").mkdir()
            shutil.copy2(
                ROOT / "agents" / "sdd-bootstrap.md",
                kit_root / "agents" / "sdd-bootstrap.md",
            )
            skill_source = kit_root / "templates" / "skills" / "playwright-e2e-testing"
            skill_source.mkdir(parents=True)
            shutil.copy2(
                ROOT / "templates" / "skills" / "playwright-e2e-testing" / "SKILL.md",
                skill_source / "SKILL.md",
            )

            stale_agent = kit_root / "dist" / "cursor" / "removed-agent.md"
            stale_agent.parent.mkdir(parents=True)
            stale_agent.write_text("stale", encoding="utf-8")
            stale_skill = kit_root / "dist" / "shared" / "skills" / "removed-skill" / "SKILL.md"
            stale_skill.parent.mkdir(parents=True)
            stale_skill.write_text("stale", encoding="utf-8")

            compile_agents(kit_root, "cursor")
            compile_shared_skills(kit_root, ["cursor"])

            self.assertFalse(stale_agent.exists())
            self.assertFalse(stale_skill.parent.exists())
            self.assertTrue((kit_root / "dist" / "cursor" / "sdd-bootstrap.md").is_file())
            self.assertTrue(
                (kit_root / "dist" / "shared" / "skills" / "playwright-e2e-testing" / "SKILL.md").is_file()
            )


if __name__ == "__main__":
    unittest.main()
