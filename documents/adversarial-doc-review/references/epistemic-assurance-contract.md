# Epistemic Assurance Contract

Use this contract when a research workflow promotes an idea, plan, result, audit, or review into stronger evidence. It is intentionally proportionate: exploratory work remains lightweight, while confirmatory and high-stakes claims receive stronger controls.

## Evidence classes

- **Exploratory / development**: hypothesis-generating, tuned, selected, or interpreted after seeing relevant outcomes. Use it to guide subsequent work, not to close a claim.
- **Confirmatory**: the target claim, decision rule, material metrics or losses, case-selection rule, and stopping logic were fixed before inspecting the targeted outcomes. Log deviations and reclassify affected conclusions as exploratory.
- **Independently verified**: confirmatory evidence was checked or reproduced by a materially independent evaluator. State the actual dimensions of independence rather than relying on a role name.
- **Operational / high-stakes**: evidence is intended to support deployment, safety, security, policy, clinical, financial, or other consequential decisions. Add realistic threat models, context-specific harms, and independent review.

## Promotion record

Before advancing evidence beyond exploratory status, record:

1. the exact claim or property and requested evidence class;
2. artifact, data, code, prompt, and model provenance;
3. the complete decision rule, including every decision-relevant error, omission, skip, null, retry, and failure state;
4. the case or sample selection rule, exclusions, and any outcome-informed changes;
5. the cheapest non-vacuity or discrimination test;
6. material predecessor failures and their evidence-backed disposition;
7. the independence statement across context, data access, implementation, oracle or evaluator, and advancement authority;
8. unresolved limitations and the resulting proceed, revise, narrow, or stop decision.

## Property, not label

Do not treat an assurance label or artifact field as proof that the underlying property holds.

- A self-hash establishes internal consistency, not externally anchored immutability.
- An environment flag does not establish network or process isolation.
- Copying a prior digest does not establish that replay regenerated the artifact.
- Agreement among systems that share policy, code, data, or hidden truth can be correlated failure.
- A comparator missing proposal-only fields is not necessarily substantively distinct.
- A successful command or structural validator does not establish semantic validity, independence, non-vacuity, or evidential sufficiency.
- Role names such as “auditor” or “adjudicator” do not create independence.

## Independence statement

Describe which dimensions are actually separated:

- **context**: separate prompt, conversation, or prior conclusions;
- **data**: no access to hidden truth or outcome labels unavailable to the evaluated system;
- **implementation**: independently written or meaningfully diverse code and tests;
- **evaluation**: distinct oracle, adjudication logic, or reproduction procedure;
- **authority**: the evaluator can block advancement and is not merely certifying its own work.

The same agent or team may perform multiple roles when necessary, but disclose that arrangement as self-review. Do not call it independent.

## Proportionate controls

- For exploratory work, preserve provenance, selection history, negative evidence, and limitations.
- For confirmatory work, freeze the decision contract, separate development from confirmatory cases, run a non-vacuity preflight, account for all outcomes, and prevent hidden-truth leakage.
- For independently verified work, require a materially separate evaluator or reproduction pass and record the independence dimensions.
- For operational or high-stakes work, require independent audit before advancement and test the relevant threat model and harms.
- When the runtime cannot provide the requested independence, continue only at a weaker evidence class and narrow the claim. Do not block useful exploration merely because independent verification is unavailable.

## Failure inheritance

- Carry material predecessor failures forward until new evidence resolves them.
- Reclassification, renaming, replacement, or omission is not resolution.
- An accepted risk must identify the unresolved failure, justify acceptance, and narrow the affected claim or route.
- Preserve failed attempts and initial resource, timeout, integrity, or execution failures when they affect feasibility or burden claims.

## Non-vacuity preflight

Before expensive or confirmatory execution, check that:

- at least one plausible case makes competing methods, policies, or actions differ;
- the decision or loss contract penalizes every decision-relevant mistake, including failure to act;
- the comparator can win under a plausible condition rather than being disabled by construction;
- selected cases were not conditioned on the oracle answer or desired outcome;
- skipped, failed, null, and retried cases remain visible in the accounting.

A failed preflight normally narrows or revises the route; it need not terminate exploratory investigation.

## Audit language

Use precise conclusions:

- `structurally valid`: required files or fields are present;
- `internally consistent`: the artifacts agree with one another;
- `supports exploratory follow-up`: useful signal, but not confirmatory evidence;
- `supports the confirmatory claim`: the predeclared decision contract is satisfied;
- `independently verified`: a materially independent pass reproduced or validated the result.

Never shorten these distinctions into an unqualified “validated,” “verified,” or “passed.”

## Source basis

This contract adapts established principles from OSF and Center for Open Science guidance on distinguishing planned confirmatory tests from exploration, NIST terminology for objective third-party verification and validation, ACM artifact-review distinctions between functional artifacts and independently reproduced results, and the 2023 ALLEA European Code of Conduct for Research Integrity.
