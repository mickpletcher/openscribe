from __future__ import annotations

import csv
import difflib
import json
import os
import re
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from openscribe.editing import staged_operation
from openscribe.locking import project_locked
from openscribe.schema import (
    SchemaValidationError,
    atomic_write_text,
    load_yaml,
    require_mapping,
    safe_template_target,
    validate_chapter_metadata,
    validate_part_metadata,
    validate_project_config,
    validate_source_metadata,
    validate_story_metadata,
    validate_template,
)

PROJECT_DIR = ".openscribe"
PROJECT_FILE = "project.yaml"
PART_FILE = "part.yaml"
STORY_IDEAS_DIR = "notes/story-ideas"
INDEX_DIR = ".openscribe/index"
SNAPSHOTS_DIR = ".openscribe/snapshots"
TEMPLATES_DIR = ".openscribe/templates"
CONFERENCE_DIR = "research/conferences"
CONFERENCE_SESSIONS_DIR = "research/conferences/sessions"
PRESENTATIONS_DIR = "notes/presentations"
SOURCES_DIR = "research/sources"
CURRENT_PROJECT_VERSION = 3
SCENE_ID_PATTERN = re.compile(r"^scene-[a-f0-9]{32}$")
SCENE_MARKER_PATTERN = re.compile(
    r"^\r?\n<!--\s*openscribe-scene-id:\s*(scene-[a-f0-9]{32})\s*-->\s*(?:\r?\n)?",
    flags=re.IGNORECASE,
)


@dataclass(slots=True)
class SceneDocument:
    scene_id: str
    title: str
    body: str
    slug: str


@dataclass(slots=True)
class SceneMatch:
    chapter: ChapterDocument | None
    chapter_title: str
    part: str
    scene_id: str
    scene_title: str
    scene_slug: str
    scene_body: str


@dataclass(slots=True)
class AuxiliaryDocument:
    path: Path
    title: str
    body: str
    category: str
    slug: str


@dataclass(slots=True)
class SourceDocument:
    path: Path
    title: str
    source_type: str
    author: str
    year: str
    url: str
    body: str
    slug: str


@dataclass(slots=True)
class ChapterDocument:
    path: Path
    chapter_id: str
    title: str
    status: str
    label: str
    synopsis: str
    pov: str
    word_target: int
    notes: str
    body: str
    part: str
    part_id: str
    slug: str
    scenes: list[SceneDocument]

    @property
    def word_count(self) -> int:
        return len([word for word in re.findall(r"\b[\w']+\b", strip_scene_markers(self.body))])

    @property
    def scene_count(self) -> int:
        return len(self.scenes)


@dataclass(slots=True)
class StoryIdea:
    path: Path
    title: str
    premise: str
    genre: str
    tone: str
    status: str
    body: str
    slug: str


@dataclass(frozen=True, slots=True)
class SceneFileChange:
    path: Path
    before: str
    after: str


@dataclass(frozen=True, slots=True)
class SceneOperation:
    summary: str
    changes: tuple[SceneFileChange, ...]


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return cleaned or "untitled"


def new_chapter_id() -> str:
    return f"chapter-{uuid4().hex}"


def new_scene_id() -> str:
    return f"scene-{uuid4().hex}"


def strip_scene_markers(text: str) -> str:
    return re.sub(
        r"^<!--[ \t]*openscribe-scene-id:[ \t]*scene-[a-f0-9]{32}[ \t]*-->[ \t]*(?:\r?\n)?",
        "",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )


def ensure_chapter_ids(root: Path) -> dict[str, str]:
    manuscript = root / "manuscript"
    if not manuscript.exists():
        return {}

    migrated: dict[str, str] = {}
    seen_ids: set[str] = set()
    for part_path in sorted(path for path in manuscript.iterdir() if path.is_dir()):
        for chapter_path in sorted(part_path.glob("*.md")):
            text = chapter_path.read_text(encoding="utf-8")
            metadata, body = parse_frontmatter(text)
            validate_chapter_metadata(metadata, f"Chapter frontmatter in '{chapter_path}'")
            chapter_id = str(metadata.get("chapter_id", "")).strip()
            if chapter_id and chapter_id in seen_ids:
                raise SchemaValidationError("Duplicate chapter ID. Resolve the duplicate before migration.")
            if not chapter_id:
                chapter_id = new_chapter_id()
                metadata["chapter_id"] = chapter_id
                atomic_write_text(
                    chapter_path,
                    f"---\n{yaml.safe_dump(metadata, sort_keys=False).strip()}\n---\n\n{body}",
                )
                migrated[chapter_path.stem] = chapter_id
            seen_ids.add(chapter_id)
    return migrated


def ensure_scene_ids(root: Path) -> dict[str, list[str]]:
    manuscript = root / "manuscript"
    if not manuscript.exists():
        return {}

    migrated: dict[str, list[str]] = {}
    seen_ids: set[str] = set()
    for part_path in sorted(path for path in manuscript.iterdir() if path.is_dir()):
        for chapter_path in sorted(part_path.glob("*.md")):
            text = chapter_path.read_text(encoding="utf-8")
            metadata, body = parse_frontmatter(text)
            preamble, scenes = _parse_scene_layout(body)
            changed_ids: list[str] = []
            for scene in scenes:
                if scene.scene_id and scene.scene_id in seen_ids:
                    raise SchemaValidationError("Duplicate scene ID. Resolve the duplicate before migration.")
                if not SCENE_ID_PATTERN.fullmatch(scene.scene_id):
                    scene.scene_id = new_scene_id()
                    changed_ids.append(scene.scene_id)
                seen_ids.add(scene.scene_id)
            if changed_ids:
                atomic_write_text(
                    chapter_path,
                    _chapter_text(metadata, _render_scene_layout(preamble, scenes)),
                )
                migrated[chapter_path.stem] = changed_ids
    return migrated


def project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / PROJECT_DIR / PROJECT_FILE).exists():
            return candidate
    raise FileNotFoundError("No openscribe project found in this directory tree.")


def init_project(base_path: Path, title: str) -> Path:
    return init_project_from_template(base_path, title, template_name="fiction")


