import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "sdd.py"
FORBIDDEN = ("sdd.config.md", ".sdd/installation-manifest.json", ".github/sdd-gates.config.md", "workspace-migrate", "sdd-state.py")


class NoProjectLegacyTests(unittest.TestCase):
    def test_public_cli_does_not_expose_project_installation_commands(self):
        help_text = subprocess.run([sys.executable, str(CLI), "--help"], capture_output=True, text=True, check=False).stdout
        for command in ("preflight", "init", "workspace-migrate"):
            self.assertNotIn(command, help_text)

    def test_release_content_has_no_project_installation_contract(self):
        excluded = {ROOT / "docs" / "ROADMAP.local.md"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or path in excluded or path == Path(__file__) or ".git" in path.parts or path.suffix not in {".md", ".py", ".json", ".sh", ".ps1", ".toml", ".yml", ".yaml", ".txt"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for forbidden in FORBIDDEN:
                self.assertNotIn(forbidden, text, path)


if __name__ == "__main__":
    unittest.main()
