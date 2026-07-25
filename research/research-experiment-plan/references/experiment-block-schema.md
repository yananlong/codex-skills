# Experiment Block Schema

Every kept experiment block should define the core fields below. Confirmatory and high-stakes blocks must also define the assurance fields; exploratory blocks should include them when useful but are not rejected solely for omitting them.

## Core fields

- `block_id`: stable ID such as `B1`
- `paper_role`: `main`, `appendix`, or `cut`
- `claim_ids`: claim IDs from `claim-map.json`
- `anti_claims_ruled_out`: anti-claims this block addresses
- `why_this_block_exists`: reviewer-relevant reason for the block
- `dataset_split_task`: exact evaluation setting
- `systems_compared`: strongest baselines, ablations, and variants only
- `fixed_factors`: factors held constant to keep the comparison fair
- `variable_factors`: the specific manipulated factor(s)
- `metrics`: decisive metrics first
- `setup_details`: backbone, budget, and key settings
- `seeds`: integer seed count
- `success_criterion`: result that would count as support
- `minimum_effect_size`: threshold or margin if applicable
- `failure_interpretation`: what a negative result would mean
- `expected_output_artifact`: table, figure, or audit artifact to produce
- `compute_budget`: expected cost or budget class
- `dependencies`: block IDs or prerequisites
- `priority`: `must-run`, `nice-to-have`, or `defer`

## Assurance fields

- `evidence_class`: `exploratory`, `confirmatory`, `independently_verified`, or `operational_high_stakes`
- `selection_rule`: how cases, samples, checkpoints, or tasks are selected; disclose any outcome-informed selection
- `non_vacuity_check`: cheapest check showing that competing systems, policies, or actions can differ and that the comparator can plausibly win
- `complete_outcome_accounting`: how successes, errors, omissions, skips, nulls, retries, timeouts, and execution failures are retained
- `hidden_information_controls`: information unavailable to the evaluated system and how leakage is prevented or detected
- `independence_requirements`: list of required separation dimensions across context, data, implementation, evaluation, and advancement authority
- `predecessor_failures`: material prior failures that this block must resolve, narrow, or carry forward

Field presence does not establish that an assurance property actually holds. Structural validation must be followed by semantic audit before confirmatory or high-stakes promotion.