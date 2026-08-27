"""`dist/` must be a byte-exact recompile of `agents/`, never hand-edited."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "scripts" / "sdd_compile.py"
INVENTORY = ROOT / "scripts" / "build_inventory.py"
COPIED = ("agents", "templates", "metadata", "runtimes", "scripts")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree(root):
    return {
        path.relative_to(root).as_posix(): digest(path)
        for path in sorted((root / "dist").rglob("*"))
        if path.is_file() and path.name != "build-manifest.json"
    }


class DistSyncTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="sdd-dist-")
        self.kit = Path(self.directory.name) / "kit"
        self.kit.mkdir()
        for name in COPIED:
            shutil.copytree(ROOT / name, self.kit / name, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(ROOT / "VERSION", self.kit / "VERSION")
        self.addCleanup(self.directory.cleanup)

    def compile(self):
        completed = subprocess.run(
            [sys.executable, str(COMPILER), "--kit-root", str(self.kit), "--runtime", "all"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, completed.returncode, msg=completed.stderr)

    def test_dist_matches_a_clean_recompile(self):
        self.compile()
        self.assertEqual(tree(ROOT), tree(self.kit))

    def test_compilation_is_deterministic(self):
        self.compile()
        first = tree(self.kit)
        self.compile()
        self.assertEqual(first, tree(self.kit))

    def test_build_manifest_matches_the_compiled_artifacts(self):
        completed = subprocess.run(
            [sys.executable, str(INVENTORY), "--kit-root", str(ROOT)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, completed.returncode, msg=completed.stderr)
        rebuilt = json.loads(completed.stdout)
        stored = json.loads((ROOT / "dist" / "build-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(rebuilt, stored)
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), stored["toolkit_version"])


if __name__ == "__main__":
    unittest.main()
