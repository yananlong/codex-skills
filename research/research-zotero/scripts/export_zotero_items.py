#!/usr/bin/env python3
"""Export Zotero library items in citation-friendly formats."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _zotero import (
    api_get_json_with_headers,
    api_get_text_with_headers,
    build_items_path,
    default_user_library,
    resolve_api_key,
    total_results,
)


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
    parser.add_argument("--limit", type=int, default=100, help="Items per request (page size, default: 100)")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Paginate until exhausted (the default; kept for compatibility)",
    )
    parser.add_argument("--max-items", type=int, help="Stop after this many items (truncated export, warned on stderr)")
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


def build_params(args: argparse.Namespace, start: int, limit: int | None = None) -> dict[str, str | list[str]]:
    params: dict[str, str | list[str]] = {
        "format": args.format,
        "limit": str(args.limit if limit is None else limit),
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

    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    if args.max_items is not None and args.max_items < 1:
        raise SystemExit("--max-items must be at least 1")

    start = 0
    text_parts: list[str] = []
    json_parts: list = []
    total: int | None = None
    exhausted = False

    while True:
        page_limit = args.limit if args.max_items is None else min(args.limit, args.max_items - start)
        if page_limit <= 0:
            break
        params = build_params(args, start, limit=page_limit)
        if args.format in TEXT_EXPORTS:
            page, headers = api_get_text_with_headers(path, api_key, params)
            if page.strip():
                text_parts.append(page)
            # Text pages cannot be counted reliably; rely on Total-Results and stop on an empty page.
            page_size = page_limit if page.strip() else 0
        else:
            page, headers = api_get_json_with_headers(path, api_key, params)
            if isinstance(page, list):
                json_parts.extend(page)
                page_size = len(page)
            else:
                json_parts.append(page)
                page_size = 0
        header_total = total_results(headers)
        if header_total is not None:
            total = header_total
        start += page_limit
        if page_size < page_limit or (total is not None and start >= total):
            exhausted = True
            break
        if total is None and args.format in TEXT_EXPORTS and args.max_items is None and start >= 100000:
            raise SystemExit("Stopping text export after 100000 items without a Total-Results header.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.format in TEXT_EXPORTS:
        args.out.write_text("\n\n".join(part for part in text_parts if part), encoding="utf-8")
    else:
        args.out.write_text(json.dumps(json_parts, indent=2), encoding="utf-8")
    print(f"wrote {args.out}")
    if not exhausted:
        print(
            f"WARNING: truncated export at {start} items"
            + (f" of {total}" if total is not None else "")
            + "; rerun without --max-items for the full slice",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
