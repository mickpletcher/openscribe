from __future__ import annotations

import os
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


class SchemaValidationError(ValueError):
    pass


def load_yaml(path: Path, *, default: Any = None) -> Any:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SchemaValidationError(f"Invalid YAML in '{path}': {exc}") from exc
    return default if data is None else data


def require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SchemaValidationError(f"{context} must be a YAML mapping.")
    return value


def require_list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise SchemaValidationError(f"{context} must be a YAML list.")
    return value


def validate_project_config(value: Any, context: str) -> dict[str, Any]:
    config = require_mapping(value, context)
    _string_fields(config, ("title", "author", "template"), context)
    _integer_fields(config, ("version",), context, minimum=1)

    compile_config = _optional_mapping(config, "compile", context)
    _string_fields(
        compile_config,
        (
            "default_format",
            "backend",
            "default_profile",
            "default_template",
            "output_filename",
            "chapter_heading_style",
        ),
        f"{context}.compile",
    )
    _boolean_fields(
        compile_config,
        ("include_title_page", "include_part_headings"),
        f"{context}.compile",
    )
    research = _optional_mapping(compile_config, "research", f"{context}.compile")
    _string_fields(research, ("citation_style", "bibliography_title"), f"{context}.compile.research")
    _boolean_fields(
        research,
        ("include_bibliography", "include_reference_heading"),
        f"{context}.compile.research",
    )

    goals = _optional_mapping(config, "goals", context)
    _integer_fields(goals, ("draft_word_target", "session_word_target"), f"{context}.goals", minimum=0)
    _string_fields(goals, ("deadline",), f"{context}.goals")

    ai = _optional_mapping(config, "ai", context)
    _boolean_fields(ai, ("enabled",), f"{context}.ai")
    _string_fields(ai, ("provider", "model"), f"{context}.ai")

    proofreading = _optional_mapping(config, "proofreading", context)
    _boolean_fields(proofreading, ("enabled",), f"{context}.proofreading")
    _string_fields(proofreading, ("endpoint", "language"), f"{context}.proofreading")
    _integer_fields(proofreading, ("timeout_seconds",), f"{context}.proofreading", minimum=1)
    return config


def validate_chapter_metadata(value: Any, context: str) -> dict[str, Any]:
    metadata = require_mapping(value, context)
    _string_fields(
        metadata,
        ("chapter_id", "title", "status", "label", "synopsis", "pov", "notes"),
        context,
    )
    _integer_fields(metadata, ("word_target",), context, minimum=0)
    return metadata


def validate_part_metadata(value: Any, context: str) -> dict[str, Any]:
    metadata = require_mapping(value, context)
    _string_fields(metadata, ("title",), context)
    return metadata


def validate_story_metadata(value: Any, context: str) -> dict[str, Any]:
    metadata = require_mapping(value, context)
    _string_fields(metadata, ("title", "premise", "genre", "tone", "status"), context)
    return metadata


def validate_source_metadata(value: Any, context: str) -> dict[str, Any]:
    metadata = require_mapping(value, context)
    _string_fields(metadata, ("title", "type", "author", "year", "url"), context)
    return metadata


def validate_board(value: Any, context: str) -> dict[str, Any]:
    board = require_mapping(value, context)
    notes = require_list(board.get("notes", []), f"{context}.notes")
    for index, note_value in enumerate(notes):
        note_context = f"{context}.notes[{index}]"
        note = require_mapping(note_value, note_context)
        _string_fields(note, ("id", "title", "body", "group"), note_context)
        _string_list_fields(note, ("links", "chapter_links"), note_context)
        _integer_fields(note, ("x", "y"), note_context)
        _boolean_fields(note, ("hidden",), note_context)
    return board


def validate_elements(value: Any, context: str) -> dict[str, Any]:
    data = require_mapping(value, context)
    elements = require_list(data.get("elements", []), f"{context}.elements")
    for index, element_value in enumerate(elements):
        element_context = f"{context}.elements[{index}]"
        element = require_mapping(element_value, element_context)
        _string_fields(element, ("id", "type", "name", "notes"), element_context)
        _string_list_fields(element, ("aliases", "tags"), element_context)
        relations = require_list(element.get("relations", []), f"{element_context}.relations")
        for relation_index, relation_value in enumerate(relations):
            relation_context = f"{element_context}.relations[{relation_index}]"
            relation = require_mapping(relation_value, relation_context)
            _string_fields(relation, ("target", "type"), relation_context)
    return data


def validate_template(value: Any, context: str) -> dict[str, Any]:
    template = require_mapping(value, context)
    _string_fields(template, ("name",), context)
    template.setdefault("compile", {})
    template.setdefault("files", {})
    _optional_mapping(template, "compile", context)
    files = _optional_mapping(template, "files", context)
    for relative_path, content in files.items():
        if not isinstance(relative_path, str) or not isinstance(content, str):
            raise SchemaValidationError(f"{context}.files must map string paths to string content.")
    return template


def validate_index(value: Any, context: str) -> dict[str, Any]:
    data = require_mapping(value, context)
    if "source_manifest" in data:
        manifest = require_mapping(data["source_manifest"], f"{context}.source_manifest")
        _string_fields(manifest, tuple(manifest), f"{context}.source_manifest")
    return data


def validate_snapshot_metadata(value: Any, context: str) -> dict[str, Any]:
    metadata = require_mapping(value, context)
    _string_fields(metadata, ("label", "mode", "created_at", "archive", "commit"), context)
    _boolean_fields(metadata, ("dirty",), context)
    _string_list_fields(metadata, ("status", "managed_paths"), context)
    return metadata


def safe_template_target(root: Path, relative_path: str) -> Path:
    normalized = relative_path.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise SchemaValidationError(f"Unsafe template path '{relative_path}'.")
    if path.parts[0] not in {"manuscript", "characters", "research", "notes"}:
        raise SchemaValidationError(
            f"Template path '{relative_path}' must be under manuscript, characters, research, or notes."
        )
    target = (root / Path(*path.parts)).resolve()
    if not target.is_relative_to(root.resolve()):
        raise SchemaValidationError(f"Template path '{relative_path}' leaves the project directory.")
    return target


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def _optional_mapping(value: dict[str, Any], key: str, context: str) -> dict[str, Any]:
    if key not in value:
        return {}
    return require_mapping(value[key], f"{context}.{key}")


def _string_fields(value: dict[str, Any], keys: tuple[str, ...], context: str) -> None:
    for key in keys:
        if key in value and not isinstance(value[key], str):
            raise SchemaValidationError(f"{context}.{key} must be a string.")


def _string_list_fields(value: dict[str, Any], keys: tuple[str, ...], context: str) -> None:
    for key in keys:
        if key not in value:
            continue
        values = require_list(value[key], f"{context}.{key}")
        if any(not isinstance(item, str) for item in values):
            raise SchemaValidationError(f"{context}.{key} must contain only strings.")


def _integer_fields(
    value: dict[str, Any],
    keys: tuple[str, ...],
    context: str,
    *,
    minimum: int | None = None,
) -> None:
    for key in keys:
        if key not in value:
            continue
        item = value[key]
        if not isinstance(item, int) or isinstance(item, bool):
            raise SchemaValidationError(f"{context}.{key} must be an integer.")
        if minimum is not None and item < minimum:
            raise SchemaValidationError(f"{context}.{key} must be at least {minimum}.")


def _boolean_fields(value: dict[str, Any], keys: tuple[str, ...], context: str) -> None:
    for key in keys:
        if key in value and not isinstance(value[key], bool):
            raise SchemaValidationError(f"{context}.{key} must be true or false.")
