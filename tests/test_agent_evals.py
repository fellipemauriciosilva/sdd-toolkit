"""Eval coverage: every agent is evaluated, including adversarially."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import sdd_lint  # noqa: E402

REQUIRED_FILES = ("input.md", "expected.md", "rubric.md")
WEIGHTED_ROW = re.compile(r"\|\s*(\d+)\s*\|\s*✓/✗\s*\|")
POINTS_ROW = re.compile(r"\|\s*(\d+)\s*\|\s*$", re.MULTILINE)


def agents():
    return sorted(path.stem for path in (ROOT / "agents").glob("*.md"))


def cases(agent):
    directory = ROOT / "evals" / agent
    return sorted(path for path in directory.glob("case-*") if path.is_dir()) if directory.is_dir() else []


class EvalCoverageTests(unittest.TestCase):
    def test_every_agent_has_evals(self):
        self.assertEqual(17, len(agents()))
        for agent in agents():
            self.assertTrue(cases(agent), f"{agent} sem evals")

    def test_every_case_has_the_three_required_files(self):
        for agent in agents():
            for case in cases(agent):
                for required in REQUIRED_FILES:
                    self.assertTrue((case / required).is_file(), f"{agent}/{case.name}/{required}")

    def test_every_agent_has_at_least_one_adversarial_case(self):
        for agent in agents():
            adversarial = [
                case for case in cases(agent)
                if "adversarial" in (case / "input.md").read_text(encoding="utf-8").lower()
            ]
            self.assertTrue(adversarial, f"{agent} sem caso adversarial")

    def test_adversarial_cases_cover_the_declared_threat_classes(self):
        """The adversarial suite as a whole must exercise every threat class."""
        corpus = "\n".join(
            (case / "input.md").read_text(encoding="utf-8").lower()
            + (case / "expected.md").read_text(encoding="utf-8").lower()
            for agent in agents() for case in cases(agent)
            if "adversarial" in (case / "input.md").read_text(encoding="utf-8").lower()
        )
        for threat in (
            "injeção", "link simbólico", "traversal", "credencial", "commit",
            "push", "pr", "sobrescrev", "gate", "produção",
        ):
            self.assertIn(threat, corpus, threat)

    def test_no_case_reintroduces_the_legacy_contract(self):
        for path in sorted((ROOT / "evals").rglob("*.md")):
            hits = sdd_lint.legacy_hits(path.read_text(encoding="utf-8"))
            self.assertEqual([], hits, f"{path.relative_to(ROOT).as_posix()}: {hits}")

    def test_rubrics_are_scored_out_of_one_hundred(self):
        for agent in agents():
            for case in cases(agent):
                text = (case / "rubric.md").read_text(encoding="utf-8")
                weights = [int(value) for value in WEIGHTED_ROW.findall(text)]
                if not weights:
                    weights = [int(value) for value in POINTS_ROW.findall(text)]
                if not weights:
                    self.assertTrue(
                        "Reprovar" in text or "Threshold" in text,
                        f"{agent}/{case.name}: rubrica sem pesos nem critério de reprovação",
                    )
                    continue
                self.assertEqual(100, sum(weights), f"{agent}/{case.name}")

    def test_readme_documents_the_contract_shared_by_every_case(self):
        readme = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        for expected in ("AGENT_RESULT", "sdd result validate", "session-state.md", "adversarial"):
            self.assertIn(expected, readme)


if __name__ == "__main__":
    unittest.main()
