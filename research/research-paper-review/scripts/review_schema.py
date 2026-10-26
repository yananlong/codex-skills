"""One review-issue schema and one review-summary schema for the research review skills.

research-paper-review, research-review-loop, and research-rebuttal read issues written by each
other and by older tools in several layouts. This module reads every known layout, maps aliased
field names onto one canonical issue and one canonical summary, keeps every unmapped field under
`extra`, and records which layout and which aliases it used. It never writes files.

The canonical copy lives in research-paper-review/scripts/. Byte-identical copies ship with
research-review-loop and research-rebuttal; scripts/tests/test_shared_modules.py fails when a copy
drifts. references/review-schema.md in research-paper-review holds the conversion table.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SEVERITIES = ("major", "moderate", "minor")
ISSUE_STATUSES = ("open", "resolved", "accepted")
STATE_STATUSES = ("open", "in_progress", "closed")

# Canonical issue fields, in write order. These are the review-loop issue object's names, so a
# state written by init_review_loop.py is already canonical. An issue may also carry `extra`, an
# object holding source fields the schema does not name, preserved verbatim.
ISSUE_FIELDS = (
    "id", "title", "severity", "impact_rating", "confidence_rating", "status", "evidence",
    "required_action", "source_quote", "source_section", "related_sections", "origin",
    "resolution", "comment_type", "prior_issue_ids",
)
ISSUE_ALIASES: dict[str, tuple[str, ...]] = {
    "id": ("id", "issue_id"),
    "title": ("title", "issue", "risk", "name"),
    "severity": ("severity", "priority"),
    "impact_rating": ("impact_rating", "impact", "impact_score"),
    "confidence_rating": ("confidence_rating", "confidence", "confidence_score"),
    "status": ("status", "state"),
    "evidence": ("evidence", "explanation", "rationale", "problem"),
    "required_action": ("required_action", "required_fix", "fix", "recommendation", "suggested_fix"),
    "source_quote": ("source_quote", "quote"),
    "source_section": ("source_section", "section", "location", "lines"),
    "related_sections": ("related_sections",),
    "origin": ("origin", "source"),
    "resolution": ("resolution", "closure", "acceptance_rationale"),
    "comment_type": ("comment_type", "category", "kind"),
    "prior_issue_ids": ("prior_issue_ids", "predecessor_id", "supersedes", "internal_issue_ids"),
}
SEVERITY_ALIASES = {
    "critical": "major", "blocker": "major", "blocking": "major", "high": "major", "major": "major",
    "medium": "moderate", "moderate": "moderate", "mid": "moderate",
    "low": "minor", "minor": "minor", "nit": "minor", "trivial": "minor",
    # rebuttal issue-board severities
    "major-blocking": "major", "major-addressable": "major", "misunderstanding": "minor",
}
STATUS_ALIASES = {
    "open": "open", "active": "open", "new": "open", "in_progress": "open", "in-progress": "open",
    "partially_resolved": "open", "partial": "open", "deferred": "open", "carried": "open", "reopened": "open",
    "resolved": "resolved", "closed": "resolved", "fixed": "resolved", "done": "resolved",
    "addressed": "resolved", "reframed": "resolved", "superseded": "resolved",
    "accepted": "accepted", "accepted_risk": "accepted", "accepted-risk": "accepted", "wontfix": "accepted",
}

SUMMARY_REQUIRED = ("overall_paper_rating", "decision_relevance_rating", "rating_confidence", "top_blockers")
SUMMARY_RATINGS = ("overall_paper_rating", "decision_relevance_rating", "rating_confidence")
SUMMARY_ALIASES: dict[str, tuple[str, ...]] = {
    "overall_paper_rating": ("overall_paper_rating", "overall_score_1_to_5", "overall_rating"),
    "decision_relevance_rating": ("decision_relevance_rating", "decision_relevance"),
    "rating_confidence": ("rating_confidence", "confidence_score_1_to_5", "overall_confidence"),
    "top_blockers": ("top_blockers", "top_open_issue_ids", "blockers"),
    "novelty_decision_rating": ("novelty_decision_rating", "novelty_score_1_to_5"),
    "issue_counts": ("issue_counts", "open_issue_counts_by_severity"),
}

# Keys of a review state that hold lists of issues, and the status each list implies.
STATE_ISSUE_LISTS = {
    "open_issues": "open",
    "resolved_issues": "resolved",
    "accepted_risks": "accepted",
}
EXTRA_LIST_STATUS = (
    (re.compile(r"resolved|closed|reframed"), "resolved"),
    (re.compile(r"accepted"), "accepted"),
)

LAYOUTS = {
    "paper_review_native": "final_issues.json array with 1-5 impact and confidence ratings",
    "openaireview_claude": "final_issues.json array with severity tiers and no ratings",
    "issue_list_aliased": "issue array that needed field aliases (impact, confidence, location, ...)",
    "review_loop_state": "REVIEW_STATE.json with open_issues, resolved_issues, accepted_risks",
    "review_loop_state_extended": "REVIEW_STATE.json whose issues also or only live in other *_issues lists",
    "review_state_without_issues": "REVIEW_STATE.json that records a verdict but no issue lists",
    "rebuttal_issue_board": "rebuttal issue-board.md table",
}


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def rating(value: Any) -> int | None:
    """A 1-5 integer rating, or None. Accepts integral floats and digit strings."""
    if isinstance(value, bool):
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value.strip())
    if isinstance(value, int) and 1 <= value <= 5:
        return value
    return None


def severity_from_impact(impact: int | None) -> str | None:
    if impact is None:
        return None
    if impact >= 4:
        return "major"
    if impact <= 2:
        return "minor"
    return "moderate"


def normalise_severity(value: Any) -> str | None:
    if isinstance(value, str):
        return SEVERITY_ALIASES.get(value.strip().lower())
    return None


def normalise_status(value: Any) -> str | None:
    if isinstance(value, str):
        key = value.strip().lower().replace(" ", "_")
        if key in STATUS_ALIASES:
            return STATUS_ALIASES[key]
        if key.startswith("resolved") or key.startswith("closed"):
            return "resolved"
        if key.startswith("accepted"):
            return "accepted"
        if key.startswith("open") or key.startswith("partially"):
            return "open"
    return None


def normalise_issue(raw: Any, *, implied_status: str | None = None, list_key: str | None = None) -> dict[str, Any]:
    """Map one issue in any known layout onto the canonical issue.

    Returns the canonical issue plus `_aliases` (canonical name -> source key used, only where the
    source key differs) and `_problems` (what could not be derived). Neither underscore key is part
    of the canonical schema; writers drop them.
    """
    if not isinstance(raw, dict):
        return {"_problems": ["issue is not an object"], "_aliases": {}, "extra": {"value": raw}}
    issue: dict[str, Any] = {}
    aliases: dict[str, str] = {}
    used: set[str] = set()
    for field, keys in ISSUE_ALIASES.items():
        for key in keys:
            if key in raw and _present(raw[key]):
                issue[field] = raw[key]
                used.add(key)
                if key != field:
                    aliases[field] = key
                break
    problems: list[str] = []
    issue["impact_rating"] = rating(issue.get("impact_rating"))
    issue["confidence_rating"] = rating(issue.get("confidence_rating"))
    severity = normalise_severity(issue.get("severity"))
    if severity is None:
        severity = severity_from_impact(issue["impact_rating"])
        if severity is not None:
            aliases["severity"] = "impact_rating"
    issue["severity"] = severity
    status = normalise_status(issue.get("status"))
    if status is None:
        status = implied_status or "open"
    elif implied_status and status != implied_status and list_key:
        problems.append(f"status '{issue.get('status')}' disagrees with list {list_key}")
    issue["status"] = status
    prior = issue.get("prior_issue_ids")
    if isinstance(prior, str):
        issue["prior_issue_ids"] = [part.strip() for part in re.split(r"[,;]", prior) if part.strip()]
    if not _present(issue.get("title")):
        problems.append("no title (title, issue, risk, or name)")
    if issue["severity"] is None:
        problems.append("no severity (severity, or a 1-5 impact rating)")
    canonical = {field: issue.get(field) for field in ISSUE_FIELDS if field in issue}
    extra: dict[str, Any] = {}
    if isinstance(raw.get("extra"), dict):
        extra.update(raw["extra"])
        used.add("extra")
    extra.update({key: value for key, value in raw.items() if key not in used})
    if extra:
        canonical["extra"] = extra
    if list_key and list_key not in STATE_ISSUE_LISTS:
        canonical.setdefault("extra", {})["source_list"] = list_key
    canonical["_aliases"] = aliases
    canonical["_problems"] = problems
    canonical["_notes"] = []
    canonical["_list"] = list_key
    return canonical


def _settle_references(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Closed entries often carry only an id, a status, and a resolution, pointing at an earlier issue.

    Fill a missing title or severity from another entry with the same id. A closed entry that still
    lacks them is a reference, recorded in `_notes`; only open issues report them as problems.
    """
    by_id: dict[str, dict[str, Any]] = {}
    for issue in issues:
        key = issue.get("id")
        if key is not None and _present(issue.get("title")) and issue.get("severity"):
            by_id.setdefault(str(key), issue)
    for issue in issues:
        source = by_id.get(str(issue.get("id"))) if issue.get("id") is not None else None
        for field in ("title", "severity"):
            if not _present(issue.get(field)) and source is not None and source is not issue:
                issue[field] = source[field]
                issue["_aliases"][field] = f"same id {issue['id']}"
        problems = []
        for problem in issue["_problems"]:
            missing_title = problem.startswith("no title") and _present(issue.get("title"))
            missing_severity = problem.startswith("no severity") and issue.get("severity")
            if missing_title or missing_severity:
                continue
            if problem.startswith("no ") and issue.get("status") in ("resolved", "accepted"):
                issue["_notes"].append(f"closed reference: {problem}")
                continue
            problems.append(problem)
        issue["_problems"] = problems
    return issues


