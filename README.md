# DataScienceKit

DataScienceKit is an agent- and session-independent workflow based on the
[IBM Data Science Methodology](https://developer.ibm.com/blogs/following-the-data-science-methodology/).
It guides empirical work from a business question through feedback while
keeping evidence, decisions, assumptions, and handoffs in durable files.

The methodology is iterative and has ten activities:

```text
Business Understanding → Analytic Approach
          ↓
Data Requirements → Data Collection
          ↓
Data Understanding → Data Preparation
          ↓
Modeling → Evaluation
          ↓
Deployment → Feedback ↺
```

IBM also describes the closely related CRISP-DM phases as business
understanding, data understanding, data preparation, modeling, evaluation, and
deployment. DataScienceKit uses IBM's more detailed ten-activity formulation.

This repository is not affiliated with or endorsed by IBM.

## Data science only

The workflow covers business questions, analytic approaches, data requirements,
collection, exploration, preparation, statistical or machine-learning methods,
evaluation, adoption of results, and feedback. Its scope ends at data-science
evidence, decisions, learning, and responsible use.

“Deployment” means putting an approved analytical result into its intended
decision, research, reporting, or operating context. It does not prescribe the
mechanism used by the surrounding organization.

## Install

Install the isolated command from this repository:

```bash
uv tool install git+https://github.com/Soliman-Elhassanein/DataScienceKit.git
```

For local development:

```bash
uv tool install --editable .
```

Initialize any data-science project:

```bash
cd your-project
dskit init
```

The generic working protocol is written to `.dskit/AGENT_GUIDE.md`. Any agent—or
a person working without an agent—can resume by running:

```bash
dskit context
```

Codex users also receive project-local skills under `.agents/skills/`. Start a
fresh session after initialization so they are discovered.

## IBM workflow commands

Start with project-wide scientific and governance rules:

```text
$dskit-principles
```

Then work through the five iterative groups:

```text
$dskit-understand
$dskit-require-collect
$dskit-understand-prepare
$dskit-model-evaluate
$dskit-deploy-feedback
$dskit-quality
```

Each group produces two numbered IBM methodology artifacts. Modeling includes
descriptive, diagnostic, forecasting, causal, experimental, optimization, and
statistical work; it does not assume every study uses machine learning.

## Continuity across agents and sessions

All continuity is file-backed:

```text
.dskit/
├── AGENT_GUIDE.md             Generic working protocol
├── config.json                Active study and methodology version
├── memory/principles.md       Project-wide scientific rules
├── logs/project.md            Human-readable decisions and handoffs
├── logs/machine.jsonl         Structured CLI event history
├── thoughts/backlog.md        Possible work, not approved scope
└── studies/NNN-study-name/    Ten IBM methodology artifacts
```

Use `$dskit-resume` in Codex or `dskit context` with any agent to reconstruct the
active study, completed stages, next stage, recent decisions, and available
studies without relying on conversation memory.

## Thoughts and logs

Capture an idea without changing approved study scope:

```bash
dskit thought "Try a time-varying threshold for seasonal demand"
```

Thoughts remain proposed until their evidence, risks, affected IBM stage, and
decision are recorded. Codex users can use `$dskit-think` to review them.

Append a human-readable decision or handoff:

```bash
dskit log --kind decision --stage "Analytic Approach" \
  "Use forecasting because the decision requires a weekly demand horizon."
```

The CLI appends structured events to `.dskit/logs/machine.jsonl` automatically.
`dskit init --force` preserves both logs and the thought backlog.

## Data-science code quality

Start a persistent review with:

```text
$dskit-quality
```

or create its report for any agent with:

```bash
dskit quality --scope "Entire project"
```

Reviews are preserved under `.dskit/quality/`. They cover reproducibility, data
integrity, leakage, analytic and statistical correctness, notebook state,
sensitive outputs, maintainability, and verification. Python reviews include
the project's configured `ruff check`; Ruff findings are evidence in the wider
scientific review rather than the entire quality gate.

## CLI reference

```text
dskit init [PATH] [--force]          Initialize a project
dskit new "STUDY TITLE"              Create and activate a study
dskit activate STUDY                 Switch the active study
dskit status [--json]                Show all IBM stages and the next stage
dskit context [--json]               Reconstruct cross-session context
dskit log MESSAGE [options]          Append a project log entry
dskit thought TEXT                   Capture a possible future improvement
dskit quality [--scope SCOPE]        Start a code-quality review
dskit validate [--json]              Check artifact completeness
dskit --version                      Show the installed version
```

Project-local template overrides belong in `.dskit/templates/` and apply to
future studies.

## Scientific safeguards

- Business success criteria and analytic measures are declared before results.
- Data provenance, permitted use, timing, and immutable snapshots are recorded.
- Leakage is audited before preparation and final evaluation.
- Final evaluation data remains sealed during method selection.
- All modeling attempts—including failures—remain in an append-only ledger.
- Post-hoc findings are labeled exploratory.
- Association is not presented as causation without an identification strategy.
- Deployment requires a passed evaluation gate and explicit ownership.
- Feedback can send the study back to any earlier IBM stage.

## Development

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
uvx ruff@0.16.2 check .
```

## Methodology references

- [IBM: Following the data science methodology](https://developer.ibm.com/blogs/following-the-data-science-methodology/)
- [IBM: Understanding and preparing data](https://dataplatform.cloud.ibm.com/docs/content/wsd/data.html?context=analytics)
