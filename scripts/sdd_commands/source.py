"""User-scoped toolkit source: validation, Git retrieval and status."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import sdd_transaction as TXN
import sdd_runtime as RUNTIME
import sdd_user_state as STATE

from .common import emit


def user_installation_path() -> Path:
    return STATE.state_dir() / "user" / "installation.json"


def load_user_installation() -> Dict[str, Any]:
    path = user_installation_path()
    if not path.exists():
        return {"schema_version": 2, "scope": "user", "managed_files": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise STATE.StateError(f"Cannot read user installation state {path}: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") not in {1, 2} or value.get("scope") != "user" or not isinstance(value.get("managed_files"), list):
        raise STATE.StateError(f"Unsupported or invalid user installation state: {path}")
    normalized: List[Dict[str, Any]] = []
    for item in value["managed_files"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise STATE.StateError(f"Invalid managed file record: {path}")
        runtimes = item.get("runtimes")
        if not isinstance(runtimes, list):
            runtimes = [item.get("runtime")] if isinstance(item.get("runtime"), str) else []
        if not runtimes or not all(isinstance(runtime, str) for runtime in runtimes):
            raise STATE.StateError(f"Invalid managed file runtimes: {path}")
        record = dict(item)
        record["runtimes"] = list(dict.fromkeys(runtimes))
        record.setdefault("runtime", record["runtimes"][0])
        normalized.append(record)
    value["managed_files"] = normalized
    value["schema_version"] = 2
    return value


def user_install_sources(kit: Path, runtime: str, profile: Path) -> List[Dict[str, Any]]:
    targets: List[Dict[str, Any]] = []
    adapters = RUNTIME.load_adapters(kit)
    try:
        runtimes = RUNTIME.selected_runtimes(runtime, adapters)
    except ValueError as exc:
        raise STATE.StateError(str(exc)) from exc
    by_relative: Dict[str, Dict[str, Any]] = {}
    for target in runtimes:
        adapter = adapters[target]
        source_root = kit / adapter.output_dir
        pattern = "*.toml" if adapter.renderer == "codex-toml" else "*.agent.md" if target == "copilot" else "*.md"
        for source in sorted(source_root.glob(pattern)):
            relative = str(Path(adapter.user_agent_dir) / source.name)
            entry = by_relative.setdefault(relative, {"runtime": target, "runtimes": [], "source": str(source), "relative": relative})
            if target not in entry["runtimes"]:
                entry["runtimes"].append(target)
        if target in {"codex", "cursor"}:
            shared_root = kit / "dist" / "shared" / "skills"
            shared_sources = list(sorted(shared_root.glob("*/SKILL.md"))) if shared_root.is_dir() else []
            shared_sources.extend(sorted((kit / "templates" / "skills").glob("*/SKILL.md")))
        else:
            shared_sources = sorted((kit / "templates" / "skills").glob("*/SKILL.md"))
        for skill in shared_sources:
            relative = str(Path(adapter.skill_dir) / skill.parent.name / "SKILL.md")
            entry = by_relative.setdefault(relative, {"runtime": target, "runtimes": [], "source": str(skill), "relative": relative})
            if target not in entry["runtimes"]:
                entry["runtimes"].append(target)
    targets = list(by_relative.values())
    if not targets:
        raise STATE.StateError(f"No compiled assets found for runtime '{runtime}' in {kit}")
    return targets


def local_source_metadata(kit: Path) -> Dict[str, str]:
    commit = "0000000"
    remote = "local"
    try:
        completed = subprocess.run(["git", "-C", str(kit), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5, check=False)
        if completed.returncode == 0 and re.fullmatch(r"[0-9a-f]{7,64}", completed.stdout.strip()):
            commit = completed.stdout.strip()
        remote_result = subprocess.run(["git", "-C", str(kit), "config", "--get", "remote.origin.url"], capture_output=True, text=True, timeout=5, check=False)
        if remote_result.returncode == 0 and remote_result.stdout.strip():
            remote = remote_result.stdout.strip()
            if "@" in remote and "://" in remote:
                scheme, remainder = remote.split("://", 1)
                remote = f"{scheme}://{remainder.split('@', 1)[-1]}"
    except (OSError, subprocess.TimeoutExpired):
        pass
    version = (kit / "VERSION").read_text(encoding="utf-8").strip()
    return {
        "source_type": "local",
        "repository_url": remote or "local",
        "channel": "explicit",
        "requested_ref": "local",
        "resolved_ref": version,
        "commit": commit,
    }


def source_state_path() -> Path:
    return STATE.state_dir() / "user" / "source.json"


def validate_kit_root(kit: Path) -> None:
    required = (
        kit / "VERSION", kit / "scripts" / "sdd.py", kit / "scripts" / "sdd_user_state.py",
        kit / "scripts" / "sdd_commands" / "__init__.py",
        kit / "dist", kit / "templates" / "skills", kit / "schemas",
    )
    missing = [str(item) for item in required if not item.exists()]
    if missing:
        raise STATE.StateError(f"Toolkit source is incomplete; missing: {', '.join(missing)}")


def git_command(arguments: List[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(["git", *arguments], capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise STATE.StateError(f"Git command failed: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[:500]
        raise STATE.StateError(f"Git command failed: {detail or 'unknown error'}")
    return completed


def validate_repository_url(value: str) -> str:
    url = value.strip()
    if not url:
        raise STATE.StateError("repository URL is required")
    if "://" in url:
        scheme, remainder = url.split("://", 1)
        if scheme not in {"https", "ssh", "file"}:
            raise STATE.StateError("repository URL must use HTTPS, SSH or an explicit local file URL")
        if "@" in remainder:
            user = remainder.split("@", 1)[0]
            if scheme != "ssh" or user != "git":
                raise STATE.StateError("repository URL must not contain embedded credentials")
    elif not re.fullmatch(r"(?:git@[^:/]+):.+", url):
        raise STATE.StateError("repository URL must use HTTPS, SSH or an explicit local file URL")
    return url


def remote_ref(url: str, channel: str, requested: str) -> str:
    if requested:
        return requested
    if channel == "main":
        return "main"
    output = git_command(["ls-remote", "--refs", "--tags", url, "v*"], timeout=30).stdout
    tags: List[tuple[tuple[int, int, int], int, str]] = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        tag = parts[1].removeprefix("refs/tags/")
        if tag.endswith("^{}"):
            continue
        match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(-([0-9A-Za-z.-]+))?", tag)
        if not match:
            continue
        prerelease = 1 if match.group(5) else 0
        if channel == "stable" and prerelease:
            continue
        if channel == "beta" and not prerelease:
            continue
        tags.append(((int(match.group(1)), int(match.group(2)), int(match.group(3))), prerelease, tag))
    if not tags:
        raise STATE.StateError(f"No valid {channel} tag found in repository")
    tags.sort(key=lambda item: (item[0], item[1], item[2]))
    return tags[-1][2]


def toolkit_version(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?", value.strip())
    if not match:
        raise STATE.StateError(f"Invalid toolkit version: {value}")
    return tuple(int(part) for part in match.groups())


def source_install(args: argparse.Namespace) -> int:
    incomplete = TXN.incomplete_journals(STATE.state_dir())
    if incomplete:
        result = {
            "schema_version": 1, "scope": "user", "status": "blocked",
            "code": "transaction_recovery_required", "incomplete_transactions": len(incomplete),
            "next_action": "sdd transaction recover --scope user --apply",
        }
        emit(result, args.json)
        return 2
    url = validate_repository_url(args.repository_url)
    root = Path(args.source_root or (STATE.state_dir() / "user" / "kit")).expanduser().resolve(strict=False)
    if root.parent == root or root == Path.home():
        raise STATE.StateError("source root must be a dedicated directory")
    existing = root.exists()
    if existing and not (root / ".git").is_dir():
        raise STATE.StateError(f"source root exists but is not a Git checkout: {root}")
    if getattr(args, "offline", False):
        if not existing or not (root / "VERSION").is_file():
            result = {
                "schema_version": 1, "scope": "user", "mode": "apply" if args.apply else "preview",
                "status": "blocked", "code": "offline_cache_missing", "repository_url": url,
                "source_root": str(root), "cache_path": str(root), "writes_project": False,
            }
            emit(result, args.json)
            return 2
        validate_kit_root(root)
        result = {
            "schema_version": 1, "scope": "user", "mode": "apply" if args.apply else "preview",
            "status": "offline-ready", "action": "reuse-cache", "repository_url": url,
            "resolved_ref": git_command(["-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"], timeout=10).stdout.strip(),
            "version": (root / "VERSION").read_text(encoding="utf-8").strip(),
            "source_root": str(root), "cache_path": str(root), "writes_project": False,
        }
        emit(result, args.json)
        return 0
    ref = remote_ref(url, args.channel, args.ref)
    mode = "update" if existing else "clone"
    result: Dict[str, Any] = {
        "schema_version": 1, "scope": "user", "mode": "apply" if args.apply else "preview",
        "status": "ready", "action": mode, "repository_url": url, "channel": args.channel,
        "requested_ref": args.ref or "", "resolved_ref": ref, "source_root": str(root),
        "writes_project": False,
    }
    if not args.apply:
        emit(result, args.json)
        return 0
    if existing:
        dirty = git_command(["-C", str(root), "status", "--porcelain"], timeout=10).stdout.strip()
        if dirty:
            result["status"] = "blocked"
            result["code"] = "source_dirty"
            result["detail"] = "source checkout has local changes; update was not attempted"
            emit(result, args.json)
            return 2
    staging_parent = Path(tempfile.mkdtemp(prefix="sdd-source-", dir=str(root.parent)))
    staging = staging_parent / "kit"
    previous = root.with_name(f".{root.name}.previous")
    promoted = False
    try:
        git_command(["clone", "--depth", "1", "--branch", ref, url, str(staging)], timeout=120)
        validate_kit_root(staging)
        candidate_version = (staging / "VERSION").read_text(encoding="utf-8").strip()
        if existing and (root / "VERSION").is_file():
            current_version = (root / "VERSION").read_text(encoding="utf-8").strip()
            if toolkit_version(candidate_version) < toolkit_version(current_version) and not getattr(args, "allow_downgrade", False):
                result.update({
                    "status": "blocked",
                    "code": "downgrade_requires_confirmation",
                    "current_version": current_version,
                    "candidate_version": candidate_version,
                    "detail": "re-run with --allow-downgrade to accept a lower toolkit version",
                })
                emit(result, args.json)
                return 2
        if previous.exists():
            raise STATE.StateError(f"source backup already exists: {previous}")
        if existing:
            os.replace(root, previous)
        os.replace(staging, root)
        promoted = True
        commit = git_command(["-C", str(root), "rev-parse", "HEAD"], timeout=10).stdout.strip()
        source = {
            "schema_version": 1, "scope": "user", "source_type": "git",
            "repository_url": url, "channel": args.channel,
            "requested_ref": args.ref or args.channel, "resolved_ref": ref, "commit": commit,
            "source_root": str(root), "updated_at": STATE.utc_now(),
            "cache_path": str(root),
        }
        with STATE.RegistryLock(source_state_path().with_suffix(".json.lock")):
            STATE.atomic_write(source_state_path(), source, backup=True)
        if previous.exists() and not getattr(args, "keep_previous_source", False):
            shutil.rmtree(previous)
        result.update({"status": "updated" if existing else "cloned", "commit": commit})
    except (OSError, STATE.StateError) as exc:
        if previous.exists():
            if root.exists():
                shutil.rmtree(root, ignore_errors=True)
            os.replace(previous, root)
        elif promoted and root.exists():
            shutil.rmtree(root, ignore_errors=True)
        result["status"] = "rolled_back"
        result["error"] = str(exc)
        emit(result, args.json)
        return 2
    finally:
        if staging_parent.exists():
            shutil.rmtree(staging_parent, ignore_errors=True)
    emit(result, args.json)
    return 0


def source_status(args: argparse.Namespace) -> int:
    path = source_state_path()
    if not path.exists():
        result = {"schema_version": 1, "scope": "user", "status": "not-configured", "source_state": str(path)}
        emit(result, args.json)
        return 0
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise STATE.StateError(f"Cannot read source state {path}: {exc}") from exc
    root = Path(source.get("source_root", ""))
    result = dict(source)
    result["status"] = "healthy" if root.is_dir() and (root / "VERSION").is_file() else "missing"
    result["source_state"] = str(path)
    emit(result, args.json)
    return 2 if result["status"] == "missing" else 0


def register_source(sub) -> None:
    source_parser = sub.add_parser("source", help="Manage the user-scoped toolkit source")
    source_sub = source_parser.add_subparsers(dest="source_command", required=True)
    source_status_parser = source_sub.add_parser("status", help="Inspect the configured toolkit source")
    source_status_parser.add_argument("--json", action="store_true")
    source_status_parser.set_defaults(handler=source_status)
    for source_command_name in ("install", "update"):
        source_command = source_sub.add_parser(source_command_name, help=f"{source_command_name.capitalize()} a user-scoped Git source")
        source_command.add_argument("--repository-url", required=True)
        source_command.add_argument("--source-root", default="")
        source_command.add_argument("--channel", choices=["stable", "beta", "main"], default="main")
        source_command.add_argument("--ref", default="")
        source_command.add_argument("--offline", action="store_true", help="Reuse the validated local source cache without network access")
        source_command.add_argument("--allow-downgrade", action="store_true", help="Allow replacing the source with a lower toolkit version")
        source_command.add_argument("--apply", action="store_true")
        source_command.add_argument("--json", action="store_true")
        source_command.set_defaults(handler=source_install)
