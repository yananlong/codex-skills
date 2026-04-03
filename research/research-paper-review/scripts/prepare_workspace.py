#!/usr/bin/env python3
"""Run the packaged OpenAIReview workspace-preparation script."""

from __future__ import annotations

import argparse
from pathlib import Path

from _engine import DEFAULT_VENV, run_packaged_skill_script


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
    return args, remainder


def main() -> int:
    args, remainder = parse_args()
    return run_packaged_skill_script(args.venv, "scripts/prepare_workspace.py", remainder)


if __name__ == "__main__":
    raise SystemExit(main())
