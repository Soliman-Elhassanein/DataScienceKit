from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from datasciencekit.cli import (
    ARTIFACTS,
    activate_study,
    append_project_log,
    append_thought,
    init_project,
    main,
    new_quality_review,
    new_study,
    project_context,
    project_status,
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
        self.assertTrue((self.root / ".dskit/AGENT_GUIDE.md").is_file())
        self.assertTrue((self.root / ".dskit/memory/principles.md").is_file())
        self.assertTrue((self.root / ".dskit/logs/project.md").is_file())
        self.assertTrue((self.root / ".dskit/thoughts/backlog.md").is_file())
        skills = sorted((self.root / ".agents/skills").glob("dskit-*/SKILL.md"))
        self.assertEqual(9, len(skills))
        event = json.loads((self.root / ".dskit/logs/machine.jsonl").read_text().splitlines()[0])
        self.assertEqual("project_initialized", event["event"])
        self.assertGreaterEqual(len(written), 15)

    def test_init_preflights_conflicts_without_partial_overwrite(self) -> None:
        conflict = self.root / ".agents/skills/dskit-understand/SKILL.md"
        conflict.parent.mkdir(parents=True)
        conflict.write_text("mine\n", encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "managed files already exist"):
            init_project(self.root)

        self.assertEqual("mine\n", conflict.read_text(encoding="utf-8"))
        self.assertFalse((self.root / ".dskit/config.json").exists())

    def test_new_study_creates_all_ten_ibm_artifacts_and_sets_active(self) -> None:
        init_project(self.root)
        study = new_study(self.root, "Customer Churn")

        self.assertEqual("001-customer-churn", study.name)
        self.assertEqual(set(ARTIFACTS), {path.name for path in study.iterdir()})
        first = study / "01-business-understanding.md"
        self.assertIn("Customer Churn", first.read_text(encoding="utf-8"))
        status = project_status(self.root)
        self.assertEqual(".dskit/studies/001-customer-churn", status["active_study"])
        self.assertEqual("Business Understanding", status["next_stage"]["name"])

    def test_project_template_override_applies_to_future_studies(self) -> None:
        init_project(self.root)
        override = self.root / ".dskit/templates/01-business-understanding.md"
        override.write_text("# {{STUDY_TITLE}} custom\n", encoding="utf-8")

        study = new_study(self.root, "Forecast Demand")

        self.assertEqual("# Forecast Demand custom\n", override.parent.parent.joinpath("studies", study.name, override.name).read_text())

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

    def test_logs_thoughts_and_context_are_durable(self) -> None:
        init_project(self.root)
        new_study(self.root, "Retention")
        append_project_log(self.root, "Outcome definition approved", "decision", "Business Understanding")
        thought_id = append_thought(self.root, "Consider survival analysis")

        context = project_context(self.root)
        project_log = (self.root / ".dskit/logs/project.md").read_text()
        thoughts = (self.root / ".dskit/thoughts/backlog.md").read_text()
        machine_events = [json.loads(line)["event"] for line in (self.root / ".dskit/logs/machine.jsonl").read_text().splitlines()]

        self.assertIn("Outcome definition approved", project_log)
        self.assertIn(thought_id, thoughts)
        self.assertIn("Consider survival analysis", thoughts)
        self.assertIn("project_log_appended", machine_events)
        self.assertIn("thought_captured", machine_events)
        self.assertEqual(["001-retention"], context["studies"])
        self.assertTrue(any("Outcome definition approved" in line for line in context["recent_project_log"]))

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
        self.assertEqual(".dskit/studies/001-first-study", project_status(self.root)["active_study"])

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
        self.assertEqual(study.relative_to(self.root).as_posix(), project_status(self.root)["active_study"])

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
            for name in ARTIFACTS:
                path = study / name
                path.write_text(path.read_text().replace("[TODO", "[DONE"))

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["validate"]))
        finally:
            os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
