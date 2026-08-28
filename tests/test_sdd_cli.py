import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "sdd.py"


class CliTests(unittest.TestCase):
    def test_architecture_cli_proposes_and_validates(self):
        proposed = subprocess.run(
            [sys.executable, str(CLI), "architecture", "propose", "--type", "feature",
             "--description", "Adicionar autenticação", "--json"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, proposed.returncode, msg=proposed.stderr)
        self.assertEqual("high", json.loads(proposed.stdout)["architecture_impact"])

    def test_version(self):
        version = subprocess.run([sys.executable, str(CLI), "--version"], capture_output=True, text=True, check=False)
        self.assertEqual(0, version.returncode)
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), version.stdout.strip())

    def test_about_exposes_the_canonical_public_identity(self):
        completed = subprocess.run(
            [sys.executable, str(CLI), "about", "--json"], capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, completed.returncode, msg=completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual("SDD Toolkit", report["project"])
        self.assertEqual("Felipe Maurício da Silva", report["maintainer"]["name"])
        self.assertEqual("fellipemauriciosilva@gmail.com", report["maintainer"]["email"])
        self.assertEqual("https://www.linkedin.com/in/felipe-mauricio-06685735/", report["maintainer"]["linkedin"])

    def test_agent_result_validation(self):
        with tempfile.TemporaryDirectory(prefix="sdd-result-") as temporary:
            result_path = Path(temporary) / "result.json"
            result_path.write_text(json.dumps({
                "schema_version": 1,
                "agent": "sdd-generate-tests",
                "agent_version": "4.0.0",
                "runtime": "copilot",
                "status": "completed",
                "summary": "Testes gerados.",
                "changes": [{"path": "tests/example", "action": "created"}],
                "evidence": [{"kind": "command", "source": "test command", "outcome": "passed"}],
                "decisions": [{"statement": "Framework existente reutilizado.", "confidence": "confirmed", "evidence_refs": [0]}],
                "preexisting_failures": [],
                "residual_risks": [],
                "blocked_on": [],
                "next_agent": "sdd-bootstrap",
            }), encoding="utf-8")
            validated = subprocess.run(
                [sys.executable, str(CLI), "result", "validate", "--file", str(result_path), "--json"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, validated.returncode, msg=validated.stderr)
            self.assertEqual("valid", json.loads(validated.stdout)["status"])

    def test_user_activation_preview_and_context_do_not_write_project(self):
        with tempfile.TemporaryDirectory(prefix="sdd-cli-") as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            state = root / "state"
            history = root / "history"
            env = {**os.environ, "SDD_TOOLKIT_STATE_DIR": str(state), "SDD_TOOLKIT_HISTORY_DIR": str(history)}
            preview = subprocess.run(
                [sys.executable, str(CLI), "activate", "--project-path", str(project), "--runtime", "copilot", "--dry-run", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, preview.returncode, msg=preview.stderr)
            preview_report = json.loads(preview.stdout)
            self.assertEqual("preview", preview_report["mode"])
            self.assertFalse((state / "user" / "activations.json").exists())

            applied = subprocess.run(
                [sys.executable, str(CLI), "activate", "--project-path", str(project), "--runtime", "copilot", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, applied.returncode, msg=applied.stderr)
            applied_report = json.loads(applied.stdout)
            self.assertEqual("activated", applied_report["status"])
            self.assertTrue(Path(applied_report["activation"]["workspace"]).is_dir())
            self.assertEqual(["copilot"], applied_report["activation"]["runtime_hints"])

            context = subprocess.run(
                [sys.executable, str(CLI), "context", "resolve", "--project-path", str(project), "--ticket", "ABC-123", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, context.returncode, msg=context.stderr)
            context_report = json.loads(context.stdout)
            self.assertEqual("user-activation", context_report["source"])
            self.assertTrue(context_report["spec_path"].endswith("ABC-123"))

    def test_activation_defaults_and_daily_handoff(self):
        with tempfile.TemporaryDirectory(prefix="sdd-cli-") as temporary:
            root = Path(temporary)
            project = root / "project"
            nested = project / "nested"
            nested.mkdir(parents=True)
            subprocess.run(["git", "init", str(project)], capture_output=True, text=True, check=False)
            state = root / "state"
            history = root / "history"
            env = {**os.environ, "SDD_TOOLKIT_STATE_DIR": str(state), "SDD_TOOLKIT_HISTORY_DIR": str(history)}

            before_activation = subprocess.run(
                [sys.executable, str(CLI), "start", "ABC-123", "--json"],
                capture_output=True, text=True, check=False, cwd=nested, env=env,
            )
            self.assertEqual(2, before_activation.returncode)
            self.assertEqual("activation-required", json.loads(before_activation.stdout)["status"])

            activated = subprocess.run(
                [sys.executable, str(CLI), "activate", "--json"],
                capture_output=True, text=True, check=False, cwd=nested, env=env,
            )
            self.assertEqual(0, activated.returncode, msg=activated.stderr)
            activation = json.loads(activated.stdout)["activation"]
            self.assertEqual(str(project.resolve()), activation["project_path"])
            self.assertNotIn("runtime", activation)

            started = subprocess.run(
                [sys.executable, str(CLI), "start", "ABC-123", "--json"],
                capture_output=True, text=True, check=False, cwd=nested, env=env,
            )
            self.assertEqual(0, started.returncode, msg=started.stderr)
            self.assertEqual("sdd-bootstrap", json.loads(started.stdout)["agent"])

            status = subprocess.run(
                [sys.executable, str(CLI), "status", "--json"],
                capture_output=True, text=True, check=False, cwd=nested, env=env,
            )
            self.assertEqual(0, status.returncode, msg=status.stderr)
            self.assertEqual("active", json.loads(status.stdout)["status"])

    def test_user_installation_is_profile_scoped_and_preserves_unknown_files(self):
        with tempfile.TemporaryDirectory(prefix="sdd-cli-") as temporary:
            root = Path(temporary)
            profile = root / "profile"
            state = root / "state"
            env = {**os.environ, "SDD_TOOLKIT_STATE_DIR": str(state)}
            preview = subprocess.run(
                [sys.executable, str(CLI), "install", "--scope", "user", "--profile-root", str(profile), "--runtime", "copilot", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, preview.returncode, msg=preview.stderr)
            self.assertEqual("preview", json.loads(preview.stdout)["mode"])
            self.assertFalse(profile.exists())

            applied = subprocess.run(
                [sys.executable, str(CLI), "install", "--scope", "user", "--profile-root", str(profile), "--runtime", "copilot", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, applied.returncode, msg=applied.stderr)
            report = json.loads(applied.stdout)
            self.assertEqual("installed", report["status"])
            self.assertFalse((root / "project" / ".github").exists())
            self.assertTrue((profile / ".copilot" / "agents" / "sdd-bootstrap.agent.md").is_file())
            self.assertTrue((profile / ".copilot" / "agents" / "sdd-generate-e2e-tests.agent.md").is_file())
            self.assertTrue((profile / ".copilot" / "skills" / "playwright-e2e-testing" / "SKILL.md").is_file())
            self.assertTrue((profile / ".copilot" / "skills").is_dir())
            self.assertTrue((state / "user" / "installation.json").is_file())

            custom = profile / ".copilot" / "agents" / "custom.agent.md"
            custom.write_text("custom agent\n", encoding="utf-8")
            second = subprocess.run(
                [sys.executable, str(CLI), "install", "--scope", "user", "--profile-root", str(profile), "--runtime", "copilot", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, second.returncode, msg=second.stderr)
            self.assertEqual("custom agent\n", custom.read_text(encoding="utf-8"))

    def test_user_doctor_update_and_uninstall_preserve_custom_files(self):
        with tempfile.TemporaryDirectory(prefix="sdd-cli-") as temporary:
            root = Path(temporary)
            profile = root / "profile"
            state = root / "state"
            env = {**os.environ, "SDD_TOOLKIT_STATE_DIR": str(state)}
            install = subprocess.run(
                [sys.executable, str(CLI), "install", "--scope", "user", "--profile-root", str(profile), "--runtime", "copilot", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, install.returncode, msg=install.stderr)
            custom = profile / ".copilot" / "agents" / "custom.agent.md"
            custom.write_text("keep me\n", encoding="utf-8")

            doctor = subprocess.run(
                [sys.executable, str(CLI), "doctor", "--scope", "user", "--profile-root", str(profile), "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, doctor.returncode, msg=doctor.stderr)
            self.assertEqual("healthy", json.loads(doctor.stdout)["status"])

            update = subprocess.run(
                [sys.executable, str(CLI), "update", "--scope", "user", "--profile-root", str(profile), "--runtime", "copilot", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, update.returncode, msg=update.stderr)
            self.assertEqual("keep me\n", custom.read_text(encoding="utf-8"))

            uninstall_preview = subprocess.run(
                [sys.executable, str(CLI), "uninstall", "--scope", "user", "--profile-root", str(profile), "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, uninstall_preview.returncode, msg=uninstall_preview.stderr)
            self.assertEqual("preview", json.loads(uninstall_preview.stdout)["mode"])
            self.assertTrue((profile / ".copilot" / "agents" / "sdd-bootstrap.agent.md").exists())

            uninstall = subprocess.run(
                [sys.executable, str(CLI), "uninstall", "--scope", "user", "--profile-root", str(profile), "--apply", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, uninstall.returncode, msg=uninstall.stderr)
            self.assertEqual("uninstalled", json.loads(uninstall.stdout)["status"])
            self.assertFalse((profile / ".copilot" / "agents" / "sdd-bootstrap.agent.md").exists())
            self.assertTrue(custom.exists())


if __name__ == "__main__":
    unittest.main()
