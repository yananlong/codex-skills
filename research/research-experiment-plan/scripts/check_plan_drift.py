#!/usr/bin/env python3
"""Report drift between an experiment plan and the runs that actually happened.

Reads run-blocks.json and experiment-tracker.md (and optionally claim-map.json, a results audit,
and a results directory) and lists:

- runs that no declared block covers, separated into those whose Kind admits it (unplanned,
  precursor, diagnostic, retry) and those still marked planned;
- must-run blocks with no run that reached a run status (running, analyzed, decisive, inconclusive,
  or a free-text status starting with completed, executed, passed, failed, or done);
- runs whose kind contradicts the plan: a retry with no earlier run of its block, a diagnostic or
  precursor run carrying a decision gate, an audited run whose kind differs from the tracker's;
- with --audit, audited runs the tracker never lists;
- with --results-dir, result files no tracker row names, and with --root, named outputs of
  executed runs that do not exist.

It reports and exits 0. With --fail-on-drift it exits 1 when anything is listed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from validate_experiment_pack import (
    RUN_KINDS,
    table_rows,
    tracker_kind_column,
    tracker_run_kind,
    unwrap_envelope,
)

RAN_STATUSES = {"running", "analyzed", "decisive", "inconclusive"}
# Free-text statuses seen in real trackers whose first word says the run happened.
RAN_WORDS = {"completed", "complete", "executed", "passed", "failed", "done"}
UNSET = {"", "-", "n/a", "na", "none"}


def has_run(status: str) -> bool:
    words = status.strip().strip("`").lower().replace(";", " ").replace("/", " ").split()
    return status.strip() in RAN_STATUSES or bool(words and words[0] in RAN_WORDS)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read {path}: {exc}") from exc


def tracker_runs(markdown: str) -> list[dict[str, str]]:
    kind_column = tracker_kind_column(markdown)
    runs = []
    for row in table_rows(markdown, "# Experiment Tracker", "run id"):
        if len(row) < 6:
            continue
        runs.append({
            "run_id": row[0],
            "block_id": row[1],
            "gate_id": row[2],
            "status": row[5],
            "output": row[8] if len(row) > 8 else "",
            "kind": tracker_run_kind(row, kind_column),
        })
    return runs


def audit_runs(audit: Any) -> list[dict[str, str]]:
    runs = []
    for record in audit.get("audits", []) if isinstance(audit, dict) else []:
        if not isinstance(record, dict):
            continue
        for field in ("source_runs", "standalone_runs"):
            for run in record.get(field, []) or []:
                if isinstance(run, dict) and run.get("run_id"):
                    runs.append({
                        "audit_id": str(record.get("audit_id")),
                        "run_id": str(run["run_id"]),
                        "block_id": str(run.get("block_id") or ""),
                        "kind": str(run.get("run_kind") or "planned"),
                    })
    return runs


def check(args: argparse.Namespace) -> dict[str, list[str]]:
    blocks = unwrap_envelope(load_json(args.run_blocks), "run-blocks.json", [])
    if not isinstance(blocks, list):
        raise SystemExit("run-blocks.json must be a list of blocks or a {blocks: [...]} envelope")
    declared = {str(b.get("block_id")): b for b in blocks if isinstance(b, dict) and b.get("block_id")}
    if args.claim_map:
        claims = unwrap_envelope(load_json(args.claim_map), "claim-map.json", [])
        linked = {
            str(block)
            for claim in claims if isinstance(claim, dict)
            for block in claim.get("linked_blocks", []) or []
        } if isinstance(claims, list) else set()
    else:
        linked = set()
    gate_ids = {str(b.get("decision_gate_id")) for b in declared.values() if b.get("decision_gate_id")}
    runs = tracker_runs(args.tracker.read_text(encoding="utf-8"))

    report: dict[str, list[str]] = {
        "undeclared_runs_marked_planned": [],
        "undeclared_runs_by_kind": [],
        "must_run_blocks_never_run": [],
        "kind_contradictions": [],
        "invalid_kinds": [],
        "audited_runs_missing_from_tracker": [],
        "unreferenced_result_files": [],
        "missing_outputs_of_executed_runs": [],
    }
    seen_blocks: set[str] = set()
    for run in runs:
        rid, block, kind = run["run_id"], run["block_id"], run["kind"]
        if kind not in RUN_KINDS:
            report["invalid_kinds"].append(f"{rid}: kind '{kind}' is not one of {sorted(RUN_KINDS)}")
            continue
        if block not in declared:
            entry = f"{rid} (block '{block or '-'}', kind {kind}, status {run['status']})"
            key = "undeclared_runs_marked_planned" if kind == "planned" else "undeclared_runs_by_kind"
            report[key].append(entry)
        if kind == "retry" and block not in seen_blocks:
            report["kind_contradictions"].append(f"{rid}: retry with no earlier run of block '{block}' above it")
        if kind in {"diagnostic", "precursor"} and run["gate_id"] in gate_ids:
            report["kind_contradictions"].append(
                f"{rid}: {kind} run carries decision gate {run['gate_id']}; only planned runs decide gates"
            )
        seen_blocks.add(block)

    ran = {
        run["block_id"]
        for run in runs
        if has_run(run["status"]) and run["kind"] in {"planned", "retry", "unplanned"}
    }
    for block_id, block in declared.items():
        if block.get("priority") == "must-run" and block_id not in ran:
            note = " (linked to a claim)" if block_id in linked else ""
            report["must_run_blocks_never_run"].append(f"{block_id}{note}")

    if args.audit:
        tracked = {run["run_id"]: run for run in runs}
        for run in audit_runs(load_json(args.audit)):
            row = tracked.get(run["run_id"])
            if row is None:
                report["audited_runs_missing_from_tracker"].append(
                    f"{run['run_id']} (audit {run['audit_id']}, kind {run['kind']})"
                )
            elif row["kind"] != run["kind"]:
                report["kind_contradictions"].append(
                    f"{run['run_id']}: audit {run['audit_id']} records kind {run['kind']}, the tracker {row['kind']}"
                )

    outputs = [run["output"] for run in runs if run["output"].strip().lower() not in UNSET]
    if args.results_dir:
        base = args.results_dir.resolve()
        for path in sorted(p for p in base.rglob("*") if p.is_file() and not p.name.startswith(".")):
            relative = path.relative_to(base).as_posix()
            if not any(out.endswith(relative) or out.endswith(path.name) or relative.endswith(out) for out in outputs):
                report["unreferenced_result_files"].append(relative)
    if args.root:
        root = args.root.resolve()
        for run in runs:
            out = run["output"].strip()
            if has_run(run["status"]) and out.lower() not in UNSET and not (root / out).exists():
                report["missing_outputs_of_executed_runs"].append(f"{run['run_id']}: {out}")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-blocks", type=Path, required=True)
    parser.add_argument("--tracker", type=Path, required=True)
    parser.add_argument("--claim-map", type=Path)
    parser.add_argument("--audit", type=Path, help="results-audit.json whose source and standalone runs to compare")
    parser.add_argument("--results-dir", type=Path, help="directory of result files to match against tracker outputs")
    parser.add_argument("--root", type=Path, help="directory that tracker output paths are relative to")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--fail-on-drift", action="store_true", help="exit 1 when any drift is listed")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = check(args)
    total = sum(len(items) for items in report.values())
    if args.json:
        print(json.dumps({"drift_items": total, **report}, indent=2))
    else:
        print(f"Plan drift: {total} item(s)")
        for section, items in report.items():
            if items:
                print(f"\n{section.replace('_', ' ')} ({len(items)}):")
                for item in items:
                    print(f"- {item}")
        if not total:
            print("Every tracked run matches a declared block, every must-run block has run, and no kind contradicts the plan.")
    return 1 if args.fail_on_drift and total else 0


if __name__ == "__main__":
    sys.exit(main())
