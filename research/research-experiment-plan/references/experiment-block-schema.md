# Experiment Block Schema

Every kept experiment block should define all of the following fields.

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
