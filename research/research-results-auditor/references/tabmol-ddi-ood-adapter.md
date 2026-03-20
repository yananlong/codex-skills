# TabMol DDI/OOD Adapter

When auditing DDI/OOD results, explicitly check:

- whether the split corresponds to a clearly defined pairwise OOD regime
- whether drift could be explained by label mix or missingness rather than true OOD difficulty
- whether negatives are defensible or should be treated as unlabeled
- whether top-k, calibration, and classwise behavior matter more than one aggregate score
- whether the result supports a framework claim or only a dataset-specific observation
