from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml

PROJECT_DIR = ".openscribe"
PROJECT_FILE = "project.yaml"


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
    slug: str

    @property
    def word_count(self) -> int:
        return len([word for word in re.findall(r"\b[\w']+\b", self.body)])


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
                "default_template": "novel",
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
    return part_path


def resolve_part_path(root: Path, part: str | None) -> Path:
    manuscript = root / "manuscript"
    if part:
        part_slug = slugify(part)
        for child in manuscript.iterdir():
            if child.is_dir() and (child.name == part or child.name.endswith(part_slug)):
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


def list_chapters(root: Path) -> list[ChapterDocument]:
    manuscript = root / "manuscript"
    chapters: list[ChapterDocument] = []
    for part_path in sorted([child for child in manuscript.iterdir() if child.is_dir()]):
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
                    part=part_path.name,
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
