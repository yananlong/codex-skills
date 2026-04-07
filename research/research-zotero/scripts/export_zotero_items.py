#!/usr/bin/env python3
"""Export Zotero library items in citation-friendly formats."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _zotero import api_get_json, api_get_text, build_items_path, default_user_library, resolve_api_key


TEXT_EXPORTS = {"bibtex", "biblatex", "ris"}
JSON_EXPORTS = {"json", "csljson"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=False)
    scope.add_argument("--user-id", help="Zotero user library ID")
    scope.add_argument("--group-id", help="Zotero group library ID")
    parser.add_argument("--collection-key", help="Restrict results to a Zotero collection key")
    parser.add_argument("--tag", action="append", default=[], help="Tag filter (repeatable)")
    parser.add_argument("--query", help="Free-text Zotero query")
    parser.add_argument("--item-type", help="Restrict by Zotero item type")
    parser.add_argument("--item-key", help="Comma-separated list of item keys")
    parser.add_argument("--limit", type=int, default=100, help="Items per request (default: 100)")
    parser.add_argument("--all", action="store_true", help="Paginate until exhausted")
    parser.add_argument("--format", required=True, choices=sorted(TEXT_EXPORTS | JSON_EXPORTS))
    parser.add_argument("--style", help="Citation style for formatted bibliography exports")
    parser.add_argument("--locale", help="Bibliography locale")
    parser.add_argument("--api-key", help="Zotero API key; defaults to $ZOTERO_API_KEY")
    parser.add_argument("--out", type=Path, required=True, help="Output path")
    return parser


def resolve_library(args: argparse.Namespace, api_key: str):
    if args.user_id:
        return "user", args.user_id
    if args.group_id:
        return "group", args.group_id
    library_type, library_id, _ = default_user_library(api_key)
    return library_type, library_id


def build_params(args: argparse.Namespace, start: int) -> dict[str, str | list[str]]:
    params: dict[str, str | list[str]] = {
        "format": args.format,
        "limit": str(args.limit),
        "start": str(start),
    }
    if args.tag:
        params["tag"] = args.tag
    if args.query:
        params["q"] = args.query
    if args.item_type:
        params["itemType"] = args.item_type
    if args.item_key:
        params["itemKey"] = args.item_key
    if args.style:
        params["style"] = args.style
    if args.locale:
        params["locale"] = args.locale
    return params


def main() -> int:
    args = build_parser().parse_args()
    api_key = resolve_api_key(args.api_key)
    library_type, library_id = resolve_library(args, api_key)
    path = build_items_path(library_type, library_id, collection_key=args.collection_key)

    start = 0
    text_parts: list[str] = []
    json_parts: list = []

    while True:
        params = build_params(args, start)
        if args.format in TEXT_EXPORTS:
            page = api_get_text(path, api_key, params)
            if page:
                text_parts.append(page)
            page_size = args.limit if args.all else 0
        else:
            page = api_get_json(path, api_key, params)
            if isinstance(page, list):
                json_parts.extend(page)
                page_size = len(page)
            else:
                json_parts.append(page)
                page_size = 0

        if not args.all or page_size < args.limit:
            break
        start += args.limit

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.format in TEXT_EXPORTS:
        args.out.write_text("\n\n".join(part for part in text_parts if part), encoding="utf-8")
    else:
        args.out.write_text(json.dumps(json_parts, indent=2), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
