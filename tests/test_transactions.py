import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, RefResolver


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "sdd.py"


class TransactionTests(unittest.TestCase):
    def test_preview_plan_id_can_guard_apply(self):
        with tempfile.TemporaryDirectory(prefix="sdd-transaction-plan-") as temporary:
            root = Path(temporary)
            profile = root / "profile"
            state = root / "state"
            env = {**os.environ, "SDD_TOOLKIT_STATE_DIR": str(state)}
            preview = subprocess.run(
                [sys.executable, str(CLI), "install", "--scope", "user", "--profile-root", str(profile),
                 "--runtime", "copilot", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, preview.returncode, msg=preview.stderr)
            plan_id = json.loads(preview.stdout)["plan_id"]
            applied = subprocess.run(
                [sys.executable, str(CLI), "install", "--scope", "user", "--profile-root", str(profile),
                 "--runtime", "copilot", "--plan-id", plan_id, "--apply", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, applied.returncode, msg=applied.stderr)
            self.assertEqual("committed", json.loads(applied.stdout)["transaction_status"])

    def test_transaction_schemas_accept_runtime_journal(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import sdd_transaction as transaction

        with tempfile.TemporaryDirectory(prefix="sdd-transaction-schema-") as temporary:
            root = Path(temporary)
            state = root / "state"
            profile = root / "profile"
            target = profile / ".copilot" / "agents" / "test.agent.md"
            plan = transaction.build_plan("install", profile, [{
                "id": "asset-0000", "kind": "asset", "operation": "create",
                "target": str(target), "before_sha256": None,
                "after_sha256": "a" * 64, "owner": "sdd-toolkit",
            }], [profile / ".copilot"])
            journal = transaction.Transaction.start(state, plan).journal
            plan_schema_path = ROOT / "schemas" / "transaction-plan.schema.json"
            journal_schema_path = ROOT / "schemas" / "transaction-journal.schema.json"
            plan_schema = json.loads(plan_schema_path.read_text(encoding="utf-8"))
            journal_schema = json.loads(journal_schema_path.read_text(encoding="utf-8"))
            Draft202012Validator(plan_schema, format_checker=FormatChecker()).validate(plan)
            resolver = RefResolver.from_schema(journal_schema, store={plan_schema["$id"]: plan_schema})
            Draft202012Validator(journal_schema, resolver=resolver, format_checker=FormatChecker()).validate(journal)

    def test_cli_recovers_install_after_forced_process_exit(self):
        with tempfile.TemporaryDirectory(prefix="sdd-transaction-crash-") as temporary:
            root = Path(temporary)
            profile = root / "profile"
            state = root / "state"
            env = {
                **os.environ,
                "SDD_TOOLKIT_STATE_DIR": str(state),
                "SDD_TOOLKIT_TEST_MODE": "1",
                "SDD_TOOLKIT_FAULT_AT": "after-assets",
            }
            crashed = subprocess.run(
                [sys.executable, str(CLI), "install", "--scope", "user", "--profile-root", str(profile),
                 "--runtime", "copilot", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(97, crashed.returncode, msg=crashed.stderr)
            self.assertTrue((profile / ".copilot" / "agents" / "sdd-bootstrap.agent.md").is_file())
            self.assertFalse((state / "user" / "installation.json").exists())

            clean_env = {**os.environ, "SDD_TOOLKIT_STATE_DIR": str(state)}
            status = subprocess.run(
                [sys.executable, str(CLI), "transaction", "status", "--scope", "user", "--active-only", "--json"],
                capture_output=True, text=True, check=False, env=clean_env,
            )
            self.assertEqual(2, status.returncode)
            self.assertEqual("recovery-required", json.loads(status.stdout)["status"])

            doctor = subprocess.run(
                [sys.executable, str(CLI), "doctor", "--scope", "user", "--profile-root", str(profile), "--json"],
                capture_output=True, text=True, check=False, env=clean_env,
            )
            self.assertEqual(2, doctor.returncode)
            doctor_report = json.loads(doctor.stdout)
            self.assertEqual("blocked", doctor_report["status"])
            self.assertIn("transaction_recovery_required", {item["code"] for item in doctor_report["issues"]})

            preview = subprocess.run(
                [sys.executable, str(CLI), "transaction", "recover", "--scope", "user", "--json"],
                capture_output=True, text=True, check=False, env=clean_env,
            )
            self.assertEqual(0, preview.returncode, msg=preview.stderr)
            self.assertEqual("ready", json.loads(preview.stdout)["status"])

            recovered = subprocess.run(
                [sys.executable, str(CLI), "transaction", "recover", "--scope", "user", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=clean_env,
            )
            self.assertEqual(0, recovered.returncode, msg=recovered.stderr)
            self.assertEqual("recovered", json.loads(recovered.stdout)["status"])
            self.assertFalse((profile / ".copilot" / "agents" / "sdd-bootstrap.agent.md").exists())

    def test_cli_recovers_assets_and_shim_in_one_transaction(self):
        with tempfile.TemporaryDirectory(prefix="sdd-transaction-shim-") as temporary:
            root = Path(temporary)
            profile = root / "profile"
            state = root / "state"
            install_root = root / "install"
            fault_environment = {
                **os.environ,
                "SDD_TOOLKIT_STATE_DIR": str(state),
                "SDD_TOOLKIT_TEST_MODE": "1",
                "SDD_TOOLKIT_FAULT_AT": "after-shim",
            }
            crashed = subprocess.run(
                [sys.executable, str(CLI), "install", "--scope", "user", "--profile-root", str(profile),
                 "--runtime", "copilot", "--with-cli", "--install-root", str(install_root),
                 "--no-path", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=fault_environment,
            )
            self.assertEqual(97, crashed.returncode, msg=crashed.stderr)
            shim = install_root / "bin" / ("sdd.cmd" if os.name == "nt" else "sdd")
            asset = profile / ".copilot" / "agents" / "sdd-bootstrap.agent.md"
            self.assertTrue(shim.is_file())
            self.assertTrue(asset.is_file())

            clean_environment = {**os.environ, "SDD_TOOLKIT_STATE_DIR": str(state)}
            recovered = subprocess.run(
                [sys.executable, str(CLI), "transaction", "recover", "--scope", "user", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=clean_environment,
            )
            self.assertEqual(0, recovered.returncode, msg=recovered.stderr)
            self.assertFalse(shim.exists())
            self.assertFalse(asset.exists())

    def test_recovery_preserves_file_modified_after_crash(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import sdd_transaction as transaction

        with tempfile.TemporaryDirectory(prefix="sdd-transaction-conflict-") as temporary:
            root = Path(temporary)
            state = root / "state"
            profile = root / "profile"
            target = profile / ".copilot" / "agents" / "test.agent.md"
            target.parent.mkdir(parents=True)
            target.write_text("before\n", encoding="utf-8")
            before = transaction.sha256_file(target)
            after_content = b"after\n"
            plan = transaction.build_plan("update", profile, [{
                "id": "asset-0000", "kind": "asset", "operation": "update",
                "target": str(target), "before_sha256": before,
                "after_sha256": transaction.sha256_bytes(after_content), "owner": "sdd-toolkit",
            }], [profile / ".copilot"])
            current = transaction.Transaction.start(state, plan)
            current.track_file("asset-0000")
            target.write_bytes(after_content)
            target.write_text("user change\n", encoding="utf-8")
            result = transaction.recover_transactions(state, apply=True)
            self.assertEqual("blocked", result["status"])
            self.assertEqual("user change\n", target.read_text(encoding="utf-8"))

    def test_cli_recovers_uninstall_after_forced_process_exit(self):
        """Um uninstall interrompido depois dos assets deve ser revertido, não completado."""
        with tempfile.TemporaryDirectory(prefix="sdd-transaction-uninstall-") as temporary:
            root = Path(temporary)
            profile = root / "profile"
            state = root / "state"
            clean_env = {**os.environ, "SDD_TOOLKIT_STATE_DIR": str(state)}
            installed = subprocess.run(
                [sys.executable, str(CLI), "install", "--scope", "user", "--profile-root", str(profile),
                 "--runtime", "copilot", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=clean_env,
            )
            self.assertEqual(0, installed.returncode, msg=installed.stderr)
            asset = profile / ".copilot" / "agents" / "sdd-bootstrap.agent.md"
            manifest = state / "user" / "installation.json"
            self.assertTrue(asset.is_file())
            self.assertTrue(manifest.is_file())
            digest = hashlib.sha256(asset.read_bytes()).hexdigest()

            fault_env = {
                **clean_env,
                "SDD_TOOLKIT_TEST_MODE": "1",
                "SDD_TOOLKIT_FAULT_AT": "after-assets",
            }
            crashed = subprocess.run(
                [sys.executable, str(CLI), "uninstall", "--scope", "user", "--profile-root", str(profile),
                 "--apply", "--json"],
                capture_output=True, text=True, check=False, env=fault_env,
            )
            self.assertEqual(97, crashed.returncode, msg=crashed.stderr)
            # A transação morreu entre remover os assets e apagar o manifesto.
            self.assertFalse(asset.exists())
            self.assertTrue(manifest.is_file())

            status = subprocess.run(
                [sys.executable, str(CLI), "transaction", "status", "--scope", "user", "--active-only", "--json"],
                capture_output=True, text=True, check=False, env=clean_env,
            )
            self.assertEqual(2, status.returncode)
            self.assertEqual("recovery-required", json.loads(status.stdout)["status"])

            preview = subprocess.run(
                [sys.executable, str(CLI), "transaction", "recover", "--scope", "user", "--json"],
                capture_output=True, text=True, check=False, env=clean_env,
            )
            self.assertEqual(0, preview.returncode, msg=preview.stderr)
            self.assertEqual("ready", json.loads(preview.stdout)["status"])
            self.assertFalse(asset.exists(), "o preview não pode alterar nada")

            recovered = subprocess.run(
                [sys.executable, str(CLI), "transaction", "recover", "--scope", "user", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=clean_env,
            )
            self.assertEqual(0, recovered.returncode, msg=recovered.stderr)
            self.assertEqual("recovered", json.loads(recovered.stdout)["status"])
            self.assertTrue(asset.is_file())
            self.assertEqual(digest, hashlib.sha256(asset.read_bytes()).hexdigest(),
                             "o asset restaurado deve ser byte a byte o original")
            self.assertTrue(manifest.is_file())

    @unittest.skipIf(os.name == "nt", "Unix profile transaction")
    def test_cli_recovers_unix_path_block_after_crash(self):
        with tempfile.TemporaryDirectory(prefix="sdd-transaction-path-") as temporary:
            root = Path(temporary)
            profile = root / "profile"
            state = root / "state"
            environment = {**os.environ, "SDD_TOOLKIT_STATE_DIR": str(state)}
            installed = subprocess.run(
                [sys.executable, str(CLI), "install", "--scope", "user", "--profile-root", str(profile),
                 "--runtime", "copilot", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=environment,
            )
            self.assertEqual(0, installed.returncode, msg=installed.stderr)
            asset = profile / ".copilot" / "agents" / "sdd-bootstrap.agent.md"
            manifest = state / "user" / "installation.json"
            self.assertTrue(asset.is_file())
            self.assertTrue(manifest.is_file())
            bin_dir = root / "bin"
            shim = bin_dir / "sdd"
            bin_dir.mkdir()
            shim.write_text("#!/bin/sh\n", encoding="utf-8")
            shell_profile = profile / ".profile"
            shell_profile.write_text(
                f'# existing\n# >>> sdd-toolkit PATH >>>\nexport PATH="{bin_dir}:$PATH"\n# <<< sdd-toolkit PATH <<<\n',
                encoding="utf-8",
            )
            registered = subprocess.run(
                [sys.executable, str(CLI), "register-user-cli", "--shim-path", str(shim),
                 "--path-strategy", "unix-profile-block", "--path-entry", str(bin_dir),
                 "--path-target", str(shell_profile), "--json"],
                capture_output=True, text=True, check=False, env=environment,
            )
            self.assertEqual(0, registered.returncode, msg=registered.stderr)

            fault_environment = {
                **environment,
                "SDD_TOOLKIT_TEST_MODE": "1",
                "SDD_TOOLKIT_FAULT_AT": "after-path",
            }
            crashed = subprocess.run(
                [sys.executable, str(CLI), "uninstall", "--scope", "user", "--profile-root", str(profile),
                 "--apply", "--json"],
                capture_output=True, text=True, check=False, env=fault_environment,
            )
            self.assertEqual(97, crashed.returncode, msg=crashed.stderr)
            self.assertNotIn("sdd-toolkit PATH", shell_profile.read_text(encoding="utf-8"))

            recovered = subprocess.run(
                [sys.executable, str(CLI), "transaction", "recover", "--scope", "user", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=environment,
            )
            self.assertEqual(0, recovered.returncode, msg=recovered.stderr)
            self.assertIn("sdd-toolkit PATH", shell_profile.read_text(encoding="utf-8"))
            self.assertTrue(shim.is_file())

            fault_env = {
                **environment,
                "SDD_TOOLKIT_TEST_MODE": "1",
                "SDD_TOOLKIT_FAULT_AT": "after-assets",
            }
            crashed = subprocess.run(
                [sys.executable, str(CLI), "uninstall", "--scope", "user", "--profile-root", str(profile),
                 "--apply", "--json"],
                capture_output=True, text=True, check=False, env=fault_env,
            )
            self.assertEqual(97, crashed.returncode, msg=crashed.stderr)
            self.assertFalse(asset.exists())
            self.assertTrue(manifest.is_file())

            recovered = subprocess.run(
                [sys.executable, str(CLI), "transaction", "recover", "--scope", "user", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=environment,
            )
            self.assertEqual(0, recovered.returncode, msg=recovered.stderr)
            self.assertTrue(asset.is_file())
            self.assertTrue(manifest.is_file())


if __name__ == "__main__":
    unittest.main()
