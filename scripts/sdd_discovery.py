"""Local, evidence-based discovery for supported coding runtimes.

The default scan only reads local metadata and resolves commands.  Version and
package-manager probes are explicit, bounded, and use fixed argv values.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

import sdd_runtime as RUNTIME


SCHEMA_VERSION = 2
CACHE_SCHEMA_VERSION = 1
CACHE_TTL_SECONDS = 300
PROBE_TIMEOUT_SECONDS = 5
TRUSTED_VSCODE_COMMANDS = ("code", "code-insiders")


def _canonical(path: Path) -> str:
    return str(path.expanduser().resolve(strict=False))


def _unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _platform_name() -> str:
    if os.name == "nt":
        return "windows"
    if platform.system().lower() == "darwin":
        return "macos"
    return "linux"


def _is_wsl() -> bool:
    if _platform_name() != "linux":
        return False
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return False


def execution_context() -> Dict[str, Any]:
    return {
        "platform": _platform_name(),
        "architecture": platform.machine().lower() or "unknown",
        "wsl": _is_wsl(),
        "container": Path("/.dockerenv").exists() or os.environ.get("container") is not None,
    }


def load_catalog(kit_root: Path) -> Dict[str, Any]:
    path = kit_root / "runtimes" / "discovery-catalog.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid runtime discovery catalog: {path}") from exc
    if value.get("schema_version") != 1 or not isinstance(value.get("runtimes"), dict):
        raise ValueError(f"Unsupported runtime discovery catalog: {path}")
    return value


def _path_candidates(command: str) -> list[str]:
    """Return every local resolution in PATH order, including Windows shims."""
    candidates: list[str] = []
    found = shutil.which(command)
    if found:
        candidates.append(_canonical(Path(found)))
    suffixes = [""]
    if os.name == "nt" and not Path(command).suffix:
        suffixes += [item.lower() for item in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";") if item]
    for raw_directory in os.environ.get("PATH", "").split(os.pathsep):
        if not raw_directory:
            continue
        directory = Path(raw_directory).expanduser()
        for suffix in suffixes:
            candidate = directory / f"{command}{suffix}"
            try:
                if candidate.is_file():
                    candidates.append(_canonical(candidate))
            except OSError:
                continue
    return _unique(candidates)


def _known_cli_paths(profile: Path, target: str) -> list[Path]:
    executable = f"{target}.exe" if os.name == "nt" else target
    names = {"cursor": "cursor-agent", "claude": "claude", "codex": "codex", "copilot": "copilot"}
    executable = f"{names[target]}.exe" if os.name == "nt" else names[target]
    roots = [profile / ".local" / "bin"]
    if _platform_name() == "windows":
        roots.extend([profile / "AppData" / "Local" / "Programs", profile / "scoop" / "shims"])
    return [root / executable for root in roots]


def _is_extension_bundled(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return "/.vscode/extensions/" in normalized or "/.vscode-insiders/extensions/" in normalized or "/.cursor/extensions/" in normalized


def _extension_roots(profile: Path, extension_dirs: Sequence[Path] = (), portable_roots: Sequence[Path] = ()) -> list[tuple[str, Path]]:
    roots = [
        ("vscode", profile / ".vscode" / "extensions"),
        ("vscode-insiders", profile / ".vscode-insiders" / "extensions"),
        ("cursor", profile / ".cursor" / "extensions"),
    ]
    if _platform_name() == "windows":
        app_data = Path(os.environ.get("APPDATA", profile / "AppData" / "Roaming"))
        roots.extend([
            ("vscode", app_data / "Code" / "User" / "extensions"),
            ("vscode-insiders", app_data / "Code - Insiders" / "User" / "extensions"),
            ("cursor", app_data / "Cursor" / "User" / "extensions"),
        ])
    roots.extend(("custom-extension-dir", path) for path in extension_dirs)
    roots.extend(("vscode-portable", root / "data" / "extensions") for root in portable_roots)
    unique: list[tuple[str, Path]] = []
    for host, path in roots:
        item = (host, path.expanduser().resolve(strict=False))
        if item not in unique:
            unique.append(item)
    return [(host, path) for host, path in unique if path.is_dir()]


def _extension_components(extension_roots: Sequence[tuple[str, Path]], extension_ids: Sequence[str]) -> list[Dict[str, Any]]:
    wanted = {item.lower() for item in extension_ids}
    components: list[Dict[str, Any]] = []
    if not wanted:
        return components
    for host, root in extension_roots:
        try:
            children = list(root.iterdir())
        except OSError:
            continue
        for extension_root in children:
            manifest = extension_root / "package.json"
            if not manifest.is_file():
                continue
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            publisher, name = data.get("publisher"), data.get("name")
            if not isinstance(publisher, str) or not isinstance(name, str):
                continue
            extension_id = f"{publisher}.{name}".lower()
            if extension_id not in wanted:
                continue
            components.append({
                "kind": "ide-extension",
                "id": extension_id,
                "status": "present",
                "host": host,
                "path": _canonical(extension_root),
                "version": data.get("version") if isinstance(data.get("version"), str) else None,
                "evidence": [{"source": "extension-manifest", "confidence": "verified", "path": _canonical(manifest)}],
            })
    return components


def _vscode_cli_components(extension_ids: Sequence[str], mode: str) -> list[Dict[str, Any]]:
    if mode != "full" or not extension_ids:
        return []
    wanted = {item.lower() for item in extension_ids}
    components: list[Dict[str, Any]] = []
    for command in TRUSTED_VSCODE_COMMANDS:
        executable = shutil.which(command)
        if not executable:
            continue
        try:
            completed = subprocess.run([executable, "--list-extensions", "--show-versions"], capture_output=True, text=True, timeout=PROBE_TIMEOUT_SECONDS, check=False)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if completed.returncode != 0:
            continue
        host = "vscode-insiders" if command == "code-insiders" else "vscode"
        for line in (completed.stdout or "").splitlines():
            extension_id, separator, version = line.strip().lower().partition("@")
            if extension_id not in wanted:
                continue
            components.append({
                "kind": "ide-extension",
                "id": extension_id,
                "status": "present",
                "host": host,
                "path": None,
                "version": version if separator and version else None,
                "evidence": [{"source": "vscode-cli", "confidence": "authoritative", "command": command}],
            })
    return components


def _merge_components(components: Sequence[Dict[str, Any]]) -> list[Dict[str, Any]]:
    merged: list[Dict[str, Any]] = []
    for component in components:
        key = (component.get("kind"), component.get("id"), component.get("host"), component.get("manager"))
        existing = next((item for item in merged if (item.get("kind"), item.get("id"), item.get("host"), item.get("manager")) == key), None)
        if existing is None:
            merged.append(component)
            continue
        existing["evidence"] = [*existing["evidence"], *component["evidence"]]
        if not existing.get("path") and component.get("path"):
            existing["path"] = component["path"]
        if not existing.get("version") and component.get("version"):
            existing["version"] = component["version"]
    return merged


def _package_components(profile: Path, packages: Mapping[str, Sequence[str]], mode: str) -> list[Dict[str, Any]]:
    """Inspect npm's local global prefix in quick mode; query other managers only in full mode."""
    components: list[Dict[str, Any]] = []
    npm_packages = packages.get("npm", [])
    npm = shutil.which("npm")
    if npm and npm_packages and mode == "full":
        try:
            completed = subprocess.run([npm, "root", "-g"], capture_output=True, text=True, timeout=PROBE_TIMEOUT_SECONDS, check=False)
            root = Path(completed.stdout.strip()) if completed.returncode == 0 and completed.stdout.strip() else None
        except (OSError, subprocess.TimeoutExpired):
            root = None
        if root:
            for package in npm_packages:
                candidate = root / package
                if candidate.is_dir():
                    components.append({"kind": "package", "id": package, "manager": "npm", "status": "present", "path": _canonical(candidate), "version": None, "evidence": [{"source": "npm-root", "confidence": "verified", "path": _canonical(candidate)}]})
    if mode != "full":
        return components
    manager_commands = {
        "winget": ("winget", ["list", "--id"], ["--exact", "--disable-interactivity"]),
        "brew": ("brew", ["list", "--cask", "--versions"], []),
        "linux": ("dpkg-query", ["-W", "-f=${Version}"], []),
    }
    for manager, (command, argv, suffix) in manager_commands.items():
        executable = shutil.which(manager)
        if manager == "linux":
            executable = shutil.which(command)
        if not executable:
            continue
        for package in packages.get(manager, []):
            try:
                completed = subprocess.run([executable, *argv, package, *suffix], capture_output=True, text=True, timeout=PROBE_TIMEOUT_SECONDS, check=False)
            except (OSError, subprocess.TimeoutExpired):
                continue
            output = (completed.stdout or "").strip()
            present = completed.returncode == 0 and (manager == "linux" or package.lower() in output.lower())
            if present:
                components.append({"kind": "package", "id": package, "manager": manager, "status": "present", "path": None, "version": output.splitlines()[0][:200] if output else None, "evidence": [{"source": f"{manager}-query", "confidence": "verified"}]})
    return components


