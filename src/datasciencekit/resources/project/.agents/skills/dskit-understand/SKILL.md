---
name: dskit-understand
description: >
  Complete IBM Data Science Methodology stages 1–2: Business Understanding and
  Analytic Approach. Use to frame a study around stakeholder value and translate
  the business question into an appropriate analytic question.
---

# Business Understanding and Analytic Approach

Work only on IBM stages 1 and 2.

1. Run `dskit context --json`. Verify Git is active and read
   `.dskit/AGENT_GUIDE.md`, principles, recent project log entries, and the
   thought backlog. Do not rely on prior conversation memory.
2. If this is a new study, run `dskit new "<short title>"`. Do not replace an
   active study without clear intent.
3. Fill `01-business-understanding.md` from stakeholder and domain evidence:
   problem, decision, value, population, current baseline, success threshold,
   constraints, intended use, and prohibited use.
4. Fill `02-analytic-approach.md`: translate the business question into a
   descriptive, diagnostic, predictive, prescriptive, causal, forecasting,
   experimental, or mixed approach. Define claim strength, baseline,
   uncertainty, validation, and falsification conditions before seeing results.
5. Ask at most three questions whose answers materially change value, scope, or
   validity. Mark claims by provenance.
6. Log findings, decisions, unresolved questions, and the next stage with
   `dskit log --kind handoff --stage "Analytic Approach" "<summary>"`.

Do not collect data, prepare data, or model in this phase.
