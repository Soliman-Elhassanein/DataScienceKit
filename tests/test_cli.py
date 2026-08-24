from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from datasciencekit.cli import (
    ARTIFACTS,
    STUDY_SUPPORT_FILES,
    activate_study,
    append_project_log,
    append_thought,
    init_project,
    main,
    new_experiment,
    new_quality_review,
    new_study,
    project_context,
    project_status,
    register_artifact,
    set_current_step,
    validate_project,
    write_handoff,
)


class DataScienceKitCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "project"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_init_installs_agent_independent_state_and_codex_skills(self) -> None:
        written = init_project(self.root)

        self.assertTrue((self.root / ".dskit/config.json").is_file())
        self.assertTrue((self.root / ".git").is_dir())
        self.assertTrue((self.root / ".dskit/AGENT_GUIDE.md").is_file())
        self.assertTrue((self.root / ".dskit/memory/principles.md").is_file())
        self.assertTrue((self.root / ".dskit/memory/code-quality.md").is_file())
        self.assertTrue((self.root / ".dskit/quality/ruff.toml").is_file())
        self.assertTrue((self.root / ".dskit/logs/project.md").is_file())
        self.assertTrue((self.root / ".dskit/thoughts/backlog.md").is_file())
        skills = sorted((self.root / ".agents/skills").glob("dskit-*/SKILL.md"))
        self.assertEqual(11, len(skills))
        self.assertTrue((self.root / ".agents/skills/dskit-setup-the-dir/SKILL.md").is_file())
        event = json.loads((self.root / ".dskit/logs/machine.jsonl").read_text().splitlines()[0])
        self.assertEqual("project_initialized", event["event"])
        self.assertTrue(project_status(self.root)["version_control"]["repository"])
        self.assertGreaterEqual(len(written), 17)

    def test_init_preflights_conflicts_without_partial_overwrite(self) -> None:
        conflict = self.root / ".agents/skills/dskit-understand/SKILL.md"
        conflict.parent.mkdir(parents=True)
        conflict.write_text("mine\n", encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "managed files already exist"):
            init_project(self.root)

        self.assertEqual("mine\n", conflict.read_text(encoding="utf-8"))
        self.assertFalse((self.root / ".dskit/config.json").exists())
        self.assertFalse((self.root / ".git").exists())

    def test_new_study_creates_all_ten_ibm_artifacts_and_sets_active(self) -> None:
        init_project(self.root)
        study = new_study(self.root, "Customer Churn")

        self.assertEqual("001-customer-churn", study.name)
        self.assertTrue((study / "history/001-01-business-understanding.md").is_file())
        self.assertEqual(1, len(list((study / "history").glob("*.md"))))
        self.assertEqual(1, project_status(self.root)["current_step"]["number"])
        for relative in STUDY_SUPPORT_FILES:
            self.assertTrue((study / relative).is_file())
        first = study / "history/001-01-business-understanding.md"
        self.assertIn("Customer Churn", first.read_text(encoding="utf-8"))
        status = project_status(self.root)
        self.assertEqual(".dskit/studies/001-customer-churn", status["active_study"])
        self.assertEqual("Business Understanding", status["next_stage"]["name"])

    def test_project_template_override_applies_to_future_studies(self) -> None:
        init_project(self.root)
        override = self.root / ".dskit/templates/01-business-understanding.md"
        override.write_text("# {{STUDY_TITLE}} custom\n", encoding="utf-8")

        study = new_study(self.root, "Forecast Demand")

        self.assertIn(
            "# Forecast Demand custom\n",
            override.parent.parent.joinpath(
                "studies", study.name, "history", "001-01-business-understanding.md"
            ).read_text(),
        )

    def test_status_json_works_from_nested_directory(self) -> None:
        init_project(self.root)
        new_study(self.root, "Fraud Risk")
        nested = self.root / "analysis/deep"
        nested.mkdir(parents=True)
        output = io.StringIO()

        previous = Path.cwd()
        try:
            os.chdir(nested)
            with contextlib.redirect_stdout(output):
                exit_code = main(["status", "--json"])
        finally:
            os.chdir(previous)

        self.assertEqual(0, exit_code)
        payload = json.loads(output.getvalue())
        self.assertEqual(str(self.root.resolve()), payload["project_root"])
        self.assertIn("01-business-understanding.md", payload["artifacts"])
        self.assertTrue(payload["version_control"]["repository"])
        self.assertEqual(0, payload["continuity"]["experiment_count"])
        self.assertIn("HANDOFF.md", payload["continuity"]["handoff"])

    def test_status_is_read_only_for_a_clean_git_repository(self) -> None:
        init_project(self.root)
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.name", "Test Agent"], check=True
        )
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.email", "agent@example.invalid"],
            check=True,
        )
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), "commit", "-m", "Initialize study workflow"],
            check=True,
            capture_output=True,
        )

        self.assertFalse(project_status(self.root)["version_control"]["dirty"])
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["status", "--json"]))
        finally:
            os.chdir(previous)
        self.assertFalse(project_status(self.root)["version_control"]["dirty"])

    def test_validate_rejects_project_without_git_repository(self) -> None:
        init_project(self.root)
        (self.root / ".git").rename(self.root / ".git-disabled")

        self.assertIn("Git version control is required", validate_project(self.root))

    def test_logs_thoughts_and_context_are_durable(self) -> None:
        init_project(self.root)
        new_study(self.root, "Retention")
        append_project_log(
            self.root, "Outcome definition approved", "decision", "Business Understanding"
        )
        thought_id = append_thought(self.root, "Consider survival analysis")

        context = project_context(self.root)
        project_log = (self.root / ".dskit/logs/project.md").read_text()
        thoughts = (self.root / ".dskit/thoughts/backlog.md").read_text()
        machine_events = [
            json.loads(line)["event"]
            for line in (self.root / ".dskit/logs/machine.jsonl").read_text().splitlines()
        ]

        self.assertIn("Outcome definition approved", project_log)
        self.assertIn(thought_id, thoughts)
        self.assertIn("Consider survival analysis", thoughts)
        self.assertIn("project_log_appended", machine_events)
        self.assertIn("thought_captured", machine_events)
        self.assertEqual(["001-retention"], context["studies"])
        self.assertTrue(
            any("Outcome definition approved" in line for line in context["recent_project_log"])
        )
        self.assertIn("Exact next action", context["handoff_snapshot"])

    def test_experiment_artifact_and_handoff_are_durable_and_numbered(self) -> None:
        init_project(self.root)
        study = new_study(self.root, "Retention")

        first = new_experiment(self.root, "Frozen-split baseline")
        second = new_experiment(self.root, "Temporal robustness")
        artifact_id = register_artifact(
            self.root,
            "results/baseline.parquet",
            "prepared-data",
            "raw/snapshot-v3",
            "sha256:abc123",
        )
        handoff = write_handoff(
            self.root,
            "Two experiments planned.",
            "Complete EXP-001.",
            "Outcome labels pending.",
        )

        self.assertEqual("EXP-001.md", first.name)
        self.assertEqual("EXP-002.md", second.name)
        registry = (study / "experiments/registry.md").read_text()
        self.assertIn("EXP-001", registry)
        self.assertIn("EXP-002", registry)
        self.assertEqual("ART-001", artifact_id)
        self.assertIn("sha256:abc123", (study / "artifacts/manifest.md").read_text())
        self.assertIn("Complete EXP-001.", handoff.read_text())
        status = project_status(self.root)
        self.assertEqual(2, status["continuity"]["experiment_count"])
        self.assertEqual(1, status["continuity"]["registered_artifact_count"])

    def test_quality_review_is_timestamped_tracked_and_uses_scope(self) -> None:
        init_project(self.root)
        report = new_quality_review(self.root, "notebooks/")

        self.assertTrue(report.is_file())
        self.assertIn("Scope: notebooks/", report.read_text())
        self.assertIn("Ruff Check", report.read_text())
        status = project_status(self.root)
        self.assertEqual([report.relative_to(self.root).as_posix()], status["quality_reviews"])
        events = [
            json.loads(line)["event"]
            for line in (self.root / ".dskit/logs/machine.jsonl").read_text().splitlines()
        ]
        self.assertIn("quality_review_created", events)

    def test_activate_switches_between_studies(self) -> None:
        init_project(self.root)
        first = new_study(self.root, "First Study")
        new_study(self.root, "Second Study")

        activated = activate_study(self.root, "001")

        self.assertEqual(first, activated)
        self.assertEqual(
            ".dskit/studies/001-first-study", project_status(self.root)["active_study"]
        )

    def test_force_reinitialization_preserves_logs_and_thoughts(self) -> None:
        init_project(self.root)
        study = new_study(self.root, "Persistent Study")
        principles = self.root / ".dskit/memory/principles.md"
        principles.write_text("# Custom principles\n")
        append_project_log(self.root, "Keep this decision", "decision")
        thought_id = append_thought(self.root, "Keep this thought")

        init_project(self.root, force=True)

        self.assertIn("Keep this decision", (self.root / ".dskit/logs/project.md").read_text())
        self.assertIn(thought_id, (self.root / ".dskit/thoughts/backlog.md").read_text())
        self.assertEqual("# Custom principles\n", principles.read_text())
        self.assertEqual(
            study.relative_to(self.root).as_posix(), project_status(self.root)["active_study"]
        )

    def test_force_reinitialization_backfills_missing_continuity_without_overwrite(self) -> None:
        init_project(self.root)
        study = new_study(self.root, "Legacy Study")
        business = study / "history/001-01-business-understanding.md"
        business.write_text("# Preserved evidence\n", encoding="utf-8")
        legacy_business = study / "01-business-understanding/README.md"
        legacy_business.parent.mkdir(parents=True)
        business.rename(legacy_business)
        for relative in STUDY_SUPPORT_FILES:
            (study / relative).unlink()
        (study / "experiments/EXPERIMENT-TEMPLATE.md").unlink()

        init_project(self.root, force=True)

        self.assertFalse(legacy_business.exists())
        self.assertEqual("# Preserved evidence\n", business.read_text())
        for relative in STUDY_SUPPORT_FILES:
            self.assertTrue((study / relative).is_file())
        self.assertTrue((study / "experiments/EXPERIMENT-TEMPLATE.md").is_file())

    def test_validate_reports_incomplete_then_passes_when_placeholders_removed(self) -> None:
        init_project(self.root)
        study = new_study(self.root, "Retention")
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(1, main(["validate"]))

            principles = self.root / ".dskit/memory/principles.md"
            principles.write_text(principles.read_text().replace("[TODO]", "Defined"))
            for number in range(2, 11):
                set_current_step(self.root, number, f"Advance to step {number} for validation.")
            for name in ARTIFACTS:
                path = Path(project_status(self.root)["artifacts"][name]["path"])
                path.write_text(path.read_text().replace("[TODO", "[DONE"))

            plan = study / "work/plan.md"
            plan.write_text(
                plan.read_text().replace("| Ready |", "| Done |").replace("[TODO]", "Evidence"),
                encoding="utf-8",
            )
            checks = study / "work/checks.md"
            checks.write_text(
                checks.read_text().replace("Pending", "Passed").replace("[TODO]", "IBM artifact"),
                encoding="utf-8",
            )
            experiment = new_experiment(self.root, "Baseline")
            experiment.write_text(
                experiment.read_text()
                .replace("- Status: Planned", "- Status: Completed")
                .replace("[TODO]", "Recorded evidence")
            )
            registry = study / "experiments/registry.md"
            registry.write_text(
                registry.read_text()
                .replace("| Planned |", "| Completed |")
                .replace("[TODO]", "Primary measure")
                .replace("| Not run |", "| Passed baseline |")
            )
            evaluation = Path(project_status(self.root)["artifacts"]["08-evaluation.md"]["path"])
            evaluation.write_text(evaluation.read_text() + "\nExperiment evidence: EXP-001\n")
            register_artifact(
                self.root,
                "results/evaluation.json",
                "evaluation",
                "EXP-001",
                "sha256:def456",
            )
            write_handoff(self.root, "Study evidence complete.", "Review feedback outcomes.")

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["validate"]))
        finally:
            os.chdir(previous)

    def test_step_records_a_numbered_iteration_and_can_revisit_understanding(self) -> None:
        init_project(self.root)
        study = new_study(self.root, "Modeling Revision")

        forward = set_current_step(self.root, 7, "Prepared data supports modeling.")
        backward = set_current_step(
            self.root,
            1,
            "Modeling showed the business problem cannot be modeled as framed.",
        )

        self.assertEqual(1, forward["iteration"])
        self.assertEqual(2, backward["iteration"])
        status = project_status(self.root)
        self.assertEqual(1, status["current_step"]["number"])
        self.assertEqual(2, status["current_step"]["iteration"])
        history = sorted((study / "history").glob("*.md"))
        self.assertEqual(
            [
                "001-01-business-understanding.md",
                "002-07-modeling.md",
                "003-01-business-understanding.md",
            ],
            [path.name for path in history],
        )
        self.assertIn("cannot be modeled as framed", history[-1].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
