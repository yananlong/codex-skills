#!/usr/bin/env python3
"""Inspect the current Zotero API key and accessible libraries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _zotero import default_user_library, list_groups, resolve_api_key


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-key", help="Zotero API key; defaults to $ZOTERO_API_KEY")
    parser.add_argument("--out", type=Path, help="Optional JSON output path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    api_key = resolve_api_key(args.api_key)
    library_type, library_id, key_info = default_user_library(api_key)
    groups = list_groups(library_id, api_key)
    payload = {
        "default_library": {
            "library_type": library_type,
            "library_id": library_id,
        },
        "key_info": key_info,
        "groups": groups,
    }

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
