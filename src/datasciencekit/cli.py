"""Command-line interface for initializing and inspecting DataScienceKit projects."""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import shutil
import subprocess
import sys
import uuid
from collections.abc import Iterable
from datetime import datetime, timezone
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

from datasciencekit import __version__

MANAGED_DIR = ".dskit"
ARTIFACTS = (
    "01-business-understanding.md",
    "02-analytic-approach.md",
    "03-data-requirements.md",
    "04-data-collection.md",
    "05-data-understanding.md",
    "06-data-preparation.md",
    "07-modeling.md",
    "08-evaluation.md",
    "09-deployment.md",
    "10-feedback.md",
)

STUDY_SUPPORT_FILES = (
    "HANDOFF.md",
    "work/plan.md",
    "work/checks.md",
    "experiments/registry.md",
    "artifacts/manifest.md",
)

REQUIRED_CHECKS = {
    "CHK-001": "Business success threshold declared",
    "CHK-002": "Data snapshot fingerprint recorded",
    "CHK-003": "Leakage audit completed",
    "CHK-004": "Baseline evaluated",
    "CHK-005": "Uncertainty reported",
    "CHK-006": "Evaluation links experiment IDs",
    "CHK-007": "Deployment owner named",
    "CHK-008": "Feedback plan defined",
}

STAGE_NAMES = {
    artifact: name
    for artifact, name in zip(
        ARTIFACTS,
        (
            "Business Understanding",
            "Analytic Approach",
            "Data Requirements",
            "Data Collection",
            "Data Understanding",
            "Data Preparation",
            "Modeling",
            "Evaluation",
            "Deployment",
            "Feedback",
        ),
        strict=True,
    )
}


class DskitError(RuntimeError):
    """A user-facing CLI error."""


def _resource_path(*parts: str):
    return files("datasciencekit").joinpath("resources", *parts)


def _stage_number(artifact: str) -> int:
    return int(Path(artifact).stem.split("-", 1)[0])


def _stage_artifact(number: int) -> str:
    if number < 1 or number > len(ARTIFACTS):
        raise DskitError("step must be an integer from 1 through 10")
    try:
        return ARTIFACTS[number - 1]
    except IndexError as exc:
        raise DskitError("step must be an integer from 1 through 10") from exc


def _stage_label(artifact: str) -> str:
    return f"{_stage_number(artifact):02d} — {STAGE_NAMES[artifact]}"


def _study_state(study: Path) -> dict[str, Any]:
    path = study / "STATE.json"
    if not path.is_file():
        return {"current_step": 1, "iteration": 1}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DskitError(f"cannot read study state: {exc}") from exc


def _history_entries(study: Path) -> list[tuple[int, str, Path]]:
    history = study / "history"
    if not history.is_dir():
        return []
    entries: list[tuple[int, str, Path]] = []
    for path in history.glob("*.md"):
        match = re.fullmatch(r"(\d{3})-(\d{2}-.+\.md)", path.name)
        if match and match.group(2) in ARTIFACTS:
            entries.append((int(match.group(1)), match.group(2), path))
    return sorted(entries)


def _create_history_entry(root: Path, study: Path, artifact: str, reason: str) -> Path:
    entries = _history_entries(study)
    sequence = max((entry[0] for entry in entries), default=0) + 1
    title = _study_state(study).get("title") or study.name
    overrides = root / MANAGED_DIR / "templates"
    source = (
        overrides / artifact
        if (overrides / artifact).is_file()
        else _resource_path("study", artifact)
    )
    with as_file(source) as source_path:
        template = source_path.read_text(encoding="utf-8")
    content = template.replace("{{STUDY_TITLE}}", str(title))
    metadata = (
        f"<!-- History entry: {sequence:03d}; IBM step: {_stage_number(artifact):02d}; "
        f"Created: {_utc_now()}; Reason: {_safe_cell(reason)} -->\n\n"
    )
    destination = study / "history" / f"{sequence:03d}-{artifact}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(metadata + content, encoding="utf-8")
    return destination


def _resource_conflicts(source_parts: tuple[str, ...], destination: Path) -> list[Path]:
    source = _resource_path(*source_parts)
    with as_file(source) as source_path:
        return [
            destination / item.relative_to(source_path)
            for item in sorted(source_path.rglob("*"))
            if item.is_file() and (destination / item.relative_to(source_path)).exists()
        ]


