#!/usr/bin/env python3
"""Create a standard market and patent diligence pack."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def normalize_name(raw_name: str) -> str:
    normalized = raw_name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized


def scope_template(case_name: str) -> str:
    return f"""# {case_name}.scope

## Asset or thesis

- Research asset:
- Technology thesis:
- Commercial question:
- Target customer or market:

## Search posture

- Mode: quick scan / patent landscape / market and competitor scan / regulatory-procurement-funding scan / full diligence pack
- Geography:
- Date range:
- Source classes:
- Known exclusions:

## Search spine

| Layer | Terms or codes |
| --- | --- |
| Technology terms |  |
| Synonyms and adjacent terms |  |
| Application/workflow terms |  |
| Customer or buyer terms |  |
| Incumbent/substitute terms |  |
| Patent classes or assignees |  |
| Regulatory/procurement/funding terms |  |

## Decision the diligence informs

- Market pull:
- Patent/IP crowding:
- Licensing or partnership targets:
- Procurement/funding path:
- Regulatory/reimbursement path:
- Commercialization handoff:
"""


def source_log_template(case_name: str) -> str:
    return f"""# {case_name}.source-log

## Retrieval context

- Search dates:
- Searcher:
- Tools used:
- Coverage level: quick / bounded / full-pack

## Source log

| Date | Query/source | Source class | Claim supported | Key observation | Reliability | Limitation | Follow-up |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  | patent-office / assignment / company / filing / procurement / regulator / reimbursement / funding / standards / industry / user-provided |  |  | high / medium / low |  |  |

## Unverified but material claims

| Claim | Why it matters | Evidence needed | Next search |
| --- | --- | --- | --- |
|  |  |  |  |
"""


def patent_landscape_template(case_name: str) -> str:
    return f"""# {case_name}.patent-landscape

## Patent search strategy

- Sources searched:
- Query families:
- Classes searched:
- Assignees/applicants searched:
- Jurisdictions:
- Stopping rule:

## Patent families and records

| Family or record | Title/theme | Assignee/applicant | Priority date | Jurisdiction | Status signal | Relevance | Source | Limits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  | high / medium / low |  |  |

## Assignee and citation signals

| Assignee/applicant | Evidence | Commercial implication | Follow-up |
| --- | --- | --- | --- |
|  |  |  |  |

## Legal caveats

- This pack reports patent landscape signals only; it does not provide legal advice, validity, infringement, patentability, enforceability, or freedom-to-operate conclusions.
"""


def market_map_template(case_name: str) -> str:
    return f"""# {case_name}.market-map

## Market and buyer hypotheses

| Segment | User | Economic buyer | Budget owner | Workflow | Current workaround | Buyer-owned metric | Evidence | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  | low / medium / high |

## Purchase and budget evidence

| Evidence | Source | What it proves | What it does not prove | Follow-up |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Market evidence limits

- Private-company opacity:
- Geography limits:
- Segment-definition limits:
- Stale or weak sources:
"""


def competitor_template(case_name: str) -> str:
    return f"""# {case_name}.competitor-substitute-map

## Competitor and substitute classes

| Alternative | Class | Buyer/workflow served | Evidence source | Relevance | Differentiation question | Follow-up |
| --- | --- | --- | --- | --- | --- | --- |
|  | direct product / platform incumbent / component supplier / service provider / internal workaround / adjacent substitute / research prototype / open-source |  |  | high / medium / low |  |  |

## Incumbent and partner targets

| Organization | Role | Evidence | Why it matters | Risk |
| --- | --- | --- | --- | --- |
|  | competitor / licensee / channel / partner / acquirer / funder |  |  |  |
"""


def regulatory_template(case_name: str) -> str:
    return f"""# {case_name}.regulatory-procurement-funding

## Regulatory, reimbursement, standards, and compliance

| Gate | Source | Evidence | Commercial implication | Follow-up |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Procurement and public purchasing

| Buyer/agency | Notice/award/source | Need language | Size or budget signal | Incumbent or vendor | Follow-up |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

## Funding and translational programs

| Program/source | Eligibility | Deadline/cycle | Risk retired | Evidence | Follow-up |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |
"""


def evidence_template(case_name: str) -> str:
    return f"""# {case_name}.evidence-ledger

## Evidence ledger

| Claim | Evidence type | Source/date | Confidence | Commercial implication | Missing proof | Decision informed |
| --- | --- | --- | --- | --- | --- | --- |
|  | source-backed fact / user-provided fact / inference / hypothesis / speculation |  | low / medium / high |  |  |  |

## Weak links

| Weak link | Why it matters | Cheapest next evidence | Next skill or owner |
| --- | --- | --- | --- |
|  |  |  |  |
"""


def handoff_json(case_name: str) -> str:
    data = {
        "case": case_name,
        "asset_or_thesis": "",
        "coverage": "quick_scan",
        "retrieval_dates": [],
        "strongest_signals": [],
        "weakest_assumptions": [],
        "patent_landscape_confidence": "low",
        "market_evidence_confidence": "low",
        "recommended_next_skill": "commercialize-academic-research",
        "questions_for_next_skill": [],
        "limits": [],
    }
    return json.dumps(data, indent=2) + "\n"


def build_file_map(case_name: str) -> dict[str, str]:
    return {
        f"{case_name}.scope.md": scope_template(case_name),
        f"{case_name}.source-log.md": source_log_template(case_name),
        f"{case_name}.patent-landscape.md": patent_landscape_template(case_name),
        f"{case_name}.market-map.md": market_map_template(case_name),
        f"{case_name}.competitor-substitute-map.md": competitor_template(case_name),
        f"{case_name}.regulatory-procurement-funding.md": regulatory_template(case_name),
        f"{case_name}.evidence-ledger.md": evidence_template(case_name),
        f"{case_name}.handoff-to-commercialization.json": handoff_json(case_name),
    }


def write_pack(case_name: str, output_dir: Path) -> Path:
    case_dir = output_dir / case_name
    if case_dir.exists():
        raise FileExistsError(f"diligence directory already exists: {case_dir}")
    case_dir.mkdir(parents=True, exist_ok=False)
    for filename, content in build_file_map(case_name).items():
        (case_dir / filename).write_text(content, encoding="utf-8")
    return case_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a market and patent diligence pack.")
    parser.add_argument("case_name", nargs="+", help="case name; normalized to hyphen-case")
    parser.add_argument("--path", required=True, help="parent directory for the diligence pack")
    args = parser.parse_args()

    case_name = normalize_name(" ".join(args.case_name))
    if not case_name:
        print("[ERROR] case name must include at least one letter or digit.")
        return 1

    try:
        case_dir = write_pack(case_name, Path(args.path).resolve())
    except FileExistsError as exc:
        print(f"[ERROR] {exc}")
        return 1
    except OSError as exc:
        print(f"[ERROR] failed to create diligence pack: {exc}")
        return 1

    print(f"[OK] created diligence pack: {case_dir}")
    for path in sorted(case_dir.iterdir()):
        print(f"[OK] {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
