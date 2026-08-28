#!/usr/bin/env python3
"""Deterministic compiler for native runtime artifacts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

try:
    import sdd_runtime as RUNTIME
except ModuleNotFoundError:
    _runtime_spec = importlib.util.spec_from_file_location(
        "sdd_runtime", Path(__file__).with_name("sdd_runtime.py")
    )
    if _runtime_spec is None or _runtime_spec.loader is None:
        raise
    RUNTIME = importlib.util.module_from_spec(_runtime_spec)
    sys.modules[_runtime_spec.name] = RUNTIME
    _runtime_spec.loader.exec_module(RUNTIME)


FRONTMATTER_DELIMITER = "---"
SECTION_START = re.compile(r"^\s*<!--\s*@([a-z0-9-]+)\s*-->\s*$", re.IGNORECASE)
SECTION_END = re.compile(r"^\s*<!--\s*@end\s*-->\s*$", re.IGNORECASE)
SHARED_POLICY = Path("templates") / "agent-policy.md"


def canonical_identity(kit_root: Path) -> Dict[str, str]:
    """Load the one public identity allowed in source agent frontmatter."""
    path = kit_root / "metadata" / "project-identity.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        maintainer = document["maintainer"]
        return {
            "author": str(maintainer["name"]),
            "author_email": str(maintainer["email"]),
            "author_linkedin": str(maintainer["linkedin"]),
        }
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid canonical project identity: {path}") from exc


def shared_policy(kit_root: Path) -> str:
    """Load the common policy injected in every compiled agent artifact."""
    path = kit_root / SHARED_POLICY
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8-sig").strip()
    for line in text.splitlines():
        if SECTION_START.match(line) or SECTION_END.match(line):
            raise ValueError(f"Shared policy must not declare runtime sections: {path}")
    return text + "\n"


def with_policy(body: str, policy: str) -> str:
    """Prefix the shared policy once, keeping a stable cacheable instruction prefix."""
    if not policy:
        return body
    if policy.strip() in body:
        return body
    return policy.rstrip("\n") + "\n\n" + body.lstrip("\n")


def attribution(values: Dict[str, str]) -> str:
    """Render portable attribution inside the agent instructions."""
    author = values.get("author", "").strip()
    email = values.get("author_email", "").strip()
    linkedin = values.get("author_linkedin", "").strip()
    if not any((author, email, linkedin)):
        return ""
    if not all((author, email, linkedin)):
        raise ValueError("Agent attribution requires author, author_email and author_linkedin")
    return f"> **Autor:** {author} · **E-mail:** {email} · **LinkedIn:** {linkedin}\n\n"


def read_source(path: Path) -> Tuple[Dict[str, str], str]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        raise ValueError(f"Missing frontmatter: {path}")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == FRONTMATTER_DELIMITER), None)
    if end is None:
        raise ValueError(f"Unclosed frontmatter: {path}")
    values: Dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values, "\n".join(lines[end + 1:]).strip() + "\n"


def filter_sections(body: str, target: str) -> str:
    output: List[str] = []
    active = True
    seen_section = False
    for line in body.splitlines():
        if SECTION_END.match(line):
            if not seen_section:
                raise ValueError("Unexpected runtime section terminator")
            active = True
            seen_section = False
            continue
        start = SECTION_START.match(line)
        if start:
            if seen_section:
                raise ValueError("Nested or adjacent runtime sections are not supported")
            seen_section = True
            active = start.group(1).lower() in {"all", target.lower()}
            continue
        if active:
            output.append(line)
    if seen_section:
        raise ValueError("Unclosed runtime section")
    return "\n".join(output).strip() + "\n"


def markdown_artifact(values: Dict[str, str], body: str) -> str:
    name = values.get("name") or "sdd-agent"
    description = values.get("description") or name
    header = f"---\nname: {name}\ndescription: {json.dumps(description, ensure_ascii=False)}\n"
    if values.get("version"):
        header += f"version: {json.dumps(values['version'], ensure_ascii=False)}\n"
    if values.get("capabilities"):
        header += f"capabilities: {json.dumps(values['capabilities'], ensure_ascii=False)}\n"
    for key in ("context_profile", "context_budget_class"):
        if values.get(key):
            header += f"{key}: {json.dumps(values[key], ensure_ascii=False)}\n"
    return f"{header}---\n\n{attribution(values)}{body}"


def claude_artifact(values: Dict[str, str], body: str) -> str:
    name = values.get("name") or "sdd-agent"
    description = values.get("description") or name
    capabilities = values.get("capabilities") or "read"
    version = values.get("version") or "1.0.0"
    return (
        "---\n"
        f"name: {json.dumps(name, ensure_ascii=False)}\n"
        f"description: {json.dumps(description, ensure_ascii=False)}\n"
        f"version: {json.dumps(version, ensure_ascii=False)}\n"
        f"capabilities: {json.dumps(capabilities, ensure_ascii=False)}\n"
        f"context_profile: {json.dumps(values.get('context_profile', ''), ensure_ascii=False)}\n"
        f"context_budget_class: {json.dumps(values.get('context_budget_class', ''), ensure_ascii=False)}\n"
        "---\n\n"
        f"{attribution(values)}{body}"
    )


def copilot_artifact(values: Dict[str, str], body: str) -> str:
    name = values.get("name") or "sdd-agent"
    description = values.get("description") or name
    capabilities = values.get("capabilities") or "read"
    version = values.get("version") or "1.0.0"
    author = values.get("author")
    if not author:
        raise ValueError("Copilot agent attribution requires author")
    selected = {item.strip().lower() for item in capabilities.split(",") if item.strip()}
    tools: List[str] = []
    if "read" in selected:
        tools.extend(["search/fileSearch", "search/textSearch"])
    if "write" in selected:
        tools.extend(["edit/editFiles", "edit/createFile"])
    if "terminal" in selected:
        tools.extend(["execute/runInTerminal", "execute/getTerminalOutput"])
    if "questions" in selected:
        tools.append("vscode/askQuestions")
    tool_lines = "\n".join(f"  - {tool}" for tool in tools)
    return (
        "---\n"
        "mode: agent\n"
        f"author: {json.dumps(author, ensure_ascii=False)}\n"
        f"description: {json.dumps(description, ensure_ascii=False)}\n"
        'model: "Claude Sonnet 4.6"\n'
        f"capabilities: {json.dumps(capabilities, ensure_ascii=False)}\n"
        f"context_profile: {json.dumps(values.get('context_profile', ''), ensure_ascii=False)}\n"
        f"context_budget_class: {json.dumps(values.get('context_budget_class', ''), ensure_ascii=False)}\n"
        "tools:\n"
        f"{tool_lines}\n"
        f"version: {json.dumps(version, ensure_ascii=False)}\n"
        "---\n\n"
        f"{attribution(values)}{body}"
    )


def codex_artifact(values: Dict[str, str], body: str) -> str:
    name = values.get("name") or "sdd-agent"
    description = values.get("description") or name
    version = values.get("version") or "1.0.0"
    capabilities = values.get("capabilities") or "read"
    return (
        f"name = {json.dumps(name, ensure_ascii=False)}\n"
        f"description = {json.dumps(description, ensure_ascii=False)}\n"
        f"version = {json.dumps(version, ensure_ascii=False)}\n"
        f"capabilities = {json.dumps(capabilities, ensure_ascii=False)}\n"
        f"context_profile = {json.dumps(values.get('context_profile', ''), ensure_ascii=False)}\n"
        f"context_budget_class = {json.dumps(values.get('context_budget_class', ''), ensure_ascii=False)}\n"
        f"developer_instructions = {json.dumps(attribution(values) + body, ensure_ascii=False)}\n"
    )


def compile_agents(kit_root: Path, target: str) -> List[Path]:
    adapters = RUNTIME.load_adapters(kit_root)
    adapter = adapters[target]
    source_root = kit_root / "agents"
    output_root = kit_root / adapter.output_dir
    output_root.mkdir(parents=True, exist_ok=True)
    outputs: List[Path] = []
    expected_files = set()
    identity = canonical_identity(kit_root)
    policy = shared_policy(kit_root)
    for source in sorted(source_root.glob("*.md")):
        values, body = read_source(source)
        missing_attribution = [
            key for key in ("author", "author_email", "author_linkedin")
            if not values.get(key, "").strip()
        ]
        if missing_attribution:
            raise ValueError(
                f"Missing agent attribution in {source}: {', '.join(missing_attribution)}"
            )
        if any(values[key].strip() != expected for key, expected in identity.items()):
            raise ValueError(f"Agent attribution differs from canonical identity: {source}")
        rendered_body = with_policy(filter_sections(body, target), policy)
        name = values.get("name") or source.stem
        filename = adapter.output_filename.format(name=name)
        expected_files.add(filename)
        destination = output_root / filename
        if adapter.renderer == "codex-toml":
            content = codex_artifact(values, rendered_body)
        elif adapter.renderer == "cursor-markdown":
            content = markdown_artifact(values, rendered_body)
        elif target == "claude":
            content = claude_artifact(values, rendered_body)
        elif target == "copilot":
            content = copilot_artifact(values, rendered_body)
        else:
            content = markdown_artifact(values, rendered_body)
        destination.write_text(content, encoding="utf-8", newline="\n")
        outputs.append(destination)
    for existing in output_root.iterdir():
        if existing.is_file() and existing.name not in expected_files:
            existing.unlink()
    return outputs


def compile_shared_skills(kit_root: Path, targets: Iterable[str]) -> List[Path]:
    sources = [kit_root / "agents" / "sdd-bootstrap.md"]
    sources.extend(sorted((kit_root / "templates" / "skills").glob("*/SKILL.md")))
    outputs: List[Path] = []
    output_root = kit_root / "dist" / "shared" / "skills"
    expected_directories = set()
    policy = shared_policy(kit_root)
    for source in sources:
        values, body = read_source(source)
        rendered = filter_sections(body, "all")
        if source.parent.name == "agents":
            rendered = with_policy(rendered, policy)
        # Keep the catalog directory name stable even when a skill's frontmatter
        # uses a display name (for example ios-swift vs. swift-ios).
        name = source.parent.name if source.name == "SKILL.md" else (values.get("name") or source.stem)
        expected_directories.add(name)
        destination = output_root / name / "SKILL.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(markdown_artifact(values, rendered), encoding="utf-8", newline="\n")
        outputs.append(destination)
    if output_root.is_dir():
        for existing in output_root.iterdir():
            if existing.is_dir() and existing.name not in expected_directories:
                shutil.rmtree(existing)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile SDD Toolkit runtime artifacts")
    parser.add_argument("--kit-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--runtime", action="append", default=None)
    args = parser.parse_args()
    kit_root = Path(args.kit_root).expanduser().resolve(strict=False)
    adapters = RUNTIME.load_adapters(kit_root)
    targets = RUNTIME.selected_runtimes(args.runtime or ["all"], adapters)
    compiled: List[str] = []
    for target in targets:
        adapter = adapters[target]
        compiled.extend(str(path) for path in compile_agents(kit_root, target))
    if any(target in {"codex", "cursor"} for target in targets):
        compiled.extend(str(path) for path in compile_shared_skills(kit_root, targets))
    print(json.dumps({"runtimes": targets, "compiled": compiled}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
