# Product-ready notebook checklist

Use this as a “definition of done” when turning an exposition into a notebook prototype.

## Run-all contract

- Kernel restart + “Run all” completes without manual intervention.
- No reliance on hidden state (e.g., previous execution order).
- Errors are handled with clear messages (avoid silent failures).

## Reproducibility

- Print environment basics (Python version; key library versions if used).
- Seed randomness (`random`, and optionally `numpy` if present).
- Make parameters explicit (single “Config” cell or a dataclass).

## Correctness / validation

- Add sanity checks: shapes, ranges, units, monotonicity, invariants.
- Add a few targeted tests (`assert`-style) for the core functions.
- For math-heavy notebooks:
  - Validate equations numerically (spot-check with random inputs).
  - Use finite differences for gradient checks when relevant.
  - Compare against a baseline/simpler special case if available.

## UX / readability

- Start with a TL;DR stating what the notebook does and what it outputs.
- Keep sections short; use headings and a consistent story arc.
- Label plots (axes labels, units, legends) and interpret them in text.
- Avoid noisy outputs; show the few outputs that matter.

## Data handling

- If no data is provided, include a synthetic/stub generator so the notebook runs.
- If data must be downloaded:
  - Cache locally and document the source.
  - Provide an “offline” fallback (sample data or cached artifacts).

## Performance (prototype-appropriate)

- Keep runtime reasonable; document expected runtime and memory.
- Avoid repeated expensive work; cache intermediate results when needed.

## Handoff quality

- Clearly state next steps (what to productionize, what to test, what to optimize).
- If code is reusable, move it into `src/` or a `*_utils.py` module and import it.

