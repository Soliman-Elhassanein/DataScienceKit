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

Git is required. If the directory is not already inside a Git repository,
`dskit init` initializes one on `main`. Every DataScienceKit agent must inspect
repository state before working and create a focused commit before handoff.

The generic working protocol is written to `.dskit/AGENT_GUIDE.md`. Any agent—or
a person working without an agent—can resume by running:

```bash
dskit context
```

Codex users also receive project-local skills under `.agents/skills/`. Start a
fresh session after initialization so they are discovered.

To upgrade an existing DataScienceKit project, install the new CLI and run
`dskit init --force`. It updates managed instructions and backfills missing
continuity files without overwriting existing studies, logs, thoughts, memory,
quality reports, or project-local templates.

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
$dskit-code
$dskit-quality
```

Each group produces two numbered IBM methodology artifacts. Modeling includes
descriptive, diagnostic, forecasting, causal, experimental, optimization, and
statistical work; it does not assume every study uses machine learning.

## Writing analysis code

Use `$dskit-code` whenever the agent implements data collection, preparation,
exploration, modeling, evaluation, or reporting code. The skill enforces this
loop:

```text
inspect state → structure the change → practical DRY → self-review
→ Ruff lint and format checks → relevant tests → staged-diff review → commit
```

The durable standard lives at `.dskit/memory/code-quality.md`, with a fallback
Ruff configuration at `.dskit/quality/ruff.toml`.

DRY is applied to definitions that must remain scientifically consistent:
outcomes, populations, partitions, transformations, features, measures,
thresholds, and domain constants. It does not require abstractions for one-off
exploration or superficial similarity.

The agent inspects existing changes before editing, stages only files belonging
to its task, excludes credentials and raw/private data, reviews the staged diff,
and commits only after required checks pass. It reports the commit hash and does
not push unless explicitly requested.

## Continuity across agents and sessions

All continuity is file-backed:

```text
.dskit/
├── AGENT_GUIDE.md             Generic working protocol
├── config.json                Active study and methodology version
├── memory/principles.md       Project-wide scientific rules
├── memory/code-quality.md     Analysis coding and commit standard
├── logs/project.md            Human-readable decisions and handoffs
├── logs/machine.jsonl         Structured CLI event history
├── quality/ruff.toml          Fallback Ruff configuration
├── thoughts/backlog.md        Possible work, not approved scope
└── studies/NNN-study-name/
    ├── HANDOFF.md             Exact cross-session restart point
    ├── work/                  Work plan and semantic evidence gates
    ├── experiments/           Append-only registry and EXP-NNN records
    ├── artifacts/manifest.md  Output lineage and fingerprints
    └── 01…10-*.md             Ten IBM methodology artifacts
```

Use `$dskit-resume` in Codex or `dskit context` with any agent to reconstruct the
active study, completed stages, next stage, recent decisions, and available
studies without relying on conversation memory.

Each study keeps planning, execution, evidence, and handoff state separate. The
work plan says what should happen; experiment records say exactly what happened;
the artifact manifest identifies the inputs and outputs; evidence gates say what
has actually been checked; and `HANDOFF.md` gives the next agent one exact action.

Create an analytical attempt before running it:

```bash
dskit experiment "Regularized baseline with frozen split"
```

Register important inputs and outputs with provenance:

```bash
dskit artifact results/baseline.parquet --kind prepared-data \
  --source raw/customer-snapshot-v3 --fingerprint sha256:0123abcd
```

End a coherent work session with a regenerated snapshot:

```bash
dskit handoff --summary "Baseline evaluated; uncertainty remains wide" \
  --next "Run the predeclared temporal robustness check" --blockers "None"
```

## Mandatory version control

Version control is a hard workflow gate:

- `dskit init` requires Git and initializes a repository when needed.
- `dskit status` and `dskit context` report the Git root, branch, and dirty state.
- `dskit validate` fails when the project is not under Git version control.
- Every agent starts with `git status --short --branch`.
- Every agent stages only its own task files and reviews `git diff --cached`.
- Every coherent methodology or analysis change is committed before handoff.
- Failed code checks cannot be committed as completed work.
- Agents report the commit hash and never push without explicit authorization.

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
dskit init [PATH] [--force]          Initialize a project and ensure Git
dskit new "STUDY TITLE"              Create and activate a study
dskit activate STUDY                 Switch the active study
dskit status [--json]                Show all IBM stages and the next stage
dskit context [--json]               Reconstruct cross-session context
dskit log MESSAGE [options]          Append a project log entry
dskit thought TEXT                   Capture a possible future improvement
dskit quality [--scope SCOPE]        Start a code-quality review
dskit experiment "TITLE"             Create the next EXP-NNN record
dskit artifact PATH [options]        Register lineage and fingerprint
dskit handoff --summary ... --next ... Write the restart snapshot
dskit validate [--json]              Check structural and semantic evidence
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
- Completion gates require evidence links; changing a status alone does not pass.
- Evaluation must link to a complete experiment record, and important outputs
  must have a source plus immutable fingerprint.
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
