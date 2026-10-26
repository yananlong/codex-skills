#!/usr/bin/env python3
"""Install the pinned upstream OpenAIReview engine outside the skill directory.

Default: OpenAIReview ENGINE_VERSION from the release commit on GitHub, in a versioned virtualenv
under $XDG_DATA_HOME/codex-skills/ (or ~/.local/share/codex-skills/). --source pypi installs the same
version from PyPI. Passing another --ref installs an unpinned engine and records that choice.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from _engine import (
    DEFAULT_VENV,
    ENGINE_COMMIT,
    ENGINE_TAG,
    ENGINE_VERSION,
    install_engine,
    package_dir,
    packaged_skill_dir,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--venv",
        type=Path,
        default=DEFAULT_VENV,
        help="Virtualenv path for the upstream engine (default: a versioned folder outside the skill).",
    )
    parser.add_argument(
        "--source",
        choices=["github", "pypi"],
        default="github",
        help=f"Install source. github installs the pinned release commit; pypi installs openaireview=={ENGINE_VERSION}.",
    )
    parser.add_argument(
        "--ref",
        default=ENGINE_COMMIT,
        help=f"Git ref when --source github is used (default: {ENGINE_TAG} at {ENGINE_COMMIT[:12]}). "
        "Any other ref installs an unpinned engine.",
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
    print(f"OpenAIReview engine is ready (pinned to {ENGINE_VERSION}).")
    print(f"venv: {venv_dir}")
    print(f"package: {package_dir(venv_dir)}")
    print(f"skill assets: {packaged_skill_dir(venv_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
