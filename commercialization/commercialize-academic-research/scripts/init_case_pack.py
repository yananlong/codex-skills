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

## Constraints

- IP or licensing:
- Regulatory:
- Data or hardware dependencies:
- Productization gaps:

## Initial commercialization objective

- Goal:
- Preferred path, if any:
- Time horizon:
"""


def pain_points_template(case_name: str) -> str:
    return f"""# {case_name}.pain-points

## Candidate segments

### Segment 1

- User:
- Buyer:
- Workflow:
- Pain:
- Current workaround:
- Cost of failure or delay:
- Switching friction:

### Segment 2

- User:
- Buyer:
- Workflow:
- Pain:
- Current workaround:
- Cost of failure or delay:
- Switching friction:

## Ranked problem theses

1. Thesis:
   Evidence:
   Weak links:
2. Thesis:
   Evidence:
   Weak links:
"""


def options_template(case_name: str) -> str:
    return f"""# {case_name}.options

## Initial wedge options

1. Option:
   Customer:
   Offer:
   Why it matters:
2. Option:
   Customer:
   Offer:
   Why it matters:

## Commercialization path comparison

| Path | Why it fits | Main risk | Proof burden | Notes |
| --- | --- | --- | --- | --- |
| Startup/spinout |  |  |  |  |
| Licensing |  |  |  |  |
| Strategic partnership |  |  |  |  |
| Service-enabled product |  |  |  |  |

## Recommendation

- Beachhead:
- Why this path wins:
- What must be true:
- What would invalidate it:
"""


def validation_plan_template(case_name: str) -> str:
    return f"""# {case_name}.validation-plan

## Critical assumptions

1. Assumption:
   Why it matters:
2. Assumption:
   Why it matters:

## Experiments

| Experiment | Purpose | Cost/time | Decision it informs | Owner |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
|  |  |  |  |  |

## Immediate next steps

1. 
2. 
3. 
"""


def decision_log_template(case_name: str) -> str:
    return f"""# {case_name}.decision-log

## Assumptions in force

- 

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
    parser.add_argument("case_name", help="Case name; normalized to hyphen-case")
    parser.add_argument("--path", required=True, help="Parent directory for the case pack")
    args = parser.parse_args()

    case_name = normalize_name(args.case_name)
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
