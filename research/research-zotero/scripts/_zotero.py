#!/usr/bin/env python3
"""Shared Zotero Web API helpers."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request


API_ROOT = "https://api.zotero.org"


def resolve_api_key(explicit_api_key: str | None) -> str:
    api_key = explicit_api_key or os.environ.get("ZOTERO_API_KEY")
    if not api_key:
        raise SystemExit("Missing Zotero API key. Pass --api-key or set $ZOTERO_API_KEY.")
    return api_key


def _request(url: str, api_key: str, accept: str = "application/json"):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "Zotero-API-Version": "3",
            "Zotero-API-Key": api_key,
        },
    )
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8")


def api_get_json(path: str, api_key: str, params: dict[str, str] | None = None):
    query = ""
    if params:
        query = "?" + urllib.parse.urlencode(params, doseq=True)
    payload = _request(API_ROOT + path + query, api_key)
    return json.loads(payload)


def api_get_text(path: str, api_key: str, params: dict[str, str] | None = None, accept: str = "*/*") -> str:
    query = ""
    if params:
        query = "?" + urllib.parse.urlencode(params, doseq=True)
    return _request(API_ROOT + path + query, api_key, accept=accept)


def resolve_current_key(api_key: str):
    return api_get_json("/keys/current", api_key)


def default_user_library(api_key: str) -> tuple[str, str, dict]:
    key_info = resolve_current_key(api_key)
    user_id = key_info.get("userID")
    if user_id in (None, ""):
        raise SystemExit("Could not resolve a default user library from the current API key.")
    return "user", str(user_id), key_info


def list_groups(user_id: str, api_key: str):
    return api_get_json(f"/users/{user_id}/groups", api_key)


def library_prefix(library_type: str, library_id: str) -> str:
    if library_type == "user":
        return f"/users/{library_id}"
    if library_type == "group":
        return f"/groups/{library_id}"
    raise ValueError(f"Unsupported library_type: {library_type}")


def build_items_path(library_type: str, library_id: str, collection_key: str | None = None) -> str:
    prefix = library_prefix(library_type, library_id)
    if collection_key:
        return f"{prefix}/collections/{collection_key}/items"
    return f"{prefix}/items"


def fetch_paginated_items(
    *,
    api_key: str,
    library_type: str,
    library_id: str,
    collection_key: str | None,
    tag_filters: list[str],
    query: str | None,
    item_type: str | None,
    limit: int,
    all_pages: bool,
):
    params: dict[str, str | list[str]] = {
        "format": "json",
        "limit": str(limit),
    }
    if query:
        params["q"] = query
    if item_type:
        params["itemType"] = item_type
    if tag_filters:
        params["tag"] = tag_filters

    path = build_items_path(library_type, library_id, collection_key=collection_key)
    start = 0
    items = []
    while True:
        page_params = dict(params)
        page_params["start"] = str(start)
        page = api_get_json(path, api_key, page_params)
        if not isinstance(page, list):
            raise SystemExit("Unexpected Zotero response: expected a JSON list of items.")
        items.extend(page)
        if not all_pages or len(page) < limit:
            break
        start += limit
    return items
