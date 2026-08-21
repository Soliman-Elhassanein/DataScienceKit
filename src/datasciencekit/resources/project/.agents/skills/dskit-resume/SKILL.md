---
name: dskit-resume
description: Reconstruct a DataScienceKit project's current state from durable files and identify the next IBM methodology stage. Use at the start of a new agent session, after a handoff, or whenever study context is uncertain.
---

# Resume From Durable State

Do not assume any prior agent or conversation memory.

1. Run `dskit context --json` from the project root.
2. Read project principles, the active study's completed artifacts in numeric
   order, the recent project log, and the thought backlog.
3. Treat artifacts and logs as evidence, not necessarily truth. Flag conflicts,
   stale assumptions, missing provenance, and incomplete placeholders.
4. Report: active study, completed IBM stages, next incomplete stage, last
   material decision, unresolved questions, relevant proposed thoughts, and the
   exact next action.
5. If the wrong study is active, list available studies and ask before running
   `dskit activate <study>`.
6. Append a handoff entry only if new state or a new next action was agreed.

Do not modify a methodology artifact merely to make status appear complete.

