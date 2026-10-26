#!/usr/bin/env python3
"""Shared Zotero Web API helpers."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


# ZOTERO_API_ROOT exists for offline tests against a local mock server.
API_ROOT = os.environ.get("ZOTERO_API_ROOT", "https://api.zotero.org").rstrip("/")
MAX_RETRIES = 3
MAX_WAIT_SECONDS = 60.0


def resolve_api_key(explicit_api_key: str | None) -> str:
    api_key = explicit_api_key or os.environ.get("ZOTERO_API_KEY")
    if not api_key:
        raise SystemExit("Missing Zotero API key. Pass --api-key or set $ZOTERO_API_KEY.")
    return api_key


def _wait_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return min(max(float(value), 0.0), MAX_WAIT_SECONDS)
    except ValueError:
        return None


def _http_error_message(code: int, path: str) -> str:
    if code == 403:
        return (
            f"Zotero API returned 403 Forbidden for {path}: the API key is invalid or lacks read access to this "
            "library. Check the key's permissions at https://www.zotero.org/settings/keys."
        )
    if code == 404:
        return f"Zotero API returned 404 Not Found for {path}: check the user/group ID and collection key."
    if code == 429:
        return f"Zotero API returned 429 Too Many Requests for {path} after {MAX_RETRIES} retries; try again later."
    return f"Zotero API request failed for {path}: HTTP {code}."


def _request_with_headers(url: str, api_key: str, accept: str = "application/json") -> tuple[str, dict[str, str]]:
    """GET a Zotero URL, honouring Backoff/Retry-After, and exit with a clear message on HTTP errors."""
    path = urllib.parse.urlsplit(url).path
    request = urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "Zotero-API-Version": "3",
            "Zotero-API-Key": api_key,
        },
    )
    for attempt in range(MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request) as response:
                body = response.read().decode("utf-8")
                headers = {key.lower(): value for key, value in response.headers.items()}
        except urllib.error.HTTPError as exc:
            wait = _wait_seconds(exc.headers.get("Retry-After") if exc.headers else None)
            if exc.code in (429, 503) and attempt < MAX_RETRIES:
                delay = wait if wait is not None else float(2**attempt)
                print(f"Zotero API returned {exc.code}; retrying in {delay:g}s", file=sys.stderr)
                time.sleep(delay)
                continue
            raise SystemExit(_http_error_message(exc.code, path)) from None
        except urllib.error.URLError as exc:
            raise SystemExit(f"Could not reach the Zotero API for {path}: {exc.reason}") from None
        backoff = _wait_seconds(headers.get("backoff"))
        if backoff:
            time.sleep(backoff)
        return body, headers
    raise SystemExit(_http_error_message(429, path))


def _request(url: str, api_key: str, accept: str = "application/json"):
    return _request_with_headers(url, api_key, accept=accept)[0]


def _url(path: str, params: dict | None) -> str:
    query = ""
    if params:
        query = "?" + urllib.parse.urlencode(params, doseq=True)
    return API_ROOT + path + query


def total_results(headers: dict[str, str]) -> int | None:
    value = headers.get("total-results")
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def api_get_json(path: str, api_key: str, params: dict[str, str] | None = None):
    return json.loads(_request(_url(path, params), api_key))


def api_get_json_with_headers(path: str, api_key: str, params: dict | None = None):
    body, headers = _request_with_headers(_url(path, params), api_key)
    return json.loads(body), headers


def api_get_text(path: str, api_key: str, params: dict[str, str] | None = None, accept: str = "*/*") -> str:
    return _request(_url(path, params), api_key, accept=accept)


def api_get_text_with_headers(path: str, api_key: str, params: dict | None = None, accept: str = "*/*"):
    return _request_with_headers(_url(path, params), api_key, accept=accept)


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


def fetch_items_with_total(
    *,
    api_key: str,
    library_type: str,
    library_id: str,
    collection_key: str | None,
    tag_filters: list[str],
    query: str | None,
    item_type: str | None,
    limit: int,
    max_items: int | None = None,
) -> tuple[list, int | None, bool]:
    """Page through items until exhausted or max_items is reached.

    Returns (items, total_results, partial). total_results comes from the Total-Results header
    (None when absent). partial is True when fewer items than the library slice holds were written.
    """
    params: dict[str, str | list[str]] = {"format": "json"}
    if query:
        params["q"] = query
    if item_type:
        params["itemType"] = item_type
    if tag_filters:
        params["tag"] = tag_filters

    path = build_items_path(library_type, library_id, collection_key=collection_key)
    start = 0
    items: list = []
    total: int | None = None
    exhausted = False
    while True:
        page_limit = limit if max_items is None else min(limit, max_items - len(items))
        if page_limit <= 0:
            break
        page_params = dict(params)
        page_params["limit"] = str(page_limit)
        page_params["start"] = str(start)
        page, headers = api_get_json_with_headers(path, api_key, page_params)
        if not isinstance(page, list):
            raise SystemExit("Unexpected Zotero response: expected a JSON list of items.")
        header_total = total_results(headers)
        if header_total is not None:
            total = header_total
        items.extend(page)
        start += len(page)
        if not page:
            exhausted = True
            break
        if total is not None:
            # Zotero caps a page at 100 whatever --limit asks, so a short page is not the end
            # while Total-Results says more remain.
            if start >= total:
                exhausted = True
                break
            continue
        if len(page) < page_limit:
            exhausted = True
            break
    if total is not None:
        partial = len(items) < total
    else:
        partial = not exhausted
    return items, total, partial


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
    items, _total, _partial = fetch_items_with_total(
        api_key=api_key,
        library_type=library_type,
        library_id=library_id,
        collection_key=collection_key,
        tag_filters=tag_filters,
        query=query,
        item_type=item_type,
        limit=limit,
        max_items=None if all_pages else limit,
    )
    return items
