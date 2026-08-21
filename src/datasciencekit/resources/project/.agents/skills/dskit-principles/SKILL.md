---
name: dskit-principles
description: Establish durable data-science standards for decisions, governance, analytic integrity, evaluation, deployment, and feedback. Use when starting a DataScienceKit project or when project-wide scientific standards change.
---

# Data Science Principles

Define rules that apply to every study, independent of any agent or session.

1. Run `dskit context --json`. Verify Git is active and read
   `.dskit/AGENT_GUIDE.md`, `.dskit/memory/principles.md`, and the project log.
2. Preserve existing evidence-backed rules. Resolve only project-wide standards:
   decision evidence, permitted data use, leakage controls, reproducibility,
   baselines, uncertainty, evaluation, approval, monitoring, and stop criteria.
3. Ask only about material governance or business rules that cannot be observed.
   Never invent legal, privacy, fairness, or safety requirements.
4. Replace every placeholder with a testable rule or a named unresolved owner.
5. Append a decision summary with `dskit log --kind decision --stage
   "Principles" "<summary and next action>"`.

Do not create a study or choose an analytic method.
