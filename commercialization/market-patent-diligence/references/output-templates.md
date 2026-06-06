# Output Templates

## Chat answer skeleton

```markdown
## Diligence read

Likely signal: ...
Confidence: low / medium / high
Coverage: quick scan / bounded scan / full diligence pack

## Scope and search posture

- Asset/thesis:
- Geography:
- Date range:
- Source classes:
- Important exclusions:

## Source-backed findings

### Patent and assignee signals

| Finding | Source | Date checked | Confidence | Commercial implication | Missing proof |
| --- | --- | --- | --- | --- | --- |

### Market, competitor, and substitute signals

| Finding | Source | Date checked | Confidence | Commercial implication | Missing proof |
| --- | --- | --- | --- | --- | --- |

### Procurement, funding, regulatory, reimbursement, or standards signals

| Finding | Source | Date checked | Confidence | Commercial implication | Missing proof |
| --- | --- | --- | --- | --- | --- |

## Red flags and weak links

## Handoff

- Send to:
- Why:
- Questions for that skill:
```

## Handoff JSON fields

```json
{
  "case": "",
  "asset_or_thesis": "",
  "coverage": "quick_scan | bounded_scan | full_pack",
  "retrieval_dates": [],
  "strongest_signals": [],
  "weakest_assumptions": [],
  "patent_landscape_confidence": "low | medium | high",
  "market_evidence_confidence": "low | medium | high",
  "recommended_next_skill": "commercialize-academic-research | research-systematic-literature-review | research-novelty-review | research-results-auditor | research-experiment-plan | research-paper-review | research-review-loop | none",
  "questions_for_next_skill": [],
  "limits": []
}
```
