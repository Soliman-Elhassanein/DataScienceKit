---
name: dskit-deploy-feedback
description: >
  Complete IBM Data Science Methodology stages 9–10: Deployment and Feedback.
  Use to put an approved analytical result into its intended context, document
  ownership and observation, collect outcomes, and decide how the study iterates.
---

# Deployment and Feedback

Deployment here means adoption of an approved analytical result in a decision,
research, report, or operating process. Implementation mechanisms are outside
this workflow.

1. Run `dskit context --json`; read principles, all completed active-study
   stages, recent project log entries, and relevant thoughts.
2. Do not recommend adoption when evaluation has a failed blocking gate.
3. Fill `09-deployment.md`: result, recipients, intended/prohibited use,
   versioned deliverables, interpretation, caveats, human approval, fallback,
   outcome measures, drift checks, review cadence, and stop/revalidation rules.
4. Adoption, publication, registration, or communication outside the project
   requires explicit user authorization. Documenting a plan does not grant it.
5. Once real feedback exists, fill `10-feedback.md` with its source, collection
   method, observed outcomes, stakeholder response, unintended effects, changed
   assumptions, lessons, and next review date.
6. Decide whether to continue, revise, pause, or retire. If revising, name the
   IBM stage to revisit rather than silently changing completed evidence.
7. Run `dskit validate` and append the decision with `dskit log --kind decision
   --stage "Feedback" "<outcome and iteration decision>"`.
