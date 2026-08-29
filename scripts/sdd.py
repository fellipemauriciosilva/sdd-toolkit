#!/usr/bin/env python3
"""Public SDD Toolkit command line interface.

The platform installers are thin wrappers around the user-scoped lifecycle so
that Windows, Linux and macOS expose the same vocabulary and exit codes.

This module is the composition root: it owns the parser skeleton and the order
of the commands. Handlers and their subparsers live in ``sdd_commands``.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

import sdd_transaction as TXN
import sdd_user_state as STATE

from sdd_commands import activation, common, context, inspection, lifecycle, source
from sdd_commands.common import ROOT
# Superfície pública histórica: importado por tests/test_release_engineering.py.
from sdd_commands.inspection import detect_harnesses  # noqa: F401


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sdd", description="SDD Toolkit lifecycle CLI")
    parser.add_argument("--version", action="version", version=(ROOT / "VERSION").read_text(encoding="utf-8").strip())
    sub = parser.add_subparsers(dest="command", required=True)

    common.register_about(sub)
    activation.register_activate(sub)
    lifecycle.register_install(sub)
    lifecycle.register_user_cli_command(sub)
    inspection.register_runtime(sub)
    inspection.register_delivery(sub)
    inspection.register_architecture(sub)
    context.register_result(sub)
    inspection.register_lint(sub)
    source.register_source(sub)
    context.register_context(sub)
    lifecycle.register_transaction(sub)
    activation.register_status(sub)
    context.register_run(sub)
    lifecycle.register_doctor(sub)
    lifecycle.register_update_uninstall(sub)
    activation.register_daily(sub)
    activation.register_activation(sub)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (OSError, STATE.StateError, TXN.TransactionError, ValueError) as exc:
        print(f"sdd: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
