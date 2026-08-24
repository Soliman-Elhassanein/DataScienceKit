---
name: dskit-setup-the-dir
description: Set up or inspect the user-owned working directories in a DataScienceKit project. Use after dskit init when a study needs a clear, reproducible layout for data, code, notebooks, reports, and tests.
---

# Set Up the Project Directory

Create a small, conventional working layout without moving, deleting, or
renaming existing user files.

1. Run `dskit context --json` and `git status --short --branch`. Read
   `.dskit/AGENT_GUIDE.md`, project principles, and the active handoff if a
   study already exists.
2. Inspect the repository before making directories. Reuse an established
   layout when it already separates raw inputs, derived data, source code,
   notebooks, reports, and tests clearly.
3. When no equivalent layout exists, create only the needed empty directories:

   ```text
   data/raw/        immutable source snapshots; never edit in place
   data/interim/    reproducible intermediate outputs
   data/processed/  versioned model-ready data
   src/             reusable collection, preparation, and analysis code
   notebooks/       exploration and communication, not hidden critical logic
   reports/         decision-ready figures, tables, and narrative outputs
   tests/           automated checks for reusable code and data boundaries
   ```

   Add a placeholder file only when Git must retain an otherwise empty
   directory. Do not create a directory just because it appears in this list.
4. Keep sensitive, restricted, or large raw data out of Git unless the user and
   project governance rules explicitly permit it. Add narrowly scoped ignore
   rules when needed; do not replace existing `.gitignore` entries.
5. For an active study, record the chosen locations and their data-flow roles in
   the relevant IBM artifact, register important immutable inputs and outputs
   with `dskit artifact`, then update the work plan and handoff.
6. Review the diff, stage only layout files belonging to this request, and make
   a focused commit if the project workflow requires a handoff.

The `.dskit/` directory is managed workflow state. Do not store notebooks,
source data, generated reports, or ordinary analysis code inside it.
