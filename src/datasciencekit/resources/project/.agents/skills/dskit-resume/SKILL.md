---
name: dskit-resume
description: Reconstruct a DataScienceKit project's current state from durable files and identify the next IBM methodology stage. Use at the start of a new agent session, after a handoff, or whenever study context is uncertain.
---

# Resume From Durable State

Do not assume any prior agent or conversation memory.

1. Run `dskit context --json` from the project root and verify Git is active.
2. Read `.dskit/AGENT_GUIDE.md`, project principles, the active study's
   `HANDOFF.md`, work plan, evidence gates, experiment registry, artifact
   manifest, completed artifacts in numeric order, recent project log, and
   thought backlog.
3. Treat artifacts and logs as evidence, not necessarily truth. Flag conflicts,
   stale assumptions, missing provenance, and incomplete placeholders.
4. Report: active study, Git base, completed IBM stages, next incomplete stage,
   open work, unpassed gates, latest experiment, last material decision,
   blockers, relevant proposed thoughts, and the exact next action.
5. If the wrong study is active, list available studies and ask before running
   `dskit activate <study>`.
6. Run `dskit handoff` only if new state or a new next action was agreed, then
   commit that handoff according to the agent guide.

Do not modify a methodology artifact merely to make status appear complete.
