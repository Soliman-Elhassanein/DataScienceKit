# Agent-Independent Working Protocol

This project does not depend on a particular agent or conversation session.
Durable files are authoritative; conversation memory is not.

Git version control is mandatory. `dskit init` creates a `main` repository when
the project is not already inside one. An agent must not perform DataScienceKit
work when `dskit context --json` reports that no Git repository exists.

## Start or Resume

1. Run `dskit context --json` from anywhere inside the project and verify
   `version_control.repository` is `true`.
2. Run `git status --short --branch`. Preserve all pre-existing and unrelated
   changes; never absorb them into the agent's commit.
3. Read `.dskit/memory/principles.md`.
4. Read `.dskit/memory/code-quality.md` before changing analysis code.
5. Read completed active-study artifacts in numeric order.
6. Read the recent entries in `.dskit/logs/project.md`.
7. Review relevant entries in `.dskit/thoughts/backlog.md` without treating
   proposed thoughts as approved work.
8. Continue from `next_stage` unless evidence requires revisiting an earlier IBM
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
5. Stage only files changed for the current task, including its methodology and
   log updates. Review `git diff --cached`, then create a focused commit.
6. Report the commit hash. If no files changed, explicitly report that no commit
   was needed. Never amend or push unless the user explicitly requests it.

Do not hand off uncommitted DataScienceKit work. If a required check fails, do
not commit code as complete; leave the worktree intact and report the blocker.

## Code Quality Review

For analysis-code review, create a durable report with `dskit quality`. Inspect
validity and reproducibility before style. For Python files and notebooks, run
the project's configured Ruff check and record the exact command and result.
Keep prior reports under `.dskit/quality/` for comparison across sessions.

## When Writing Analysis Code

Follow `.dskit/memory/code-quality.md`. Preserve the existing coherent
organization, apply DRY to definitions whose inconsistency would change results,
and add focused verification. For Python and Jupyter changes, Ruff lint and
format checks are mandatory. Review the staged diff and commit only the agent's
task files after all required checks pass. Never commit raw/private data,
credentials, caches, or large generated output. Do not push without explicit
authorization.
