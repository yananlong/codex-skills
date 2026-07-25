# Claim-Evidence Map Template

Use the compact table for exploratory plans. For confirmatory or high-stakes plans, also populate the assurance record below and mirror the fields in `claim-map.json`.

| Claim ID | Priority | Claim | Why it matters | Minimum convincing evidence | Anti-claim | What would falsify it | Decision if unproven | Linked experiment blocks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | primary / supporting | | | | | | reframe / drop / defer | |

## Assurance Record

| Claim ID | Current evidence class | Requested evidence class | Frozen decision rule | Complete loss or outcome contract | Case-selection rule | Material predecessor failures | Independence statement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | exploratory / confirmatory / independently_verified / operational_high_stakes | | | | | | |

For machine-readable confirmatory claims, include non-empty `evidence_class`, `decision_rule`, `loss_contract`, and `falsification_test` fields, plus a `predecessor_failures` list. Field presence is not proof that the underlying controls hold.