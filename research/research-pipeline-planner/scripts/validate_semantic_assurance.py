#!/usr/bin/env python3
"""Validate PR15 semantic assurance across commitment, literature, and evidence authorities."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from semantic_assurance import (
    load_json, load_text, print_result, validate_commitment_transitions,
    validate_evidence_semantics, validate_fixture_index, validate_literature_semantics,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    transitions = subparsers.add_parser("transitions")
    transitions.add_argument("--history", type=Path, required=True)
    transitions.add_argument("--ledger", type=Path, required=True)
    transitions.add_argument("--work-items", type=Path)
    literature = subparsers.add_parser("literature")
    literature.add_argument("--manifest", type=Path, required=True)
    literature.add_argument("--novelty-decision", type=Path, required=True)
    literature.add_argument("--prior-art-matrix", type=Path, required=True)
    literature.add_argument("--novelty-search-log", type=Path, required=True)
    literature.add_argument("--challenge-evaluation", type=Path, required=True)
    evidence = subparsers.add_parser("evidence")
    evidence.add_argument("--results-audit", type=Path, required=True)
    evidence.add_argument("--paper-bindings", type=Path, required=True)
    evidence.add_argument("--work-items", type=Path, required=True)
    fixtures = subparsers.add_parser("fixtures")
    fixtures.add_argument("--fixture-index", type=Path, required=True)
    route = subparsers.add_parser("route")
    for action in (
        ("--history", Path), ("--ledger", Path), ("--manifest", Path),
        ("--novelty-decision", Path), ("--prior-art-matrix", Path),
        ("--novelty-search-log", Path), ("--challenge-evaluation", Path),
        ("--results-audit", Path), ("--paper-bindings", Path),
        ("--work-items", Path), ("--fixture-index", Path),
    ):
        route.add_argument(action[0], type=action[1], required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    if args.command in {"transitions", "route"}:
        history = load_json(args.history, "commitment history", errors)
        ledger = load_json(args.ledger, "commitment transition ledger", errors)
        work_items = load_json(args.work_items, "work-items", errors) if getattr(args, "work_items", None) else None
        if history is not None and ledger is not None:
            errors.extend(validate_commitment_transitions(history, ledger, work_items))
    if args.command in {"literature", "route"}:
        manifest = load_json(args.manifest, "literature manifest", errors)
        novelty = load_json(args.novelty_decision, "novelty decision", errors)
        prior_art = load_text(args.prior_art_matrix, "prior-art matrix", errors)
        novelty_search = load_text(args.novelty_search_log, "novelty search log", errors)
        challenge = load_json(args.challenge_evaluation, "challenge evaluation", errors)
        if manifest is not None and novelty is not None and challenge is not None:
            errors.extend(validate_literature_semantics(manifest, novelty, prior_art, novelty_search, challenge))
    if args.command in {"evidence", "route"}:
        audit = load_json(args.results_audit, "results audit", errors)
        paper = load_json(args.paper_bindings, "paper bindings", errors)
        work_items = load_json(args.work_items, "work-items", errors)
        if audit is not None and paper is not None and work_items is not None:
            errors.extend(validate_evidence_semantics(audit, paper, work_items))
    if args.command in {"fixtures", "route"}:
        fixtures = load_json(args.fixture_index, "fixture index", errors)
        if fixtures is not None:
            errors.extend(validate_fixture_index(fixtures))
    return print_result(errors, "Validation passed: PR15 semantic controls and locked regressions are internally consistent. This does not establish prospective scientific effectiveness.")


if __name__ == "__main__":
    sys.exit(main())