def _desktop_components(profile: Path, names: Sequence[str]) -> list[Dict[str, Any]]:
    """Inventory desktop applications without launching them or reading their state."""
    wanted = {name.lower() for name in names}
    components: list[Dict[str, Any]] = []
    if not wanted:
        return components
    if _platform_name() == "windows":
        try:
            import winreg
        except ImportError:
            return components
        uninstall_roots = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        seen: set[str] = set()
        for hive, key_path in uninstall_roots:
            try:
                key = winreg.OpenKey(hive, key_path)
            except OSError:
                continue
            with key:
                for index in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        child_name = winreg.EnumKey(key, index)
                        with winreg.OpenKey(key, child_name) as child:
                            display_name = winreg.QueryValueEx(child, "DisplayName")[0]
                            try:
                                display_version = winreg.QueryValueEx(child, "DisplayVersion")[0]
                            except OSError:
                                display_version = None
                            try:
                                location = winreg.QueryValueEx(child, "InstallLocation")[0]
                            except OSError:
                                location = None
                    except OSError:
                        continue
                    if not isinstance(display_name, str) or display_name.lower() not in wanted:
                        continue
                    identity = f"{display_name.lower()}::{location}"
                    if identity in seen:
                        continue
                    seen.add(identity)
                    components.append({"kind": "desktop", "id": display_name, "status": "present", "path": location if isinstance(location, str) and location else None, "version": display_version if isinstance(display_version, str) else None, "evidence": [{"source": "windows-uninstall-registry", "confidence": "authoritative"}]})
        return components
    if _platform_name() == "macos":
        for root in (Path("/Applications"), profile / "Applications"):
            if not root.is_dir():
                continue
            for bundle in root.glob("*.app"):
                if bundle.stem.lower() in wanted:
                    components.append({"kind": "desktop", "id": bundle.stem, "status": "present", "path": _canonical(bundle), "version": None, "evidence": [{"source": "macos-app-bundle", "confidence": "verified", "path": _canonical(bundle)}]})
        return components
    desktop_roots = [profile / ".local" / "share" / "applications", Path("/usr/share/applications")]
    for root in desktop_roots:
        if not root.is_dir():
            continue
        for entry in root.glob("*.desktop"):
            try:
                text = entry.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            name = next((line[5:] for line in text.splitlines() if line.startswith("Name=")), "")
            if name.lower() in wanted:
                components.append({"kind": "desktop", "id": name, "status": "present", "path": _canonical(entry), "version": None, "evidence": [{"source": "linux-desktop-entry", "confidence": "verified", "path": _canonical(entry)}]})
    return components


