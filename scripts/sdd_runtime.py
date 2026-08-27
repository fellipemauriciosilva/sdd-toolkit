"""Runtime adapter registry shared by the CLI, compiler and installers.

The registry intentionally has no third-party YAML dependency.  Adapter files
use a small, documented subset of YAML and this module parses only scalar
metadata required by the lifecycle.  Runtime-specific renderers remain in the
compiler, while paths and discovery metadata live in the adapter files.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence


RUNTIME_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
SEMVER_PATTERN = re.compile(r"(?<![0-9])([0-9]+)\.([0-9]+)\.([0-9]+)(?![0-9])")


@dataclass(frozen=True)
class RuntimeAdapter:
    target: str
    adapter_schema_version: int
    min_version: str
    aliases: tuple[str, ...]
    commands: tuple[str, ...]
    version_args: tuple[str, ...]
    scopes: tuple[str, ...]
    capabilities: tuple[str, ...]
    user_profile: str
    project_agent_dir: str
    user_agent_dir: str
    skill_dir: str
    output_dir: str
    output_filename: str
    renderer: str
    section: str

    @property
    def all_names(self) -> tuple[str, ...]:
        return (self.target, *self.aliases)


def _value(text: str) -> str:
    value = text.strip()
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = [item.strip().strip("\"'") for item in value[1:-1].split(",") if item.strip()]
        return "\x00".join(str(item) for item in parsed)
    return value.strip("\"'")


def _parse_adapter(path: Path) -> Mapping[str, str]:
    values: Dict[str, str] = {}
    section = ""
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 0 and stripped.endswith(":"):
            section = stripped[:-1]
            continue
        if ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        full_key = f"{section}.{key.strip()}" if indent else key.strip()
        values[full_key] = _value(raw_value)
    return values


def _tuple(values: Mapping[str, str], key: str) -> tuple[str, ...]:
    value = values.get(key, "")
    return tuple(item for item in value.split("\x00") if item)


def load_adapters(kit_root: Path) -> Dict[str, RuntimeAdapter]:
    root = (kit_root / "runtimes").resolve(strict=False)
    adapters: Dict[str, RuntimeAdapter] = {}
    if not root.is_dir():
        raise ValueError(f"Runtime adapter directory does not exist: {root}")
    for path in sorted(root.glob("*.yaml")):
        values = _parse_adapter(path)
        target = values.get("target", "")
        if not RUNTIME_PATTERN.fullmatch(target):
            raise ValueError(f"Invalid runtime target in {path}: {target!r}")
        if target in adapters:
            raise ValueError(f"Duplicate runtime adapter: {target}")
        adapter = RuntimeAdapter(
            target=target,
            adapter_schema_version=int(values.get("adapter_schema_version", "1")),
            min_version=values.get("min_version", "unknown"),
            aliases=_tuple(values, "aliases"),
            commands=_tuple(values, "detection.commands"),
            version_args=_tuple(values, "detection.version_args") or ("--version",),
            scopes=_tuple(values, "detection.scopes") or ("user",),
            capabilities=_tuple(values, "capabilities") or ("agents", "skills"),
            user_profile=values.get("detection.user_profile", f".{target}"),
            project_agent_dir=values.get("project_agent_dir", f".{target}/agents"),
            user_agent_dir=values.get("user_agent_dir", f".{target}/agents"),
            skill_dir=values.get("skill_dir", f".{target}/skills"),
            output_dir=values.get("output_dir", f"dist/{target}"),
            output_filename=values.get("output_filename", "{name}.md"),
            renderer=values.get("renderer", "markdown"),
            section=values.get("section", f"@{target}"),
        )
        if not adapter.commands:
            raise ValueError(f"Runtime adapter has no detection command: {path}")
        adapters[target] = adapter
    if not adapters:
        raise ValueError(f"No runtime adapters found in {root}")
    aliases: Dict[str, str] = {}
    for target, adapter in adapters.items():
        for name in adapter.all_names:
            if name in aliases:
                raise ValueError(f"Runtime alias collision: {name}")
            aliases[name] = target
    return adapters


def canonical_runtime(value: str, adapters: Mapping[str, RuntimeAdapter]) -> str:
    normalized = value.strip().lower()
    for target, adapter in adapters.items():
        if normalized in adapter.all_names:
            return target
    raise ValueError(f"Unsupported runtime: {value}")


def selected_runtimes(value: str | Sequence[str], adapters: Mapping[str, RuntimeAdapter]) -> List[str]:
    values = [value] if isinstance(value, str) else list(value)
    flattened: List[str] = []
    for item in values:
        flattened.extend(part.strip() for part in item.split(",") if part.strip())
    if not flattened:
        raise ValueError("At least one runtime is required")
    if any(item.lower() == "all" for item in flattened):
        if len(flattened) != 1:
            raise ValueError("'all' cannot be combined with another runtime")
        return list(adapters)
    result: List[str] = []
    for item in flattened:
        target = canonical_runtime(item, adapters)
        if target not in result:
            result.append(target)
    return result


def runtime_choices(kit_root: Path) -> List[str]:
    adapters = load_adapters(kit_root)
    return ["all", *adapters.keys()]


def parse_semver(text: str) -> tuple[int, int, int] | None:
    """Extract a conservative SemVer triple from a harness version output."""
    match = SEMVER_PATTERN.search(text or "")
    if not match:
        return None
    return tuple(int(match.group(index)) for index in range(1, 4))


def versioned_capabilities(kit_root: Path, target: str, version_output: str | None) -> Dict[str, object]:
    """Resolve capabilities from reviewed local rules without assuming future versions."""
    path = kit_root / "runtimes" / "capabilities.json"
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
        rules = catalog["runtimes"][target]["rules"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid runtime capability catalog: {path}") from exc
    parsed = parse_semver(version_output or "")
    normalized = []
    for rule in rules:
        minimum = parse_semver(str(rule.get("min_version", "")))
        capabilities = rule.get("capabilities")
        if minimum is None or not isinstance(capabilities, list):
            raise ValueError(f"Invalid capability rule for runtime: {target}")
        normalized.append((minimum, rule))
    normalized.sort(key=lambda item: item[0])
    if parsed is None:
        return {
            "version": None,
            "status": "unknown-version",
            "capabilities": [],
            "evidence": "none",
            "next_action": "verify harness version or use an explicit compatible runtime policy",
        }
    compatible = [item for item in normalized if item[0] <= parsed]
    if not compatible:
        return {
            "version": ".".join(map(str, parsed)),
            "status": "unsupported-version",
            "capabilities": [],
            "evidence": "none",
            "next_action": "upgrade the harness or add a reviewed capability rule",
        }
    minimum, rule = compatible[-1]
    return {
        "version": ".".join(map(str, parsed)),
        "status": "compatible",
        "min_version": ".".join(map(str, minimum)),
        "capabilities": list(rule["capabilities"]),
        "evidence": rule["evidence"],
        "next_action": "run the harness canary before release" if rule["evidence"] != "verified-harness" else None,
    }
