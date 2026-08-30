#!/usr/bin/env python3
"""Semantic linter for SDD agent sources, compiled artifacts and evals.

The compiler guarantees that ``dist/`` is a deterministic render of ``agents/``.
This linter checks what the compiler cannot: that the contract the agents
describe is the contract the toolkit actually enforces.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

CANONICAL_VARIABLES = ("PROJECT_PATH", "SDD_WORKSPACE", "SPEC_PATH", "RUNTIME")
CONTEXT_COMMAND = "sdd context resolve"
ALLOWED_CAPABILITIES = ("read", "write", "terminal", "questions")
CONTEXT_PROFILES = {"analysis", "architecture", "orchestration", "scaffold", "e2e", "tests", "implementation", "support", "investigation", "review", "discovery", "documentation"}
BUDGET_CLASSES = {"low", "medium", "high"}

DEMAND_AGENTS = {
    "sdd-analyze-demand", "sdd-analyze-migration", "sdd-architect",
    "sdd-orchestrator", "sdd-create-spec", "sdd-generate-e2e-tests",
    "sdd-generate-integration-tests", "sdd-generate-tests",
    "sdd-implement-spec", "sdd-investigate-bug", "sdd-refactor-code",
    "sdd-review-code", "sdd-update-documentation",
}
SUPPORT_AGENTS = {
    "sdd-install-sdd-kit", "sdd-read-document", "sdd-setup-project",
    "sdd-workspace-sync",
}
PAYLOAD_BY_AGENT = {
    "sdd-analyze-demand": {"analysis"},
    "sdd-analyze-migration": {"migration_analysis"},
    "sdd-architect": {"architecture"},
    "sdd-orchestrator": {"orchestration", "e2e"},
    "sdd-create-spec": {"scaffold"},
    "sdd-generate-e2e-tests": {"delivery", "e2e"},
    "sdd-generate-integration-tests": {"integration"},
    "sdd-generate-tests": {"unit"},
    "sdd-implement-spec": {"delivery"},
    "sdd-install-sdd-kit": {"install"},
    "sdd-investigate-bug": {"investigation"},
    "sdd-read-document": {"document"},
    "sdd-refactor-code": {"delivery"},
    "sdd-review-code": {"review"},
    "sdd-setup-project": {"project_discovery"},
    "sdd-update-documentation": {"documentation"},
    "sdd-workspace-sync": {"workspace"},
}

LEGACY_TOKENS = (
    "tasks.md", "status-task.md", "sdd-fill-project-context", "--profile=yolo",
    "github-copilot", "claude-code", "JT-",
)
NEGATIONS = ("não", "nao", "nunca", "nem ", "sem ", "proibido", "legado")
REMOVED_AGENTS = (
    "sdd-inspect-infra", "sdd-sharepoint-migration-analyst",
    "sdd-java-legacy-analyst", "sdd-migrate-kustomize-to-helm",
)

# Stack names an agnostic agent must not adopt as a default. The E2E agent is
# allowed to name Playwright because the framework is its declared subject.
STACK_TOKENS = (
    "spring boot", "jboss", "wildfly", "kafka", "db2", "postgres", "mysql",
    "oracle", "maven", "gradle", "django", "fastapi", "express", "rabbitmq",
)
STACK_EXEMPT = {"sdd-generate-e2e-tests": ("playwright",)}

# Evals descrevem o comportamento esperado, então precisam obedecer às mesmas
# regras de posse que os agentes. Uma rubrica que premia escrita de estado ou
# aprovação de gate transforma um agente correto em um agente reprovado.
STATE_ARTIFACTS = ("session-state.md", "state.json", "events.ndjson")
# sdd-create-spec cria a visão session-state.md durante o scaffold; atualizá-la
# depois continua exclusivo do orquestrador.
EVAL_STATE_EXCEPTION = {"sdd-create-spec": ("session-state.md",)}
EVAL_STATE_WRITE = re.compile(
    r"\b(cria|criar|criou|escreve|escrever|escreveu|atualiza|atualizar|atualizou"
    r"|registra|registrar|registrou|marca|marcar|marcou|grava|gravar|gravou)\b"
    r"[^.\n]{0,60}?(" + "|".join(token.replace(".", r"\.") for token in STATE_ARTIFACTS) + r")",
    re.IGNORECASE,
)
EVAL_GATE_CLAIM = re.compile(
    r"\bG[1-6]\s*:?\s*(passed|failed|skipped)\b"
    r"|\b(marca|marcar|marcou|registra|registrar|registrou|aprova|aprovar|aprovou"
    r"|declara|declarar|declarou)\s+(?:o\s+)?G[1-6]\b",
    re.IGNORECASE,
)
# Atribuir a ação ao orquestrador não é reivindicá-la.
EVAL_DELEGATION = "orquestrador"

WRITE_MARKERS = ("crie ", "criar ", "cria ", "escreva ", "grave ", "atualize ",
                 "edite ", "gere ", "salve ")
QUESTION_MARKERS = ("pergunte", "aguarde aprovação", "confirmação do usuário",
                    "aguarde confirmação")
DESTRUCTIVE = ("reset --hard", "checkout -- .", "git clean", "git stash",
               "rm -rf", "push --force")

SHARED_POLICY_MARKERS = (
    "Política comum SDD",
    "Entradas não confiáveis",
    "Caminhos canônicos",
    "Rede e dependências",
    "Git e publicação",
    "Segredos e dados pessoais",
    "Capabilities declaradas",
    "Incerteza",
    "Idempotência",
    "Resultado e estado",
)


class Finding(Tuple[str, str, str]):
    pass


def finding(scope: str, target: str, message: str) -> Dict[str, str]:
    return {"scope": scope, "target": target, "message": message}


def frontmatter(path: Path) -> Tuple[Dict[str, str], str]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"missing frontmatter: {path.name}")
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    values: Dict[str, str] = {}
    for line in lines[1:end]:
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return values, "\n".join(lines[end + 1:])


def negated(text: str, index: int, window: int = 90) -> bool:
    """True when the mention is part of an explicit prohibition."""
    context = text[max(0, index - window):index].lower()
    return any(negation in context for negation in NEGATIONS)


def mentions(text: str, token: str) -> bool:
    """True when the token appears at least once as an affirmative instruction.

    A line that carries a negation anywhere is read as a prohibition, so
    "Nao crie tasks.md" and "tasks.md nao faz parte do contrato" both pass.
    """
    needle = token.lower()
    for line in text.splitlines():
        lowered = line.lower()
        if needle in lowered and not any(negation in lowered for negation in NEGATIONS):
            return True
    return False


def legacy_hits(text: str) -> List[str]:
    return sorted({token for token in LEGACY_TOKENS if mentions(text, token)})


def lint_agents(root: Path, toolkit_version: str) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    sources = sorted((root / "agents").glob("*.md"))
    known = DEMAND_AGENTS | SUPPORT_AGENTS
    names = {path.stem for path in sources}
    if names != known:
        results.append(finding("agents", "inventory",
                               f"agentes fora do contrato: {sorted(names ^ known)}"))
    for path in sources:
        stem = path.stem
        values, body = frontmatter(path)
        if values.get("name") != stem:
            results.append(finding("agents", stem, "name do frontmatter difere do arquivo"))
        if values.get("version") != toolkit_version:
            results.append(finding("agents", stem,
                                   f"version {values.get('version')} difere do VERSION {toolkit_version}"))
        declared = [item.strip() for item in values.get("capabilities", "").split(",") if item.strip()]
        if not declared or "read" not in declared:
            results.append(finding("agents", stem, "capabilities deve incluir read"))
        unknown = [item for item in declared if item not in ALLOWED_CAPABILITIES]
        if unknown:
            results.append(finding("agents", stem, f"capabilities desconhecidas: {unknown}"))
        if values.get("context_profile") not in CONTEXT_PROFILES:
            results.append(finding("agents", stem, "context_profile ausente ou inválido"))
        if values.get("context_budget_class") not in BUDGET_CLASSES:
            results.append(finding("agents", stem, "context_budget_class ausente ou inválido"))

        lowered = body.lower()
        for token in legacy_hits(body):
            results.append(finding("agents", stem, f"referência legada: {token}"))
        for removed in REMOVED_AGENTS:
            if removed in body:
                results.append(finding("agents", stem, f"agente removido citado: {removed}"))

        # capability versus effect
        runs_command = CONTEXT_COMMAND in body or "```bash" in body or re.search(r"`sdd [a-z]", body)
        if runs_command and "terminal" not in declared:
            results.append(finding("agents", stem, "instrui executar comando sem declarar terminal"))
        writes = any(mentions(body, marker) for marker in WRITE_MARKERS)
        if writes and "write" not in declared:
            results.append(finding("agents", stem, "instrui escrever arquivo sem declarar write"))
        if "write" not in declared and "não edita arquivos" not in lowered and "estritamente de leitura" not in lowered:
            results.append(finding("agents", stem, "sem write, precisa declarar explicitamente que não altera arquivos"))
        asks = any(mentions(body, marker) for marker in QUESTION_MARKERS)
        if asks and "questions" not in declared and "blocked" not in lowered:
            results.append(finding("agents", stem, "pergunta ao usuário sem declarar questions nem usar blocked"))

        # canonical context
        if stem in DEMAND_AGENTS:
            if CONTEXT_COMMAND not in body:
                results.append(finding("agents", stem, f"agente de demanda sem `{CONTEXT_COMMAND}`"))
            missing = [name for name in CANONICAL_VARIABLES if name not in body]
            if missing:
                results.append(finding("agents", stem, f"variáveis canônicas ausentes: {missing}"))
        elif CONTEXT_COMMAND in body and "SPEC_PATH" not in body:
            results.append(finding("agents", stem, "resolve contexto mas não usa SPEC_PATH"))

        # orchestration state ownership
        if stem == "sdd-orchestrator":
            if "proprietário de `session-state.md`" not in body:
                results.append(finding("agents", stem, "orquestrador deve declarar posse de session-state.md"))
        else:
            if "proprietário de `session-state.md`" in body:
                results.append(finding("agents", stem, "somente o orquestrador é proprietário do estado"))
            for match in re.finditer(r"[Aa]tualiz\w* .{0,20}session-state\.md", body):
                line_start = body.rfind(chr(10), 0, match.start()) + 1
                if not negated(body[line_start:match.end()], match.start() - line_start):
                    results.append(finding("agents", stem, "agente de execução não atualiza session-state.md"))
                    break

        # result contract
        if "AGENT_RESULT" not in body:
            results.append(finding("agents", stem, "sem bloco AGENT_RESULT"))
        legacy_result = {name for name in re.findall(r"\b([A-Z][A-Z_]*_RESULT)\b", body)} - {"AGENT_RESULT"}
        if legacy_result:
            results.append(finding("agents", stem, f"resultado fora do envelope: {sorted(legacy_result)}"))
        used = set(re.findall(r"payload\.([a-z0-9_]+)", body))
        expected = PAYLOAD_BY_AGENT[stem]
        if not used:
            results.append(finding("agents", stem, "sem chave payload declarada"))
        elif not used <= expected | {"context_request"}:
            results.append(finding("agents", stem, f"payload fora do contrato: {sorted(used - expected - {'context_request'})}"))

        # stack neutrality
        exempt = STACK_EXEMPT.get(stem, ())
        for token in STACK_TOKENS:
            if token not in exempt and mentions(body, token):
                results.append(finding("agents", stem, f"acoplamento de stack: {token}"))

        for token in DESTRUCTIVE:
            if mentions(body, token):
                results.append(finding("agents", stem, f"operação destrutiva sem negação explícita: {token}"))
    return results


def lint_dist(root: Path) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    policy_path = root / "templates" / "agent-policy.md"
    if not policy_path.is_file():
        results.append(finding("policy", "templates/agent-policy.md", "política comum ausente"))
        return results
    policy = policy_path.read_text(encoding="utf-8-sig")
    for marker in SHARED_POLICY_MARKERS:
        if marker not in policy:
            results.append(finding("policy", "templates/agent-policy.md", f"seção ausente: {marker}"))

    layouts = {
        "claude": ("dist/claude", "{name}.md"),
        "copilot": ("dist/copilot", "{name}.agent.md"),
        "codex": ("dist/codex", "{name}.toml"),
        "cursor": ("dist/cursor", "{name}.md"),
    }
    for path in sorted((root / "agents").glob("*.md")):
        values, _ = frontmatter(path)
        name = values.get("name", path.stem)
        rendered: Dict[str, str] = {}
        for runtime, (directory, pattern) in layouts.items():
            artifact = root / directory / pattern.format(name=name)
            if not artifact.is_file():
                results.append(finding("dist", f"{runtime}/{name}", "artefato ausente"))
                continue
            text = artifact.read_text(encoding="utf-8")
            rendered[runtime] = text
            for marker in SHARED_POLICY_MARKERS:
                if marker not in text:
                    results.append(finding("dist", f"{runtime}/{name}", f"política não injetada: {marker}"))
                    break
            if values.get("version") and values["version"] not in text:
                results.append(finding("dist", f"{runtime}/{name}", "version não propagado"))
            if values.get("capabilities") and values["capabilities"] not in text:
                results.append(finding("dist", f"{runtime}/{name}", "capabilities não propagadas"))
        # cross-runtime equivalence: the instruction body must be identical
        bodies = {}
        for runtime, text in rendered.items():
            if runtime == "codex":
                match = re.search(r'developer_instructions = "(.*)"\n?$', text, re.DOTALL)
                body = json.loads('"' + match.group(1) + '"') if match else ""
            else:
                body = text.split("---", 2)[-1]
            marker = "## Política comum SDD"
            bodies[runtime] = body[body.find(marker):].strip() if marker in body else body.strip()
        distinct = set(bodies.values())
        if len(distinct) > 1:
            divergent = sorted(r for r in bodies if bodies[r] != max(distinct, key=list(bodies.values()).count))
            results.append(finding("dist", name, f"corpo divergente entre runtimes: {divergent}"))
    return results


def lint_supporting_files(root: Path) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    targets: Iterable[Path] = [
        *sorted((root / "templates").rglob("*.md")),
        *sorted((root / "evals").rglob("*.md")),
    ]
    for path in targets:
        relative = path.relative_to(root).as_posix()
        for token in legacy_hits(path.read_text(encoding="utf-8")):
            results.append(finding("content", relative, f"referência legada: {token}"))

    agents = {path.stem for path in (root / "agents").glob("*.md")}
    for agent in sorted(agents):
        directory = root / "evals" / agent
        cases = sorted(p for p in directory.glob("case-*") if p.is_dir()) if directory.is_dir() else []
        if not cases:
            results.append(finding("evals", agent, "agente sem evals"))
            continue
        for path in cases:
            for required in ("input.md", "expected.md", "rubric.md"):
                if not (path / required).is_file():
                    results.append(finding("evals", f"{agent}/{path.name}", f"arquivo ausente: {required}"))
        adversarial = any(
            "adversarial" in (path / "input.md").read_text(encoding="utf-8").lower()
            for path in cases if (path / "input.md").is_file()
        )
        if not adversarial:
            results.append(finding("evals", agent, "sem caso adversarial"))
    return results


def lint_eval_contract(root: Path) -> List[Dict[str, str]]:
    """Check that the evals score the contract the agents actually follow.

    ``lint_supporting_files`` only checks that the eval files exist. This checks
    what they expect: an eval that rewards writing state or approving a gate is
    a contract violation wearing a rubric, and it survives every other check.
    """
    results: List[Dict[str, str]] = []
    for directory in sorted((root / "evals").glob("sdd-*")):
        if not directory.is_dir():
            continue
        agent = directory.name
        allowed = EVAL_STATE_EXCEPTION.get(agent, ())
        for path in sorted(directory.rglob("*.md")):
            relative = path.relative_to(root).as_posix()
            text = path.read_text(encoding="utf-8")
            reported: set = set()
            # Só o que o caso exige do agente é contrato. input.md descreve o
            # cenário e, num caso adversarial, cita o próprio pedido hostil.
            if agent != "sdd-orchestrator" and path.name in ("expected.md", "rubric.md"):
                for line in text.splitlines():
                    lowered = line.lower()
                    if EVAL_DELEGATION in lowered or any(negation in lowered for negation in NEGATIONS):
                        continue
                    state = EVAL_STATE_WRITE.search(line)
                    if state and state.group(2).lower() not in allowed and "state" not in reported:
                        reported.add("state")
                        results.append(finding("evals", relative, f"espera escrita de estado pelo agente: {state.group(2)}"))
                    if EVAL_GATE_CLAIM.search(line) and "gate" not in reported:
                        reported.add("gate")
                        results.append(finding("evals", relative, "espera que o agente declare gate; o dono é o orquestrador"))
            lowered_text = text.lower()
            exempt = STACK_EXEMPT.get(agent, ())
            for token in STACK_TOKENS:
                if token in lowered_text and token not in exempt:
                    results.append(finding("evals", relative, f"acoplamento de stack: {token}"))
    return results


def lint(root: Path) -> Dict[str, object]:
    toolkit_version = (root / "VERSION").read_text(encoding="utf-8").strip()
    findings = lint_agents(root, toolkit_version)
    findings += lint_dist(root)
    findings += lint_supporting_files(root)
    findings += lint_eval_contract(root)
    return {
        "status": "clean" if not findings else "findings",
        "toolkit_version": toolkit_version,
        "count": len(findings),
        "findings": findings,
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint SDD agent contracts")
    parser.add_argument("--kit-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.kit_root).expanduser().resolve(strict=False)
    report = lint(root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for item in report["findings"]:  # type: ignore[index]
            print(f"{item['scope']}: {item['target']}: {item['message']}")
        print(f"{report['count']} finding(s)")
    return 0 if report["status"] == "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