def _copy_resource_tree(
    source_parts: tuple[str, ...], destination: Path, force: bool
) -> list[Path]:
    written: list[Path] = []
    source = _resource_path(*source_parts)
    with as_file(source) as source_path:
        items = [item for item in sorted(source_path.rglob("*")) if item.is_file()]
        conflicts = [destination / item.relative_to(source_path) for item in items]
        conflicts = [target for target in conflicts if target.exists()]
        if conflicts and not force:
            rendered = "\n".join(f"- {target}" for target in conflicts)
            raise DskitError(f"managed files already exist:\n{rendered}")
        for item in items:
            relative = item.relative_to(source_path)
            target = destination / relative
            durable_state = relative.parts[:2] in {
                (".dskit", "logs"),
                (".dskit", "memory"),
                (".dskit", "quality"),
                (".dskit", "templates"),
                (".dskit", "thoughts"),
            }
            if force and target.exists() and durable_state:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, target)
            written.append(target)
    return written


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _append_machine_event(root: Path, event: str, **details: Any) -> None:
    config_path = root / MANAGED_DIR / "config.json"
    active_study = None
    if config_path.is_file():
        with contextlib.suppress(OSError, json.JSONDecodeError):
            active_study = json.loads(config_path.read_text(encoding="utf-8")).get("active_study")
    payload = {
        "timestamp": _utc_now(),
        "event": event,
        "tool_version": __version__,
        "active_study": active_study,
        "details": details,
    }
    path = root / MANAGED_DIR / "logs" / "machine.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, sort_keys=True) + "\n")


def append_project_log(root: Path, message: str, kind: str, stage: str | None = None) -> None:
    config = _load_config(root)
    path = root / MANAGED_DIR / "logs" / "project.md"
    label = f" — {stage}" if stage else ""
    entry = (
        f"\n## {_utc_now()} — {kind}{label}\n\n"
        f"- Study: `{config.get('active_study') or 'project-wide'}`\n"
        f"- Note: {message.strip()}\n"
    )
    with path.open("a", encoding="utf-8") as stream:
        stream.write(entry)
    _append_machine_event(root, "project_log_appended", kind=kind, stage=stage)


def append_thought(root: Path, thought: str) -> str:
    config = _load_config(root)
    thought_id = f"TH-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:6]}"
    path = root / MANAGED_DIR / "thoughts" / "backlog.md"
    entry = (
        f"\n## {thought_id} — Proposed\n\n"
        f"- Captured: {_utc_now()}\n"
        f"- Study: `{config.get('active_study') or 'project-wide'}`\n"
        f"- Thought: {thought.strip()}\n"
        "- Evidence needed: Not assessed\n"
        "- Decision: Not evaluated\n"
    )
    with path.open("a", encoding="utf-8") as stream:
        stream.write(entry)
    _append_machine_event(root, "thought_captured", thought_id=thought_id)
    return thought_id


def new_quality_review(root: Path, scope: str = "Entire data-science project") -> Path:
    created_at = _utc_now()
    review_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:6]}"
    reviews = root / MANAGED_DIR / "quality"
    reviews.mkdir(parents=True, exist_ok=True)
    destination = reviews / f"{review_id}-code-quality.md"
    override = root / MANAGED_DIR / "templates" / "code-quality.md"
    source = override if override.is_file() else _resource_path("quality", "code-quality.md")
    with as_file(source) as source_path:
        content = source_path.read_text(encoding="utf-8")
    content = content.replace("{{SCOPE}}", scope.strip()).replace("{{CREATED_AT}}", created_at)
    destination.write_text(content, encoding="utf-8")
    _append_machine_event(
        root,
        "quality_review_created",
        scope=scope.strip(),
        report=destination.relative_to(root).as_posix(),
    )
    return destination


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / MANAGED_DIR / "config.json").is_file():
            return candidate
    raise DskitError("not inside a DataScienceKit project; run `dskit init` first")


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def ensure_git_repository(root: Path) -> Path:
    if shutil.which("git") is None:
        raise DskitError("Git is required for every DataScienceKit project but was not found")
    existing = _run_git(root, "rev-parse", "--show-toplevel")
    if existing.returncode == 0:
        return Path(existing.stdout.strip()).resolve()
    initialized = _run_git(root, "init", "-b", "main")
    if initialized.returncode != 0:
        detail = initialized.stderr.strip() or initialized.stdout.strip()
        raise DskitError(f"could not initialize Git version control: {detail}")
    return root.resolve()


def version_control_status(root: Path) -> dict[str, Any]:
    if shutil.which("git") is None:
        return {"system": "git", "available": False, "repository": False}
    repository = _run_git(root, "rev-parse", "--show-toplevel")
    if repository.returncode != 0:
        return {"system": "git", "available": True, "repository": False}
    branch = _run_git(root, "branch", "--show-current")
    changes = _run_git(root, "status", "--short")
    return {
        "system": "git",
        "available": True,
        "repository": True,
        "root": str(Path(repository.stdout.strip()).resolve()),
        "branch": branch.stdout.strip() or None,
        "dirty": bool(changes.stdout.strip()),
        "change_count": len(changes.stdout.splitlines()),
    }


