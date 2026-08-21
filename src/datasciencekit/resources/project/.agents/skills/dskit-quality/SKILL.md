---
name: dskit-quality
description: Review data-science analysis code for validity, reproducibility, leakage, statistical correctness, notebook hygiene, data protection, maintainability, and verification. Use for a project code-quality check; do not use for application architecture or product engineering review.
---

# Data Science Code Quality Review

Assess whether analysis code can support trustworthy and reproducible findings.

1. Run `dskit context --json`. Read principles, relevant active-study artifacts,
   recent project log entries, and prior quality reviews. Do not rely on session
   memory.
2. Unless continuing a named existing review, run `dskit quality --scope
   "<entire project or requested directory>" --json` and use the returned report.
3. Inventory analytical entry points, notebooks, queries, transformations,
   environment declarations, configurations, tests/checks, and generated
   results. Exclude third-party, environment, cache, and generated data folders.
4. Run existing safe checks when available. When Python files or notebooks are
   in scope, run the project's configured `ruff check` command and record its
   version, command, exit result, and findings. If Ruff is unavailable, mark it
   **Not found** and give the exact command needed; do not silently install it.
   Do not access new data, reveal secrets, or execute costly analyses merely to
   complete the review.
5. Trace actual data paths and error paths. Check reproducibility, randomness,
   raw-data immutability, joins, missingness, partitions, transformation fitting,
   outcome timing, leakage, measures, uncertainty, repeated comparisons,
   notebook execution state, hard-coded values, duplicated domain rules, DRY
   violations that can make results inconsistent, silent
   coercion, edge cases, and sensitive output.
6. Fill the report with evidence-backed strengths and findings. Every finding
   must cite a path and line, notebook cell, query, or generated output. Rank by
   scientific/business risk and give the smallest correction.
7. Missing evidence is **Not found**, never an assumed pass. Separate established
   defects from risks that require execution or domain confirmation.
8. Append a summary with `dskit log --kind finding --stage "Code Quality"
   "<gate, highest risks, report path, and next action>"`.

This is a review task. Do not change analysis code unless the user also asks for
fixes. Do not expand into application architecture or general product review.
