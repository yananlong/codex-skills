# Prospective evaluation of the research suite

Maintainer tooling for studying whether the research skills improve real projects: research
convergence, literature recall, and retention of adverse evidence. Project work never uses it, so
it lives here and not inside `research-pipeline-planner`, and skill packages do not carry it.

- `prospective-evaluation-contract.md`: the study protocol, custody, accounting, and conclusion rules.
- `scripts/init_prospective_evaluation.py`: create draft protocol, observation, and summary files.
- `scripts/validate_prospective_evaluation.py`: validate a study pack and recompute its metrics.
- `studies/`: one folder per study. Study 001 is a draft pack; CI validates it under the structural profile.
- `tests/`: regression tests, run by the research-assurance workflow.

```bash
python evals/prospective/scripts/validate_prospective_evaluation.py \
  --protocol evals/prospective/studies/study-001-category-theory/prospective-protocol.json \
  --observations evals/prospective/studies/study-001-category-theory/prospective-observations.json \
  --summary evals/prospective/studies/study-001-category-theory/prospective-summary.json \
  --assurance-profile structural
```
