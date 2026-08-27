#!/usr/bin/env python3
"""Fail closed on accidental private material before a community release."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTENSIONS = {
    ".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".sh", ".ps1", ".py",
    ".ts", ".tsx", ".js", ".mjs", ".xml", ".html", ".ini", ".cfg",
}
BLOCKED = re.compile(
    r"casas\s*bahia|via\s*v[ae]rejo|casasbahia\.com|grupocasasbahia|"
    r"viavarejo\.com|workspace-gcb|convair-helm|saas-enterprise|"
    r"felipe\.silva|gcb-(?:hr|project|example|other)-|organization-helm|"
    r"gcbregistry|grupoexample",
    re.IGNORECASE,
)
SECRET = re.compile(
    r"sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|"
    r"BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY|"
    r"(?:https?|ssh)://[^\s/@:]+:[^\s/@]+@",
)
PERSONAL_PATH = re.compile(
    r"(?:[A-Za-z]:[\\/]Users[\\/](?!<user>|user(?:name)?(?:[\\/]|\b))[^\s\\/]+|"
    r"(?<![A-Za-z0-9._-])/(?:home|Users)/(?!<user>|user(?:name)?(?:/|\b))[^\s/]+)",
)


def files_to_scan() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--cached", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=True,
        )
        paths = [ROOT / line for line in result.stdout.splitlines()]
    except (OSError, subprocess.CalledProcessError):
        paths = [path for path in ROOT.rglob("*") if path.is_file()]
    return [
        path for path in paths
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS
        and ".git" not in path.parts
        and "node_modules" not in path.parts
        and "test-results" not in path.parts
        and "playwright-report" not in path.parts
        and path.name not in {"public_content_check.py", "validate-public-content.sh", "validate-public-content.ps1"}
    ]


def main() -> int:
    findings: list[tuple[str, str]] = []
    for path in files_to_scan():
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        relative = path.relative_to(ROOT).as_posix()
        for pattern, label in ((BLOCKED, "internal reference"), (SECRET, "credential/private key"), (PERSONAL_PATH, "personal path")):
            if pattern.search(text):
                findings.append((relative, label))
    if findings:
        for path, label in findings:
            print(f"public-content check failed: {label}: {path}", file=sys.stderr)
        return 1
    print(f"Public-content validation passed ({len(files_to_scan())} text files scanned).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
