#!/usr/bin/env python3
"""Create a standard working pack for a research commercialization case."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def normalize_name(raw_name: str) -> str:
    normalized = raw_name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized


def context_template(case_name: str) -> str:
    return f"""# {case_name}.context

## Research asset

- Source:
- Type:
- Date/version:

## Core technical claim

- What it does:
- Under what conditions:
- What is still unproven:
- Readiness: TRL / MRL / ARL:

## Constraints

- IP or licensing:
- Freedom to operate:
- Regulatory:
- Data or hardware dependencies:
- Productization gaps:

## Initial commercialization objective

- Goal:
- Preferred path, if any:
- Time horizon:

## Required analysis chain

| Link | Current answer | Evidence | Weak link |
| --- | --- | --- | --- |
| Research claim |  |  |  |
| Workflow pain |  |  |  |
| Current workaround |  |  |  |
| Buyer/budget |  |  |  |
| Why now |  |  |  |
| Evidence |  |  |  |
| Validation test |  |  |  |
"""


def evidence_ledger_template(case_name: str) -> str:
    return f"""# {case_name}.evidence-ledger

## Commercialization evidence table

| Claim | Evidence type | Confidence | Missing proof | Cheapest next test | Decision informed |
| --- | --- | --- | --- | --- | --- |
|  | user-provided fact / sourced fact / inference / speculation | low / medium / high |  |  | continue / pivot / kill / defer |

## Hypothesis ledger

| Hypothesis | Current belief | Evidence | Confidence | Weak link | Cheapest next test | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| Customer segment |  |  |  |  |  |  |
| Job/pain severity |  |  |  |  |  |  |
| Current workaround |  |  |  |  |  |  |
| Buyer/budget |  |  |  |  |  |  |
| Willingness to pay |  |  |  |  |  |  |
| Channel/access |  |  |  |  |  |  |
| Deployment blocker |  |  |  |  |  |  |
| IP/FTO |  |  |  |  |  |  |
| Regulatory/procurement |  |  |  |  |  |  |

## Evidence log

| Date | Source | Observation | Type | Hypothesis affected | Confidence change |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |
"""


def pain_points_template(case_name: str) -> str:
    return f"""# {case_name}.pain-points

## Candidate segments

### Segment 1

- User:
- Economic buyer:
- Budget owner:
- Procurement/compliance gate:
- Operator:
- Beneficiary:
- Workflow:
- Pain:
- Current workaround:
- Cost of failure or delay:
- Why now:
- Switching friction:

### Segment 2

- User:
- Economic buyer:
- Budget owner:
- Procurement/compliance gate:
- Operator:
- Beneficiary:
- Workflow:
- Pain:
- Current workaround:
- Cost of failure or delay:
- Why now:
- Switching friction:

## Ranked problem theses

1. Thesis:
   Evidence:
   Weak links:
   Cheapest next test:
2. Thesis:
   Evidence:
   Weak links:
   Cheapest next test:

## Stakeholder map

| Segment | User | Economic buyer | Budget owner | Procurement/compliance | Operator | Champion | Buyer-owned metric |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |
"""


def options_template(case_name: str) -> str:
    return f"""# {case_name}.options

## Initial wedge options

1. Option:
   Customer:
   Offer:
   Why it matters:
   Proof milestone:
2. Option:
   Customer:
   Offer:
   Why it matters:
   Proof milestone:

## Commercialization path comparison

| Path | TRL/MRL/ARL fit | Budget proximity | Buyer access | Proof burden | Channel difficulty | Value quantifiability | Defensibility | Fit | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Startup/spinout |  |  |  |  |  |  |  |  |  |
| Licensing |  |  |  |  |  |  |  |  |  |
| Strategic partnership |  |  |  |  |  |  |  |  |  |
| Service-enabled product |  |  |  |  |  |  |  |  |  |
| Tooling/component/data asset |  |  |  |  |  |  |  |  |  |

## Sequence

- Initial wedge:
- Proof milestone:
- Adjacent expansion:
- Longer-term platform only if:

## Recommendation

- Beachhead:
- Why this path wins:
- What must be true:
- What would invalidate it:
- Kill/pivot/continue:
"""


def validation_plan_template(case_name: str) -> str:
    return f"""# {case_name}.validation-plan

## Risk-retirement priorities

1. Weak link:
   Why it matters:
   Cheapest decisive test:
   Pass/fail criterion:
2. Weak link:
   Why it matters:
   Cheapest decisive test:
   Pass/fail criterion:

## Experiments

| Experiment | Hypothesis tested | Method | Cost/time | Pass/fail criterion | Decision it informs | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| Customer discovery |  |  |  |  |  |  |
| Workaround/cost model |  |  |  |  |  |  |
| WTP/procurement test |  |  |  |  |  |  |
| Technical replication/productization test |  |  |  |  |  |  |
| Regulatory/IP/FTO diligence |  |  |  |  |  |  |

## Pilot gate

- Economic buyer:
- Paid or conversion commitment:
- Success metric:
- Timeline:
- Required data/integration access:
- Adoption owner:
- Decision after pilot:

## Immediate next steps

1. 
2. 
3. 
"""


def decision_log_template(case_name: str) -> str:
    return f"""# {case_name}.decision-log

## Assumptions in force

- 

## Kill / pivot / continue decisions

| Date | Decision | Scope | Evidence | Weak link retired | Next review trigger |
| --- | --- | --- | --- | --- | --- |
|  | continue / pivot / kill / defer |  |  |  |  |

## Decisions made

| Date | Decision | Why | Evidence status |
| --- | --- | --- | --- |
|  |  |  |  |

## Open questions

- 
"""


def build_file_map(case_name: str) -> dict[str, str]:
    return {
        f"{case_name}.context.md": context_template(case_name),
        f"{case_name}.evidence-ledger.md": evidence_ledger_template(case_name),
        f"{case_name}.pain-points.md": pain_points_template(case_name),
        f"{case_name}.options.md": options_template(case_name),
        f"{case_name}.validation-plan.md": validation_plan_template(case_name),
        f"{case_name}.decision-log.md": decision_log_template(case_name),
    }


def write_pack(case_name: str, output_dir: Path) -> Path:
    case_dir = output_dir / case_name
    if case_dir.exists():
        raise FileExistsError(f"Case directory already exists: {case_dir}")

    case_dir.mkdir(parents=True, exist_ok=False)
    for filename, content in build_file_map(case_name).items():
        (case_dir / filename).write_text(content)
    return case_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Initialize a commercialization case working pack."
    )
    parser.add_argument("case_name", nargs="+", help="Case name; normalized to hyphen-case")
    parser.add_argument("--path", required=True, help="Parent directory for the case pack")
    args = parser.parse_args()

    case_name = normalize_name(" ".join(args.case_name))
    if not case_name:
        print("[ERROR] Case name must include at least one letter or digit.")
        return 1

    try:
        case_dir = write_pack(case_name, Path(args.path).resolve())
    except FileExistsError as exc:
        print(f"[ERROR] {exc}")
        return 1
    except OSError as exc:
        print(f"[ERROR] Failed to create case pack: {exc}")
        return 1

    print(f"[OK] Created case pack: {case_dir}")
    for path in sorted(case_dir.iterdir()):
        print(f"[OK] {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
