"""Search-log columns a search tool can fill honestly, shared by the full pack and the paper context.

A web-search tool shows a ranked page of results, not the size of a database's hit set, so a
`records_returned` count is usually invented. The honest columns record what was actually done:
the `tool` used, how many results were looked at (`results_inspected`), and which of them were
opened and checked (`spot_checked`). Each row holds one query, so a reader can rerun it.
"""
from __future__ import annotations

import re

HONEST_COLUMNS = ("tool", "results_inspected", "spot_checked")
LEGACY_COUNT_COLUMN = "records_returned"
_SPLIT = re.compile(r";|<br\s*/?>|\n", re.I)
_PLACEHOLDERS = {"", "todo", "tbd", "-", "n/a"}


def is_legacy(header: list[str]) -> bool:
    """A log written before the honest columns existed."""
    return not set(HONEST_COLUMNS) <= set(header)


def legacy_warning(label: str) -> str:
    return (
        f"{label} uses the older columns; add tool, results_inspected, and spot_checked "
        f"(which results were opened and checked) and drop {LEGACY_COUNT_COLUMN}, which a web-search "
        "tool cannot report"
    )


def query_count(cell: str) -> int:
    """Count the queries written in one cell; boolean operators inside one query count once."""
    return len([part for part in _SPLIT.split(cell or "") if part.strip()])


def check_row(row: dict[str, str], query_field: str, label: str, errors: list[str]) -> None:
    """Errors for one row of an honest-column log."""
    if query_count(row.get(query_field, "")) > 1:
        errors.append(f"{label}.{query_field} holds more than one query; write one query per row")
    tool = row.get("tool", "").strip()
    if tool.lower() in _PLACEHOLDERS or "todo" in tool.lower():
        errors.append(f"{label}.tool must name the search tool or database used")
    inspected = row.get("results_inspected", "").strip()
    if not re.fullmatch(r"\d+", inspected):
        errors.append(f"{label}.results_inspected must be the number of results looked at (an integer)")
    spot = row.get("spot_checked", "").strip()
    if spot.lower() in _PLACEHOLDERS or "todo" in spot.lower():
        errors.append(
            f"{label}.spot_checked must list the results opened and checked, or say none"
        )
