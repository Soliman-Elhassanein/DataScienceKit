# Agent-Independent Working Protocol

This project does not depend on a particular agent or conversation session.
Durable files are authoritative; conversation memory is not.

## Start or Resume

1. Run `dskit context --json` from anywhere inside the project.
2. Read `.dskit/memory/principles.md`.
3. Read completed active-study artifacts in numeric order.
4. Read the recent entries in `.dskit/logs/project.md`.
5. Review relevant entries in `.dskit/thoughts/backlog.md` without treating
   proposed thoughts as approved work.
6. Continue from `next_stage` unless evidence requires revisiting an earlier IBM
   stage. Record that iteration explicitly.

## While Working

- Base claims on stakeholder statements, domain documentation, or observed data.
- Preserve provenance and distinguish facts, assumptions, and interpretations.
- Never erase unfavorable modeling attempts or prior decisions.
- Keep raw sensitive values out of methodology documents and logs.
- Do not alter success criteria after observing evaluation results.

## End or Handoff

1. Leave the current stage artifact internally consistent, even if incomplete.
2. Record findings, decisions, blockers, and the exact next action:

   `dskit log --kind handoff --stage "<IBM stage>" "<summary>"`

3. Capture non-approved possibilities separately:

   `dskit thought "<idea and motivation>"`

4. Run `dskit status` and report the active study and next stage.

## Code Quality Review

For analysis-code review, create a durable report with `dskit quality`. Inspect
validity and reproducibility before style. For Python files and notebooks, run
the project's configured Ruff check and record the exact command and result.
Keep prior reports under `.dskit/quality/` for comparison across sessions.
