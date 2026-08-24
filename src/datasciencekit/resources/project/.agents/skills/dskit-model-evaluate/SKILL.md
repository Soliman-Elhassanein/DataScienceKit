---
name: dskit-model-evaluate
description: >
  Complete IBM Data Science Methodology stages 7–8: Modeling and Evaluation. Use
  to run statistical, forecasting, optimization, experimental, or machine-learning
  analyses and judge them against predeclared business and analytic criteria.
---

# Modeling and Evaluation

Work on IBM stages 7 and 8 while keeping planning distinct from judgment.

1. Run `dskit context --json`; verify Git is active and read
   `.dskit/AGENT_GUIDE.md`, principles, handoff, work plan, evidence gates,
   artifact manifest, stages 1–6, recent project log entries, and relevant
   thoughts. Do not rely on remembered session context.
2. Before observing final results, fill the Modeling Plan in `07-modeling.md`:
   baseline, candidate methods, fixed measures, acceptance rules, search budget,
   repetitions, stopping rule, and reproducibility record.
3. Before every attempt, run `dskit experiment "<title>"`. Complete its
   `EXP-NNN.md` record and registry row, including failures and unfavorable
   results. Record exact procedure, parameters, data fingerprint, randomness,
   results, uncertainty, warnings, outputs, and deviations.
4. Do not redefine the primary measure, slice, hypothesis, or threshold after
   observing results. Mark any post-hoc finding exploratory.
5. Fill `08-evaluation.md` and link every evaluated candidate to its `EXP-NNN`
   record. Compare with the declared baseline and business
   threshold; assess uncertainty, robustness, errors, subgroups, fairness,
   generalizability, and intended-use fitness. Missing evidence is not a pass.
6. Distinguish association from causation. Recommend deployment, revision of a
   named earlier IBM stage, more evidence, or stopping. When revisiting a stage,
   run `dskit step NUMBER --reason "<evidence-backed reason>"`; this preserves
   the modeling record and starts a new iteration.
7. Register decision-relevant outputs with `dskit artifact`, update the work
   plan and evidence gates, then write the snapshot with `dskit handoff`.

Any analysis or modeling code must follow `.dskit/memory/code-quality.md`.
Centralize measures and partitions, use practical DRY, run Ruff and relevant
checks, review the staged diff, and create a focused commit only after checks
pass. Do not commit failed or unverified analytical code as complete work.
