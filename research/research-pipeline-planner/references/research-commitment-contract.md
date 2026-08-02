# Research Commitment Contract

Use this contract in orchestrated research suites once a project moves from open exploration to a paper-bearing route. The canonical artifact is `./research-commitment.json`.

## Purpose

Freeze the paper-level identity across work items so local review, novelty search, ideation, or implementation difficulty cannot silently replace the project. This contract governs project continuity; frozen work items still govern individual episodes.

## Required object

```json
{
  "schema_version": "1.0",
  "paper_id": "stable-project-id",
  "identity_version": 1,
  "status": "exploring",
  "main_question": "",
  "central_object_or_phenomenon": "",
  "contribution_class": "theory",
  "minimum_publishable_claim": "",
  "primary_evidence_obligation": "",
  "intended_audience": "",
  "permitted_refinements": [],
  "pivot_triggers": [],
  "kill_conditions": [],
  "successor_idea_policy": "park",
  "next_mandatory_evidence_artifact": "",
  "reconsideration_gate": "",
  "selection_history": [],
  "predecessor_failures": [],
  "last_change_class": "D0",
  "last_change_rationale": "initialized"
}
```

## Allowed values

- `status`: `exploring`, `committed`, `executing`, `interpreting`, `closed`
- `contribution_class`: `theory`, `method`, `protocol`, `benchmark`, `dataset`, `empirical-finding`, `position`, `mixed`
- `successor_idea_policy`: `park`, `reject`, `separate-project`
- `last_change_class`: `D0`, `D1`, `D2`, `D3`, `D4`

`paper_id` must be a stable identifier using letters, numbers, dot, underscore, colon, or hyphen. `identity_version` starts at 1 and changes only under an explicit identity-change decision.

## Selection-history entries

Each entry is an object with at least:

```json
{
  "decision": "select-route",
  "rationale": "Why this decision was made",
  "timestamp": "optional ISO timestamp",
  "evidence": ["optional artifact references"]
}
```

D3 and D4 states outside exploration require an entry whose decision is `authorize-D3` or `close-and-create-D4`.

## Identity-change classes

- `D0`: wording, formatting, or presentation only.
- `D1`: local technical repair preserving the question, central object, contribution class, and evidence obligation.
- `D2`: claim narrowing or strengthening that preserves the paper identity and does not substitute a different contribution.
- `D3`: contribution reconfiguration, central-object replacement, primary-evidence replacement, or route change that might remain in the same programme but requires explicit pivot authorization.
- `D4`: new paper identity. Close or park the current lineage and initialize a successor contract.

## Operating rules

1. Exploration may revise the contract freely while `status=exploring`, but every consequential selection remains in `selection_history`.
2. Moving to `committed` requires a concrete main question, central object, minimum publishable claim, primary evidence obligation, intended audience, next mandatory evidence artifact, reconsideration gate, pivot triggers, and kill conditions.
3. A closed lineage retains its question, object, claim, evidence obligation, and audience so historical identity is not erased.
4. While committed, executing, or interpreting, D0-D2 changes may proceed with a recorded rationale; D3-D4 changes require a planner-authorized pivot decision and human approval when configured.
5. Downstream skills may recommend `continue`, `narrow`, `pivot-request`, `kill`, or `park-successor`; they may not enact D3-D4 changes themselves.
6. A new attractive idea defaults to the successor policy. It does not replace the active paper merely because it scores better after later information became available.
7. Conceptual reconsideration is blocked until `next_mandatory_evidence_artifact` exists and passes its declared gate, unless a recorded pivot trigger or kill condition has fired.
8. Reframing, renaming, deleting a claim, or changing contribution class does not resolve predecessor failures. Preserve their dispositions explicitly.
9. `scripts/init_research_pack.py --force` preserves an existing commitment. Reset it only with the explicit `--reset-commitment` flag or `init_research_commitment.py --force`.

## Pivot request

A D3 or D4 request must record:

- the incumbent identity and maturity state;
- the concrete fatal defect or fired trigger;
- why D0-D2 repair is insufficient;
- evidence supporting the replacement;
- discarded artifacts and switching cost;
- new literature, validation, and venue burden;
- whether the replacement can be a successor project;
- the requested disposition: `authorize-D3`, `close-and-create-D4`, or `reject-pivot`.

## Minimum acceptance gate

A committed project may advance only when:

- the commitment object validates;
- the active work item matches the paper identity and next mandatory evidence obligation;
- no unapproved D3-D4 drift is present;
- predecessor failures remain visible;
- literature assurance is proportionate to any novelty or priority claims;
- the next transition depends on evidence rather than artifact polish alone.

A passing structural validator does not authenticate the approver, establish scientific validity, prove independence, or enforce the contract outside the repository.