def init_project_from_template(
    base_path: Path,
    title: str,
    template_name: str = "fiction",
    template_file: Path | None = None,
) -> Path:
    project_path = base_path.resolve()
    config_dir = project_path / PROJECT_DIR
    if (config_dir / PROJECT_FILE).exists():
        raise FileExistsError(f"Project already exists at {project_path}")

    resolved_template_name, template = load_template_definition(template_name, template_file)
    validate_template(template, f"Project template '{resolved_template_name}'")
    for relative_path in template.get("files", {}):
        safe_template_target(project_path, str(relative_path))

    for directory in (
        config_dir,
        config_dir / "templates",
        project_path / "manuscript",
        project_path / "research",
        project_path / "characters",
        project_path / "notes",
        project_path / STORY_IDEAS_DIR,
        project_path / INDEX_DIR,
        project_path / SNAPSHOTS_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    write_yaml(
        config_dir / PROJECT_FILE,
        {
            "title": title,
            "author": "",
            "version": CURRENT_PROJECT_VERSION,
            "template": resolved_template_name,
            "compile": {
                "default_format": str(template["compile"].get("default_format", "docx")),
                "backend": "auto",
                "default_profile": "",
                "default_template": str(template["compile"].get("default_template", "novel")),
                "output_filename": "",
                "include_title_page": bool(template["compile"].get("include_title_page", True)),
                "include_part_headings": bool(template["compile"].get("include_part_headings", True)),
                "chapter_heading_style": str(template["compile"].get("chapter_heading_style", "title-only")),
                "research": {
                    "citation_style": "APA",
                    "include_bibliography": False,
                    "include_reference_heading": True,
                    "bibliography_title": "References",
                },
            },
            "goals": {
                "draft_word_target": 0,
                "session_word_target": 0,
                "deadline": "",
            },
            "ai": {
                "enabled": False,
                "provider": "openai",
                "model": "gpt-4.1",
            },
            "proofreading": {
                "enabled": False,
                "endpoint": "http://127.0.0.1:8081/v2/check",
                "language": "en-US",
                "timeout_seconds": 30,
            },
        },
    )
    _apply_template_files(project_path, title, template)
    return project_path


def built_in_templates() -> dict[str, dict[str, Any]]:
    return {
        "fiction": {
            "compile": {
                "default_format": "docx",
                "default_template": "novel",
                "include_title_page": True,
                "include_part_headings": True,
                "chapter_heading_style": "title-only",
            },
            "files": {
                "characters/protagonist.md": "# Protagonist\n\nRole: Main point of view\n\nConflict:\n\n* \n",
                "research/setting-notes.md": "# Setting Notes\n\nLocation:\n\nEra:\n\nAtmosphere:\n",
                "notes/revision-notes.md": "# Revision Notes\n\n* \n",
            },
        },
        "nonfiction": {
            "compile": {
                "default_format": "docx",
                "default_template": "manuscript",
                "include_title_page": True,
                "include_part_headings": True,
                "chapter_heading_style": "chapter-number-title",
            },
            "files": {
                "research/source-log.md": "# Source Log\n\n## References\n\n* \n",
                "research/citation-log.md": "# Citation Log\n\n| Section | Source | Use | Notes |\n| --- | --- | --- | --- |\n",
                "research/bibliography-notes.md": "# Bibliography Notes\n\n## Style\n\nChicago, APA, MLA, or house style.\n",
                "notes/argument-map.md": "# Argument Map\n\n## Core Claim\n\n\n## Supporting Points\n\n* \n",
            },
        },
        "technical": {
            "compile": {
                "default_format": "docx",
                "default_template": "minimal",
                "include_title_page": False,
                "include_part_headings": True,
                "chapter_heading_style": "chapter-number-title",
            },
            "files": {
                "research/reference-links.md": "# Reference Links\n\n* \n",
                "notes/implementation-notes.md": "# Implementation Notes\n\n## Audience\n\n\n## Open Questions\n\n* \n",
            },
        },
        "screenwriting": {
            "compile": {
                "default_format": "docx",
                "default_template": "minimal",
                "include_title_page": True,
                "include_part_headings": False,
                "chapter_heading_style": "title-only",
            },
            "files": {
                "research/visual-references.md": "# Visual References\n\n* \n",
                "notes/beat-sheet.md": "# Beat Sheet\n\n## Opening Image\n\n\n## Midpoint\n\n\n## Finale\n\n",
                "characters/lead.md": "# Lead\n\nWant:\n\nNeed:\n\nContradiction:\n",
            },
        },
        "research": {
            "compile": {
                "default_format": "docx",
                "default_template": "academic",
                "include_title_page": True,
                "include_part_headings": False,
                "chapter_heading_style": "section-number-title",
            },
            "files": {
                "research/source-log.md": "# Source Log\n\n## References\n\n* \n",
                "research/literature-review.md": "# Literature Review\n\n## Key Sources\n\n* \n",
                "research/citation-log.md": "# Citation Log\n\n| Section | Source | Use | Notes |\n| --- | --- | --- | --- |\n",
                "research/bibliography-notes.md": "# Bibliography Notes\n\n## Style\n\nAPA, IEEE, ACM, or venue style.\n",
                "notes/research-questions.md": "# Research Questions\n\n## Primary Question\n\n\n## Secondary Questions\n\n* \n",
                "notes/presentations/slide-draft.md": "# Slide Draft\n\n## Opening\n\n* \n",
            },
        },
    }


def _apply_template_files(root: Path, title: str, template: dict[str, Any]) -> None:
    for relative_path, content in template.get("files", {}).items():
        target_path = safe_template_target(root, str(relative_path))
        target_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(target_path, content.replace("{title}", title))


def template_library_path(root: Path) -> Path:
    return root / TEMPLATES_DIR


def save_project_template(root: Path, name: str) -> Path:
    config = load_project_config(root)
    template_data = {
        "name": name,
        "compile": dict(config.get("compile", {})),
        "files": {},
    }
    for category in ("characters", "research", "notes"):
        for document in list_auxiliary_documents(root, category):
            relative_path = str(document.path.relative_to(root)).replace("\\", "/")
            template_data["files"][relative_path] = document.body
    target_path = template_library_path(root) / f"{slugify(name)}.yaml"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(target_path, template_data)
    return target_path


def load_template_definition(template_name: str, template_file: Path | None = None) -> tuple[str, dict[str, Any]]:
    if template_file is not None:
        if not template_file.exists():
            raise FileNotFoundError(f"Template file '{template_file}' was not found.")
        data = validate_template(
            load_yaml(template_file, default={}),
            f"Template '{template_file}'",
        )
        resolved_name = str(data.get("name", template_file.stem)).strip() or template_file.stem
        return slugify(resolved_name), data

    normalized = template_name.strip().lower()
    template = built_in_templates().get(normalized)
    if template is None:
        supported = ", ".join(sorted(built_in_templates()))
        raise ValueError(f"Unknown project template '{template_name}'. Use {supported} or provide --template-file.")
    return normalized, template


@project_locked
def load_project_config(root: Path) -> dict[str, Any]:
    from openscribe.snapshots import recover_interrupted_restores

    recover_interrupted_restores(root)
    config_path = root / PROJECT_DIR / PROJECT_FILE
    if not config_path.exists():
        raise FileNotFoundError(f"Missing project config at {config_path}")
    raw_config = load_yaml(config_path, default={})
    config = validate_project_config(raw_config, f"Project config '{config_path}'")
    version = config.get("version", 1)
    if version != CURRENT_PROJECT_VERSION:
        from openscribe.migrations import MigrationError

        raise MigrationError(
            f"Project format {version} is not supported for editing. "
            "Run `openscribe migrate status` and explicitly apply any available migration."
        )
    compile_config = config.setdefault("compile", {})
    compile_config.setdefault("default_format", "docx")
    compile_config.setdefault("backend", "auto")
    compile_config.setdefault("default_profile", "")
    compile_config.setdefault("default_template", "novel")
    compile_config.setdefault("output_filename", "")
    compile_config.setdefault("include_title_page", True)
    compile_config.setdefault("include_part_headings", True)
    compile_config.setdefault("chapter_heading_style", "title-only")
    research_compile = compile_config.setdefault("research", {})
    research_compile.setdefault("citation_style", "APA")
    research_compile.setdefault("include_bibliography", False)
    research_compile.setdefault("include_reference_heading", True)
    research_compile.setdefault("bibliography_title", "References")
    goals = config.setdefault("goals", {})
    goals.setdefault("draft_word_target", 0)
    goals.setdefault("session_word_target", 0)
    goals.setdefault("deadline", "")
    proofreading = config.setdefault("proofreading", {})
    proofreading.setdefault("enabled", False)
    proofreading.setdefault("endpoint", "http://127.0.0.1:8081/v2/check")
    proofreading.setdefault("language", "en-US")
    proofreading.setdefault("timeout_seconds", 30)
    return config


def save_project_config(root: Path, config: dict[str, Any]) -> Path:
    config_path = root / PROJECT_DIR / PROJECT_FILE
    write_yaml(config_path, config)
    return config_path


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    atomic_write_text(
        path,
        yaml.safe_dump(data, sort_keys=False, allow_unicode=False),
    )


def next_part_number(root: Path) -> int:
    manuscript = root / "manuscript"
    existing = []
    for child in manuscript.iterdir():
        if child.is_dir():
            match = re.match(r"part-(\d+)", child.name)
            if match:
                existing.append(int(match.group(1)))
    return (max(existing) + 1) if existing else 1


def next_chapter_number(part_path: Path) -> int:
    existing = []
    for child in part_path.iterdir():
        if child.is_file() and child.suffix == ".md":
            match = re.match(r"ch-(\d+)", child.name)
            if match:
                existing.append(int(match.group(1)))
    return (max(existing) + 1) if existing else 1


@project_locked
def create_part(root: Path, title: str) -> Path:
    load_project_config(root)
    part_number = next_part_number(root)
    folder_name = f"part-{part_number:02d}-{slugify(title)}"
    part_path = root / "manuscript" / folder_name
    part_path.mkdir(parents=True, exist_ok=False)
    write_yaml(part_path / PART_FILE, {"title": title})
    return part_path


def story_ideas_path(root: Path) -> Path:
    return root / STORY_IDEAS_DIR


def create_story_idea(
    root: Path,
    title: str,
    *,
    premise: str = "",
    genre: str = "",
    tone: str = "",
    status: str = "seed",
    notes: str = "",
) -> Path:
    ideas_dir = story_ideas_path(root)
    ideas_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(title)
    idea_path = ideas_dir / f"{slug}.md"
    suffix = 2
    while idea_path.exists():
        idea_path = ideas_dir / f"{slug}-{suffix}.md"
        suffix += 1

    frontmatter = {
        "title": title,
        "premise": premise,
        "genre": genre,
        "tone": tone,
        "status": status,
    }
    atomic_write_text(
        idea_path,
        f"---\n{yaml.safe_dump(frontmatter, sort_keys=False).strip()}\n---\n\n{notes.strip()}".rstrip() + "\n",
    )
    return idea_path


def resolve_part_path(root: Path, part: str | None) -> Path:
    manuscript = root / "manuscript"
    if part:
        part_slug = slugify(part)
        for child in manuscript.iterdir():
            if not child.is_dir():
                continue
            part_title = load_part_title(child)
            if (
                child.name == part
                or child.name.endswith(part_slug)
                or part_title.strip().lower() == part.strip().lower()
            ):
                return child
        raise FileNotFoundError(f"Part '{part}' was not found.")

    parts = sorted([child for child in manuscript.iterdir() if child.is_dir()])
    if not parts:
        raise FileNotFoundError("No manuscript part exists yet. Create one first.")
    return parts[-1]


@project_locked
def create_chapter(
    root: Path,
    title: str,
    part: str | None = None,
    status: str = "draft",
    label: str = "default",
    pov: str = "",
    word_target: int = 0,
    synopsis: str = "",
    notes: str = "",
) -> Path:
    load_project_config(root)
    part_path = resolve_part_path(root, part)
    chapter_number = next_chapter_number(part_path)
    chapter_slug = slugify(title)
    chapter_path = part_path / f"ch-{chapter_number:02d}-{chapter_slug}.md"
    frontmatter = {
        "chapter_id": new_chapter_id(),
        "title": title,
        "status": status,
        "label": label,
        "synopsis": synopsis,
        "pov": pov,
        "word_target": word_target,
        "notes": notes,
    }
    atomic_write_text(
        chapter_path,
        f"---\n{yaml.safe_dump(frontmatter, sort_keys=False).strip()}\n---\n\n",
    )
    return chapter_path


def create_nonfiction_section(
    root: Path,
    title: str,
    *,
    part: str | None = None,
    synopsis: str = "",
    notes: str = "",
) -> Path:
    if part is not None:
        try:
            resolve_part_path(root, part)
        except FileNotFoundError:
            create_part(root, part)
    return create_chapter(
        root,
        title,
        part=part,
        status="draft",
        label="section",
        synopsis=synopsis,
        notes=notes,
    )


def create_research_paper_structure(
    root: Path,
    *,
    part: str = "Paper",
    include_appendix: bool = False,
) -> list[Path]:
    try:
        part_path = resolve_part_path(root, part)
    except FileNotFoundError:
        part_path = create_part(root, part)

    sections = [
        ("Abstract", "Research summary and core findings."),
        ("Introduction", "Problem statement, context, and motivation."),
        ("Related Work", "Relevant literature and prior approaches."),
        ("Methods", "Methodology, data, and experimental setup."),
        ("Results", "Observed results and supporting evidence."),
        ("Discussion", "Interpretation, limits, and implications."),
        ("Conclusion", "Final takeaways and next steps."),
        ("References", "Citation placeholder section."),
    ]
    if include_appendix:
        sections.append(("Appendix", "Supplemental material."))

    created_paths: list[Path] = []
    existing_titles = {
        str(parse_frontmatter(path.read_text(encoding="utf-8"))[0].get("title", path.stem)).strip().lower()
        for path in part_path.glob("*.md")
    }
    for title, synopsis in sections:
        if title.strip().lower() in existing_titles:
            continue
        created_paths.append(
            create_chapter(
                root,
                title,
                part=part,
                status="draft",
                label="research",
                synopsis=synopsis,
                notes="Academic paper section.",
            )
        )
    return created_paths


def create_conference_materials(
    root: Path,
    title: str,
    *,
    venue: str = "",
    include_poster: bool = True,
) -> list[Path]:
    slug = slugify(title)
    created_paths: list[Path] = []
    files: list[tuple[Path, str]] = [
        (
            root / CONFERENCE_DIR / f"{slug}-submission-checklist.md",
            "# Submission Checklist\n\n"
            f"## Project\n\n{title}\n\n"
            f"## Venue\n\n{venue or 'TBD'}\n\n"
            "## Required Items\n\n"
            "* Abstract\n"
            "* Paper draft\n"
            "* Author details\n"
            "* Figure review\n"
            "* Final proof pass\n",
        ),
        (
            root / CONFERENCE_DIR / f"{slug}-conference-abstract.md",
            "# Conference Abstract\n\n"
            f"## Title\n\n{title}\n\n"
            f"## Venue\n\n{venue or 'TBD'}\n\n"
            "## Abstract\n\n\n"
            "## Key Findings\n\n* \n",
        ),
        (
            root / PRESENTATIONS_DIR / f"{slug}-talk-outline.md",
            "# Talk Outline\n\n"
            f"## Title\n\n{title}\n\n"
            "## Audience\n\n\n"
            "## Opening\n\n* \n"
            "## Core Points\n\n* \n"
            "## Closing\n\n* \n",
        ),
        (
            root / PRESENTATIONS_DIR / f"{slug}-slide-draft.md",
            "# Slide Draft\n\n"
            f"## Title Slide\n\n{title}\n\n"
            "## Slide 1\n\n* Problem\n\n"
            "## Slide 2\n\n* Method\n\n"
            "## Slide 3\n\n* Results\n\n"
            "## Slide 4\n\n* Discussion\n\n"
            "## Slide 5\n\n* Questions\n",
        ),
        (
            root / PRESENTATIONS_DIR / f"{slug}-speaker-notes.md",
            "# Speaker Notes\n\n"
            f"## Session\n\n{title}\n\n"
            "## Timing\n\n* Intro\n* Main points\n* Questions\n\n"
            "## Notes\n\n* \n",
        ),
    ]
    if include_poster:
        files.append(
            (
                root / CONFERENCE_DIR / f"{slug}-poster-outline.md",
                "# Poster Outline\n\n"
                f"## Title\n\n{title}\n\n"
                "## Sections\n\n* Background\n* Methods\n* Results\n* Conclusion\n",
            )
        )
    files.extend(
        [
            (
                root / CONFERENCE_DIR / f"{slug}-submission-status.md",
                "# Submission Status\n\n"
                f"## Project\n\n{title}\n\n"
                f"## Venue\n\n{venue or 'TBD'}\n\n"
                "## Current State\n\nDrafting\n\n"
                "## Deadlines\n\n* Abstract\n* Paper\n* Slides\n\n"
                "## Notes\n\n* \n",
            ),
            (
                root / PRESENTATIONS_DIR / f"{slug}-timed-talk-plan.md",
                "# Timed Talk Plan\n\n"
                f"## Session\n\n{title}\n\n"
                "## Run Of Show\n\n"
                "| Segment | Minutes | Goal |\n| --- | --- | --- |\n| Opening | 2 | Context |\n| Core result | 6 | Main finding |\n| Discussion | 3 | Implications |\n| Questions | 2 | Close |\n",
            ),
            (
                root / CONFERENCE_DIR / f"{slug}-poster-revision-log.md",
                "# Poster Revision Log\n\n"
                f"## Poster\n\n{title}\n\n"
                "| Revision | Date | Change | Owner |\n| --- | --- | --- | --- |\n",
            ),
        ]
    )

    for path, content in files:
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(path, content)
        created_paths.append(path)
    return created_paths


def import_conference_schedule(
    root: Path,
    schedule_path: Path,
    *,
    venue: str = "",
    create_checklists: bool = True,
) -> list[Path]:
    if not schedule_path.exists():
        raise FileNotFoundError(f"Schedule file '{schedule_path}' was not found.")

    sessions = _load_schedule_rows(schedule_path)
    if not sessions:
        raise ValueError("Conference schedule file did not contain any sessions.")

    venue_name = venue.strip() or schedule_path.stem.replace("-", " ").replace("_", " ").title()
    venue_slug = slugify(venue_name)
    created_paths: list[Path] = []
    session_lines = [
        "# Conference Schedule",
        "",
        "## Venue",
        "",
        venue_name,
        "",
        "| Session | Day | Time | Room | Format | Presenter | Status |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    checklist_lines = [
        "# Session Checklist",
        "",
        "## Venue",
        "",
        venue_name,
        "",
        "| Session | Slides | Notes | Timing | Poster | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for index, session in enumerate(sessions, start=1):
        title = session.get("title", f"Session {index}")
        day = session.get("day", "")
        time = session.get("time", "")
        room = session.get("room", "")
        format_name = session.get("format", "")
        presenter = session.get("presenter", "")
        status = session.get("status", "planned")
        notes = session.get("notes", "")
        session_slug = slugify(title)
        session_lines.append(
            f"| {title} | {day or 'TBD'} | {time or 'TBD'} | {room or 'TBD'} | {format_name or 'TBD'} | {presenter or 'TBD'} | {status} |"
        )
        checklist_lines.append(f"| {title} | [ ] | [ ] | [ ] | {'[ ]' if create_checklists else 'n/a'} | {status} |")

        session_path = root / CONFERENCE_SESSIONS_DIR / f"{venue_slug}-{index:02d}-{session_slug}.md"
        if not session_path.exists():
            session_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_text(
                session_path,
                "# Conference Session\n\n"
                f"## Title\n\n{title}\n\n"
                f"## Venue\n\n{venue_name}\n\n"
                f"## Day\n\n{day or 'TBD'}\n\n"
                f"## Time\n\n{time or 'TBD'}\n\n"
                f"## Room\n\n{room or 'TBD'}\n\n"
                f"## Format\n\n{format_name or 'TBD'}\n\n"
                f"## Presenter\n\n{presenter or 'TBD'}\n\n"
                f"## Status\n\n{status}\n\n"
                "## Session Checklist\n\n"
                "* [ ] Slide deck checked\n"
                "* [ ] Speaker notes checked\n"
                "* [ ] Timed run completed\n"
                "* [ ] Handout or poster checked\n"
                "* [ ] Submission portal reviewed\n\n"
                "## Notes\n\n"
                f"{notes.strip() or '* '}\n",
            )
            created_paths.append(session_path)

    overview_path = root / CONFERENCE_DIR / f"{venue_slug}-session-schedule.md"
    if not overview_path.exists():
        overview_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(overview_path, "\n".join(session_lines) + "\n")
        created_paths.append(overview_path)

    if create_checklists:
        checklist_path = root / CONFERENCE_DIR / f"{venue_slug}-session-checklist.md"
        if not checklist_path.exists():
            checklist_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_text(checklist_path, "\n".join(checklist_lines) + "\n")
            created_paths.append(checklist_path)

    return created_paths


def create_source_note(
    root: Path,
    title: str,
    *,
    source_type: str = "article",
    author: str = "",
    year: str = "",
    url: str = "",
    notes: str = "",
) -> Path:
    sources_dir = root / SOURCES_DIR
    sources_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(title)
    source_path = sources_dir / f"{slug}.md"
    suffix = 2
    while source_path.exists():
        source_path = sources_dir / f"{slug}-{suffix}.md"
        suffix += 1

    frontmatter = {
        "title": title,
        "type": source_type,
        "author": author,
        "year": year,
        "url": url,
    }
    body = (f"## Summary\n\n\n## Key Quotes\n\n* \n\n## Relevance\n\n\n## Notes\n\n{notes.strip()}").rstrip()
    atomic_write_text(
        source_path,
        f"---\n{yaml.safe_dump(frontmatter, sort_keys=False).strip()}\n---\n\n{body}\n",
    )
    return source_path


def ensure_citation_tracking_files(root: Path, *, style: str = "APA") -> list[Path]:
    files = [
        (
            root / "research" / "citation-log.md",
            f"# Citation Log\n\n## Style\n\n{style}\n\n| Section | Source | Use | Notes |\n| --- | --- | --- | --- |\n",
        ),
        (
            root / "research" / "bibliography-notes.md",
            "# Bibliography Notes\n\n"
            f"## Style\n\n{style}\n\n"
            "## Rules\n\n* Track in text citations\n* Track bibliography edge cases\n",
        ),
        (
            root / "research" / "source-usage-map.md",
            "# Source Usage Map\n\n## Sections\n\n* Introduction\n* Methods\n* Results\n* Discussion\n",
        ),
    ]
    created_paths: list[Path] = []
    for path, content in files:
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(path, content)
        created_paths.append(path)
    return created_paths


@project_locked
def add_scene(root: Path, chapter_ref: str, title: str, body: str = "") -> Path:
    from openscribe.editing import FileEdit, apply_edits

    if not title.strip() or "\n" in title or "\r" in title:
        raise ValueError("Scene titles must be nonempty single lines.")
    if parse_scenes(body) or "openscribe-scene-id:" in body:
        raise ValueError("Scene prose cannot introduce additional scene headings or IDs.")
    chapter = find_chapter(root, chapter_ref)
    before = chapter.path.read_bytes()
    text = before.decode("utf-8")
    metadata, current_body = parse_frontmatter(text)
    scene_heading = f"## {title.strip()}\n<!-- openscribe-scene-id: {new_scene_id()} -->\n\n"
    scene_body = body.strip()
    new_scene = scene_heading + (scene_body + "\n" if scene_body else "")
    separator = "\n\n" if current_body.strip() else ""
    updated = (
        f"---\n{yaml.safe_dump(metadata, sort_keys=False).strip()}\n---\n\n{current_body.rstrip()}{separator}{new_scene}".rstrip()
        + "\n"
    )
    apply_edits(root, (FileEdit(chapter.path, before, updated.encode("utf-8")),), "automatic backup before adding scene")
    return chapter.path


def add_screenplay_scene(root: Path, chapter_ref: str, slugline: str, body: str = "") -> Path:
    normalized_slugline = slugline.strip().upper()
    return add_scene(root, chapter_ref, normalized_slugline, body=body)


def update_part_title(root: Path, part: str, title: str) -> Path:
    part_path = resolve_part_path(root, part)
    metadata_path = part_path / PART_FILE
    metadata = {}
    if metadata_path.exists():
        metadata = validate_part_metadata(
            load_yaml(metadata_path, default={}),
            f"Part metadata '{metadata_path}'",
        )
    metadata["title"] = title
    write_yaml(metadata_path, metadata)
    return part_path


def update_goals(
    root: Path,
    *,
    draft_word_target: int | None = None,
    session_word_target: int | None = None,
    deadline: str | None = None,
) -> Path:
    config = load_project_config(root)
    goals = config.setdefault("goals", {})
    if draft_word_target is not None:
        goals["draft_word_target"] = draft_word_target
    if session_word_target is not None:
        goals["session_word_target"] = session_word_target
    if deadline is not None:
        goals["deadline"] = deadline
    return save_project_config(root, config)


def update_research_compile_settings(
    root: Path,
    *,
    citation_style: str | None = None,
    include_bibliography: bool | None = None,
    include_reference_heading: bool | None = None,
    bibliography_title: str | None = None,
) -> Path:
    config = load_project_config(root)
    compile_config = config.setdefault("compile", {})
    research = compile_config.setdefault("research", {})
    if citation_style is not None:
        research["citation_style"] = citation_style
    if include_bibliography is not None:
        research["include_bibliography"] = include_bibliography
    if include_reference_heading is not None:
        research["include_reference_heading"] = include_reference_heading
    if bibliography_title is not None:
        research["bibliography_title"] = bibliography_title
    return save_project_config(root, config)


@staged_operation("automatic backup before part reorder")
def reorder_part(root: Path, part: str, position: int) -> list[Path]:
    manuscript = root / "manuscript"
    parts = sorted([child for child in manuscript.iterdir() if child.is_dir()])
    if not parts:
        raise FileNotFoundError("No manuscript part exists yet.")

    target_path = resolve_part_path(root, part)
    reordered = [child for child in parts if child != target_path]
    bounded_position = max(1, min(position, len(parts)))
    reordered.insert(bounded_position - 1, target_path)
    _renumber_parts(reordered)
    return sorted([child for child in manuscript.iterdir() if child.is_dir()])


@staged_operation("automatic backup before chapter reorder")
def reorder_chapter(root: Path, chapter_ref: str, position: int, part: str | None = None) -> list[Path]:
    chapter = find_chapter(root, chapter_ref)
    source_path = chapter.path
    target_part_path = resolve_part_path(root, part) if part else source_path.parent

    target_chapters = sorted([child for child in target_part_path.glob("*.md") if child.name != PART_FILE])
    if source_path.parent == target_part_path:
        target_chapters = [child for child in target_chapters if child != source_path]
    bounded_position = max(1, min(position, len(target_chapters) + 1))

    moved_path = source_path
    if source_path.parent != target_part_path:
        moved_path = target_part_path / source_path.name
        source_path.rename(moved_path)
        _renumber_chapters(source_path.parent)

    reordered = sorted(
        [child for child in target_part_path.glob("*.md") if child.name != PART_FILE and child != moved_path]
    )
    reordered.insert(bounded_position - 1, moved_path)
    _renumber_chapters(target_part_path, reordered)
    return sorted([child for child in target_part_path.glob("*.md") if child.name != PART_FILE])


@project_locked
def update_chapter_metadata(
    root: Path,
    chapter_ref: str,
    *,
    title: str | None = None,
    status: str | None = None,
    label: str | None = None,
    synopsis: str | None = None,
    pov: str | None = None,
    word_target: int | None = None,
    notes: str | None = None,
    expected: bytes | None = None,
) -> Path:
    from openscribe.editing import EditConflictError, FileEdit, apply_edits

    chapter = find_chapter(root, chapter_ref)
    before = chapter.path.read_bytes()
    if expected is not None and before != expected:
        raise EditConflictError("Chapter metadata changed on disk. Reload before saving.")
    text = before.decode("utf-8")
    metadata, body = parse_frontmatter(text)
    metadata.setdefault("chapter_id", chapter.chapter_id)
    metadata.setdefault("title", chapter.title)
    metadata.setdefault("status", chapter.status)
    metadata.setdefault("label", chapter.label)
    metadata.setdefault("synopsis", chapter.synopsis)
    metadata.setdefault("pov", chapter.pov)
    metadata.setdefault("word_target", chapter.word_target)
    metadata.setdefault("notes", chapter.notes)

    if title is not None:
        metadata["title"] = title
    if status is not None:
        metadata["status"] = status
    if label is not None:
        metadata["label"] = label
    if synopsis is not None:
        metadata["synopsis"] = synopsis
    if pov is not None:
        metadata["pov"] = pov
    if word_target is not None:
        metadata["word_target"] = word_target
    if notes is not None:
        metadata["notes"] = notes

    validate_chapter_metadata(metadata, "Updated chapter metadata")
    updated = f"---\n{yaml.safe_dump(metadata, sort_keys=False).strip()}\n---\n\n{body}"
    apply_edits(root, (FileEdit(chapter.path, before, updated.encode("utf-8")),), "automatic backup before metadata save")
    return chapter.path


@project_locked
def update_chapter_body(root: Path, chapter_ref: str, visible_body: str, *, expected: bytes | None = None) -> Path:
    from openscribe.editing import EditConflictError, FileEdit, apply_edits

    chapter = find_chapter(root, chapter_ref)
    original_bytes = chapter.path.read_bytes()
    if expected is not None and original_bytes != expected:
        raise EditConflictError("Chapter changed on disk. Reload and review before saving.")
    original_text = original_bytes.decode("utf-8")
    metadata, original_body = parse_frontmatter(original_text)
    _, original_scenes = _parse_scene_layout(original_body)
    new_preamble, new_scenes = _parse_scene_layout(visible_body)

    if original_scenes:
        if any(not scene.scene_id for scene in original_scenes):
            raise ValueError("Scene identity is missing. Run `openscribe migrate repair` first.")
        if [scene.title for scene in new_scenes] != [scene.title for scene in original_scenes]:
            raise ValueError(
                "Chapter editing cannot infer scene identity after heading changes. "
                "Use the scene editor or scene move/split/merge commands; your draft has not been saved."
            )
        for scene, original in zip(new_scenes, original_scenes, strict=True):
            if scene.scene_id and scene.scene_id != original.scene_id:
                raise ValueError("Scene identity cannot be replaced in the chapter editor.")
            scene.scene_id = original.scene_id
    else:
        for scene in new_scenes:
            scene.scene_id = new_scene_id()

    updated_body = _render_scene_layout(new_preamble, new_scenes) if new_scenes else visible_body.rstrip() + "\n"
    apply_edits(root, (FileEdit(chapter.path, original_bytes, _chapter_text(metadata, updated_body).encode("utf-8")),),
                "automatic backup before chapter save")
    return chapter.path


@project_locked
def update_scene_body(
    root: Path, chapter_ref: str, scene_ref: str, body: str, *, expected: bytes | None = None
) -> Path:
    from openscribe.editing import EditConflictError, FileEdit, apply_edits

    chapter = find_chapter(root, chapter_ref)
    original_bytes = chapter.path.read_bytes()
    if expected is not None and original_bytes != expected:
        raise EditConflictError("Chapter changed on disk. Reload and review before saving.")
    if parse_scenes(body) or "openscribe-scene-id:" in body:
        raise ValueError("Use scene commands to change structure, not headings or identity markers inside scene prose.")
    original_text = original_bytes.decode("utf-8")
    metadata, chapter_body = parse_frontmatter(original_text)
    preamble, scenes = _parse_scene_layout(chapter_body)
    scene = scenes[_find_scene_index(scenes, scene_ref)]
    scene.body = body.strip()
    updated = _chapter_text(metadata, _render_scene_layout(preamble, scenes)).encode("utf-8")
    apply_edits(root, (FileEdit(chapter.path, original_bytes, updated),), "automatic backup before scene save")
    return chapter.path


def cycle_chapter_label(root: Path, chapter_ref: str, labels: list[str] | None = None) -> Path:
    chapter = find_chapter(root, chapter_ref)
    label_order = labels or _default_label_order(root)
    try:
        next_index = (label_order.index(chapter.label) + 1) % len(label_order)
    except ValueError:
        next_index = 0
    return update_chapter_metadata(root, chapter_ref, label=label_order[next_index])


def cycle_chapter_pov(root: Path, chapter_ref: str) -> Path:
    chapter = find_chapter(root, chapter_ref)
    pov_order = [""] + [value for value in _known_povs(root) if value]
    if chapter.pov and chapter.pov not in pov_order:
        pov_order.append(chapter.pov)
    try:
        next_index = (pov_order.index(chapter.pov) + 1) % len(pov_order)
    except ValueError:
        next_index = 0
    return update_chapter_metadata(root, chapter_ref, pov=pov_order[next_index])


def adjust_chapter_word_target(root: Path, chapter_ref: str, delta: int) -> Path:
    chapter = find_chapter(root, chapter_ref)
    next_target = max(0, int(chapter.word_target or 0) + delta)
    return update_chapter_metadata(root, chapter_ref, word_target=next_target)


def batch_update_chapters(
    root: Path,
    *,
    match_status: str | None = None,
    match_label: str | None = None,
    match_pov: str | None = None,
    match_part: str | None = None,
    match_text: str | None = None,
    title: str | None = None,
    status: str | None = None,
    label: str | None = None,
    synopsis: str | None = None,
    pov: str | None = None,
    word_target: int | None = None,
    notes: str | None = None,
) -> list[Path]:
    matches = find_chapters(
        root,
        status=match_status,
        label=match_label,
        pov=match_pov,
        part=match_part,
        text=match_text,
    )
    updated_paths: list[Path] = []
    for chapter in matches:
        updated_paths.append(
            update_chapter_metadata(
                root,
                chapter.slug,
                title=title,
                status=status,
                label=label,
                synopsis=synopsis,
                pov=pov,
                word_target=word_target,
                notes=notes,
            )
        )
    return updated_paths


def _default_label_order(root: Path) -> list[str]:
    baseline = ["default", "setup", "scene", "action", "research"]
    labels = []
    for value in baseline + sorted({chapter.label for chapter in list_chapters(root) if chapter.label}):
        if value not in labels:
            labels.append(value)
    return labels


def _known_povs(root: Path) -> list[str]:
    values: list[str] = []
    for chapter in list_chapters(root):
        if chapter.pov and chapter.pov not in values:
            values.append(chapter.pov)
    return values


def _load_schedule_rows(schedule_path: Path) -> list[dict[str, str]]:
    suffix = schedule_path.suffix.lower()
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with schedule_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            return [_normalize_schedule_row(row) for row in reader if row]
    if suffix == ".json":
        data = json.loads(schedule_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("sessions", [])
        if not isinstance(data, list):
            raise ValueError("Conference schedule JSON must contain a list or a top level 'sessions' list.")
        return [_normalize_schedule_row(dict(item)) for item in data if isinstance(item, dict)]
    if suffix in {".yaml", ".yml"}:
        data = load_yaml(schedule_path, default=[])
        if isinstance(data, dict):
            data = data.get("sessions", [])
        if not isinstance(data, list):
            raise ValueError("Conference schedule YAML must contain a list or a top level 'sessions' list.")
        return [_normalize_schedule_row(dict(item)) for item in data if isinstance(item, dict)]
    raise ValueError("Conference schedule import supports .csv, .tsv, .json, .yaml, and .yml files.")


def _normalize_schedule_row(row: dict[str, Any]) -> dict[str, str]:
    normalized = {
        slugify(str(key)).replace("-", "_"): str(value).strip() for key, value in row.items() if key is not None
    }
    return {
        "title": normalized.get("title") or normalized.get("session") or normalized.get("name") or "",
        "day": normalized.get("day") or normalized.get("date") or "",
        "time": normalized.get("time") or normalized.get("slot") or "",
        "room": normalized.get("room") or normalized.get("location") or "",
        "format": normalized.get("format") or normalized.get("type") or "",
        "presenter": normalized.get("presenter") or normalized.get("speaker") or normalized.get("author") or "",
        "status": normalized.get("status") or "planned",
        "notes": normalized.get("notes") or normalized.get("summary") or "",
    }


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return {}, text

    parts = text.split("\n---\n", maxsplit=1)
    if len(parts) != 2:
        return {}, text

    _, remainder = parts
    raw_frontmatter = text[4 : text.find("\n---\n")]
    try:
        metadata = yaml.safe_load(raw_frontmatter) or {}
    except yaml.YAMLError as exc:
        raise SchemaValidationError(f"Invalid YAML frontmatter: {exc}") from exc
    return require_mapping(metadata, "Frontmatter"), remainder.lstrip("\n")


def list_story_ideas(root: Path) -> list[StoryIdea]:
    ideas_dir = story_ideas_path(root)
    if not ideas_dir.exists():
        return []

    ideas: list[StoryIdea] = []
    for idea_path in sorted(ideas_dir.glob("*.md")):
        metadata, body = parse_frontmatter(idea_path.read_text(encoding="utf-8"))
        validate_story_metadata(metadata, f"Story idea frontmatter in '{idea_path}'")
        ideas.append(
            StoryIdea(
                path=idea_path,
                title=str(metadata.get("title", idea_path.stem)),
                premise=str(metadata.get("premise", "")),
                genre=str(metadata.get("genre", "")),
                tone=str(metadata.get("tone", "")),
                status=str(metadata.get("status", "seed")),
                body=body,
                slug=idea_path.stem,
            )
        )
    return ideas


def find_story_idea(root: Path, idea_ref: str) -> StoryIdea:
    normalized = idea_ref.strip().lower()
    for idea in list_story_ideas(root):
        if idea.slug.lower() == normalized:
            return idea
        if idea.title.strip().lower() == normalized:
            return idea
        if idea.path.stem.lower() == normalized:
            return idea
    raise FileNotFoundError(f"Story idea '{idea_ref}' was not found.")


def list_auxiliary_documents(root: Path, category: str) -> list[AuxiliaryDocument]:
    category_path = root / category
    if not category_path.exists():
        return []

    documents: list[AuxiliaryDocument] = []
    for path in sorted(category_path.rglob("*.md")):
        if category == "notes" and STORY_IDEAS_DIR.replace("/", "\\") in str(path.relative_to(root)).replace("/", "\\"):
            continue
        text = path.read_text(encoding="utf-8")
        title = _title_from_markdown(path, text)
        documents.append(
            AuxiliaryDocument(
                path=path,
                title=title,
                body=text,
                category=category,
                slug=path.stem,
            )
        )
    return documents


def list_source_notes(root: Path) -> list[SourceDocument]:
    source_dir = root / SOURCES_DIR
    if not source_dir.exists():
        return []

    results: list[SourceDocument] = []
    for path in sorted(source_dir.glob("*.md")):
        metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        validate_source_metadata(metadata, f"Source frontmatter in '{path}'")
        results.append(
            SourceDocument(
                path=path,
                title=str(metadata.get("title", path.stem.replace("-", " ").title())),
                source_type=str(metadata.get("type", "source")),
                author=str(metadata.get("author", "")),
                year=str(metadata.get("year", "")),
                url=str(metadata.get("url", "")),
                body=body,
                slug=path.stem,
            )
        )
    return results


@project_locked
def list_chapters(root: Path) -> list[ChapterDocument]:
    from openscribe.snapshots import recover_interrupted_restores

    recover_interrupted_restores(root)
    manuscript = root / "manuscript"
    chapters: list[ChapterDocument] = []
    seen_ids: set[str] = set()
    seen_scene_ids: set[str] = set()
    for part_path in sorted([child for child in manuscript.iterdir() if child.is_dir()]):
        part_title = load_part_title(part_path)
        for chapter_path in sorted(part_path.glob("*.md")):
            text = chapter_path.read_text(encoding="utf-8")
            metadata, body = parse_frontmatter(text)
            validate_chapter_metadata(metadata, f"Chapter frontmatter in '{chapter_path}'")
            chapter_id = str(metadata.get("chapter_id", ""))
            if chapter_id and chapter_id in seen_ids:
                raise SchemaValidationError("Duplicate chapter ID. No files were modified.")
            seen_ids.add(chapter_id)
            for scene in parse_scenes(body):
                if scene.scene_id and scene.scene_id in seen_scene_ids:
                    raise SchemaValidationError("Duplicate scene ID. No files were modified.")
                seen_scene_ids.add(scene.scene_id)
            chapters.append(
                ChapterDocument(
                    path=chapter_path,
                    chapter_id=chapter_id,
                    title=metadata.get("title", chapter_path.stem),
                    status=metadata.get("status", "draft"),
                    label=metadata.get("label", "default"),
                    synopsis=metadata.get("synopsis", ""),
                    pov=metadata.get("pov", ""),
                    word_target=int(metadata.get("word_target", 0) or 0),
                    notes=metadata.get("notes", ""),
                    body=body,
                    part=part_title,
                    part_id=part_path.name,
                    slug=chapter_path.stem,
                    scenes=parse_scenes(body),
                )
            )
    return chapters


def find_chapter(root: Path, chapter_ref: str) -> ChapterDocument:
    normalized = chapter_ref.strip().lower()
    chapters = list_chapters(root)
    for chapter in chapters:
        if chapter.chapter_id.lower() == normalized:
            return chapter
        if chapter.slug.lower() == normalized:
            return chapter
        if chapter.title.strip().lower() == normalized:
            return chapter
        if chapter.path.stem.lower() == normalized:
            return chapter
    raise FileNotFoundError(f"Chapter '{chapter_ref}' was not found.")


def load_part_title(part_path: Path) -> str:
    metadata_path = part_path / PART_FILE
    if metadata_path.exists():
        metadata = validate_part_metadata(
            load_yaml(metadata_path, default={}),
            f"Part metadata '{metadata_path}'",
        )
        title = str(metadata.get("title", "")).strip()
        if title:
            return title
    return part_path.name


def load_part_metadata(root: Path, part: str) -> dict[str, Any]:
    part_path = resolve_part_path(root, part)
    metadata_path = part_path / PART_FILE
    metadata = {}
    if metadata_path.exists():
        metadata = validate_part_metadata(
            load_yaml(metadata_path, default={}),
            f"Part metadata '{metadata_path}'",
        )
    metadata["title"] = str(metadata.get("title", load_part_title(part_path)))
    metadata["part_id"] = part_path.name
    metadata["path"] = str(part_path)
    return metadata


def find_chapters(
    root: Path,
    *,
    status: str | None = None,
    label: str | None = None,
    pov: str | None = None,
    part: str | None = None,
    text: str | None = None,
) -> list[ChapterDocument]:
    chapters = list_chapters(root)
    results: list[ChapterDocument] = []
    part_filter = part.strip().lower() if part else None
    text_filter = text.strip().lower() if text else None

    for chapter in chapters:
        if status and chapter.status.strip().lower() != status.strip().lower():
            continue
        if label and chapter.label.strip().lower() != label.strip().lower():
            continue
        if pov and chapter.pov.strip().lower() != pov.strip().lower():
            continue
        if part_filter and part_filter not in {
            chapter.part.strip().lower(),
            chapter.part_id.strip().lower(),
            slugify(chapter.part),
        }:
            continue
        if text_filter:
            haystacks = [
                chapter.title,
                chapter.synopsis,
                chapter.notes,
                chapter.body,
            ]
            if not any(text_filter in haystack.lower() for haystack in haystacks):
                continue
        results.append(chapter)

    return results


def find_scenes(
    root: Path,
    *,
    status: str | None = None,
    label: str | None = None,
    pov: str | None = None,
    part: str | None = None,
    text: str | None = None,
) -> list[SceneMatch]:
    results: list[SceneMatch] = []
    scene_filter = text.strip().lower() if text else None
    for chapter in find_chapters(root, status=status, label=label, pov=pov, part=part):
        for scene in chapter.scenes:
            haystacks = [scene.title, scene.body, chapter.title, chapter.synopsis, chapter.notes]
            if scene_filter and not any(scene_filter in haystack.lower() for haystack in haystacks):
                continue
            results.append(
                SceneMatch(
                    chapter=chapter,
                    chapter_title=chapter.title,
                    part=chapter.part,
                    scene_id=scene.scene_id,
                    scene_title=scene.title,
                    scene_slug=scene.slug,
                    scene_body=scene.body,
                )
            )
    return results


def chapter_report(root: Path) -> dict[str, Any]:
    chapters = list_chapters(root)
    config = load_project_config(root)
    goals = config.get("goals", {})
    by_status: dict[str, int] = {}
    by_label: dict[str, int] = {}
    by_pov: dict[str, int] = {}
    by_part: dict[str, int] = {}
    part_word_totals: dict[str, int] = {}
    scene_title_counts: dict[str, int] = {}

    for chapter in chapters:
        _increment(by_status, chapter.status or "n/a")
        _increment(by_label, chapter.label or "n/a")
        _increment(by_pov, chapter.pov or "n/a")
        _increment(by_part, chapter.part or "n/a")
        part_word_totals[chapter.part] = part_word_totals.get(chapter.part, 0) + chapter.word_count
        for scene in chapter.scenes:
            _increment(scene_title_counts, scene.title or "n/a")

    return {
        "chapter_count": len(chapters),
        "word_count": sum(chapter.word_count for chapter in chapters),
        "scene_count": sum(chapter.scene_count for chapter in chapters),
        "by_status": by_status,
        "by_label": by_label,
        "by_pov": by_pov,
        "by_part": by_part,
        "part_word_totals": part_word_totals,
        "scene_title_counts": scene_title_counts,
        "goals": manuscript_goal_stats(chapters, goals),
    }


def manuscript_goal_stats(chapters: list[ChapterDocument], goals: dict[str, Any]) -> dict[str, Any]:
    total_words = sum(chapter.word_count for chapter in chapters)
    total_target = sum(chapter.word_target for chapter in chapters)
    draft_word_target = int(goals.get("draft_word_target", 0) or 0)
    session_word_target = int(goals.get("session_word_target", 0) or 0)
    deadline = str(goals.get("deadline", "") or "")
    progress_target = draft_word_target or total_target
    progress_percent = round((total_words / progress_target) * 100, 1) if progress_target else 0.0
    return {
        "draft_word_target": draft_word_target,
        "session_word_target": session_word_target,
        "deadline": deadline,
        "chapter_word_target_total": total_target,
        "progress_target": progress_target,
        "progress_percent": progress_percent,
        "words_remaining": max(progress_target - total_words, 0) if progress_target else 0,
    }


def linked_sources_for_chapter(root: Path, chapter: ChapterDocument) -> list[SourceDocument]:
    source_notes = list_source_notes(root)
    haystacks = [
        chapter.title.lower(),
        chapter.synopsis.lower(),
        chapter.notes.lower(),
        chapter.body.lower(),
    ]
    matches: list[SourceDocument] = []
    for source in source_notes:
        terms = {
            source.slug.replace("-", " ").lower(),
            source.title.lower(),
        }
        if source.author:
            terms.add(source.author.lower())
        if any(term.strip() and any(term in haystack for haystack in haystacks) for term in terms):
            matches.append(source)
    return matches


def insert_citation_reference(
    root: Path,
    chapter_ref: str,
    source_ref: str,
    *,
    scene_ref: str | None = None,
    citation_style: str = "APA",
) -> Path:
    chapter = find_chapter(root, chapter_ref)
    source = find_source_note(root, source_ref)
    text = chapter.path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)
    citation_line = _citation_marker(source, citation_style)

    if scene_ref:
        updated_body = _insert_into_scene(body, scene_ref, citation_line)
    else:
        updated_body = body.rstrip() + ("\n\n" if body.strip() else "") + citation_line + "\n"

    atomic_write_text(
        chapter.path,
        f"---\n{yaml.safe_dump(metadata, sort_keys=False).strip()}\n---\n\n{updated_body.rstrip()}\n",
    )
    return chapter.path


def find_source_note(root: Path, source_ref: str) -> SourceDocument:
    normalized = source_ref.strip().lower()
    for source in list_source_notes(root):
        if source.slug.lower() == normalized or source.title.strip().lower() == normalized:
            return source
    raise FileNotFoundError(f"Source note '{source_ref}' was not found.")


def resolve_editor_target(
    root: Path, kind: str, reference: str | None = None, *, text: str | None = None, index: int = 1
) -> Path:
    normalized_kind = kind.strip().lower()
    if normalized_kind == "chapter":
        if not reference:
            raise FileNotFoundError("Chapter reference is required.")
        return find_chapter(root, reference).path
    if normalized_kind == "part":
        if not reference:
            raise FileNotFoundError("Part reference is required.")
        return resolve_part_path(root, reference)
    if normalized_kind == "search":
        if not text:
            raise FileNotFoundError("Search text is required.")
        matches = find_chapters(root, text=text)
        if not matches:
            raise FileNotFoundError("No chapter matched the search text.")
        bounded_index = max(1, min(index, len(matches)))
        return matches[bounded_index - 1].path
    raise FileNotFoundError(f"Unsupported editor target '{kind}'.")


def open_in_editor(path: Path) -> None:
    os.startfile(str(path))


def scene_report(root: Path, *, text: str | None = None) -> dict[str, Any]:
    matches = find_scenes(root, text=text)
    by_chapter: dict[str, int] = {}
    by_part: dict[str, int] = {}
    for match in matches:
        _increment(by_chapter, match.chapter_title)
        _increment(by_part, match.part)
    return {
        "scene_matches": len(matches),
        "by_chapter": by_chapter,
        "by_part": by_part,
        "matches": matches,
    }


def chapter_deadline_status(root: Path) -> dict[str, Any]:
    config = load_project_config(root)
    deadline_text = str(config.get("goals", {}).get("deadline", "") or "")
    if not deadline_text:
        return {"deadline": "", "days_remaining": None}
    try:
        deadline_date = date.fromisoformat(deadline_text)
    except ValueError:
        return {"deadline": deadline_text, "days_remaining": None}
    return {"deadline": deadline_text, "days_remaining": (deadline_date - date.today()).days}


def source_link_map(root: Path) -> dict[str, list[ChapterDocument]]:
    links: dict[str, list[ChapterDocument]] = {}
    chapters = list_chapters(root)
    for source in list_source_notes(root):
        matches = [chapter for chapter in chapters if source in linked_sources_for_chapter(root, chapter)]
        links[source.slug] = matches
    return links


def _insert_into_scene(body: str, scene_ref: str, citation_line: str) -> str:
    scenes = parse_scenes(body)
    if not scenes:
        raise FileNotFoundError("The chapter does not contain scene headings.")
    normalized = scene_ref.strip().lower()
    lines = body.splitlines()
    heading_indexes = [index for index, line in enumerate(lines) if line.startswith("## ")]
    for idx, scene in enumerate(scenes):
        if normalized not in {scene.scene_id.lower(), scene.slug.lower(), scene.title.strip().lower()}:
            continue
        start = heading_indexes[idx] + 1
        if start < len(lines) and lines[start].strip().startswith("<!-- openscribe-scene-id:"):
            start += 1
        end = heading_indexes[idx + 1] if idx + 1 < len(heading_indexes) else len(lines)
        scene_lines = lines[start:end]
        while scene_lines and not scene_lines[-1].strip():
            scene_lines.pop()
        scene_lines.append("")
        scene_lines.append(citation_line)
        lines[start:end] = scene_lines
        return "\n".join(lines).rstrip() + "\n"
    raise FileNotFoundError(f"Scene '{scene_ref}' was not found.")


def _citation_marker(source: SourceDocument, citation_style: str) -> str:
    if citation_style.strip().upper() == "CHICAGO":
        return f'> Citation: {source.author or "Unknown"}. "{source.title}." {source.year or "n.d."}'
    if citation_style.strip().upper() == "MLA":
        return f"> Citation: {source.author or 'Unknown'}. {source.title}. {source.year or 'n.d.'}"
    return f"> Citation: {source.author or source.title} ({source.year or 'n.d.'})"


def find_scene(chapter: ChapterDocument, scene_ref: str) -> SceneDocument:
    scenes = chapter.scenes
    return scenes[_find_scene_index(scenes, scene_ref)]


def plan_reorder_scene(
    root: Path,
    chapter_ref: str,
    scene_ref: str,
    position: int,
    *,
    target_chapter_ref: str | None = None,
) -> SceneOperation:
    source_chapter = find_chapter(root, chapter_ref)
    target_chapter = find_chapter(root, target_chapter_ref) if target_chapter_ref else source_chapter
    source_text = source_chapter.path.read_text(encoding="utf-8")
    source_metadata, source_body = parse_frontmatter(source_text)
    source_preamble, source_scenes = _parse_scene_layout(source_body)
    source_index = _find_scene_index(source_scenes, scene_ref)
    moved_scene = source_scenes.pop(source_index)

    if target_chapter.path == source_chapter.path:
        target_metadata = source_metadata
        target_preamble = source_preamble
        target_scenes = source_scenes
    else:
        target_text = target_chapter.path.read_text(encoding="utf-8")
        target_metadata, target_body = parse_frontmatter(target_text)
        target_preamble, target_scenes = _parse_scene_layout(target_body)

    if position < 1 or position > len(target_scenes) + 1:
        raise ValueError(f"Scene position must be between 1 and {len(target_scenes) + 1}.")
    target_scenes.insert(position - 1, moved_scene)

    changes = [
        SceneFileChange(
            source_chapter.path,
            source_text,
            _chapter_text(source_metadata, _render_scene_layout(source_preamble, source_scenes)),
        )
    ]
    if target_chapter.path != source_chapter.path:
        changes.append(
            SceneFileChange(
                target_chapter.path,
                target_text,
                _chapter_text(target_metadata, _render_scene_layout(target_preamble, target_scenes)),
            )
        )
    return SceneOperation(
        summary=f"Move scene '{moved_scene.title}' to position {position} in '{target_chapter.title}'.",
        changes=tuple(change for change in changes if change.before != change.after),
    )


def plan_split_scene(
    root: Path,
    chapter_ref: str,
    scene_ref: str,
    at_text: str,
    new_title: str,
) -> SceneOperation:
    chapter = find_chapter(root, chapter_ref)
    original_text = chapter.path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(original_text)
    preamble, scenes = _parse_scene_layout(body)
    scene_index = _find_scene_index(scenes, scene_ref)
    scene = scenes[scene_index]
    split_at = scene.body.lower().find(at_text.lower())
    if not at_text.strip() or split_at <= 0 or split_at >= len(scene.body):
        raise ValueError("Split text must identify a nonempty point inside the scene body.")
    first_body = scene.body[:split_at].rstrip()
    second_body = scene.body[split_at:].lstrip()
    scene.body = first_body
    new_scene = SceneDocument(
        scene_id=new_scene_id(),
        title=new_title.strip(),
        body=second_body,
        slug=slugify(new_title),
    )
    if not new_scene.title:
        raise ValueError("New scene title cannot be empty.")
    scenes.insert(scene_index + 1, new_scene)
    updated_text = _chapter_text(metadata, _render_scene_layout(preamble, scenes))
    return SceneOperation(
        summary=f"Split scene '{scene.title}' into '{scene.title}' and '{new_scene.title}'.",
        changes=(SceneFileChange(chapter.path, original_text, updated_text),),
    )


def plan_merge_scene(
    root: Path,
    chapter_ref: str,
    scene_ref: str,
    other_scene_ref: str,
    *,
    other_chapter_ref: str | None = None,
) -> SceneOperation:
    chapter = find_chapter(root, chapter_ref)
    other_chapter = find_chapter(root, other_chapter_ref) if other_chapter_ref else chapter
    original_text = chapter.path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(original_text)
    preamble, scenes = _parse_scene_layout(body)
    scene_index = _find_scene_index(scenes, scene_ref)
    scene = scenes[scene_index]

    if other_chapter.path == chapter.path:
        other_text = original_text
        other_metadata = metadata
        other_preamble = preamble
        other_scenes = scenes
    else:
        other_text = other_chapter.path.read_text(encoding="utf-8")
        other_metadata, other_body = parse_frontmatter(other_text)
        other_preamble, other_scenes = _parse_scene_layout(other_body)
    other_index = _find_scene_index(other_scenes, other_scene_ref)
    other_scene = other_scenes[other_index]
    if scene.scene_id == other_scene.scene_id:
        raise ValueError("A scene cannot be merged with itself.")

    scene.body = "\n\n".join(part for part in (scene.body.rstrip(), other_scene.body.lstrip()) if part)
    other_scenes.pop(other_index)
    changes = [
        SceneFileChange(
            chapter.path,
            original_text,
            _chapter_text(metadata, _render_scene_layout(preamble, scenes)),
        )
    ]
    if other_chapter.path != chapter.path:
        changes.append(
            SceneFileChange(
                other_chapter.path,
                other_text,
                _chapter_text(other_metadata, _render_scene_layout(other_preamble, other_scenes)),
            )
        )
    return SceneOperation(
        summary=f"Merge scene '{other_scene.title}' into '{scene.title}'.",
        changes=tuple(change for change in changes if change.before != change.after),
    )


@project_locked
def apply_scene_operation(root: Path, operation: SceneOperation) -> Path:
    if not operation.changes:
        raise ValueError("The scene operation would not change the manuscript.")

    from openscribe.editing import FileEdit, apply_edits

    edits = []
    for change in operation.changes:
        before = change.path.read_bytes()
        if before.decode("utf-8").replace("\r\n", "\n") != change.before.replace("\r\n", "\n"):
            raise ValueError("Scene plan is stale. Preview again before applying.")
        edits.append(FileEdit(change.path, before, change.after.encode("utf-8")))
    return apply_edits(root, tuple(edits), f"automatic backup before {operation.summary}")


def scene_operation_diff(root: Path, operation: SceneOperation) -> str:
    chunks: list[str] = []
    for change in operation.changes:
        relative_path = change.path.relative_to(root).as_posix()
        chunks.append(
            "\n".join(
                difflib.unified_diff(
                    change.before.splitlines(),
                    change.after.splitlines(),
                    fromfile=f"before/{relative_path}",
                    tofile=f"after/{relative_path}",
                    lineterm="",
                )
            )
        )
    return "\n\n".join(chunk for chunk in chunks if chunk.strip()) or "[No changes]"


def parse_scenes(body: str) -> list[SceneDocument]:
    return _parse_scene_layout(body)[1]


def _parse_scene_layout(body: str) -> tuple[str, list[SceneDocument]]:
    matches = _scene_headings(body)
    if not matches:
        return body.rstrip(), []

    preamble = body[: matches[0].start()].strip("\r\n")
    scenes: list[SceneDocument] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        scene_title = match.group(1).strip()
        content = body[start:end]
        marker = SCENE_MARKER_PATTERN.match(content)
        scene_id = marker.group(1).lower() if marker else ""
        scene_body = content[marker.end() if marker else 0 :].strip("\r\n")
        scenes.append(SceneDocument(scene_id=scene_id, title=scene_title, body=scene_body, slug=slugify(scene_title)))
    return preamble, scenes


def _scene_headings(body: str) -> list[re.Match]:
    headings: list[re.Match] = []
    fence = ""
    for match in re.finditer(r"^.*$", body, re.MULTILINE):
        line = match.group().rstrip("\r")
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            run = marker.group(1)
            if not fence:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence) and not line[marker.end():].strip():
                fence = ""
            continue
        if not fence:
            heading = re.compile(r"##[ \t]+([^\r\n]+?)[ \t]*\r?$").match(body, match.start(), match.end())
            if heading:
                headings.append(heading)
    return headings


def _render_scene_layout(preamble: str, scenes: list[SceneDocument]) -> str:
    blocks: list[str] = []
    if preamble.strip():
        blocks.append(preamble.strip("\r\n"))
    for scene in scenes:
        block = f"## {scene.title}\n<!-- openscribe-scene-id: {scene.scene_id} -->"
        if scene.body.strip():
            block += f"\n\n{scene.body.strip(chr(13) + chr(10))}"
        blocks.append(block)
    return ("\n\n".join(blocks).rstrip("\r\n") + "\n") if blocks else ""


def _chapter_text(metadata: dict[str, Any], body: str) -> str:
    return f"---\n{yaml.safe_dump(metadata, sort_keys=False).strip()}\n---\n\n{body}"


def _find_scene_index(scenes: list[SceneDocument], scene_ref: str) -> int:
    normalized = scene_ref.strip().lower()
    for index, scene in enumerate(scenes):
        if normalized in {scene.scene_id.lower(), scene.slug.lower(), scene.title.strip().lower()}:
            return index
    raise FileNotFoundError(f"Scene '{scene_ref}' was not found.")


def import_folder_project(
    target_path: Path,
    source_path: Path,
    title: str,
    template_name: str = "fiction",
    template_file: Path | None = None,
) -> Path:
    source_root = source_path.resolve()
    if not source_root.exists():
        raise FileNotFoundError(f"Source folder '{source_path}' was not found.")

    project_root_path = init_project_from_template(
        target_path, title, template_name=template_name, template_file=template_file
    )

    root_markdown_files = sorted(source_root.glob("*.md"))
    if root_markdown_files:
        create_part(project_root_path, "Imported Draft")
        for markdown_file in root_markdown_files:
            _import_markdown_as_chapter(project_root_path, markdown_file, part="Imported Draft")

    for child in sorted(source_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name.lower() in {"characters", "research", "notes"}:
            destination = project_root_path / child.name
            shutil.copytree(child, destination, dirs_exist_ok=True)
            continue
        markdown_files = sorted(child.glob("*.md"))
        if not markdown_files:
            continue
        create_part(project_root_path, child.name.replace("-", " ").title())
        for markdown_file in markdown_files:
            _import_markdown_as_chapter(
                project_root_path,
                markdown_file,
                part=child.name.replace("-", " ").title(),
            )

    return project_root_path


def _title_from_markdown(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return path.stem.replace("-", " ").title()


def _import_markdown_as_chapter(root: Path, source_file: Path, part: str) -> Path:
    text = source_file.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)
    title = str(metadata.get("title", _title_from_markdown(source_file, text)))
    chapter_path = create_chapter(
        root,
        title,
        part=part,
        status=str(metadata.get("status", "draft")),
        label=str(metadata.get("label", "default")),
        pov=str(metadata.get("pov", "")),
        word_target=int(metadata.get("word_target", 0) or 0),
        synopsis=str(metadata.get("synopsis", "")),
        notes=str(metadata.get("notes", "")),
    )
    created_metadata, _ = parse_frontmatter(chapter_path.read_text(encoding="utf-8"))
    imported_metadata = dict(metadata)
    imported_metadata.update(created_metadata)
    atomic_write_text(
        chapter_path,
        f"---\n{yaml.safe_dump(imported_metadata, sort_keys=False).strip()}\n---\n\n"
        + body.strip()
        + ("\n" if body.strip() else ""),
    )
    return chapter_path


def _increment(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


def _renumber_parts(parts: list[Path]) -> None:
    temp_paths: list[Path] = []
    for index, part_path in enumerate(parts, start=1):
        temp_path = part_path.with_name(f"tmp-part-{index:02d}-{part_path.name}")
        part_path.rename(temp_path)
        temp_paths.append(temp_path)

    for index, temp_path in enumerate(temp_paths, start=1):
        suffix = _name_without_number(temp_path.name, "part")
        final_path = temp_path.with_name(f"part-{index:02d}-{suffix}")
        temp_path.rename(final_path)
        _renumber_chapters(final_path)


def _renumber_chapters(part_path: Path, ordered_paths: list[Path] | None = None) -> None:
    chapter_paths = ordered_paths or sorted([child for child in part_path.glob("*.md") if child.name != PART_FILE])
    temp_paths: list[Path] = []
    for index, chapter_path in enumerate(chapter_paths, start=1):
        temp_path = chapter_path.with_name(f"tmp-ch-{index:02d}-{chapter_path.name}")
        chapter_path.rename(temp_path)
        temp_paths.append(temp_path)

    for index, temp_path in enumerate(temp_paths, start=1):
        suffix = _name_without_number(temp_path.stem, "ch")
        final_path = temp_path.with_name(f"ch-{index:02d}-{suffix}.md")
        temp_path.rename(final_path)


def _name_without_number(name: str, prefix: str) -> str:
    if prefix == "part":
        match = re.match(r"tmp-part-\d+-(?:part-\d+-)?(.+)$", name)
    else:
        match = re.match(r"tmp-ch-\d+-(?:ch-\d+-)?(.+)$", name)
    if match:
        return match.group(1)
    if prefix == "part":
        match = re.match(r"part-\d+-(.+)$", name)
    else:
        match = re.match(r"ch-\d+-(.+)$", name)
    if match:
        return match.group(1)
    return name
