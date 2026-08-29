#!/usr/bin/env python3
"""Produce a deterministic inventory of compiled runtime artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import sdd_runtime


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path) -> dict:
    adapters = sdd_runtime.load_adapters(root)
    runtimes = {}
    for name, adapter in adapters.items():
        pattern = "*.toml" if adapter.renderer == "codex-toml" else "*.agent.md" if name == "copilot" else "*.md"
        files = [path for path in sorted((root / adapter.output_dir).glob(pattern)) if path.is_file()]
        runtimes[name] = {
            "renderer": adapter.renderer,
            "count": len(files),
            "files": [{"path": path.relative_to(root).as_posix(), "sha256": sha256(path)} for path in files],
        }
    shared = [path for path in sorted((root / "dist" / "shared" / "skills").glob("*/SKILL.md")) if path.is_file()]
    identity = json.loads((root / "metadata" / "project-identity.json").read_text(encoding="utf-8"))
    return {
        "schema_version": 1,
        "toolkit_version": (root / "VERSION").read_text(encoding="utf-8").strip(),
        "provenance": {
            "origin": "repository-maintained",
            "license": "MIT",
            "maintainer": identity["maintainer"],
            "review_status": "pending-release-review",
        },
        "runtimes": runtimes,
        "shared_skills": {
            "count": len(shared),
            "files": [{"path": path.relative_to(root).as_posix(), "sha256": sha256(path)} for path in shared],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create SDD Toolkit build inventory")
    parser.add_argument("--kit-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--write", default="")
    args = parser.parse_args()
    root = Path(args.kit_root).expanduser().resolve(strict=False)
    value = inventory(root)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        destination = root / args.write
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload.encode("utf-8"))
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
