import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]


class SchemaTests(unittest.TestCase):
    def load(self, name):
        value = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(value)
        return Draft202012Validator(value, format_checker=FormatChecker())

    def test_registry_schema_rejects_unknown_properties(self):
        validator = self.load("installations.schema.json")
        invalid = {"schema_version": 2, "installations": [], "unexpected": True}
        self.assertTrue(list(validator.iter_errors(invalid)))

    def test_user_activation_and_profile_schemas_accept_contracts(self):
        activation = self.load("project-activation.schema.json")
        record = {
            "schema_version": 1,
            "scope": "user",
            "profile": "default",
            "runtime": "all",
            "project_id": "a" * 64,
            "project_name": "example",
            "project_path": "C:/workspace/example",
            "workspace_root": "C:/Users/user/sdd-history-implementations/example-aaaaaaaaaaaa",
            "workspace": "C:/Users/user/sdd-history-implementations/example-aaaaaaaaaaaa/example/specs",
            "kit_root": "C:/tools/sdd-toolkit",
            "toolkit_version": "3.1.1",
            "created_at": "2026-08-26T12:00:00Z",
            "updated_at": "2026-08-26T12:00:00Z",
        }
        activation.validate(record)
        invalid = json.loads(json.dumps(record))
        invalid["scope"] = "organization"
        self.assertTrue(list(activation.iter_errors(invalid)))

        profile = self.load("sdd-profile.schema.json")
        profile.validate({
            "schema_version": 1,
            "scope": "user",
            "name": "default",
            "runtimes": ["copilot", "claude"],
            "toolkit_version": "3.1.1",
        })

    def test_user_installation_schema_rejects_non_toolkit_ownership(self):
        validator = self.load("user-installation.schema.json")
        valid = {
            "schema_version": 1,
            "scope": "user",
            "profile_root": "C:/Users/user",
            "kit_root": "C:/tools/sdd-toolkit",
            "toolkit_version": "3.1.1",
            "updated_at": "2026-08-26T12:00:00Z",
            "managed_files": [{
                "path": ".copilot/agents/example.agent.md",
                "runtime": "copilot",
                "sha256": "b" * 64,
                "owner": "sdd-toolkit",
            }],
        }
        validator.validate(valid)
        invalid = json.loads(json.dumps(valid))
        invalid["managed_files"][0]["owner"] = "other"
        self.assertTrue(list(validator.iter_errors(invalid)))

        enriched = json.loads(json.dumps(valid))
        enriched["cli"] = {
            "path": "C:/Users/user/AppData/Local/SDD-Toolkit/bin/sdd.cmd",
            "sha256": "c" * 64,
            "owner": "sdd-toolkit",
            "registered_at": "2026-08-26T12:00:00Z",
        }
        enriched["path_integration"] = {
            "strategy": "windows-user-env",
            "entry": "C:/Users/user/AppData/Local/SDD-Toolkit/bin",
            "target": "windows-user-env",
            "marker": "sdd-toolkit",
            "updated_at": "2026-08-26T12:00:00Z",
        }
        validator.validate(enriched)

        shared = json.loads(json.dumps(valid))
        shared["schema_version"] = 2
        shared["managed_files"][0].pop("runtime")
        shared["managed_files"][0]["runtimes"] = ["codex", "cursor"]
        validator.validate(shared)

    def test_user_source_schema_accepts_git_contract(self):
        validator = self.load("user-source.schema.json")
        validator.validate({
            "schema_version": 1,
            "scope": "user",
            "source_type": "git",
            "repository_url": "https://github.com/example/sdd-toolkit.git",
            "channel": "stable",
            "requested_ref": "",
            "resolved_ref": "v3.2.0",
            "commit": "a" * 40,
            "source_root": "C:/Users/user/AppData/Local/SDD-Toolkit/kit",
            "updated_at": "2026-08-26T12:00:00Z",
        })

    def test_context_resolution_schema_accepts_user_contract(self):
        validator = self.load("context-resolution.schema.json")
        validator.validate({
            "schema_version": 1,
            "status": "ready",
            "scope": "user",
            "source": "user-activation",
            "profile": "default",
            "runtime": "copilot",
            "project": {"name": "demo", "path": "C:/workspace/demo", "project_id": "a" * 64},
            "workspace": "C:/Users/user/sdd-history/demo/specs",
            "activation_state": "C:/Users/user/.local/state/sdd-toolkit/user/activations.json",
            "writes_project": False,
            "ticket": "ABC-1",
            "spec_path": "C:/Users/user/sdd-history/demo/specs/ABC-1",
        })

    def test_delivery_contract_schema_accepts_e2e_delivery(self):
        validator = self.load("delivery-contract.schema.json")
        validator.validate({
            "schema_version": 1,
            "contract_version": "1.0",
            "delivery_kind": "e2e-tests",
            "verification": ["e2e"],
            "rationale": "A suíte E2E é a entrega solicitada.",
            "owner": "sdd-analyze-demand",
            "expected_evidence": ["DELIVERY_RESULT", "E2E_RESULT"],
            "commands": [],
        })
        invalid = {
            "schema_version": 1,
            "delivery_kind": "e2e-tests",
            "verification": ["unit"],
            "rationale": "invalid",
            "owner": "sdd-analyze-demand",
            "expected_evidence": ["DELIVERY_RESULT"],
        }
        self.assertTrue(list(validator.iter_errors(invalid)))

    def test_architecture_contract_schema_accepts_design_proposal(self):
        validator = self.load("architecture-contract.schema.json")
        validator.validate({
            "schema_version": 1,
            "contract_version": "1.0",
            "architecture_impact": "medium",
            "architecture_status": "pending",
            "architecture_agent": "sdd-architect",
            "architecture_mode": "design",
            "architecture_artifact": "technical-design.md",
            "rationale": "A demanda altera um fluxo existente.",
            "decisions": [],
            "required_evidence": ["ARCHITECTURE_RESULT"],
            "full_design_required": True,
        })

    def test_identity_and_versioned_capabilities_schemas_accept_repository_metadata(self):
        identity = json.loads((ROOT / "metadata" / "project-identity.json").read_text(encoding="utf-8"))
        capabilities = json.loads((ROOT / "runtimes" / "capabilities.json").read_text(encoding="utf-8"))
        self.load("project-identity.schema.json").validate(identity)
        self.load("runtime-capabilities.schema.json").validate(capabilities)

    def test_runtime_discovery_catalog_schema_accepts_repository_catalog(self):
        catalog = json.loads((ROOT / "runtimes" / "discovery-catalog.json").read_text(encoding="utf-8"))
        self.load("runtime-discovery-catalog.schema.json").validate(catalog)


if __name__ == "__main__":
    unittest.main()
