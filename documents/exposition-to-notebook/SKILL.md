---
name: exposition-to-notebook
description: Convert mathematical derivations, research notes, and textual specs into runnable, product-ready Jupyter notebooks (.ipynb) with clear narrative, LaTeX, modular code, plots, and sanity checks/tests. Use when asked to turn an exposition/paper/spec into a notebook, prototype a method in Jupyter, create a demo notebook, or convert Markdown/LaTeX notes into an executable notebook.
---

# Exposition To Notebook

## Quick start

1. Pin down constraints (or assume defaults and add a TODO cell).
2. Extract the “computable core” (symbols, inputs/outputs, equations, algorithms).
3. Choose a notebook outline and scaffolding approach.
4. Build the notebook (`.ipynb`) and keep code importable/testable.
5. Add validation (sanity checks + minimal tests) and rerun top-to-bottom.
6. Polish for handoff (clear narrative, stable outputs, next steps).

## Workflow

### 1) Intake (constraints + deliverables)

Capture:
- Goal: what the notebook should demonstrate/produce.
- Audience: research peer vs. product engineer vs. stakeholder.
- Runtime + environment: CPU/GPU, offline/online, expected Python version.
- Data: provided vs. needs a stub/synthetic generator.

If missing, assume:
- Python 3.10+, CPU-only, no internet, small synthetic data.
- Minimal dependencies (stdlib first; optional `numpy`, `pandas`, `matplotlib`).

Add a top “Open Questions / TODO” markdown cell if anything is unclear.

### 2) Decompose the exposition into “things to implement”

Produce (in a markdown cell) a compact inventory:
- **Definitions table**: symbol → meaning → units/shape/type → notes.
- **Assumptions**: e.g. independence, boundary conditions, ranges.
- **Inputs/outputs**: what goes in/out of the core functions.
- **Algorithm steps**: numbered, with edge cases.

For math: identify which equations must be computed vs. just documented.

### 3) Notebook design (default section order)

Default section order (adjust to repo conventions):
1. Title + TL;DR
2. Goal + success criteria
3. Setup (deps, versions, seeds)
4. Background / exposition (LaTeX + narrative)
5. Implementation (small, reusable functions/classes)
6. Validation (sanity checks + tests)
7. Demo / experiments (plots, tables)
8. Conclusion + next steps
9. Appendix (derivations, references)

Prefer moving reusable code into a module (e.g. `src/` or `*_utils.py`) and importing it, keeping the notebook focused on orchestration and narrative.

### 4) Scaffold the `.ipynb`

- Start from scratch: run `scripts/scaffold_notebook.py --out <path>.ipynb --title "<title>"`
- Start from existing Markdown notes: run `scripts/md_to_ipynb.py <notes>.md --out <path>.ipynb --title "<title>" --with-scaffold`

### 5) Implement the computable core

- Convert each computable equation/step into a function with a docstring stating inputs/outputs and assumptions.
- Keep cells idempotent: no hidden state; rerun-from-scratch should match.
- Add small, readable examples next to new functionality.

### 6) Validate (make it “product-ready”)

Minimum bar:
- Restart kernel + “Run all” completes without errors.
- Deterministic results when possible (seeded randomness).
- At least:
  - shape/range/unit sanity checks, and
  - a few `assert`-style tests for key invariants.

For deeper guidance, see `references/product_ready_checklist.md`.

## Typical outputs

- A single runnable notebook: `notebooks/<slug>.ipynb` (or repo-standard location).
- Optional support files when helpful:
  - `src/<module>.py` for reusable code
  - `requirements.txt` or `pyproject.toml` snippet for dependencies
  - synthetic data generator (so the notebook runs without external data)
