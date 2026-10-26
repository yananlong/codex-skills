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

D3 and D4 states outside exploration require an entry whose decision is `authorize-D3` (for D3) or `close-and-create-D4` (for D4) and that names the identity it authorizes with `to_identity_version` (and optionally `to_paper_id`), for example `{"decision": "authorize-D3", "to_identity_version": 4, "rationale": "..."}`. The named version must equal the current `identity_version`, so an old authorization cannot cover a later pivot. Entries without `to_identity_version` are accepted as legacy authorizations with a validator warning.

`contribution_floor` is optional and recommended once the status leaves `exploring`; the validator warns when a committed commitment lacks it. It states the least contribution that still justifies the paper, in a form that can fail:

```json
"contribution_floor": {
  "statement": "the least contribution that still justifies the paper",
  "non_vacuity_outcome": "an observable result that would show the floor is not met",
  "invariants": ["properties any narrowed claim must keep"],
  "status": "unchecked"
}
```

Projects that recorded a success criterion or vision invariants in fields of their own can move them here.

A `selection_history` entry may carry a `trajectory` record (the shared claim-trajectory object in `suite-contract.md`). When one claim collects two `scope_narrowing` records, the validator requires a project-level review entry after the latest one: `{"decision": "project-review", "claim_id": "C1", "route_action": "continue", "floor_status": "met", "rationale": "..."}`. `route_action` takes the route-action values; `floor_status` (`unchecked`, `met`, `not_met`) is required when a `contribution_floor` exists. Each later narrowing of the same claim needs a new review.

`identity_anchors` is optional. When present it must hold digest-bound `question`, `central_object`, and `evidence_obligation` anchors, checked exactly as the semantic-assurance transition ledger checks them.

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
9. `scripts/init_research_pack.py --force` and `--adopt` preserve an existing commitment. Reset it only with the explicit `--reset-commitment` flag or `init_research_commitment.py --force`.

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

## Recording identity changes in a harness suite

Identity changes enter the harness event chain, so a verifier can tell an authorized pivot from drift:

```bash
python scripts/harness_runtime.py --root <suite> commitment-edit --change-class D1 --reason "..." --actor <who>
python scripts/harness_runtime.py --root <suite> pivot-request --change-class D3 --defect "..." \
    --why-not-repair "..." --requested-disposition authorize-D3 --actor <requesting skill or person>
python scripts/harness_runtime.py --root <suite> pivot-decision PV-0001 --decision authorize-D3 \
    --rationale "..." --actor <owner>
```

- Initialization and `--adopt` record the commitment's digest in a first `commitment_edited` event.
- `commitment-edit` validates the file and records its digest with the declared change class. It refuses a changed `paper_id` or `identity_version`; those change only through `pivot-decision`. A D3 or D4 edit needs an authorized decision for the current identity and the owner as actor.
- `pivot-request` may come from a downstream skill; it records the fields above and returns a request ID.
- `pivot-decision` must come from the owner, and not from the actor who made the request. It refuses while the commitment holds unrecorded edits. `authorize-D3` raises `identity_version` by one; `close-and-create-D4` takes `--to-paper-id` and starts the successor at version 1; `reject-pivot` changes no identity. Each writes its `selection_history` entry (naming `to_identity_version` where it applies) and records the new digest in one event.
- While both the recorded and the current commitment are `exploring`, an unrecorded edit is a validator warning (rule 1). Anywhere else, a commitment that does not match the last commitment event fails as drifted identity. A suite whose chain has no commitment event yet gets a warning that names the anchoring command.

## Minimum acceptance gate

A committed project may advance only when:

- the commitment object validates;
- the active work item matches the paper identity and next mandatory evidence obligation;
- no unapproved D3-D4 drift is present, and in a harness suite the commitment on disk matches the last commitment event;
- predecessor failures remain visible;
- literature assurance is proportionate to any novelty or priority claims;
- the next transition depends on evidence rather than artifact polish alone.

A passing structural validator does not authenticate the approver, establish scientific validity, prove independence, or enforce the contract outside the repository.
