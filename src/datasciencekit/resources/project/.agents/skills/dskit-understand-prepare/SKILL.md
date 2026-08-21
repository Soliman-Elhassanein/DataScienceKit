---
name: dskit-understand-prepare
description: >
  Complete IBM Data Science Methodology stages 5–6: Data Understanding and Data
  Preparation. Use for exploration, quality and bias assessment, leakage audits,
  cleaning, integration, transformation, and partitioning.
---

# Data Understanding and Data Preparation

Work only on IBM stages 5 and 6.

1. Run `dskit context --json`; verify Git is active and read
   `.dskit/AGENT_GUIDE.md`, then reconstruct the study from principles, handoff,
   work plan, evidence gates, artifact manifest, stages 1–4, recent project log
   entries, and relevant thoughts.
2. Produce reproducible aggregate evidence about structure, distributions,
   missingness, duplicates, invalid values, time behavior, relationships,
   segment differences, sampling bias, measurement bias, and outcome quality.
3. Audit leakage using actual availability relative to the intended decision.
   Check post-outcome variables, entity overlap, time leakage, proxy identifiers,
   and transformations learned before partitioning.
4. Fill `05-data-understanding.md`, separating measured facts from assumptions.
   Revisit requirements or approach if the data cannot answer the question.
5. Fill `06-data-preparation.md` with every selection, exclusion, cleaning,
   integration, derivation, imbalance treatment, partition rule, and resulting
   data version. Fit learned transformations only within development data.
6. Keep the final evaluation partition sealed. Register the prepared snapshot,
   update the work plan plus `CHK-002` and `CHK-003` evidence, and write the
   limitations and exact next action with `dskit handoff`.

When writing preparation or exploration code, follow
`.dskit/memory/code-quality.md`: centralize shared data rules, keep notebooks free
of hidden critical logic, run Ruff and relevant checks, inspect the staged diff,
and create a focused commit only after checks pass.

Do not choose a result based on final evaluation performance.
