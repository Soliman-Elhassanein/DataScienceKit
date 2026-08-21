# Data Science Code Quality Review

- Created: {{CREATED_AT}}
- Scope: {{SCOPE}}
- Status: Draft

This review evaluates analysis code only where code supports data-science work.
Rank findings by risk to validity, reproducibility, data protection, or the
business decision—not by style preference.

## Overall Gate

- Result (Pass / Conditional / Fail): [TODO]
- Highest-risk issue: [TODO]
- Evidence confidence: [TODO]

## Reproduction and Automated Checks

| Check or command | Result | Evidence/output | Limitation |
|---|---|---|---|
| [TODO] | [TODO] | [TODO] | [TODO] |

### Ruff Check (Python and Jupyter)

- Ruff version: [TODO]
- Command: [TODO]
- Result and exit status: [TODO]
- Findings or **Not applicable**: [TODO]

## Findings

Every finding must cite a path and line, notebook cell, query, or generated
output. Use **Not found** when evidence is absent.

| ID | Severity | Area | Finding | Evidence | Scientific/business risk | Smallest correction | Status |
|---|---|---|---|---|---|---|---|
| Q001 | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] | Open |

Severity reflects consequence and likelihood:

- **Critical** — can invalidate results, expose protected data, or materially
  mislead the decision.
- **High** — likely to change results or prevent independent reproduction.
- **Medium** — raises maintenance or verification cost and can conceal errors.
- **Low** — bounded clarity or consistency issue with little validity risk.

## Review Areas

### Reproducibility and Execution

- Clear analysis entry point or execution order: [TODO]
- Declared analytical environment and dependencies: [TODO]
- Controlled randomness and deterministic data versions: [TODO]
- Clean-session reproduction result: [TODO]

### Data Integrity and Leakage

- Raw data immutability and lineage: [TODO]
- Schema, range, missingness, and join validation: [TODO]
- Partition isolation and transformation fitting: [TODO]
- Outcome timing and leakage controls: [TODO]

### Analytic and Statistical Correctness

- Measures match the declared question and population: [TODO]
- Baselines, uncertainty, repeated comparisons, and stopping rules: [TODO]
- Association/causation claims match the evidence design: [TODO]
- Edge cases and numerical stability: [TODO]

### Notebook and Analysis Hygiene

- Hidden execution state or out-of-order dependencies: [TODO]
- Stored outputs with sensitive, stale, or misleading content: [TODO]
- Repeated transformations and inconsistent definitions: [TODO]
- Hard-coded paths, dates, thresholds, or credentials: [TODO]

### Maintainability and Verification

- Shared domain definitions and transformations: [TODO]
- Clear names, bounded responsibilities, and documented assumptions: [TODO]
- Checks for transformations, measures, and representative edge cases: [TODO]
- Failures are explicit rather than silently coerced or dropped: [TODO]

## Strengths

- [TODO]

## Unchecked or Unavailable Evidence

- [TODO]

## Recommended Order

1. [TODO]