def init_project(target: Path, force: bool = False) -> list[Path]:
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    config_path = target / MANAGED_DIR / "config.json"
    if config_path.exists() and not force:
        raise DskitError(f"DataScienceKit is already initialized at {target}")

    if not force:
        conflicts = _resource_conflicts(("project",), target)
        if conflicts:
            rendered = "\n".join(f"- {path}" for path in conflicts)
            raise DskitError(f"managed files already exist:\n{rendered}")

    git_root = ensure_git_repository(target)

    previous_config: dict[str, Any] = {}
    if config_path.exists() and force:
        previous_config = _load_config(target)

    written = _copy_resource_tree(("project",), target, force)
    if force:
        written.extend(_install_missing_study_support(target))
    _write_json(
        config_path,
        {
            "schema_version": 4,
            "tool_version": __version__,
            "active_study": previous_config.get("active_study"),
            "methodology": "IBM Data Science Methodology",
            "version_control": "git",
        },
    )
    if config_path not in written:
        written.append(config_path)
    machine_log = target / MANAGED_DIR / "logs" / "machine.jsonl"
    _append_machine_event(target, "project_initialized", force=force, git_root=str(git_root))
    if machine_log not in written:
        written.append(machine_log)
    return written


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:60].rstrip("-") or "study"


def _load_config(root: Path) -> dict[str, Any]:
    try:
        return json.loads((root / MANAGED_DIR / "config.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DskitError(f"cannot read {MANAGED_DIR}/config.json: {exc}") from exc


def _active_study(root: Path) -> Path:
    active = _load_config(root).get("active_study")
    if not active:
        raise DskitError('no active study; run `dskit new "STUDY TITLE"`')
    study = root / active
    if not study.is_dir():
        raise DskitError(f"active study does not exist: {active}")
    return study


def _markdown_rows(path: Path) -> list[list[str]]:
    if not path.is_file():
        return []
    rows: list[list[str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or re.match(r"^\|[-:| ]+\|$", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells and cells[0] not in {"ID", "[TODO]"}:
            rows.append(cells)
    return rows


def _safe_cell(value: str) -> str:
    return " ".join(value.strip().replace("|", "/").splitlines())


def _replace_placeholder_row(path: Path, row: str) -> None:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    replaced = False
    output: list[str] = []
    for line in lines:
        if not replaced and line.startswith("| [TODO]"):
            output.append(row)
            replaced = True
        else:
            output.append(line)
    if not replaced:
        output.append(row)
    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def _install_missing_study_support(root: Path) -> list[Path]:
    studies = root / MANAGED_DIR / "studies"
    if not studies.is_dir():
        return []
    installed: list[Path] = []
    relative_files = (*STUDY_SUPPORT_FILES, "experiments/EXPERIMENT-TEMPLATE.md")
    for study in sorted(path for path in studies.iterdir() if path.is_dir()):
        title = re.sub(r"^\d{3}-", "", study.name).replace("-", " ").title()
        if not _history_entries(study):
            for sequence, artifact in enumerate(ARTIFACTS, start=1):
                folder_source = study / Path(artifact).stem / "README.md"
                flat_source = study / artifact
                source = folder_source if folder_source.is_file() else flat_source
                if not source.is_file():
                    continue
                destination = study / "history" / f"{sequence:03d}-{artifact}"
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(destination))
                installed.append(destination)
            if not _history_entries(study):
                state = _study_state(study)
                first = _create_history_entry(root, study, ARTIFACTS[0], "Imported existing study.")
                state["current_entry"] = first.relative_to(study).as_posix()
                state.setdefault("current_step", 1)
                state.setdefault("iteration", 1)
                state.setdefault("title", title)
                _write_json(study / "STATE.json", state)
                installed.append(first)
            else:
                state = _study_state(study)
                current_number = int(state.get("current_step", 1))
                current_artifact = _stage_artifact(current_number)
                entries = _history_entries(study)
                matching = [path for _, artifact, path in entries if artifact == current_artifact]
                current = matching[-1] if matching else entries[-1][2]
                state.update(
                    {
                        "title": state.get("title", title),
                        "current_step": _stage_number(current.name.split("-", 1)[1]),
                        "iteration": int(state.get("iteration", 1)),
                        "current_entry": current.relative_to(study).as_posix(),
                    }
                )
                _write_json(study / "STATE.json", state)
        for relative in relative_files:
            destination = study / relative
            if destination.exists():
                continue
            source = _resource_path("study", *Path(relative).parts)
            with as_file(source) as source_path:
                content = source_path.read_text(encoding="utf-8")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content.replace("{{STUDY_TITLE}}", title), encoding="utf-8")
            installed.append(destination)
        state = study / "STATE.json"
        if not state.exists():
            entries = _history_entries(study)
            first = (
                entries[-1][2]
                if entries
                else _create_history_entry(root, study, ARTIFACTS[0], "Imported existing study.")
            )
            _write_json(
                state,
                {
                    "title": title,
                    "current_step": _stage_number(first.name.split("-", 1)[1]),
                    "iteration": 1,
                    "current_entry": first.relative_to(study).as_posix(),
                },
            )
            installed.append(state)
    return installed


def new_study(root: Path, title: str) -> Path:
    studies = root / MANAGED_DIR / "studies"
    studies.mkdir(parents=True, exist_ok=True)
    existing_numbers = []
    for path in studies.iterdir():
        match = re.match(r"^(\d{3})-", path.name)
        if path.is_dir() and match:
            existing_numbers.append(int(match.group(1)))
    number = max(existing_numbers, default=0) + 1
    study = studies / f"{number:03d}-{_slugify(title)}"
    if study.exists():
        raise DskitError(f"study already exists: {study}")
    study.mkdir()

    template_root = _resource_path("study")
    overrides = root / MANAGED_DIR / "templates"
    with as_file(template_root) as source_path:
        relative_files = [
            path.relative_to(source_path)
            for path in source_path.rglob("*")
            if path.is_file() and not re.fullmatch(r"\d{2}-.+\.md", path.name)
        ]
        for relative in relative_files:
            source = (
                overrides / relative if (overrides / relative).is_file() else source_path / relative
            )
            content = source.read_text(encoding="utf-8")
            content = content.replace("{{STUDY_TITLE}}", title.strip())
            destination = study / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")

    _write_json(study / "STATE.json", {"title": title.strip(), "current_step": 1, "iteration": 1})
    first = _create_history_entry(root, study, ARTIFACTS[0], "Study created.")
    state = _study_state(study)
    state["current_entry"] = first.relative_to(study).as_posix()
    _write_json(study / "STATE.json", state)

    config = _load_config(root)
    config["active_study"] = study.relative_to(root).as_posix()
    _write_json(root / MANAGED_DIR / "config.json", config)
    _append_machine_event(
        root, "study_created", title=title.strip(), study=study.relative_to(root).as_posix()
    )
    append_project_log(root, f"Created and activated study: {title.strip()}", "study")
    return study


def new_experiment(root: Path, title: str) -> Path:
    if not title.strip():
        raise DskitError("experiment title cannot be empty")
    study = _active_study(root)
    experiments = study / "experiments"
    experiments.mkdir(parents=True, exist_ok=True)
    numbers = [
        int(match.group(1))
        for path in experiments.glob("EXP-*.md")
        if (match := re.match(r"EXP-(\d{3})\.md$", path.name))
    ]
    experiment_id = f"EXP-{max(numbers, default=0) + 1:03d}"
    destination = experiments / f"{experiment_id}.md"
    template = experiments / "EXPERIMENT-TEMPLATE.md"
    if not template.is_file():
        template = _resource_path("study", "experiments", "EXPERIMENT-TEMPLATE.md")
    with as_file(template) as source_path:
        content = source_path.read_text(encoding="utf-8")
    content = (
        content.replace("{{EXPERIMENT_ID}}", experiment_id)
        .replace("{{EXPERIMENT_TITLE}}", title.strip())
        .replace("{{CREATED_AT}}", _utc_now())
    )
    destination.write_text(content, encoding="utf-8")
    registry = experiments / "registry.md"
    if not registry.is_file():
        raise DskitError(f"missing experiment registry: {registry.relative_to(root)}")
    row = (
        f"| {experiment_id} | Planned | {_safe_cell(title)} | [TODO] | Not run | "
        f"[{experiment_id}.md]({experiment_id}.md) |"
    )
    _replace_placeholder_row(registry, row)
    _append_machine_event(
        root,
        "experiment_created",
        experiment_id=experiment_id,
        record=destination.relative_to(root).as_posix(),
    )
    return destination


def register_artifact(
    root: Path,
    path_or_uri: str,
    kind: str,
    source: str,
    fingerprint: str,
    notes: str = "—",
) -> str:
    required = {
        "path or URI": path_or_uri,
        "kind": kind,
        "source": source,
        "fingerprint": fingerprint,
    }
    if missing := [name for name, value in required.items() if not value.strip()]:
        raise DskitError(f"artifact fields cannot be empty: {', '.join(missing)}")
    study = _active_study(root)
    manifest = study / "artifacts" / "manifest.md"
    if not manifest.is_file():
        raise DskitError(f"missing artifact manifest: {manifest.relative_to(root)}")
    numbers = [
        int(row[0].split("-")[1])
        for row in _markdown_rows(manifest)
        if row and re.fullmatch(r"ART-\d{3}", row[0])
    ]
    artifact_id = f"ART-{max(numbers, default=0) + 1:03d}"
    values = (
        artifact_id,
        _safe_cell(kind),
        _safe_cell(path_or_uri),
        _safe_cell(fingerprint),
        _safe_cell(source),
        _utc_now(),
        _safe_cell(notes),
    )
    row = f"| {' | '.join(values)} |"
    _replace_placeholder_row(manifest, row)
    _append_machine_event(
        root,
        "artifact_registered",
        artifact_id=artifact_id,
        path_or_uri=path_or_uri,
        fingerprint=fingerprint,
    )
    return artifact_id


def write_handoff(root: Path, summary: str, next_action: str, blockers: str = "None known") -> Path:
    if not summary.strip() or not next_action.strip():
        raise DskitError("handoff summary and next action cannot be empty")
    study = _active_study(root)
    status = project_status(root)
    git = status["version_control"]
    revision = _run_git(root, "rev-parse", "HEAD")
    commit = revision.stdout.strip() if revision.returncode == 0 else "unborn branch"
    next_stage = status["next_stage"]["name"] if status["next_stage"] else "Feedback complete"
    current_stage = status["current_step"]["label"]
    continuity = status.get("continuity", {})
    recent_experiment = continuity.get("latest_experiment") or "None recorded"
    content = f"""# Handoff — {study.name}

- Updated: {_utc_now()}
- Git base commit: {commit}
- Git branch: {git.get("branch") or "unborn branch"}
- Working tree at handoff: {"dirty" if git.get("dirty") else "clean"}
- Current IBM stage: {current_stage}
- Next IBM stage: {next_stage}

## Current state

{summary.strip()}

## Decisions and evidence

See the numbered IBM artifacts, experiment records, evidence gates, and artifact manifest.

## Blockers and unknowns

{blockers.strip()}

## Open work and checks

- Open work items: {continuity.get("open_work", 0)}
- Unpassed evidence gates: {continuity.get("open_checks", len(REQUIRED_CHECKS))}

## Most recent experiment

{recent_experiment}

## Exact next action

{next_action.strip()}
"""
    destination = study / "HANDOFF.md"
    destination.write_text(content, encoding="utf-8")
    _append_machine_event(root, "handoff_written", handoff=destination.relative_to(root).as_posix())
    append_project_log(root, summary.strip(), "handoff", current_stage)
    return destination


def set_current_step(root: Path, number: int, reason: str) -> dict[str, Any]:
    if not reason.strip():
        raise DskitError("a reason is required for every step transition")
    artifact = _stage_artifact(number)
    study = _active_study(root)
    state = _study_state(study)
    previous = int(state.get("current_step", 1))
    iteration = int(state.get("iteration", 1)) + (number < previous)
    entry = _create_history_entry(root, study, artifact, reason)
    state.update(
        {
            "current_step": number,
            "iteration": iteration,
            "current_entry": entry.relative_to(study).as_posix(),
            "updated_at": _utc_now(),
        }
    )
    _write_json(study / "STATE.json", state)
    _append_machine_event(
        root,
        "step_changed",
        history_entry=entry.relative_to(study).as_posix(),
        from_step=previous,
        to_step=number,
        reason=reason.strip(),
    )
    append_project_log(root, reason.strip(), "iteration", _stage_label(artifact))
    return {"step": number, "label": _stage_label(artifact), "iteration": iteration}


def activate_study(root: Path, study_name: str) -> Path:
    studies = root / MANAGED_DIR / "studies"
    candidates = [path for path in studies.iterdir() if path.is_dir()] if studies.is_dir() else []
    matches = [
        path for path in candidates if path.name == study_name or path.name.startswith(study_name)
    ]
    if not matches:
        raise DskitError(f"study not found: {study_name}")
    if len(matches) > 1:
        raise DskitError(f"study name is ambiguous: {study_name}")
    study = matches[0]
    config = _load_config(root)
    config["active_study"] = study.relative_to(root).as_posix()
    _write_json(root / MANAGED_DIR / "config.json", config)
    _append_machine_event(root, "study_activated", study=study.relative_to(root).as_posix())
    return study


def _todo_count(path: Path) -> int:
    if not path.is_file():
        return -1
    return path.read_text(encoding="utf-8").count("[TODO")


def project_status(root: Path) -> dict[str, Any]:
    config = _load_config(root)
    principles = root / MANAGED_DIR / "memory" / "principles.md"
    result: dict[str, Any] = {
        "project_root": str(root),
        "tool_version": config.get("tool_version"),
        "principles": {
            "path": str(principles),
            "complete": _todo_count(principles) == 0,
            "todo_count": _todo_count(principles),
        },
        "active_study": config.get("active_study"),
        "methodology": config.get("methodology"),
        "project_log": str(root / MANAGED_DIR / "logs" / "project.md"),
        "machine_log": str(root / MANAGED_DIR / "logs" / "machine.jsonl"),
        "thoughts": str(root / MANAGED_DIR / "thoughts" / "backlog.md"),
        "quality_reviews": [],
        "version_control": version_control_status(root),
        "artifacts": {},
        "continuity": {},
        "current_step": None,
        "next_stage": None,
    }
    active = config.get("active_study")
    if active:
        study = root / active
        state = _study_state(study)
        current_number = int(state.get("current_step", 1))
        current_artifact = _stage_artifact(current_number)
        current_path = study / state.get("current_entry", "")
        result["current_step"] = {
            "number": current_number,
            "name": STAGE_NAMES[current_artifact],
            "label": _stage_label(current_artifact),
            "path": str(current_path),
            "iteration": int(state.get("iteration", 1)),
        }
        latest = {artifact: path for _, artifact, path in _history_entries(study)}
        for artifact in ARTIFACTS:
            path = latest.get(artifact, study / "history" / artifact)
            count = _todo_count(path)
            result["artifacts"][artifact] = {
                "stage": STAGE_NAMES[artifact],
                "path": str(path),
                "complete": count == 0,
                "todo_count": count,
            }
            if result["next_stage"] is None and count != 0:
                result["next_stage"] = {
                    "name": STAGE_NAMES[artifact],
                    "artifact": artifact,
                    "path": str(path),
                }
        plan_rows = _markdown_rows(study / "work" / "plan.md")
        check_rows = _markdown_rows(study / "work" / "checks.md")
        experiment_rows = _markdown_rows(study / "experiments" / "registry.md")
        artifact_rows = _markdown_rows(study / "artifacts" / "manifest.md")
        experiment_ids = [row[0] for row in experiment_rows if re.fullmatch(r"EXP-\d{3}", row[0])]
        result["continuity"] = {
            "handoff": str(study / "HANDOFF.md"),
            "work_plan": str(study / "work" / "plan.md"),
            "checks": str(study / "work" / "checks.md"),
            "experiment_registry": str(study / "experiments" / "registry.md"),
            "artifact_manifest": str(study / "artifacts" / "manifest.md"),
            "history": str(study / "history"),
            "open_work": sum(
                len(row) > 1 and row[1].lower() not in {"done", "abandoned"} for row in plan_rows
            ),
            "open_checks": sum(
                len(row) > 2 and row[2].lower() not in {"passed", "not applicable"}
                for row in check_rows
            ),
            "experiment_count": len(experiment_ids),
            "latest_experiment": experiment_ids[-1] if experiment_ids else None,
            "registered_artifact_count": sum(
                bool(row) and re.fullmatch(r"ART-\d{3}", row[0]) is not None
                for row in artifact_rows
            ),
        }
    quality_dir = root / MANAGED_DIR / "quality"
    if quality_dir.is_dir():
        result["quality_reviews"] = [
            path.relative_to(root).as_posix()
            for path in sorted(quality_dir.glob("*-code-quality.md"))
        ]
    return result


def project_context(root: Path) -> dict[str, Any]:
    status = project_status(root)
    log_path = root / MANAGED_DIR / "logs" / "project.md"
    log_lines = log_path.read_text(encoding="utf-8").splitlines() if log_path.is_file() else []
    status["recent_project_log"] = log_lines[-24:]
    studies = root / MANAGED_DIR / "studies"
    status["studies"] = (
        sorted(path.name for path in studies.iterdir() if path.is_dir()) if studies.is_dir() else []
    )
    handoff = status.get("continuity", {}).get("handoff")
    status["handoff_snapshot"] = (
        Path(handoff).read_text(encoding="utf-8") if handoff and Path(handoff).is_file() else None
    )
    return status


def validate_project(root: Path) -> list[str]:
    status = project_status(root)
    errors: list[str] = []
    if not status["version_control"].get("repository"):
        errors.append("Git version control is required")
    if not status["principles"]["complete"]:
        errors.append("project principles are incomplete")
    if not status["active_study"]:
        errors.append("no active study")
    for name, artifact in status["artifacts"].items():
        if artifact["todo_count"] == -1:
            errors.append(f"missing artifact: {name}")
        elif not artifact["complete"]:
            errors.append(f"incomplete artifact: {name} ({artifact['todo_count']} TODOs)")
    active = status["active_study"]
    if not active:
        return errors
    study = root / active
    for relative in STUDY_SUPPORT_FILES:
        if not (study / relative).is_file():
            errors.append(f"missing continuity file: {relative}")

    plan = study / "work" / "plan.md"
    plan_rows = _markdown_rows(plan)
    if not plan_rows:
        errors.append("work plan has no durable work items")
    for row in plan_rows:
        if len(row) < 6:
            errors.append(f"malformed work-plan row: {row[0]}")
        elif row[1].lower() not in {"done", "abandoned"}:
            errors.append(f"open work item: {row[0]} ({row[1]})")
        elif "[TODO" in row[5]:
            errors.append(f"work item lacks evidence: {row[0]}")

    check_rows = {row[0]: row for row in _markdown_rows(study / "work" / "checks.md") if row}
    for check_id in REQUIRED_CHECKS:
        row = check_rows.get(check_id)
        if row is None:
            errors.append(f"missing evidence gate: {check_id}")
        elif len(row) < 4:
            errors.append(f"malformed evidence gate: {check_id}")
        elif row[2].lower() not in {"passed", "not applicable"}:
            errors.append(f"unpassed evidence gate: {check_id} ({row[2]})")
        elif not row[3] or "[TODO" in row[3]:
            errors.append(f"evidence gate lacks evidence: {check_id}")

    experiment_rows = _markdown_rows(study / "experiments" / "registry.md")
    experiment_ids = [
        row[0] for row in experiment_rows if row and re.fullmatch(r"EXP-\d{3}", row[0])
    ]
    if not experiment_ids:
        errors.append("no experiments recorded")
    for row in experiment_rows:
        if not row or not re.fullmatch(r"EXP-\d{3}", row[0]):
            continue
        experiment_id = row[0]
        if len(row) < 6:
            errors.append(f"malformed experiment registry row: {experiment_id}")
        elif row[1].lower() not in {"completed", "failed", "abandoned"}:
            errors.append(f"experiment is not finished: {experiment_id} ({row[1]})")
        elif any("[TODO" in cell for cell in row[2:]):
            errors.append(f"experiment registry row is incomplete: {experiment_id}")
        record = study / "experiments" / f"{experiment_id}.md"
        if not record.is_file():
            errors.append(f"missing experiment record: {experiment_id}")
        elif _todo_count(record) != 0:
            errors.append(f"incomplete experiment record: {experiment_id}")
    evaluation = next(
        (path for _, artifact, path in _history_entries(study) if artifact == "08-evaluation.md"),
        study / "history" / "08-evaluation.md",
    )
    evaluation_text = evaluation.read_text(encoding="utf-8") if evaluation.is_file() else ""
    if experiment_ids and not any(
        experiment_id in evaluation_text for experiment_id in experiment_ids
    ):
        errors.append("evaluation does not link a recorded experiment ID")

    manifest_rows = [
        row
        for row in _markdown_rows(study / "artifacts" / "manifest.md")
        if row and re.fullmatch(r"ART-\d{3}", row[0])
    ]
    if not manifest_rows:
        errors.append("no artifacts registered with provenance")
    for row in manifest_rows:
        if len(row) < 7 or any(not row[index] or "[TODO" in row[index] for index in (2, 3, 4)):
            errors.append(f"artifact lacks path, fingerprint, or source: {row[0]}")

    handoff = study / "HANDOFF.md"
    if handoff.is_file() and _todo_count(handoff) != 0:
        errors.append("handoff snapshot is incomplete")
    return errors


def _print_status(status: dict[str, Any]) -> None:
    principles = status["principles"]
    marker = "complete" if principles["complete"] else f"{principles['todo_count']} TODOs"
    print(f"Project: {status['project_root']}")
    print(f"Principles: {marker}")
    print(f"Active study: {status['active_study'] or 'none'}")
    version_control = status["version_control"]
    if version_control.get("repository"):
        branch = version_control.get("branch") or "unborn branch"
        state = "dirty" if version_control.get("dirty") else "clean"
        print(f"Version control: Git ({branch}, {state})")
    else:
        print("Version control: REQUIRED — Git repository not found")
    if status["current_step"]:
        current = status["current_step"]
        print(f"Current step: {current['label']} (iteration {current['iteration']})")
    if status["next_stage"]:
        print(f"Next incomplete stage: {status['next_stage']['name']}")
    continuity = status.get("continuity", {})
    if continuity:
        print(
            "Continuity: "
            f"{continuity['open_work']} open work, "
            f"{continuity['open_checks']} open gates, "
            f"{continuity['experiment_count']} experiments, "
            f"{continuity['registered_artifact_count']} registered artifacts"
        )
    for artifact in status["artifacts"].values():
        if artifact["todo_count"] == -1:
            marker = "missing"
        elif artifact["complete"]:
            marker = "complete"
        else:
            marker = f"{artifact['todo_count']} TODOs"
        print(f"  {artifact['stage']}: {marker}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dskit",
        description="Artifact-driven workflows for reproducible data science.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="initialize a project and install agent skills")
    init.add_argument("path", nargs="?", default=".")
    init.add_argument(
        "--force", action="store_true", help="replace only DataScienceKit-managed files"
    )

    new = subparsers.add_parser("new", help="create and activate a study")
    new.add_argument("title")

    activate = subparsers.add_parser("activate", help="make an existing study active")
    activate.add_argument("study")

    step = subparsers.add_parser(
        "step", help="set the active numbered IBM step and record the transition"
    )
    step.add_argument("number", type=int, choices=range(1, 11))
    step.add_argument("--reason", required=True)

    status = subparsers.add_parser("status", help="show workflow artifact status")
    status.add_argument("--json", action="store_true", dest="as_json")

    context = subparsers.add_parser(
        "context", help="show durable context for a new agent or session"
    )
    context.add_argument("--json", action="store_true", dest="as_json")

    log = subparsers.add_parser("log", help="append a human-readable project log entry")
    log.add_argument("message")
    log.add_argument(
        "--kind", default="progress", choices=("decision", "progress", "finding", "handoff")
    )
    log.add_argument("--stage")

    thought = subparsers.add_parser(
        "thought", help="capture a possible future improvement without committing to it"
    )
    thought.add_argument("text")

    quality = subparsers.add_parser("quality", help="start a data-science code-quality review")
    quality.add_argument("--scope", default="Entire data-science project")
    quality.add_argument("--json", action="store_true", dest="as_json")

    experiment = subparsers.add_parser("experiment", help="create a durable experiment record")
    experiment.add_argument("title")

    artifact = subparsers.add_parser("artifact", help="register an output and its provenance")
    artifact.add_argument("path_or_uri")
    artifact.add_argument("--kind", required=True)
    artifact.add_argument("--source", required=True)
    artifact.add_argument("--fingerprint", required=True)
    artifact.add_argument("--notes", default="—")

    handoff = subparsers.add_parser("handoff", help="write the active study handoff snapshot")
    handoff.add_argument("--summary", required=True)
    handoff.add_argument("--next", required=True, dest="next_action")
    handoff.add_argument("--blockers", default="None known")

    validate = subparsers.add_parser("validate", help="check that required artifacts are complete")
    validate.add_argument("--json", action="store_true", dest="as_json")
    return parser


def run(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.command == "init":
        target = Path(args.path)
        written = init_project(target, args.force)
        print(f"Initialized DataScienceKit in {target.resolve()}")
        print(f"Version control: Git ({version_control_status(target)['root']})")
        print(f"Installed {len(written)} managed files. Start with $dskit-principles.")
        return 0

    root = find_project_root()
    if args.command == "new":
        study = new_study(root, args.title)
        print(json.dumps({"project_root": str(root), "study_dir": str(study)}, indent=2))
        return 0
    if args.command == "activate":
        study = activate_study(root, args.study)
        print(f"Active study: {study.relative_to(root).as_posix()}")
        return 0
    if args.command == "step":
        transition = set_current_step(root, args.number, args.reason)
        print(f"Current step: {transition['label']} (iteration {transition['iteration']})")
        return 0
    if args.command == "status":
        status = project_status(root)
        if args.as_json:
            print(json.dumps(status, indent=2))
        else:
            _print_status(status)
        return 0
    if args.command == "context":
        context = project_context(root)
        if args.as_json:
            print(json.dumps(context, indent=2))
        else:
            _print_status(context)
            print("\nRecent project log:")
            print("\n".join(context["recent_project_log"]) or "No entries")
        return 0
    if args.command == "log":
        append_project_log(root, args.message, args.kind, args.stage)
        print("Project log updated.")
        return 0
    if args.command == "thought":
        thought_id = append_thought(root, args.text)
        print(f"Captured {thought_id} in .dskit/thoughts/backlog.md")
        return 0
    if args.command == "quality":
        report = new_quality_review(root, args.scope)
        payload = {"project_root": str(root), "report": str(report), "scope": args.scope}
        if args.as_json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"Quality review created: {report.relative_to(root).as_posix()}")
        return 0
    if args.command == "experiment":
        record = new_experiment(root, args.title)
        print(f"Experiment created: {record.relative_to(root).as_posix()}")
        return 0
    if args.command == "artifact":
        artifact_id = register_artifact(
            root,
            args.path_or_uri,
            args.kind,
            args.source,
            args.fingerprint,
            args.notes,
        )
        print(f"Registered {artifact_id} in the active study artifact manifest.")
        return 0
    if args.command == "handoff":
        handoff = write_handoff(root, args.summary, args.next_action, args.blockers)
        print(f"Handoff written: {handoff.relative_to(root).as_posix()}")
        return 0
    if args.command == "validate":
        errors = validate_project(root)
        if args.as_json:
            print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        elif errors:
            print("Validation failed:")
            for error in errors:
                print(f"- {error}")
        else:
            print("DataScienceKit project is complete.")
        return 1 if errors else 0
    raise AssertionError(f"unhandled command: {args.command}")


def main(argv: Iterable[str] | None = None) -> int:
    try:
        return run(argv)
    except DskitError as exc:
        print(f"dskit: {exc}", file=sys.stderr)
        return 2
