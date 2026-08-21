# Analysis Code Standard

This standard applies whenever an agent creates or changes code used for data
collection, preparation, exploration, modeling, evaluation, or reporting.

## Structure

- Follow the project's existing organization when it is coherent.
- Keep notebooks focused on exploration and communication. Move reusable or
  decision-critical logic into importable modules or equivalent reusable units.
- Separate data access, validation, preparation, analysis/modeling, measures,
  and presentation when they change for different reasons.
- Make inputs, outputs, parameters, data versions, and randomness explicit.
- Keep raw data immutable and generated artifacts separate from source material.

## DRY

- Define each target/outcome, population rule, partition rule, transformation,
  feature, measure, threshold, and domain constant in one authoritative place.
- Reuse shared behavior rather than copying analytical logic across notebooks,
  scripts, or queries.
- Do not abstract superficial similarity or one-off exploration. An abstraction
  must reduce the risk of inconsistent scientific behavior.

## Correctness and Verification

- Validate schemas, joins, missingness, ranges, partition isolation, and outcome
  timing at the boundary where assumptions enter.
- Add or update focused checks for transformations, measures, representative
  edge cases, and previously observed failures.
- Fail explicitly on invalid assumptions; do not silently coerce or drop data.
- Reproduce the affected analysis from a clean session when practical.

## Ruff Gate

For Python and Jupyter changes, run both:

```bash
ruff check <affected paths>
ruff format --check <affected paths>
```

Use the project's Ruff configuration when present. Otherwise use the fallback
`.dskit/quality/ruff.toml`. Fix findings, inspect changes, and rerun both checks.

## Commit Gate

- Inspect `git status` before editing and preserve unrelated user changes.
- Stage only files created or changed for the requested data-science task.
- Never commit credentials, raw/private data, caches, or large generated output.
- Review `git diff --cached` before committing.
- Commit only after Ruff and relevant checks pass, using a concise message that
  describes the data-science change.
- Do not amend existing commits or push unless the user explicitly requests it.

