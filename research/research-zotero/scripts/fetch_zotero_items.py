#!/usr/bin/env python3
"""Fetch Zotero library items via the Zotero Web API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _zotero import default_user_library, fetch_paginated_items, resolve_api_key


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=False)
    scope.add_argument("--user-id", help="Zotero user library ID")
    scope.add_argument("--group-id", help="Zotero group library ID")
    parser.add_argument("--collection-key", help="Restrict results to a Zotero collection key")
    parser.add_argument("--tag", action="append", default=[], help="Tag filter (repeatable)")
    parser.add_argument("--query", help="Free-text Zotero query")
    parser.add_argument("--item-type", help="Restrict by Zotero item type")
    parser.add_argument("--limit", type=int, default=100, help="Items per request (default: 100)")
    parser.add_argument("--all", action="store_true", help="Paginate until exhausted")
    parser.add_argument("--api-key", help="Zotero API key; defaults to $ZOTERO_API_KEY")
    parser.add_argument("--out", type=Path, required=True, help="Output JSON path")
    parser.add_argument("--sync-note", type=Path, help="Optional Markdown sync note path")
    return parser


def resolve_library(args: argparse.Namespace, api_key: str):
    if args.user_id:
        return "user", args.user_id, "explicit-user"
    if args.group_id:
        return "group", args.group_id, "explicit-group"
    library_type, library_id, _key_info = default_user_library(api_key)
    return library_type, library_id, "api-key-default"


def write_sync_note(path: Path, *, library_type: str, library_id: str, collection_key: str | None, query: str | None, tags: list[str], item_type: str | None, item_count: int, resolved_via: str) -> None:
    text = f"""# Zotero Sync

- Library type: {library_type}
- Library ID: {library_id}
- Resolved via: {resolved_via}
- Collection key: {collection_key or ""}
- Query: {query or ""}
- Tags: {", ".join(tags)}
- Item type: {item_type or ""}
- Items retrieved: {item_count}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    api_key = resolve_api_key(args.api_key)
    library_type, library_id, resolved_via = resolve_library(args, api_key)

    items = fetch_paginated_items(
        api_key=api_key,
        library_type=library_type,
        library_id=library_id,
        collection_key=args.collection_key,
        tag_filters=args.tag,
        query=args.query,
        item_type=args.item_type,
        limit=args.limit,
        all_pages=args.all,
    )

    payload = {
        "library_type": library_type,
        "library_id": library_id,
        "resolved_via": resolved_via,
        "collection_key": args.collection_key,
        "query": args.query,
        "tags": args.tag,
        "item_type": args.item_type,
        "item_count": len(items),
        "items": items,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {args.out} ({len(items)} items)")

    if args.sync_note:
        write_sync_note(
            args.sync_note,
            library_type=library_type,
            library_id=library_id,
            collection_key=args.collection_key,
            query=args.query,
            tags=args.tag,
            item_type=args.item_type,
            item_count=len(items),
            resolved_via=resolved_via,
        )
        print(f"wrote {args.sync_note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
