---
name: dskit-think
description: Capture, review, or promote possible future data-science improvements without silently changing an active study. Use for hypotheses, alternative data sources, methodological ideas, new analyses, or lessons that may be implemented later.
---

# Thought Backlog

Thoughts are proposals, not approved scope or established evidence.

1. Run `dskit context --json`; verify Git is active and read
   `.dskit/AGENT_GUIDE.md` and `.dskit/thoughts/backlog.md`.
2. To capture an idea, run `dskit thought "<concise idea and motivation>"`.
3. When reviewing, assess relevance, expected value, evidence needed, affected
   IBM stage, risks, and conflicts with project principles.
4. Mark a thought as accepted, rejected, superseded, or still proposed by
   editing its entry. Never delete the original idea or its decision history.
5. An accepted thought is not automatically executed. Record the approval and
   affected stage in the project log, then revise that stage transparently.

Do not use the thought backlog to bypass success criteria, final-partition
protections, data governance, or stakeholder approval.
