#!/usr/bin/env python3
"""Install or update the upstream OpenAIReview engine for this skill."""

from __future__ import annotations

import argparse
from pathlib import Path

from _engine import DEFAULT_VENV, install_engine, package_dir, packaged_skill_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--venv",
        type=Path,
        default=DEFAULT_VENV,
        help="Virtualenv path for the upstream engine.",
    )
    parser.add_argument(
        "--source",
        choices=["github", "pypi"],
        default="github",
        help="Install source. Default uses the upstream GitHub repository.",
    )
    parser.add_argument(
        "--ref",
        default="main",
        help="Git ref when --source github is used.",
    )
    parser.add_argument(
        "--with",
        dest="extras",
        action="append",
        default=[],
        choices=["mistral", "deepseek"],
        help="Optional OCR extras to install.",
    )
    parser.add_argument(
        "--reinstall",
        action="store_true",
        help="Force reinstall even if the package already exists.",
    )
    parser.add_argument(
        "--no-upgrade",
        action="store_true",
        help="Skip pip --upgrade for the package install step.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    venv_dir = install_engine(
        venv_dir=args.venv,
        source=args.source,
        ref=args.ref,
        extras=args.extras,
        upgrade=not args.no_upgrade,
        reinstall=args.reinstall,
    )
    print("OpenAIReview engine is ready.")
    print(f"venv: {venv_dir}")
    print(f"package: {package_dir(venv_dir)}")
    print(f"skill assets: {packaged_skill_dir(venv_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
