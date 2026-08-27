#!/usr/bin/env python3
"""Fail CI when commits in a revision range do not contain a DCO sign-off."""

from __future__ import annotations

import argparse
import subprocess
import sys


def commits(revision_range: str) -> list[tuple[str, str]]:
    completed = subprocess.run(
        ["git", "log", "--format=%H%x00%B%x00", revision_range],
        check=False, capture_output=True, text=True, encoding="utf-8",
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "git log failed")
    parts = completed.stdout.split("\x00")
    return [(parts[index], parts[index + 1]) for index in range(0, len(parts) - 1, 2) if parts[index]]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Developer Certificate of Origin sign-offs")
    parser.add_argument("--range", dest="revision_range", required=True, help="Git revision range, for example base..head")
    args = parser.parse_args()
    try:
        missing = [commit for commit, body in commits(args.revision_range) if "signed-off-by:" not in body.casefold()]
    except RuntimeError as exc:
        print(f"DCO check failed: {exc}", file=sys.stderr)
        return 2
    if missing:
        print("DCO sign-off missing from: " + ", ".join(missing), file=sys.stderr)
        print("Use: git commit -s", file=sys.stderr)
        return 1
    print("DCO validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
