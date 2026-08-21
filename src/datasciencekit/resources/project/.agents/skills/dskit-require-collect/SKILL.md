---
name: dskit-require-collect
description: >
  Complete IBM Data Science Methodology stages 3–4: Data Requirements and Data
  Collection. Use to define required data, document sources and lineage, collect
  authorized data, and decide whether evidence is sufficient.
---

# Data Requirements and Data Collection

Work only on IBM stages 3 and 4.

1. Run `dskit context --json`; read principles, the active study's stages 1–2,
   recent project log entries, and relevant thoughts.
2. Fill `03-data-requirements.md` before collection. Specify concepts,
   population, unit, outcome, timing, history, volume, relationships, formats,
   quality thresholds, access, permitted purpose, and infeasibility conditions.
3. Collect only data authorized by the user and recorded governance rules. Do
   not place raw sensitive values in methodology artifacts.
4. Fill `04-data-collection.md` with source owners, collection method, lineage,
   sampling, time coverage, immutable snapshot identifiers, permissions,
   failures, exclusions, and coverage against requirements.
5. Stop if authorization, permitted purpose, outcome timing, or identity rules
   are too unclear to support valid collection.
6. Record the sufficiency decision and append a handoff with `dskit log --kind
   handoff --stage "Data Collection" "<evidence, gaps, and next action>"`.

If collection code is created or changed, follow `.dskit/memory/code-quality.md`:
keep source definitions and validation reusable, run Ruff and relevant checks,
review the staged diff, and create a focused commit after checks pass.

Do not perform data preparation or modeling.
