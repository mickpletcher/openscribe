from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from openscribe.locking import project_locked
from openscribe.schema import atomic_write_text, load_yaml, require_mapping, validate_project_config


class MigrationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class MigrationStep:
    from_version: int
    to_version: int
    name: str
    apply: Callable[[Path], None]


@dataclass(frozen=True, slots=True)
class MigrationPlan:
    current_version: int
    target_version: int
    steps: tuple[MigrationStep, ...]


@dataclass(frozen=True, slots=True)
class MigrationResult:
    plan: MigrationPlan
    backup_path: Path | None


def _migrate_v1_to_v2(root: Path) -> None:
    from openscribe.board import migrate_chapter_links
    from openscribe.project import ensure_chapter_ids

    ensure_chapter_ids(root)
    migrate_chapter_links(root)


def _migrate_v2_to_v3(root: Path) -> None:
    from openscribe.project import ensure_scene_ids

    ensure_scene_ids(root)


MIGRATIONS = (
    MigrationStep(1, 2, "Add immutable chapter IDs and migrate board links", _migrate_v1_to_v2),
    MigrationStep(2, 3, "Add immutable inline scene IDs", _migrate_v2_to_v3),
)


def plan_project_migration(root: Path) -> MigrationPlan:
    from openscribe.project import CURRENT_PROJECT_VERSION, PROJECT_DIR, PROJECT_FILE

    config_path = root / PROJECT_DIR / PROJECT_FILE
    config = require_mapping(load_yaml(config_path, default={}), f"Project config '{config_path}'")
    validate_project_config(config, f"Project config '{config_path}'")
    current_version = _project_version(config)
    if current_version > CURRENT_PROJECT_VERSION:
        raise MigrationError(
            f"Project format version {current_version} is newer than this OpenScribe build supports "
            f"({CURRENT_PROJECT_VERSION})."
        )

    steps: list[MigrationStep] = []
    version = current_version
    while version < CURRENT_PROJECT_VERSION:
        step = next((candidate for candidate in MIGRATIONS if candidate.from_version == version), None)
        if step is None:
            raise MigrationError(f"No migration is registered from project format version {version}.")
        steps.append(step)
        version = step.to_version
    return MigrationPlan(current_version, CURRENT_PROJECT_VERSION, tuple(steps))


@project_locked
def migrate_project(root: Path) -> MigrationResult:
    from openscribe.editing import transform_project
    from openscribe.project import PROJECT_DIR, PROJECT_FILE

    plan = plan_project_migration(root)
    if not plan.steps:
        return MigrationResult(plan, None)

    def apply_steps(stage: Path) -> None:
        config_path = stage / PROJECT_DIR / PROJECT_FILE
        for step in plan.steps:
            step.apply(stage)
            config = require_mapping(load_yaml(config_path, default={}), f"Project config '{config_path}'")
            config["version"] = step.to_version
            atomic_write_text(config_path, yaml.safe_dump(config, sort_keys=False))

    try:
        backup_path, _ = transform_project(
            root, f"automatic backup before migration v{plan.current_version} to v{plan.target_version}", apply_steps,
            allow_legacy=True,
        )
    except Exception as exc:
        raise MigrationError(
            f"Project migration failed. An automatic backup was created before staging. {exc}"
        ) from exc
    return MigrationResult(plan, backup_path)


@project_locked
def repair_project_identities(root: Path) -> Path:
    from openscribe.board import migrate_chapter_links
    from openscribe.editing import transform_project
    from openscribe.project import ensure_chapter_ids, ensure_scene_ids, load_project_config

    load_project_config(root)
    def repair(stage: Path) -> None:
        ensure_chapter_ids(stage)
        ensure_scene_ids(stage)
        migrate_chapter_links(stage)

    return transform_project(root, "automatic backup before explicit identity repair", repair)[0]


def _project_version(config: dict[str, Any]) -> int:
    value = config.get("version", 1)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise MigrationError("Project format version must be a positive integer.")
    return value