def _probe_version(path: str, args: Sequence[str]) -> tuple[str | None, str]:
    try:
        completed = subprocess.run([path, *args], capture_output=True, text=True, timeout=PROBE_TIMEOUT_SECONDS, check=False)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except OSError:
        return None, "unavailable"
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return (output[0][:200] if output else None, "detected" if completed.returncode == 0 and output else "unknown")


def _cache_root() -> Path:
    explicit = os.environ.get("SDD_TOOLKIT_STATE_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve(strict=False) / "runtime-discovery-cache"
    if _platform_name() == "windows":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "SDD-Toolkit" / "runtime-discovery-cache"
    return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "sdd-toolkit" / "runtime-discovery-cache"


def _stamp(path: Path) -> Dict[str, int | None]:
    try:
        stat = path.stat()
        return {"mtime_ns": stat.st_mtime_ns, "size": stat.st_size}
    except OSError:
        return {"mtime_ns": None, "size": None}


def _fingerprint(profile: Path, kit_root: Path, runtime: str, mode: str, extension_dirs: Sequence[Path], portable_roots: Sequence[Path]) -> str:
    adapters = RUNTIME.load_adapters(kit_root)
    paths = []
    for adapter in adapters.values():
        paths.extend(_path_candidates(command) for command in adapter.commands)
    extension_roots = _extension_roots(profile, extension_dirs, portable_roots)
    manifests = []
    for host, root in extension_roots:
        for manifest in sorted(root.glob("*/package.json")):
            manifests.append([host, _canonical(manifest), _stamp(manifest)])
    payload = {
        "schema": CACHE_SCHEMA_VERSION,
        "profile": _canonical(profile),
        "runtime": runtime,
        "mode": mode,
        "context": execution_context(),
        "path": os.environ.get("PATH", ""),
        "pathext": os.environ.get("PATHEXT", ""),
        "candidates": [[item, _stamp(Path(item))] for group in paths for item in group],
        "extension_roots": [[host, _canonical(path), _stamp(path)] for host, path in extension_roots],
        "extension_manifests": manifests,
        "kit_catalog": _stamp(kit_root / "runtimes" / "discovery-catalog.json"),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _cache_path(fingerprint: str) -> Path:
    return _cache_root() / f"{fingerprint}.json"


def _load_cache(fingerprint: str) -> Dict[str, Any] | None:
    path = _cache_path(fingerprint)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if value.get("schema_version") != CACHE_SCHEMA_VERSION or value.get("fingerprint") != fingerprint:
        return None
    if not isinstance(value.get("created_at"), (int, float)) or time.time() - value["created_at"] > CACHE_TTL_SECONDS:
        return None
    report = value.get("report")
    if not isinstance(report, dict):
        return None
    return report


def _write_cache(fingerprint: str, report: Mapping[str, Any]) -> None:
    root = _cache_root()
    path = _cache_path(fingerprint)
    root.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    document = {"schema_version": CACHE_SCHEMA_VERSION, "fingerprint": fingerprint, "created_at": time.time(), "report": report}
    temporary.write_text(json.dumps(document, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def _runtime_record(profile: Path, kit_root: Path, target: str, adapter: RUNTIME.RuntimeAdapter, catalog_entry: Mapping[str, Any], mode: str, extension_roots: Sequence[tuple[str, Path]]) -> Dict[str, Any]:
    paths = _unique(path for command in adapter.commands for path in _path_candidates(command))
    known = [_canonical(path) for path in _known_cli_paths(profile, target) if path.is_file()]
    paths = _unique([*paths, *known])
    cli_paths = [path for path in paths if not _is_extension_bundled(path)]
    embedded_paths = [path for path in paths if _is_extension_bundled(path)]
    components: list[Dict[str, Any]] = []
    for index, path in enumerate(cli_paths):
        components.append({
            "kind": "cli",
            "id": target,
            "status": "cli_available",
            "path": path,
            "version": None,
            "evidence": [{"source": "path" if index == 0 else "path-shadowed", "confidence": "verified", "path": path}],
        })
    for path in embedded_paths:
        components.append({
            "kind": "embedded-cli",
            "id": target,
            "status": "present",
            "path": path,
            "version": None,
            "evidence": [{"source": "extension-bundled-binary", "confidence": "hint", "path": path}],
        })
    components.extend(_extension_components(extension_roots, catalog_entry.get("extension_ids", [])))
    components.extend(_vscode_cli_components(catalog_entry.get("extension_ids", []), mode))
    components.extend(_package_components(profile, catalog_entry.get("packages", {}), mode))
    components.extend(_desktop_components(profile, catalog_entry.get("desktop_names", [])))
    components = _merge_components(components)
    executable = cli_paths[0] if cli_paths else None
    version, version_status = (None, "not-installed") if not executable else (None, "unknown")
    if executable and mode == "full":
        version, version_status = _probe_version(executable, adapter.version_args)
        components[0]["version"] = version
        components[0]["status"] = "version_verified" if version_status == "detected" else "cli_available"
    capability: Dict[str, Any] = {
        "capabilities": [],
        "status": "unknown-version" if executable else "not-installed",
        "evidence": "none",
        "next_action": "run 'sdd runtime detect --mode full' to verify the selected CLI" if executable else None,
    }
    if executable and version_status == "detected":
        capability = RUNTIME.versioned_capabilities(kit_root, target, version)
    agent_root = profile / adapter.user_agent_dir
    skill_root = profile / adapter.skill_dir
    extension_present = any(item["kind"] == "ide-extension" for item in components)
    installed = bool(components)
    status = "absent"
    if executable:
        status = "cli_available"
    elif extension_present:
        status = "present"
    elif installed:
        status = "present"
    if len(cli_paths) > 1:
        status = "conflict"
    readiness = "integration_ready" if executable or extension_present else "absent"
    return {
        "runtime": target,
        "status": status,
        "installed": installed,
        "cli_available": bool(executable),
        "integration_ready": readiness == "integration_ready",
        "executable": executable,
        "version": version,
        "version_status": version_status,
        "version_args": list(adapter.version_args),
        "scopes": list(adapter.scopes),
        "capabilities": capability["capabilities"],
        "capability_status": capability["status"],
        "capability_evidence": capability["evidence"],
        "capability_next_action": capability.get("next_action"),
        "shadowed_executables": cli_paths[1:],
        "embedded_executables": embedded_paths,
        "components": components,
        "evidence": [evidence for component in components for evidence in component["evidence"]],
        "conflicts": ["multiple-cli-candidates"] if len(paths) > 1 else [],
        "targets": {"agents": str(agent_root), "skills": str(skill_root)},
        "remediation": (
            "install or enable a supported CLI or IDE extension" if not installed
            else "select a CLI candidate explicitly" if len(cli_paths) > 1
            else "install the standalone CLI to use this runtime outside its editor" if embedded_paths and not executable
            else "run 'sdd runtime detect --mode full' to verify version and capabilities" if executable and mode == "quick"
            else None
        ),
    }


def discover_runtimes(
    profile: Path,
    kit_root: Path,
    runtime: str = "all",
    mode: str = "quick",
    extension_dirs: Sequence[Path] = (),
    portable_roots: Sequence[Path] = (),
    use_cache: bool = False,
) -> Dict[str, Any]:
    if mode not in {"quick", "full"}:
        raise ValueError("Discovery mode must be 'quick' or 'full'")
    adapters = RUNTIME.load_adapters(kit_root)
    selected = RUNTIME.selected_runtimes(runtime, adapters)
    catalog = load_catalog(kit_root)
    extension_roots = _extension_roots(profile, extension_dirs, portable_roots)
    fingerprint = _fingerprint(profile, kit_root, runtime, mode, extension_dirs, portable_roots) if use_cache and mode == "quick" else None
    cached = _load_cache(fingerprint) if fingerprint else None
    if cached is not None:
        report = json.loads(json.dumps(cached))
        report["cache"] = {"status": "hit", "ttl_seconds": CACHE_TTL_SECONDS}
        return report
    report = {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "context": execution_context(),
        "catalog_schema_version": catalog["schema_version"],
        "runtimes": {
            target: _runtime_record(profile, kit_root, target, adapters[target], catalog["runtimes"].get(target, {}), mode, extension_roots)
            for target in selected
        },
        "network_accessed": False,
        "read_only": not bool(fingerprint),
        "writes_cache": bool(fingerprint),
        "cache": {"status": "miss" if fingerprint else "disabled", "ttl_seconds": CACHE_TTL_SECONDS if fingerprint else None},
    }
    if fingerprint:
        _write_cache(fingerprint, report)
    return report