def strip_private(issue: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in issue.items() if not key.startswith("_")}


def _issue_list_layout(items: list[Any]) -> str:
    dicts = [item for item in items if isinstance(item, dict)]
    keys = set().union(*(set(item) for item in dicts)) if dicts else set()
    if {"impact_rating", "confidence_rating"} & keys and {"title", "quote", "explanation"} <= keys:
        return "paper_review_native"
    if "severity" in keys and {"title", "quote", "explanation"} <= keys and not {"impact_rating", "confidence_rating"} & keys:
        return "openaireview_claude"
    return "issue_list_aliased"


def _state_issue_lists(state: dict[str, Any]) -> list[tuple[str, str | None, list[Any]]]:
    lists: list[tuple[str, str | None, list[Any]]] = []
    for key, value in state.items():
        if not isinstance(value, list) or not value or not any(isinstance(item, dict) for item in value):
            continue
        if key in STATE_ISSUE_LISTS:
            lists.append((key, STATE_ISSUE_LISTS[key], value))
        elif key in ("issues", "tracked_issues") or key.endswith("_issues") or key in ("deferred_issues",):
            implied = None
            for pattern, status in EXTRA_LIST_STATUS:
                if pattern.search(key):
                    implied = status
            lists.append((key, implied, value))
    return lists


