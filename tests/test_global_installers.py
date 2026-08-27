import json
import os
import platform
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


class GlobalInstallerTests(unittest.TestCase):
    def command(self, install_root: Path, profile_root: Path, dry_run: bool = False):
        system = platform.system()
        if system == "Windows":
            command = [
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(ROOT / "install.ps1"),
                "-Scope", "user", "-Runtime", "copilot",
                "-InstallRoot", str(install_root),
                "-ProfileRoot", str(profile_root),
                "-NoPath",
            ]
            if dry_run:
                command.append("-DryRun")
            return command
        command = [
            "bash", str(ROOT / "install.sh"),
            "--scope=user", "--runtime=copilot",
            f"--install-root={install_root}",
            f"--profile-root={profile_root}",
            "--no-path",
        ]
        if dry_run:
            command.append("--dry-run")
        return command

    def test_global_installer_dry_run_and_apply(self):
        with tempfile.TemporaryDirectory(prefix="sdd-global-wrapper-") as temporary:
            fixture = Path(temporary)
            install_root = fixture / "global root"
            profile_root = fixture / "user profile"
            state_root = fixture / "state"
            env = {**os.environ, "SDD_TOOLKIT_STATE_DIR": str(state_root)}

            preview = subprocess.run(
                self.command(install_root, profile_root, dry_run=True),
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, preview.returncode, msg=preview.stderr or preview.stdout)
            self.assertFalse(install_root.exists())
            self.assertFalse(profile_root.exists())
            self.assertFalse(state_root.exists())

            applied = subprocess.run(
                self.command(install_root, profile_root),
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, applied.returncode, msg=applied.stderr or applied.stdout)
            self.assertTrue((profile_root / ".copilot" / "agents" / "sdd-bootstrap.agent.md").is_file())
            self.assertTrue((profile_root / ".copilot" / "agents" / "sdd-generate-e2e-tests.agent.md").is_file())
            self.assertTrue((profile_root / ".copilot" / "skills" / "playwright-e2e-testing" / "SKILL.md").is_file())
            self.assertTrue((profile_root / ".copilot" / "skills").is_dir())
            self.assertTrue((state_root / "user" / "installation.json").is_file())
            installation = json.loads((state_root / "user" / "installation.json").read_text(encoding="utf-8"))
            self.assertEqual("sdd-toolkit", installation["cli"]["owner"])
            self.assertEqual("none", installation["path_integration"]["strategy"])

            if platform.system() == "Windows":
                shim = install_root / "bin" / "sdd.cmd"
                version = subprocess.run(
                    ["cmd.exe", "/d", "/c", str(shim), "--version"],
                    capture_output=True, text=True, check=False, env=env,
                )
            else:
                shim = install_root / "bin" / "sdd"
                version = subprocess.run(
                    [str(shim), "--version"], capture_output=True, text=True, check=False, env=env,
                )
            self.assertTrue(shim.is_file())
            self.assertEqual(0, version.returncode, msg=version.stderr or version.stdout)
            self.assertEqual(VERSION, version.stdout.strip())

    def test_organization_scope_fails_closed(self):
        if platform.system() == "Windows":
            command = [
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(ROOT / "install.ps1"), "-Scope", "organization",
            ]
        else:
            command = ["bash", str(ROOT / "install.sh"), "--scope=organization"]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("organization", (result.stderr + result.stdout).lower())


if __name__ == "__main__":
    unittest.main()
