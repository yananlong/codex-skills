#!/usr/bin/env python3
"""Show, diff, and check rows of the shared venue table (references/venues.json).

research-paper-plan and research-rebuttal ship byte-identical copies of this script and of
venues.json; the repository test scripts/tests/test_shared_modules.py fails when a copy drifts.
Edit the copies in research-paper-plan and copy them over.

Subcommands:
  list                     one line per venue with its family, response limit, and freshness
  show VENUE               every field of one row
  diff FROM TO             fields that differ between two rows, for porting a paper or response
  limit VENUE              the numeric response limit as "<unit> <value> <scope>" (exit 3 when none)
  check                    validate the table; list stale (older than stale_after_days) and unverified rows

A row whose verified_on is older than stale_after_days, or whose status is not verified, is flagged
on every command that prints it, so a decision never rests on an unmarked old fact.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_TABLE = Path(__file__).resolve().parents[1] / "references" / "venues.json"
FIELDS = (
    "venue", "family", "rebuttal_mode", "response_format", "response_limit", "page_limits",
    "revision_during_response", "anonymity", "external_links", "mandatory_sections",
    "supplementary_rules", "revision_mechanics", "key_constraints", "sources", "verified_on", "status",
)
FAMILIES = {
    "one_shot_pdf", "threaded_discussion", "per_review", "rolling_review", "single_feedback",
    "no_rebuttal_found", "unresolved", "platform_default",
}
STATUSES = {"verified", "inferred", "unverified"}
LIMIT_UNITS = {"chars", "words", "pages"}
LIMIT_SCOPES = {"whole", "per_review", "per_round"}


def load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"venue table not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"venue table is not valid JSON: {exc}")
    if not isinstance(data, dict) or not isinstance(data.get("venues"), list):
        raise SystemExit("venue table must be an object with a venues list")
    return data


def find(data: dict[str, Any], key: str) -> dict[str, Any]:
    wanted = key.strip().lower()
    for row in data["venues"]:
        if wanted in {str(row.get("venue_id", "")).lower(), str(row.get("venue", "")).lower()}:
            return row
    known = ", ".join(str(row.get("venue_id")) for row in data["venues"])
    raise SystemExit(f"unknown venue '{key}'. Known venue_id values: {known}")


def freshness(row: dict[str, Any], data: dict[str, Any], today: dt.date) -> list[str]:
    flags: list[str] = []
    try:
        checked = dt.date.fromisoformat(str(row.get("verified_on")))
    except ValueError:
        return [f"verified_on '{row.get('verified_on')}' is not a date"]
    age = (today - checked).days
    limit = int(data.get("stale_after_days", 365))
    if age > limit:
        flags.append(f"STALE: verified {age} days ago (more than {limit}); re-check the sources before relying on it")
    if row.get("status") != "verified":
        flags.append(f"{str(row.get('status')).upper()}: re-check the sources before relying on this row")
    return flags


def describe_limit(limit: Any) -> str:
    if not isinstance(limit, dict):
        return "none stated"
    return f"{limit.get('value')} {limit.get('unit')} ({limit.get('scope')})"


def render(value: Any) -> str:
    if value is None:
        return "not stated"
    if isinstance(value, list):
        return "; ".join(map(str, value)) if value else "none"
    if isinstance(value, dict):
        return ", ".join(f"{key}={val}" for key, val in value.items())
    return str(value)


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(data["venues"], 1):
        label = f"venues[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label} must be an object")
            continue
        venue_id = row.get("venue_id")
        if not isinstance(venue_id, str) or not venue_id:
            errors.append(f"{label}.venue_id must be a non-empty string")
        elif venue_id in seen:
            errors.append(f"duplicate venue_id {venue_id}")
        seen.add(str(venue_id))
        missing = [field for field in FIELDS if field not in row]
        if missing:
            errors.append(f"{label} ({venue_id}) lacks fields: {', '.join(missing)}")
        if row.get("family") not in FAMILIES:
            errors.append(f"{label}.family must be one of {sorted(FAMILIES)}")
        if row.get("status") not in STATUSES:
            errors.append(f"{label}.status must be one of {sorted(STATUSES)}")
        try:
            dt.date.fromisoformat(str(row.get("verified_on")))
        except ValueError:
            errors.append(f"{label}.verified_on must be an ISO date")
        sources = row.get("sources")
        if not isinstance(sources, list) or not sources or not all(
            isinstance(url, str) and url.startswith(("http://", "https://")) for url in sources
        ):
            errors.append(f"{label}.sources must list at least one source URL")
        limit = row.get("response_limit")
        if limit is not None and (
            not isinstance(limit, dict)
            or limit.get("unit") not in LIMIT_UNITS
            or not isinstance(limit.get("value"), int)
            or limit.get("scope") not in LIMIT_SCOPES
        ):
            errors.append(f"{label}.response_limit must be null or {{unit, value, scope}}")
    return errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--today", help="ISO date used for staleness (default: today)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    show = sub.add_parser("show")
    show.add_argument("venue")
    diff = sub.add_parser("diff")
    diff.add_argument("source")
    diff.add_argument("target")
    limit = sub.add_parser("limit")
    limit.add_argument("venue")
    sub.add_parser("check")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data = load(args.table)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()

    if args.command == "check":
        errors = validate(data)
        flagged = [(row.get("venue_id"), freshness(row, data, today)) for row in data["venues"] if isinstance(row, dict)]
        for venue_id, flags in flagged:
            for flag in flags:
                print(f"{venue_id}: {flag}")
        if errors:
            print("Venue table invalid:")
            for error in errors:
                print(f"- {error}")
            return 1
        print(f"Venue table valid: {len(data['venues'])} rows, {sum(1 for _, flags in flagged if flags)} flagged.")
        return 0

    if args.command == "list":
        for row in data["venues"]:
            flags = freshness(row, data, today)
            marker = "  [" + "; ".join(flag.split(":")[0] for flag in flags) + "]" if flags else ""
            print(f"{row['venue_id']}: {row['family']}, limit {describe_limit(row.get('response_limit'))}, verified {row['verified_on']}{marker}")
        return 0

    if args.command == "show":
        row = find(data, args.venue)
        print(f"{row['venue_id']}")
        for field in FIELDS:
            print(f"  {field}: {render(row.get(field))}")
        for flag in freshness(row, data, today):
            print(f"  {flag}")
        return 0

    if args.command == "diff":
        source, target = find(data, args.source), find(data, args.target)
        print(f"Porting {source['venue_id']} -> {target['venue_id']}")
        changed = 0
        for field in FIELDS:
            if field in {"venue", "sources", "verified_on", "status"}:
                continue
            if source.get(field) != target.get(field):
                changed += 1
                print(f"  {field}:\n    from: {render(source.get(field))}\n    to:   {render(target.get(field))}")
        if not changed:
            print("  no differences in the recorded fields")
        for row in (source, target):
            for flag in freshness(row, data, today):
                print(f"  {row['venue_id']} {flag}")
        return 0

    if args.command == "limit":
        row = find(data, args.venue)
        for flag in freshness(row, data, today):
            print(f"{row['venue_id']} {flag}", file=sys.stderr)
        limit = row.get("response_limit")
        if not isinstance(limit, dict):
            print(f"{row['venue_id']} records no numeric response limit", file=sys.stderr)
            return 3
        print(f"{limit['unit']} {limit['value']} {limit['scope']}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
