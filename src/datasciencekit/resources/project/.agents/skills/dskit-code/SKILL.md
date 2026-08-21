---
name: dskit-code
description: Implement or modify code for a data-science study with coherent structure, practical DRY, reproducibility, focused verification, mandatory Ruff checks for Python/Jupyter, and a reviewed Git commit. Use when an agent is asked to write data collection, preparation, analysis, modeling, evaluation, or reporting code.
---

# Write High-Quality Data Science Code

Complete the requested analytical change and leave a focused, verified commit.

1. Run `dskit context --json`. Read project principles,
   `.dskit/memory/code-quality.md`, relevant IBM-stage artifacts, and recent
   project log entries. Treat durable files as context, not conversation memory.
2. Run `git status --short` before editing. Identify pre-existing changes and do
   not modify, stage, or commit unrelated user work. If this is not a Git
   repository, ask before initializing one.
3. Inspect the existing analysis organization and follow coherent conventions.
   Keep notebooks for exploration/communication and move reusable or
   decision-critical behavior into structured reusable units. Make data inputs,
   versions, parameters, outputs, and randomness explicit.
4. Apply practical DRY. Centralize definitions that must remain scientifically
   consistent—outcomes, populations, partitions, transformations, features,
   measures, thresholds, and domain constants. Do not create abstractions for
   superficial similarity or single-use exploration.
5. Implement the smallest complete change. Add or update focused checks for data
   boundaries, transformations, measures, edge cases, and prior failures. Never
   silently coerce invalid data or fit learned transformations across protected
   partitions.
6. Self-review the diff for correctness, leakage, hidden notebook state,
   sensitive output, hard-coded paths/credentials, duplication, unclear names,
   dead work, and unnecessary complexity.
7. For affected Python and Jupyter files, run `ruff check <affected paths>` and
   `ruff format --check <affected paths>`. Prefer the project's configuration;
   otherwise pass `--config .dskit/quality/ruff.toml`. If Ruff is not installed
   and `uv` is available, use `uvx ruff@0.16.2` with the same arguments. Apply
   safe fixes or formatting, inspect the changes, and rerun until both pass.
8. Run the narrowest relevant tests/checks, then the broader project checks when
   proportionate. Reproduce the affected analysis from a clean session when
   practical. Do not claim success for checks that were not run.
9. Update the relevant IBM artifact and append check evidence with `dskit log
   --kind progress --stage "<stage>" "<change, Ruff result, tests, and risks>"`.
10. Stage only your task files. Review `git diff --cached`, check again for
    secrets/data/generated output, and commit with a concise data-science-focused
    message. Do not commit when required checks fail. Do not amend or push unless
    explicitly requested.

Report the commit hash, changed structure, Ruff commands, tests, and any residual
risks or unchecked evidence.

