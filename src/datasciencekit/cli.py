"""Command-line interface for initializing and inspecting DataScienceKit projects."""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import shutil
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

STAGE_NAMES = {
    "01-business-understanding.md": "Business Understanding",
    "02-analytic-approach.md": "Analytic Approach",
    "03-data-requirements.md": "Data Requirements",
    "04-data-collection.md": "Data Collection",
    "05-data-understanding.md": "Data Understanding",
    "06-data-preparation.md": "Data Preparation",
    "07-modeling.md": "Modeling",
    "08-evaluation.md": "Evaluation",
    "09-deployment.md": "Deployment",
    "10-feedback.md": "Feedback",
}


class DskitError(RuntimeError):
    """A user-facing CLI error."""


def _resource_path(*parts: str):
    return files("datasciencekit").joinpath("resources", *parts)


def _copy_resource_tree(source_parts: tuple[str, ...], destination: Path, force: bool) -> list[Path]:
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


def init_project(target: Path, force: bool = False) -> list[Path]:
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    config_path = target / MANAGED_DIR / "config.json"
    if config_path.exists() and not force:
        raise DskitError(f"DataScienceKit is already initialized at {target}")

    previous_config: dict[str, Any] = {}
    if config_path.exists() and force:
        previous_config = _load_config(target)

    written = _copy_resource_tree(("project",), target, force)
    _write_json(
        config_path,
        {
            "schema_version": 2,
            "tool_version": __version__,
            "active_study": previous_config.get("active_study"),
            "methodology": "IBM Data Science Methodology",
        },
    )
    if config_path not in written:
        written.append(config_path)
    machine_log = target / MANAGED_DIR / "logs" / "machine.jsonl"
    _append_machine_event(target, "project_initialized", force=force)
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
        for artifact in ARTIFACTS:
            source = overrides / artifact if (overrides / artifact).is_file() else source_path / artifact
            content = source.read_text(encoding="utf-8")
            content = content.replace("{{STUDY_TITLE}}", title.strip())
            (study / artifact).write_text(content, encoding="utf-8")

    config = _load_config(root)
    config["active_study"] = study.relative_to(root).as_posix()
    _write_json(root / MANAGED_DIR / "config.json", config)
    _append_machine_event(root, "study_created", title=title.strip(), study=study.relative_to(root).as_posix())
    append_project_log(root, f"Created and activated study: {title.strip()}", "study")
    return study


def activate_study(root: Path, study_name: str) -> Path:
    studies = root / MANAGED_DIR / "studies"
    candidates = [path for path in studies.iterdir() if path.is_dir()] if studies.is_dir() else []
    matches = [path for path in candidates if path.name == study_name or path.name.startswith(study_name)]
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
        "artifacts": {},
        "next_stage": None,
    }
    active = config.get("active_study")
    if active:
        study = root / active
        for artifact in ARTIFACTS:
            path = study / artifact
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
    status["studies"] = sorted(path.name for path in studies.iterdir() if path.is_dir()) if studies.is_dir() else []
    return status


def validate_project(root: Path) -> list[str]:
    status = project_status(root)
    errors: list[str] = []
    if not status["principles"]["complete"]:
        errors.append("project principles are incomplete")
    if not status["active_study"]:
        errors.append("no active study")
    for name, artifact in status["artifacts"].items():
        if artifact["todo_count"] == -1:
            errors.append(f"missing artifact: {name}")
        elif not artifact["complete"]:
            errors.append(f"incomplete artifact: {name} ({artifact['todo_count']} TODOs)")
    return errors


def _print_status(status: dict[str, Any]) -> None:
    principles = status["principles"]
    marker = "complete" if principles["complete"] else f"{principles['todo_count']} TODOs"
    print(f"Project: {status['project_root']}")
    print(f"Principles: {marker}")
    print(f"Active study: {status['active_study'] or 'none'}")
    if status["next_stage"]:
        print(f"Next stage: {status['next_stage']['name']}")
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
    init.add_argument("--force", action="store_true", help="replace only DataScienceKit-managed files")

    new = subparsers.add_parser("new", help="create and activate a study")
    new.add_argument("title")

    activate = subparsers.add_parser("activate", help="make an existing study active")
    activate.add_argument("study")

    status = subparsers.add_parser("status", help="show workflow artifact status")
    status.add_argument("--json", action="store_true", dest="as_json")

    context = subparsers.add_parser("context", help="show durable context for a new agent or session")
    context.add_argument("--json", action="store_true", dest="as_json")

    log = subparsers.add_parser("log", help="append a human-readable project log entry")
    log.add_argument("message")
    log.add_argument("--kind", default="progress", choices=("decision", "progress", "finding", "handoff"))
    log.add_argument("--stage")

    thought = subparsers.add_parser("thought", help="capture a possible future improvement without committing to it")
    thought.add_argument("text")

    quality = subparsers.add_parser("quality", help="start a data-science code-quality review")
    quality.add_argument("--scope", default="Entire data-science project")
    quality.add_argument("--json", action="store_true", dest="as_json")

    validate = subparsers.add_parser("validate", help="check that required artifacts are complete")
    validate.add_argument("--json", action="store_true", dest="as_json")
    return parser


def run(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.command == "init":
        target = Path(args.path)
        written = init_project(target, args.force)
        print(f"Initialized DataScienceKit in {target.resolve()}")
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
    if args.command == "status":
        status = project_status(root)
        _append_machine_event(root, "status_read", json=args.as_json)
        if args.as_json:
            print(json.dumps(status, indent=2))
        else:
            _print_status(status)
        return 0
    if args.command == "context":
        context = project_context(root)
        _append_machine_event(root, "context_read", json=args.as_json)
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
    if args.command == "validate":
        errors = validate_project(root)
        _append_machine_event(root, "project_validated", valid=not errors, error_count=len(errors))
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
