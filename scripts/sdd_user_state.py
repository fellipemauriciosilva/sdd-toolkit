"""Primitives for user-scoped SDD Toolkit state."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Union


class StateError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_path(value: Union[str, Path]) -> Path:
    return Path(value).expanduser().resolve(strict=False)


def state_dir() -> Path:
    override = os.environ.get("SDD_TOOLKIT_STATE_DIR")
    if override:
        candidate = canonical_path(override)
        if candidate.parent == candidate or candidate == Path.home():
            raise StateError("SDD_TOOLKIT_STATE_DIR must point to a dedicated state directory")
        return candidate
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")
        return canonical_path(Path(base) / "SDD-Toolkit")
    if system == "Darwin":
        return canonical_path(Path.home() / "Library" / "Application Support" / "sdd-toolkit")
    base = os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state")
    return canonical_path(Path(base) / "sdd-toolkit")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def installation_id(project: Path) -> str:
    canonical = str(canonical_path(project))
    return hashlib.sha256(os.path.normcase(canonical).encode("utf-8")).hexdigest()


def safe_lexical_path(root: Path, relative: str, label: str) -> Path:
    root = canonical_path(root)
    candidate = Path(os.path.abspath(root / Path(relative)))
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise StateError(f"{label} escapes root: {relative}") from exc
    current = candidate
    while current != root:
        if current.is_symlink():
            raise StateError(f"{label} contains a symbolic link: {relative}")
        current = current.parent
    return candidate


def atomic_write(path: Path, value: Dict[str, Any], backup: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        os.chmod(path.parent, 0o700)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        temporary = Path(temporary_name)
        if backup and path.exists():
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        os.replace(temporary, path)
        if os.name != "nt":
            os.chmod(path, 0o600)
    finally:
        try:
            Path(temporary_name).unlink()
        except FileNotFoundError:
            pass


class RegistryLock:
    def __init__(self, path: Path, timeout: float = 10.0) -> None:
        self.path = path
        self.timeout = timeout
        self.acquired = False

    def __enter__(self) -> "RegistryLock":
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(descriptor)
                self.acquired = True
                return self
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise StateError(f"Timed out waiting for state lock: {self.path}")
                time.sleep(0.1)

    def __exit__(self, *_: object) -> None:
        if self.acquired:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
