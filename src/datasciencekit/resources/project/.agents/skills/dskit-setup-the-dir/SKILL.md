---
name: dskit-setup-the-dir
description: Prepare a DataScienceKit project for real data-science work by creating its fixed layout and safely classifying loose data, notebooks, and Python files. Use when setting up or organizing a project.
---

# Set Up the Project Directory

Leave a structurally ready DataScienceKit project while preserving evidence and
never guessing about data meaning.

1. Inspect `git status --short --branch` and the repository root. If `.dskit/`
   is absent, run `dskit init .`; otherwise run `dskit context --json` and read
   `.dskit/AGENT_GUIDE.md`, project principles, and the active handoff when one
   exists.
2. Create this fixed user-owned layout when directories are absent. Preserve an
   existing equivalent directory rather than creating a duplicate:

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
   directory.
3. Before relocating a loose candidate file, inspect its name, extension,
   parent directory, and safe metadata or text header. Preserve existing
   organization and do not inspect raw sensitive values beyond what is needed
   to classify the file. Move only files whose placement is unambiguous:

   - tabular, geospatial, image, audio, or archive inputs → `data/raw/`;
   - `.ipynb` exploration or communication notebooks → `notebooks/`;
   - reusable non-test `.py` modules → `src/`;
   - Python test modules and fixtures → `tests/`;
   - generated figures, tables, or decision documents → `reports/`.

   Do not infer that data is `interim` or `processed` from its format alone;
   only place it there when its provenance or generating code establishes that
   role. Leave ambiguous files in place, list them, and ask for direction.
   Never relocate project configuration, dependency files, credentials,
   licenses, READMEs, Git files, existing package directories, or files already
   in the fixed layout.
4. `dskit init` copies packaged workflow files; it does not clone a repository.
   Do not clone one merely for setup. If setup itself explicitly created a
   temporary clone, verify the installed project first, then remove only that
   exact temporary directory. Never delete the project root or a pre-existing
   clone.
5. Ensure `.gitignore` contains exactly these required entries, adding only a
   missing line and preserving all existing rules: `data/` and
   `.dskit/logs/machine.jsonl`. Keep sensitive, restricted, or large raw data
   out of Git unless the user and project governance rules explicitly permit it.
6. For an active study, record chosen locations and data-flow roles in the
   current append-only file under `history/`, register important immutable
   inputs and outputs with `dskit artifact`, then update the work plan and
   handoff. If no study exists, do not invent a business question or study title;
   report that `$dskit-understand` or `dskit new "TITLE"` is the next step.
7. Review the diff, stage only layout files belonging to this request, and make
   a focused commit if the project workflow requires a handoff.

The `.dskit/` directory is managed workflow state. Do not store notebooks,
source data, generated reports, or ordinary analysis code inside it.
