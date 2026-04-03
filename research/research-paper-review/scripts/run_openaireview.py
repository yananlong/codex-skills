#!/usr/bin/env python3
"""Mirror the upstream openaireview CLI from the local skill."""

from __future__ import annotations

import argparse
from pathlib import Path

from _engine import DEFAULT_VENV, run_cli


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--venv",
        type=Path,
        default=DEFAULT_VENV,
        help="Virtualenv path created by install_engine.py.",
    )
    args, remainder = parser.parse_known_args()
    if remainder and remainder[0] == "--":
        remainder = remainder[1:]
    if not remainder:
        parser.error("Pass an openaireview subcommand such as review, extract, or serve.")
    return args, remainder


def main() -> int:
    args, remainder = parse_args()
    return run_cli(args.venv, remainder)


if __name__ == "__main__":
    raise SystemExit(main())
