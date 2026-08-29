"""The public-content gate must fail closed on real leaks and stay quiet otherwise.

A false positive here is not harmless: it blocks every release until someone
edits unrelated content, which trains people to loosen the pattern under
pressure. So both directions are asserted.
"""

import unittest

from scripts.public_content_check import BLOCKED, PERSONAL_PATH, SECRET


class SecretDetectionTests(unittest.TestCase):
    def test_real_credentials_are_detected(self):
        leaks = (
            "OPENAI_KEY = sk-abcdefghij0123456789",
            'token: "sk-proj-AbCdEfGhIjKlMnOp"',
            "ghp_AbCdEf0123456789abcdef",
            "github_pat_11ABCDEFG_0123456789abcdefg",
            "-----BEGIN RSA PRIVATE KEY-----",
            "-----BEGIN OPENSSH PRIVATE KEY-----",
            "git clone https://user:hunter2@example.com/repo.git",
            "ssh://deploy:s3cr3t@host/path",
        )
        for text in leaks:
            with self.subTest(text=text):
                self.assertTrue(SECRET.search(text), "credential should be detected")

    def test_hyphenated_words_are_not_credentials(self):
        """`task-greenfield` contains `sk-greenfield`: a prefix, not a key."""
        safe = (
            "templates/specs/types/task-greenfield.md",
            '"task-greenfield.md": "application",',
            "risk-assessment0123456789",
            "disk-performance12345678901",
        )
        for text in safe:
            with self.subTest(text=text):
                self.assertIsNone(SECRET.search(text), "should not flag a hyphenated word")

    def test_every_task_template_name_stays_clean(self):
        for name in ("feature", "bugfix", "greenfield", "refactor", "migration", "test-e2e"):
            with self.subTest(name=name):
                self.assertIsNone(SECRET.search(f"templates/specs/types/task-{name}.md"))


class PersonalPathTests(unittest.TestCase):
    def test_real_home_paths_are_detected(self):
        for text in ("/home/someone/projects", "C:\\Users\\someone\\AppData", "/Users/someone/code"):
            with self.subTest(text=text):
                self.assertTrue(PERSONAL_PATH.search(text))

    def test_placeholder_paths_are_allowed(self):
        for text in ("/home/<user>/specs", "C:\\Users\\<user>\\AppData", "/home/user/specs"):
            with self.subTest(text=text):
                self.assertIsNone(PERSONAL_PATH.search(text))


class BlockedReferenceTests(unittest.TestCase):
    def test_internal_reference_is_detected(self):
        self.assertTrue(BLOCKED.search("workspace-gcb"))

    def test_neutral_text_is_allowed(self):
        self.assertIsNone(BLOCKED.search("um servico de exemplo neutro"))


if __name__ == "__main__":
    unittest.main()
