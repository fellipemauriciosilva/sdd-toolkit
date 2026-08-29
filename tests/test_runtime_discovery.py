import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sdd_discovery


class RuntimeDiscoveryTests(unittest.TestCase):
    def test_quick_scan_does_not_probe_or_access_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            with mock.patch.dict(os.environ, {"PATH": ""}, clear=False), mock.patch("sdd_discovery.subprocess.run") as run:
                report = sdd_discovery.discover_runtimes(profile, ROOT, "all", "quick")
            self.assertEqual(2, report["schema_version"])
            self.assertFalse(report["network_accessed"])
            self.assertFalse(run.called)
            self.assertEqual("absent", report["runtimes"]["codex"]["status"])

    def test_extension_is_detected_without_a_cli(self):
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            extension = profile / ".vscode" / "extensions" / "openai.chatgpt-1.2.3"
            extension.mkdir(parents=True)
            (extension / "package.json").write_text(json.dumps({"publisher": "openai", "name": "chatgpt", "version": "1.2.3"}), encoding="utf-8")
            with mock.patch.dict(os.environ, {"PATH": ""}, clear=False), mock.patch("sdd_discovery.shutil.which", return_value=None):
                report = sdd_discovery.discover_runtimes(profile, ROOT, "codex", "quick")["runtimes"]["codex"]
            self.assertTrue(report["installed"])
            self.assertFalse(report["cli_available"])
            self.assertTrue(report["integration_ready"])
            self.assertEqual("present", report["status"])
            self.assertEqual("openai.chatgpt", report["components"][0]["id"])

    def test_all_path_candidates_are_preserved_as_a_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second = root / "first", root / "second"
            first.mkdir()
            second.mkdir()
            executable_name = "codex.exe" if os.name == "nt" else "codex"
            for directory in (first, second):
                candidate = directory / executable_name
                candidate.write_text("placeholder", encoding="utf-8")
            with mock.patch.dict(os.environ, {"PATH": os.pathsep.join([str(first), str(second)])}, clear=False), mock.patch("sdd_discovery.shutil.which", return_value=str(first / executable_name)):
                report = sdd_discovery.discover_runtimes(root, ROOT, "codex", "quick")["runtimes"]["codex"]
            self.assertEqual("conflict", report["status"])
            self.assertEqual(1, len(report["shadowed_executables"]))

    def test_full_scan_probes_the_selected_cli_with_fixed_version_arguments(self):
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            with mock.patch.dict(os.environ, {"PATH": ""}, clear=False), mock.patch("sdd_discovery.shutil.which", side_effect=lambda item: "/trusted/codex" if item == "codex" else None), mock.patch(
                "sdd_discovery.subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout="codex 1.2.3\n", stderr="")
            ) as run:
                report = sdd_discovery.discover_runtimes(profile, ROOT, "codex", "full")["runtimes"]["codex"]
            self.assertEqual("detected", report["version_status"])
            self.assertIn("toml-agents", report["capabilities"])
            # O caminho é normalizado pelo SO; comparar componentes evita fixar o separador.
            self.assertTrue(any(
                call.args[0][-1] == "--version" and Path(call.args[0][0]).parts[-2:] == ("trusted", "codex")
                for call in run.call_args_list
            ))

    def test_full_scan_reads_vscode_extension_inventory_with_fixed_arguments(self):
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            def which(name):
                return "/trusted/code" if name == "code" else None
            with mock.patch.dict(os.environ, {"PATH": ""}, clear=False), mock.patch("sdd_discovery.shutil.which", side_effect=which), mock.patch(
                "sdd_discovery.subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout="openai.chatgpt@1.2.3\n", stderr="")
            ) as run:
                report = sdd_discovery.discover_runtimes(profile, ROOT, "codex", "full")["runtimes"]["codex"]
            self.assertFalse(report["cli_available"])
            self.assertTrue(report["integration_ready"])
            component = report["components"][0]
            self.assertEqual("openai.chatgpt", component["id"])
            self.assertEqual("vscode-cli", component["evidence"][0]["source"])
            self.assertIn(["/trusted/code", "--list-extensions", "--show-versions"], [call.args[0] for call in run.call_args_list])

    def test_cursor_uses_the_official_cli_command(self):
        adapter = __import__("sdd_runtime").load_adapters(ROOT)["cursor"]
        self.assertEqual(("cursor-agent",), adapter.commands)

    def test_extension_bundled_binary_is_not_selected_as_a_global_cli(self):
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            bundled = profile / ".vscode" / "extensions" / "openai.chatgpt-1.0.0" / "bin" / "codex"
            bundled.parent.mkdir(parents=True)
            bundled.write_text("placeholder", encoding="utf-8")
            with mock.patch.dict(os.environ, {"PATH": ""}, clear=False), mock.patch("sdd_discovery.shutil.which", return_value=str(bundled)):
                report = sdd_discovery.discover_runtimes(profile, ROOT, "codex", "quick")["runtimes"]["codex"]
            self.assertFalse(report["cli_available"])
            self.assertEqual([str(bundled.resolve())], report["embedded_executables"])
            self.assertEqual("embedded-cli", report["components"][0]["kind"])

    def test_detected_install_selects_only_ready_runtime_targets(self):
        cli = ROOT / "scripts" / "sdd.py"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / "profile"
            extension = profile / ".vscode" / "extensions" / "anthropic.claude-code-1.0.0"
            extension.mkdir(parents=True)
            (extension / "package.json").write_text(json.dumps({"publisher": "anthropic", "name": "claude-code", "version": "1.0.0"}), encoding="utf-8")
            environment = {**os.environ, "PATH": "", "SDD_TOOLKIT_STATE_DIR": str(root / "state")}
            completed = subprocess.run([sys.executable, str(cli), "install", "--scope", "user", "--runtime", "detected", "--profile-root", str(profile), "--no-path", "--json"], capture_output=True, text=True, check=False, env=environment)
            self.assertEqual(0, completed.returncode, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(["claude"], report["selected_runtimes"])
            self.assertTrue(report["files"])
            self.assertTrue(all(".claude" in item["path"] for item in report["files"]))

    def test_quick_cache_hits_and_invalidates_when_extension_root_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / "profile"
            environment = {"PATH": "", "SDD_TOOLKIT_STATE_DIR": str(root / "state")}
            with mock.patch.dict(os.environ, environment, clear=False), mock.patch("sdd_discovery.shutil.which", return_value=None):
                first = sdd_discovery.discover_runtimes(profile, ROOT, "codex", "quick", use_cache=True)
                second = sdd_discovery.discover_runtimes(profile, ROOT, "codex", "quick", use_cache=True)
                extension = profile / ".vscode" / "extensions" / "openai.chatgpt-1.0.0"
                extension.mkdir(parents=True)
                (extension / "package.json").write_text(json.dumps({"publisher": "openai", "name": "chatgpt", "version": "1.0.0"}), encoding="utf-8")
                third = sdd_discovery.discover_runtimes(profile, ROOT, "codex", "quick", use_cache=True)
            self.assertEqual("miss", first["cache"]["status"])
            self.assertEqual("hit", second["cache"]["status"])
            self.assertEqual("miss", third["cache"]["status"])
            self.assertTrue(third["runtimes"]["codex"]["integration_ready"])

    def test_quick_cache_invalidates_when_an_existing_manifest_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / "profile"
            manifest = profile / ".vscode" / "extensions" / "openai.chatgpt-1.0.0" / "package.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"publisher": "openai", "name": "chatgpt", "version": "1.0.0"}), encoding="utf-8")
            environment = {"PATH": "", "SDD_TOOLKIT_STATE_DIR": str(root / "state")}
            with mock.patch.dict(os.environ, environment, clear=False), mock.patch("sdd_discovery.shutil.which", return_value=None):
                first = sdd_discovery.discover_runtimes(profile, ROOT, "codex", "quick", use_cache=True)
                second = sdd_discovery.discover_runtimes(profile, ROOT, "codex", "quick", use_cache=True)
                manifest.write_text(json.dumps({"publisher": "openai", "name": "chatgpt", "version": "2.0.0"}), encoding="utf-8")
                third = sdd_discovery.discover_runtimes(profile, ROOT, "codex", "quick", use_cache=True)
            self.assertEqual("miss", first["cache"]["status"])
            self.assertEqual("hit", second["cache"]["status"])
            self.assertEqual("miss", third["cache"]["status"])
            self.assertEqual("2.0.0", third["runtimes"]["codex"]["components"][0]["version"])

    def test_portable_mode_extension_root_is_discovered_explicitly(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile, portable = root / "profile", root / "portable"
            extension = portable / "data" / "extensions" / "openai.chatgpt-1.0.0"
            extension.mkdir(parents=True)
            (extension / "package.json").write_text(json.dumps({"publisher": "openai", "name": "chatgpt", "version": "1.0.0"}), encoding="utf-8")
            with mock.patch.dict(os.environ, {"PATH": ""}, clear=False), mock.patch("sdd_discovery.shutil.which", return_value=None):
                report = sdd_discovery.discover_runtimes(profile, ROOT, "codex", "quick", portable_roots=[portable])
            component = report["runtimes"]["codex"]["components"][0]
            self.assertEqual("vscode-portable", component["host"])
            self.assertTrue(report["runtimes"]["codex"]["integration_ready"])


if __name__ == "__main__":
    unittest.main()
