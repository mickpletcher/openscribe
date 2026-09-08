from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml

from openscribe.elements import list_element_records
from openscribe.locking import project_locked
from openscribe.project import (
    INDEX_DIR,
    AuxiliaryDocument,
    list_auxiliary_documents,
    list_chapters,
    list_story_ideas,
    load_project_config,
)
from openscribe.schema import atomic_write_text, load_yaml, validate_index

INDEX_FILE = "project-index.yaml"
TEXT_SOURCE_SUFFIXES = {".csv", ".json", ".md", ".markdown", ".tsv", ".txt", ".yaml", ".yml"}


def index_path(root: Path) -> Path:
    return root / INDEX_DIR / INDEX_FILE


@project_locked
def rebuild_project_index(root: Path) -> Path:
    chapters = list_chapters(root)
    ideas = list_story_ideas(root)
    elements = list_element_records(root)
    characters = list_auxiliary_documents(root, "characters")
    research = list_auxiliary_documents(root, "research")
    notes = list_auxiliary_documents(root, "notes")
    config = load_project_config(root)

    data: dict[str, Any] = {
        "title": str(config.get("title", "Untitled Project")),
        "template": str(config.get("template", "fiction")),
        "chapter_count": len(chapters),
        "scene_count": sum(chapter.scene_count for chapter in chapters),
        "word_count": sum(chapter.word_count for chapter in chapters),
        "story_idea_count": len(ideas),
        "element_count": len(elements),
        "characters_count": len(characters),
        "research_count": len(research),
        "notes_count": len(notes),
        "source_manifest": _source_manifest(root),
        "chapters": [
            {
                "chapter_id": chapter.chapter_id,
                "title": chapter.title,
                "part": chapter.part,
                "part_id": chapter.part_id,
                "status": chapter.status,
                "label": chapter.label,
                "pov": chapter.pov,
                "word_count": chapter.word_count,
                "scene_count": chapter.scene_count,
                "path": str(chapter.path.relative_to(root)),
                "search_text": " ".join([chapter.title, chapter.synopsis, chapter.notes, chapter.body]).strip(),
                "scenes": [{"title": scene.title, "slug": scene.slug} for scene in chapter.scenes],
            }
            for chapter in chapters
        ],
        "story_ideas": [
            {
                "title": idea.title,
                "status": idea.status,
                "genre": idea.genre,
                "tone": idea.tone,
                "path": str(idea.path.relative_to(root)),
            }
            for idea in ideas
        ],
        "elements": [
            {
                "id": element.element_id,
                "type": element.type_name,
                "name": element.name,
                "aliases": element.aliases,
                "tags": element.tags,
            }
            for element in elements
        ],
        "characters": _auxiliary_entries(root, characters),
        "research": _auxiliary_entries(root, research),
        "notes": _auxiliary_entries(root, notes),
    }

    target_path = index_path(root)
    atomic_write_text(target_path, yaml.safe_dump(data, sort_keys=False))
    return target_path


def load_project_index(root: Path) -> dict[str, Any]:
    path = index_path(root)
    if not path.exists():
        raise FileNotFoundError("Project index does not exist yet. Run `openscribe index rebuild`.")
    return validate_index(load_yaml(path, default={}), f"Project index '{path}'")


def index_is_current(root: Path) -> bool:
    path = index_path(root)
    if not path.exists():
        return False
    try:
        data = load_project_index(root)
    except (OSError, ValueError):
        return False
    recorded = data.get("source_manifest")
    if not isinstance(recorded, dict):
        return False
    return recorded == _source_manifest(root)


def _index_sources(root: Path) -> list[Path]:
    sources: list[Path] = []
    config_path = root / ".openscribe" / "project.yaml"
    if config_path.is_file():
        sources.append(config_path)
    for folder_name in (
        ".openscribe/boards",
        ".openscribe/elements",
        "manuscript",
        "characters",
        "research",
        "notes",
    ):
        folder = root / folder_name
        if not folder.exists():
            continue
        sources.extend(path for path in folder.rglob("*") if path.is_file() and not path.is_symlink())
    return sorted(sources)


def _source_manifest(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)).replace("\\", "/"): _source_hash(path)
        for path in _index_sources(root)
    }


def _source_hash(path: Path) -> str:
    content = path.read_bytes()
    if path.suffix.lower() in TEXT_SOURCE_SUFFIXES:
        content = content.replace(b"\r\n", b"\n")
    return sha256(content).hexdigest()


def _auxiliary_entries(root: Path, documents: list[AuxiliaryDocument]) -> list[dict[str, str]]:
    return [
        {
            "title": document.title,
            "path": str(document.path.relative_to(root)),
        }
        for document in documents
    ]
