import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "sdd.py"


class SourceLifecycleTests(unittest.TestCase):
    def git(self, directory, *arguments):
        return subprocess.run(
            ["git", "-C", str(directory), *arguments],
            capture_output=True, text=True, check=False,
        )

    def test_local_clone_ref_dirty_protection_and_status(self):
        with tempfile.TemporaryDirectory(prefix="sdd-source-") as temporary:
            root = Path(temporary)
            repository = root / "repository"
            repository.mkdir()
            for name in ("VERSION",):
                shutil.copy2(ROOT / name, repository / name)
            for directory in ("scripts", "dist", "templates", "schemas"):
                shutil.copytree(ROOT / directory, repository / directory)
            self.assertEqual(0, self.git(repository, "init", "-q").returncode)
            self.assertEqual(0, self.git(repository, "config", "user.email", "tests@example.invalid").returncode)
            self.assertEqual(0, self.git(repository, "config", "user.name", "SDD Tests").returncode)
            self.assertEqual(0, self.git(repository, "add", ".").returncode)
            self.assertEqual(0, self.git(repository, "commit", "-qm", "fixture").returncode)
            self.assertEqual(0, self.git(repository, "branch", "-M", "main").returncode)

            state = root / "state"
            source_root = root / "installed-kit"
            env = {**os.environ, "SDD_TOOLKIT_STATE_DIR": str(state)}
            repository_url = repository.as_uri()
            install = subprocess.run(
                [sys.executable, str(CLI), "source", "install", "--repository-url", repository_url,
                 "--source-root", str(source_root), "--channel", "main", "--ref", "main", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, install.returncode, msg=install.stderr)
            self.assertEqual("cloned", json.loads(install.stdout)["status"])
            self.assertTrue((source_root / "VERSION").is_file())

            status = subprocess.run(
                [sys.executable, str(CLI), "source", "status", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, status.returncode, msg=status.stderr)
            self.assertEqual("healthy", json.loads(status.stdout)["status"])

            offline = subprocess.run(
                [sys.executable, str(CLI), "source", "install", "--repository-url", repository_url,
                 "--source-root", str(source_root), "--offline", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, offline.returncode, msg=offline.stderr)
            self.assertEqual("offline-ready", json.loads(offline.stdout)["status"])

            (source_root / "local-change.txt").write_text("dirty\n", encoding="utf-8")
            blocked = subprocess.run(
                [sys.executable, str(CLI), "source", "update", "--repository-url", repository_url,
                 "--source-root", str(source_root), "--channel", "main", "--ref", "main", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(2, blocked.returncode)
            self.assertEqual("blocked", json.loads(blocked.stdout)["status"])
            self.assertTrue((source_root / "local-change.txt").is_file())

    def test_downgrade_requires_explicit_confirmation(self):
        with tempfile.TemporaryDirectory(prefix="sdd-source-downgrade-") as temporary:
            root = Path(temporary)
            repository = root / "repository"
            repository.mkdir()
            shutil.copy2(ROOT / "VERSION", repository / "VERSION")
            for directory in ("scripts", "dist", "templates", "schemas"):
                shutil.copytree(ROOT / directory, repository / directory)
            self.assertEqual(0, self.git(repository, "init", "-q").returncode)
            self.assertEqual(0, self.git(repository, "config", "user.email", "tests@example.invalid").returncode)
            self.assertEqual(0, self.git(repository, "config", "user.name", "SDD Tests").returncode)
            self.assertEqual(0, self.git(repository, "add", ".").returncode)
            self.assertEqual(0, self.git(repository, "commit", "-qm", "current").returncode)
            self.assertEqual(0, self.git(repository, "branch", "-M", "main").returncode)
            (repository / "VERSION").write_text("0.1.0\n", encoding="utf-8")
            self.assertEqual(0, self.git(repository, "add", "VERSION").returncode)
            self.assertEqual(0, self.git(repository, "commit", "-qm", "lower version").returncode)
            initial_ref = self.git(repository, "rev-parse", "HEAD~1").stdout.strip()
            self.assertEqual(0, self.git(repository, "branch", "current", initial_ref).returncode)

            state = root / "state"
            source_root = root / "installed-kit"
            env = {**os.environ, "SDD_TOOLKIT_STATE_DIR": str(state)}
            url = repository.as_uri()
            first = subprocess.run(
                [sys.executable, str(CLI), "source", "install", "--repository-url", url,
                 "--source-root", str(source_root), "--ref", "current", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(0, first.returncode, msg=first.stderr)
            blocked = subprocess.run(
                [sys.executable, str(CLI), "source", "update", "--repository-url", url,
                 "--source-root", str(source_root), "--ref", "main", "--apply", "--json"],
                capture_output=True, text=True, check=False, env=env,
            )
            self.assertEqual(2, blocked.returncode)
            self.assertEqual("downgrade_requires_confirmation", json.loads(blocked.stdout)["code"])


if __name__ == "__main__":
    unittest.main()
