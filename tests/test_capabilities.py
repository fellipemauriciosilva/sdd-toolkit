import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"read", "write", "terminal", "questions"}


def source_frontmatter(path: Path):
    values = {}
    in_header = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip("\ufeff").strip() == "---":
            if not in_header:
                in_header = True
            else:
                break
            continue
        if in_header and ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


class CapabilityTests(unittest.TestCase):
    def test_every_source_agent_declares_safe_capabilities(self):
        agents = sorted((ROOT / "agents").glob("*.md"))
        self.assertTrue(agents)
        for agent in agents:
            values = source_frontmatter(agent)
            self.assertTrue(values.get("capabilities"), agent.name)
            capabilities = {item.strip() for item in values["capabilities"].split(",") if item.strip()}
            self.assertTrue(capabilities)
            self.assertTrue(capabilities <= ALLOWED, f"{agent.name}: {capabilities - ALLOWED}")
            self.assertIn("read", capabilities, agent.name)

    def test_compiled_copilot_tools_match_declared_capabilities(self):
        for source in sorted((ROOT / "agents").glob("*.md")):
            values = source_frontmatter(source)
            capabilities = {item.strip() for item in values["capabilities"].split(",") if item.strip()}
            compiled = ROOT / "dist" / "copilot" / f"{values['name']}.agent.md"
            self.assertTrue(compiled.is_file(), compiled)
            text = compiled.read_text(encoding="utf-8")
            tools = set(re.findall(r"^\s+- ([^\r\n]+)$", text, flags=re.MULTILINE))
            if "read" in capabilities:
                self.assertIn("search/fileSearch", tools)
                self.assertIn("search/textSearch", tools)
            if "write" in capabilities:
                self.assertIn("edit/editFiles", tools)
                self.assertIn("edit/createFile", tools)
            else:
                self.assertNotIn("edit/editFiles", tools)
                self.assertNotIn("edit/createFile", tools)
            if "terminal" in capabilities:
                self.assertIn("execute/runInTerminal", tools)
                self.assertIn("execute/getTerminalOutput", tools)
            else:
                self.assertNotIn("execute/runInTerminal", tools)
                self.assertNotIn("execute/getTerminalOutput", tools)
            if "questions" in capabilities:
                self.assertIn("vscode/askQuestions", tools)
            else:
                self.assertNotIn("vscode/askQuestions", tools)


if __name__ == "__main__":
    unittest.main()