def issues_from_state(state: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    lists = _state_issue_lists(state)
    issues: list[dict[str, Any]] = []
    for key, implied, items in lists:
        for item in items:
            if isinstance(item, dict):
                issues.append(normalise_issue(item, implied_status=implied, list_key=key))
    issues = _settle_references(issues)
    if not lists:
        return "review_state_without_issues", issues
    standard_only = all(key in STATE_ISSUE_LISTS for key, _, _ in lists)
    return ("review_loop_state" if standard_only else "review_loop_state_extended"), issues


BOARD_COLUMNS = {
    "issue id": "id", "reviewer": "reviewer", "internal issue ids": "prior_issue_ids",
    "severity": "severity", "category": "comment_type", "strategy": "required_action",
    "stance": "stance", "status": "status", "shared with": "shared_with",
    "evidence source": "evidence", "notes": "title",
}


def issues_from_board(markdown: str) -> list[dict[str, Any]]:
    """Read a rebuttal issue-board table. The Notes column is the issue's title."""
    header: list[str] | None = None
    issues: list[dict[str, Any]] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            header = None if not stripped else header
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if header is None:
            header = [cell.lower() for cell in cells]
            continue
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        row = dict(zip(header, cells))
        issue_id = row.get("issue id", "")
        others = [value for column, value in row.items() if column != "issue id"]
        if not any(others) or re.search(r"<[^>]+>", issue_id):
            continue  # an empty or template placeholder row
        raw: dict[str, Any] = {}
        for column, value in row.items():
            target = BOARD_COLUMNS.get(column, column.replace(" ", "_"))
            if value:
                raw[target] = value
        if "title" not in raw and "comment_type" in raw:
            raw["title"] = raw["comment_type"]
        if "reviewer" in raw:
            raw["origin"] = f"reviewer {raw.pop('reviewer')}"
        issues.append(normalise_issue(raw))
    return _settle_references(issues)


def load_issues(path: Path) -> tuple[str, list[dict[str, Any]], dict[str, Any] | None]:
    """Read issues from a file or review directory in any known layout.

    Returns (layout, canonical issues with _aliases and _problems, the raw state or None).
    A directory resolves to final_issues.json, then REVIEW_STATE.json, then issue-board.md.
    """
    path = Path(path).expanduser()
    if path.is_dir():
        for name in ("final_issues.json", "REVIEW_STATE.json", "issue-board.md"):
            if (path / name).is_file():
                path = path / name
                break
        else:
            raise FileNotFoundError(f"no final_issues.json, REVIEW_STATE.json, or issue-board.md in {path}")
    if path.suffix == ".md":
        return "rebuttal_issue_board", issues_from_board(path.read_text(encoding="utf-8")), None
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return _issue_list_layout(data), _settle_references([normalise_issue(item) for item in data]), None
    if isinstance(data, dict):
        layout, issues = issues_from_state(data)
        return layout, issues, data
    raise ValueError(f"{path} holds neither an issue array nor a review state object")


def normalise_summary(raw: Any) -> tuple[dict[str, Any], dict[str, str], list[str]]:
    """Map a review summary onto the canonical summary.

    Returns (summary, aliases used, problems). Unmapped keys are kept under `extra`.
    """
    if not isinstance(raw, dict):
        return {}, {}, ["summary is not a JSON object"]
    summary: dict[str, Any] = {}
    aliases: dict[str, str] = {}
    used: set[str] = set()
    for field, keys in SUMMARY_ALIASES.items():
        for key in keys:
            if key in raw:
                summary[field] = raw[key]
                used.add(key)
                if key != field:
                    aliases[field] = key
                break
    for key, value in raw.items():
        if key not in used and key not in summary:
            summary[key] = value
            used.add(key)
    problems: list[str] = []
    missing = [field for field in SUMMARY_REQUIRED if field not in summary]
    if missing:
        problems.append("missing required keys: " + ", ".join(missing))
    for field in SUMMARY_RATINGS:
        value = summary.get(field)
        if field in summary and (isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5):
            problems.append(f"{field} must be an integer in [1, 5]")
    if "top_blockers" in summary and not isinstance(summary["top_blockers"], list):
        problems.append("top_blockers must be a list")
    return summary, aliases, problems
