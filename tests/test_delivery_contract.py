import json
import subprocess
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.sdd_delivery import extract_task_contract, propose, validate
from scripts.sdd_architecture import extract_task_contract as extract_architecture_contract
from scripts.sdd_architecture import propose as propose_architecture, validate as validate_architecture


ROOT = Path(__file__).resolve().parents[1]


class DeliveryContractTests(unittest.TestCase):
    def test_e2e_type_is_primary_delivery(self):
        contract = propose("test-e2e", "Criar jornada de login no navegador")
        self.assertEqual("e2e-tests", contract["delivery_kind"])
        self.assertEqual(["e2e"], contract["verification"])
        self.assertEqual("sdd-generate-e2e-tests", validate(contract)["delivery_agent"])

    def test_web_feature_keeps_application_delivery_and_adds_verification(self):
        contract = propose("feature", "Adicionar tela web para consultar pedidos")
        self.assertEqual("application", contract["delivery_kind"])
        self.assertIn("e2e", contract["verification"])

    def test_greenfield_delivers_an_application_through_the_normal_route(self):
        contract = validate(propose("greenfield", "Criar do zero o serviço de cobranças"))
        self.assertEqual("application", contract["delivery_kind"])
        self.assertEqual("sdd-implement-spec", contract["delivery_agent"])
        self.assertIn("irreversible", contract["rationale"])

    def test_greenfield_aliases_normalize(self):
        for alias in ("new-project", "novo-projeto", "GREENFIELD"):
            with self.subTest(alias=alias):
                self.assertEqual("application", propose(alias)["delivery_kind"])

    def test_greenfield_never_gets_a_short_design(self):
        """The foundation decision is irreversible, so G2 cannot be waived."""
        for description in ("", "typo local isolado", "ajuste de validation"):
            with self.subTest(description=description):
                contract = propose_architecture("greenfield", description)
                self.assertEqual("high", contract["architecture_impact"])
                self.assertTrue(contract["full_design_required"])

    def test_invalid_e2e_contract_fails_closed(self):
        contract = propose("test-e2e")
        contract["verification"] = ["unit"]
        with self.assertRaises(ValueError):
            validate(contract)

    def test_contract_schema_accepts_proposal(self):
        schema = json.loads((ROOT / "schemas" / "delivery-contract.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(propose("test-e2e"))

    def test_task_strategy_is_machine_validated(self):
        contract = extract_task_contract(ROOT / "templates" / "specs" / "types" / "task-test-e2e.md")
        self.assertEqual("e2e-tests", contract["delivery_kind"])
        self.assertEqual(["e2e"], contract["verification"])

    def test_all_task_templates_expose_a_valid_strategy(self):
        expected = {
            "task-feature.md": "application",
            "task-bugfix.md": "application",
            "task-greenfield.md": "application",
            "task-refactor.md": "refactor",
            "task-migration.md": "migration",
            "task-test-e2e.md": "e2e-tests",
        }
        for filename, delivery_kind in expected.items():
            with self.subTest(filename=filename):
                self.assertEqual(
                    delivery_kind,
                    extract_task_contract(ROOT / "templates" / "specs" / "types" / filename)["delivery_kind"],
                )

    def test_public_cli_validates_task_strategy(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sdd.py"), "delivery", "validate",
             "--task", str(ROOT / "templates" / "specs" / "types" / "task-test-e2e.md"), "--json"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)
        self.assertEqual("sdd-generate-e2e-tests", json.loads(result.stdout)["delivery_agent"])

    def test_architecture_contract_classifies_and_validates_task(self):
        high = propose_architecture("feature", "Adicionar autenticação com nova tabela de usuários")
        self.assertEqual("high", high["architecture_impact"])
        self.assertEqual("sdd-architect", validate_architecture(high)["architecture_agent"])
        task = extract_architecture_contract(ROOT / "templates" / "specs" / "types" / "task-feature.md")
        self.assertEqual("medium", task["architecture_impact"])

    def test_all_task_templates_expose_architecture_strategy(self):
        for filename in ("task-feature.md", "task-bugfix.md", "task-greenfield.md", "task-refactor.md", "task-migration.md", "task-test-e2e.md"):
            with self.subTest(filename=filename):
                contract = extract_architecture_contract(ROOT / "templates" / "specs" / "types" / filename)
                self.assertEqual("sdd-architect", contract["architecture_agent"])

    def test_architecture_contract_rejects_unsafe_artifact(self):
        contract = propose_architecture("bugfix", "Corrigir validação local")
        contract["architecture_artifact"] = "../outside.md"
        with self.assertRaises(ValueError):
            validate_architecture(contract)


if __name__ == "__main__":
    unittest.main()
