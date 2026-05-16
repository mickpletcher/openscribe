from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
from typing import Any

import yaml

PROJECT_DIR = ".openscribe"
PROJECT_FILE = "project.yaml"
PART_FILE = "part.yaml"
STORY_IDEAS_DIR = "notes/story-ideas"
INDEX_DIR = ".openscribe/index"
SNAPSHOTS_DIR = ".openscribe/snapshots"
TEMPLATES_DIR = ".openscribe/templates"
CONFERENCE_DIR = "research/conferences"
PRESENTATIONS_DIR = "notes/presentations"
SOURCES_DIR = "research/sources"


@dataclass(slots=True)
class SceneDocument:
    title: str
    body: str
    slug: str


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
        return len([word for word in re.findall(r"\b[\w']+\b", self.body)])

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


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return cleaned or "untitled"


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

    resolved_template_name, template = load_template_definition(template_name, template_file)

    write_yaml(
        config_dir / PROJECT_FILE,
        {
            "title": title,
            "author": "",
            "version": 1,
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
        target_path = root / str(relative_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content.replace("{title}", title), encoding="utf-8")


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
        data = yaml.safe_load(template_file.read_text(encoding="utf-8")) or {}
        resolved_name = str(data.get("name", template_file.stem)).strip() or template_file.stem
        return slugify(resolved_name), data

    normalized = template_name.strip().lower()
    template = built_in_templates().get(normalized)
    if template is None:
        supported = ", ".join(sorted(built_in_templates()))
        raise ValueError(f"Unknown project template '{template_name}'. Use {supported} or provide --template-file.")
    return normalized, template


def load_project_config(root: Path) -> dict[str, Any]:
    config_path = root / PROJECT_DIR / PROJECT_FILE
    if not config_path.exists():
        raise FileNotFoundError(f"Missing project config at {config_path}")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
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
    return config


def save_project_config(root: Path, config: dict[str, Any]) -> Path:
    config_path = root / PROJECT_DIR / PROJECT_FILE
    write_yaml(config_path, config)
    return config_path


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
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


def create_part(root: Path, title: str) -> Path:
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
    idea_path.write_text(
        f"---\n{yaml.safe_dump(frontmatter, sort_keys=False).strip()}\n---\n\n{notes.strip()}".rstrip() + "\n",
        encoding="utf-8",
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
    part_path = resolve_part_path(root, part)
    chapter_number = next_chapter_number(part_path)
    chapter_slug = slugify(title)
    chapter_path = part_path / f"ch-{chapter_number:02d}-{chapter_slug}.md"
    frontmatter = {
        "title": title,
        "status": status,
        "label": label,
        "synopsis": synopsis,
        "pov": pov,
        "word_target": word_target,
        "notes": notes,
    }
    chapter_path.write_text(
        f"---\n{yaml.safe_dump(frontmatter, sort_keys=False).strip()}\n---\n\n",
        encoding="utf-8",
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

    for path, content in files:
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created_paths.append(path)
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
    body = (
        "## Summary\n\n\n"
        "## Key Quotes\n\n* \n\n"
        "## Relevance\n\n\n"
        "## Notes\n\n"
        f"{notes.strip()}"
    ).rstrip()
    source_path.write_text(
        f"---\n{yaml.safe_dump(frontmatter, sort_keys=False).strip()}\n---\n\n{body}\n",
        encoding="utf-8",
    )
    return source_path


def ensure_citation_tracking_files(root: Path, *, style: str = "APA") -> list[Path]:
    files = [
        (
            root / "research" / "citation-log.md",
            "# Citation Log\n\n"
            f"## Style\n\n{style}\n\n"
            "| Section | Source | Use | Notes |\n| --- | --- | --- | --- |\n",
        ),
        (
            root / "research" / "bibliography-notes.md",
            "# Bibliography Notes\n\n"
            f"## Style\n\n{style}\n\n"
            "## Rules\n\n* Track in text citations\n* Track bibliography edge cases\n",
        ),
        (
            root / "research" / "source-usage-map.md",
            "# Source Usage Map\n\n"
            "## Sections\n\n"
            "* Introduction\n* Methods\n* Results\n* Discussion\n",
        ),
    ]
    created_paths: list[Path] = []
    for path, content in files:
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created_paths.append(path)
    return created_paths


def add_scene(root: Path, chapter_ref: str, title: str, body: str = "") -> Path:
    chapter = find_chapter(root, chapter_ref)
    text = chapter.path.read_text(encoding="utf-8")
    metadata, current_body = parse_frontmatter(text)
    scene_heading = f"## {title.strip()}\n\n"
    scene_body = body.strip()
    new_scene = scene_heading + (scene_body + "\n" if scene_body else "")
    separator = "\n" if current_body.strip() else ""
    chapter.path.write_text(
        f"---\n{yaml.safe_dump(metadata, sort_keys=False).strip()}\n---\n\n{current_body.rstrip()}{separator}{new_scene}".rstrip() + "\n",
        encoding="utf-8",
    )
    return chapter.path


def add_screenplay_scene(root: Path, chapter_ref: str, slugline: str, body: str = "") -> Path:
    normalized_slugline = slugline.strip().upper()
    return add_scene(root, chapter_ref, normalized_slugline, body=body)


def update_part_title(root: Path, part: str, title: str) -> Path:
    part_path = resolve_part_path(root, part)
    write_yaml(part_path / PART_FILE, {"title": title})
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

    reordered = sorted([child for child in target_part_path.glob("*.md") if child.name != PART_FILE and child != moved_path])
    reordered.insert(bounded_position - 1, moved_path)
    _renumber_chapters(target_part_path, reordered)
    return sorted([child for child in target_part_path.glob("*.md") if child.name != PART_FILE])


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
) -> Path:
    chapter = find_chapter(root, chapter_ref)
    text = chapter.path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)
    metadata = {
        "title": metadata.get("title", chapter.title),
        "status": metadata.get("status", chapter.status),
        "label": metadata.get("label", chapter.label),
        "synopsis": metadata.get("synopsis", chapter.synopsis),
        "pov": metadata.get("pov", chapter.pov),
        "word_target": int(metadata.get("word_target", chapter.word_target) or 0),
        "notes": metadata.get("notes", chapter.notes),
    }

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

    chapter.path.write_text(
        f"---\n{yaml.safe_dump(metadata, sort_keys=False).strip()}\n---\n\n{body}",
        encoding="utf-8",
    )
    return chapter.path


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


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text

    parts = text.split("\n---\n", maxsplit=1)
    if len(parts) != 2:
        return {}, text

    _, remainder = parts
    raw_frontmatter = text[4 : text.find("\n---\n")]
    metadata = yaml.safe_load(raw_frontmatter) or {}
    return metadata, remainder.lstrip("\n")


def list_story_ideas(root: Path) -> list[StoryIdea]:
    ideas_dir = story_ideas_path(root)
    if not ideas_dir.exists():
        return []

    ideas: list[StoryIdea] = []
    for idea_path in sorted(ideas_dir.glob("*.md")):
        metadata, body = parse_frontmatter(idea_path.read_text(encoding="utf-8"))
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


def list_chapters(root: Path) -> list[ChapterDocument]:
    manuscript = root / "manuscript"
    chapters: list[ChapterDocument] = []
    for part_path in sorted([child for child in manuscript.iterdir() if child.is_dir()]):
        part_title = load_part_title(part_path)
        for chapter_path in sorted(part_path.glob("*.md")):
            text = chapter_path.read_text(encoding="utf-8")
            metadata, body = parse_frontmatter(text)
            chapters.append(
                ChapterDocument(
                    path=chapter_path,
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
        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
        title = str(metadata.get("title", "")).strip()
        if title:
            return title
    return part_path.name


def load_part_metadata(root: Path, part: str) -> dict[str, Any]:
    part_path = resolve_part_path(root, part)
    metadata_path = part_path / PART_FILE
    metadata = {}
    if metadata_path.exists():
        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
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


def chapter_report(root: Path) -> dict[str, Any]:
    chapters = list_chapters(root)
    config = load_project_config(root)
    goals = config.get("goals", {})
    by_status: dict[str, int] = {}
    by_label: dict[str, int] = {}
    by_pov: dict[str, int] = {}
    by_part: dict[str, int] = {}
    part_word_totals: dict[str, int] = {}

    for chapter in chapters:
        _increment(by_status, chapter.status or "n/a")
        _increment(by_label, chapter.label or "n/a")
        _increment(by_pov, chapter.pov or "n/a")
        _increment(by_part, chapter.part or "n/a")
        part_word_totals[chapter.part] = part_word_totals.get(chapter.part, 0) + chapter.word_count

    return {
        "chapter_count": len(chapters),
        "word_count": sum(chapter.word_count for chapter in chapters),
        "scene_count": sum(chapter.scene_count for chapter in chapters),
        "by_status": by_status,
        "by_label": by_label,
        "by_pov": by_pov,
        "by_part": by_part,
        "part_word_totals": part_word_totals,
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


def source_link_map(root: Path) -> dict[str, list[ChapterDocument]]:
    links: dict[str, list[ChapterDocument]] = {}
    chapters = list_chapters(root)
    for source in list_source_notes(root):
        matches = [chapter for chapter in chapters if source in linked_sources_for_chapter(root, chapter)]
        links[source.slug] = matches
    return links


def parse_scenes(body: str) -> list[SceneDocument]:
    heading_pattern = re.compile(r"^##\s+(.+?)\s*$", flags=re.MULTILINE)
    matches = list(heading_pattern.finditer(body))
    if not matches:
        return []

    scenes: list[SceneDocument] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        scene_title = match.group(1).strip()
        scene_body = body[start:end].strip()
        scenes.append(SceneDocument(title=scene_title, body=scene_body, slug=slugify(scene_title)))
    return scenes


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

    project_root_path = init_project_from_template(target_path, title, template_name=template_name, template_file=template_file)

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
    chapter_path.write_text(
        chapter_path.read_text(encoding="utf-8") + body.strip() + ("\n" if body.strip() else ""),
        encoding="utf-8",
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
