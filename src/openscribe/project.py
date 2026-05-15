from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml

PROJECT_DIR = ".openscribe"
PROJECT_FILE = "project.yaml"
PART_FILE = "part.yaml"
STORY_IDEAS_DIR = "notes/story-ideas"


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

    @property
    def word_count(self) -> int:
        return len([word for word in re.findall(r"\b[\w']+\b", self.body)])


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
    ):
        directory.mkdir(parents=True, exist_ok=True)

    write_yaml(
        config_dir / PROJECT_FILE,
        {
            "title": title,
            "author": "",
            "version": 1,
            "compile": {
                "default_format": "docx",
                "backend": "auto",
                "default_template": "novel",
                "output_filename": "",
                "include_title_page": True,
                "include_part_headings": True,
                "chapter_heading_style": "title-only",
            },
            "ai": {
                "enabled": False,
                "provider": "openai",
                "model": "gpt-4.1",
            },
        },
    )
    return project_path


def load_project_config(root: Path) -> dict[str, Any]:
    config_path = root / PROJECT_DIR / PROJECT_FILE
    if not config_path.exists():
        raise FileNotFoundError(f"Missing project config at {config_path}")
    return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}


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


def update_part_title(root: Path, part: str, title: str) -> Path:
    part_path = resolve_part_path(root, part)
    write_yaml(part_path / PART_FILE, {"title": title})
    return part_path


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
        "by_status": by_status,
        "by_label": by_label,
        "by_pov": by_pov,
        "by_part": by_part,
        "part_word_totals": part_word_totals,
    }


def _increment(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1
