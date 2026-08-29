"""Command groups of the ``sdd`` CLI.

``scripts/sdd.py`` stays the entry point and the single place that defines the
order of the commands; each module here owns one group's handlers and registers
its own subparsers.
"""

from __future__ import annotations

from . import activation, common, context, inspection, lifecycle, source

__all__ = ["activation", "common", "context", "inspection", "lifecycle", "source"]
