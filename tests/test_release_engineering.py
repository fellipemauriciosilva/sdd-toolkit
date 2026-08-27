import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sdd

RELEASE = ROOT / "scripts" / "sdd_release.py"
DCO = ROOT / "scripts" / "check_dco.py"


class ReleaseEngineeringTests(unittest.TestCase):
    def test_fake_harness_detection_is_versioned_and_does_not_collapse_all(self):
        profile = ROOT / "tests" / "fixture-profile"
        with mock.patch("sdd_discovery.shutil.which", side_effect=lambda name: f"/fake/{name}" if name in {"codex", "claude"} else None), mock.patch(
            "sdd_discovery.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, stdout="Codex 1.2.3\n", stderr=""),
        ):
            report = sdd.detect_harnesses(profile, ROOT, "all")
        self.assertEqual({"claude", "codex", "copilot", "cursor"}, set(report))
        self.assertEqual("compatible", report["codex"]["capability_status"])
        self.assertIn("toml-agents", report["codex"]["capabilities"])
        self.assertEqual("not-installed", report["copilot"]["capability_status"])

    def test_release_builder_generates_packages_checksums_sbom_and_provenance(self):
        with tempfile.TemporaryDirectory(prefix="sdd-release-") as temporary:
            output = Path(temporary) / "release"
            completed = subprocess.run(
                [sys.executable, str(RELEASE), "--kit-root", str(ROOT), "--out-dir", str(output)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual("ready", report["status"])
            self.assertTrue((output / "SHA256SUMS").is_file())
            self.assertTrue((output / "sbom.cdx.json").is_file())
            provenance = json.loads((output / "provenance.json").read_text(encoding="utf-8"))
            self.assertEqual("Felipe Maurício da Silva", provenance["identity"]["name"])
            for artifact in report["artifacts"]:
                self.assertTrue((output / artifact["name"]).is_file())

    def test_release_archives_are_reproducible(self):
        with tempfile.TemporaryDirectory(prefix="sdd-release-repeat-") as temporary:
            root = Path(temporary)
            first, second = root / "first", root / "second"
            for output in (first, second):
                completed = subprocess.run([sys.executable, str(RELEASE), "--kit-root", str(ROOT), "--out-dir", str(output)], capture_output=True, text=True, check=False)
                self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual((first / "SHA256SUMS").read_text(encoding="utf-8"), (second / "SHA256SUMS").read_text(encoding="utf-8"))
            self.assertEqual((first / "provenance.json").read_bytes(), (second / "provenance.json").read_bytes())

    def test_extracted_release_contains_a_self_sufficient_user_installer(self):
        with tempfile.TemporaryDirectory(prefix="sdd-release-install-") as temporary:
            root = Path(temporary)
            output = root / "release"
            subprocess.run([sys.executable, str(RELEASE), "--kit-root", str(ROOT), "--out-dir", str(output)], check=True, capture_output=True, text=True)
            archive = next(output.glob("*.zip"))
            with zipfile.ZipFile(archive) as package:
                self.assertNotIn("sdd-toolkit/docs/ROADMAP.local.md", package.namelist())
                self.assertIn("sdd-toolkit/docs/MAINTAINERS.md", package.namelist())
                self.assertIn("sdd-toolkit/docs/THIRD_PARTY_NOTICES.md", package.namelist())
                package.extractall(root / "unpacked")
            kit = root / "unpacked" / "sdd-toolkit"
            environment = {**os.environ, "SDD_TOOLKIT_STATE_DIR": str(root / "state")}
            installed = subprocess.run(
                [sys.executable, str(kit / "scripts" / "sdd.py"), "install", "--scope", "user", "--profile-root", str(root / "profile"), "--runtime", "codex", "--apply", "--json"],
                check=False, capture_output=True, text=True, env=environment,
            )
            self.assertEqual(0, installed.returncode, installed.stderr)
            self.assertTrue((root / "profile" / ".codex" / "agents" / "sdd-bootstrap.toml").is_file())

    def test_root_document_hygiene_keeps_only_public_entry_points(self):
        allowed = {
            "README.md", "CHANGELOG.md", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md",
            "LICENSE", "SECURITY.md", "SUPPORT.md", "VERSION", "requirements-dev.txt",
            "install.ps1", "install.sh", ".gitignore",
        }
        root_files = {path.name for path in ROOT.iterdir() if path.is_file()}
        self.assertEqual(allowed, root_files)

    def test_public_readme_is_a_concise_entry_point_with_reference_docs(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(readme.splitlines()), 220)
        for document in (
            "ARCHITECTURE.md", "PIPELINE.md", "AGENTS.md", "SKILLS.md",
            "CLI-REFERENCE.md", "EVALUATIONS.md",
        ):
            self.assertTrue((ROOT / "docs" / document).is_file(), document)
            self.assertIn(f"docs/{document}", readme)

    def test_dco_checker_accepts_a_signed_commit_body(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import check_dco
        with mock.patch.object(check_dco, "commits", return_value=[("abc", "change\n\nSigned-off-by: Example <dev@example.test>\n")]):
            with mock.patch.object(sys, "argv", [str(DCO), "--range", "HEAD~1..HEAD"]):
                self.assertEqual(0, check_dco.main())


if __name__ == "__main__":
    unittest.main()
