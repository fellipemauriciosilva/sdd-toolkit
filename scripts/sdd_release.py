#!/usr/bin/env python3
"""Create deterministic, self-contained SDD Toolkit release artifacts."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import tarfile
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import build_inventory


PACKAGE_DIRECTORIES = ("agents", "dist", "docs", "metadata", "runtimes", "schemas", "scripts", "templates")
PACKAGE_FILES = ("CHANGELOG.md", "CITATION.cff", "LICENSE", "README.md", "VERSION", "install.ps1", "install.sh")
EPOCH = (1980, 1, 1, 0, 0, 0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def release_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for name in PACKAGE_FILES:
        path = root / name
        if not path.is_file():
            raise ValueError(f"Release-required file is missing: {path}")
        files.append(path)
    for name in PACKAGE_DIRECTORIES:
        directory = root / name
        if not directory.is_dir():
            raise ValueError(f"Release-required directory is missing: {directory}")
        files.extend(path for path in directory.rglob("*") if path.is_file() and "__pycache__" not in path.parts and path.name != "ROADMAP.local.md")
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def write_zip(root: Path, destination: Path, files: Iterable[Path]) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(f"sdd-toolkit/{relative}", date_time=EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if os.access(path, os.X_OK) else 0o644) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def write_tar(root: Path, destination: Path, files: Iterable[Path]) -> None:
    with destination.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for path in files:
                info = archive.gettarinfo(str(path), arcname=f"sdd-toolkit/{path.relative_to(root).as_posix()}")
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mtime = 0
                with path.open("rb") as stream:
                    archive.addfile(info, stream)


def timestamp() -> str:
    """Use SOURCE_DATE_EPOCH when supplied; otherwise keep local artifacts reproducible."""
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "0"))
    return datetime.fromtimestamp(epoch, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic SDD Toolkit release assets")
    parser.add_argument("--kit-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--version", default="")
    args = parser.parse_args()
    root = Path(args.kit_root).resolve(strict=True)
    version = args.version or (root / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        raise ValueError("Release version is empty")
    output = Path(args.out_dir).resolve(strict=False)
    output.mkdir(parents=True, exist_ok=True)

    # Rebuild the inventory in the source tree before packaging it.
    manifest = build_inventory.inventory(root)
    (root / "dist" / "build-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    files = release_files(root)
    zip_path = output / f"sdd-toolkit-{version}.zip"
    tar_path = output / f"sdd-toolkit-{version}.tar.gz"
    write_zip(root, zip_path, files)
    write_tar(root, tar_path, files)
    artifacts = [{"name": path.name, "sha256": sha256(path), "bytes": path.stat().st_size} for path in (zip_path, tar_path)]
    (output / "SHA256SUMS").write_text("".join(f"{item['sha256']}  {item['name']}\n" for item in artifacts), encoding="utf-8", newline="\n")
    identity = json.loads((root / "metadata" / "project-identity.json").read_text(encoding="utf-8"))
    sbom = {
        "bomFormat": "CycloneDX", "specVersion": "1.5", "serialNumber": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'https://sdd-toolkit.dev/releases/' + version)}", "version": 1,
        "metadata": {"timestamp": timestamp(), "component": {"type": "application", "name": "sdd-toolkit", "version": version, "licenses": [{"license": {"id": "MIT"}}]}},
        "components": [{"type": "library", "name": "jsonschema", "version": "requirements-dev", "scope": "optional", "licenses": [{"license": {"id": "MIT"}}]}],
    }
    (output / "sbom.cdx.json").write_text(json.dumps(sbom, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    provenance = {"schema_version": 1, "generated_at": timestamp(), "toolkit_version": version, "identity": identity["maintainer"], "build_manifest": manifest, "artifacts": artifacts, "attestation": "unsigned-local; sign the release tag and attach provider attestation in CI"}
    (output / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "ready", "version": version, "out_dir": str(output), "artifacts": artifacts}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
