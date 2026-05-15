from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from openscribe.elements import list_element_records
from openscribe.project import (
    INDEX_DIR,
    AuxiliaryDocument,
    list_auxiliary_documents,
    list_chapters,
    list_story_ideas,
    load_project_config,
)

INDEX_FILE = "project-index.yaml"


def index_path(root: Path) -> Path:
    return root / INDEX_DIR / INDEX_FILE


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
        "chapters": [
            {
                "title": chapter.title,
                "part": chapter.part,
                "part_id": chapter.part_id,
                "status": chapter.status,
                "label": chapter.label,
                "pov": chapter.pov,
                "word_count": chapter.word_count,
                "scene_count": chapter.scene_count,
                "path": str(chapter.path.relative_to(root)),
                "search_text": " ".join(
                    [chapter.title, chapter.synopsis, chapter.notes, chapter.body]
                ).strip(),
                "scenes": [
                    {"title": scene.title, "slug": scene.slug}
                    for scene in chapter.scenes
                ],
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
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return target_path


def load_project_index(root: Path) -> dict[str, Any]:
    path = index_path(root)
    if not path.exists():
        raise FileNotFoundError("Project index does not exist yet. Run `openscribe index rebuild`.")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def index_is_current(root: Path) -> bool:
    path = index_path(root)
    if not path.exists():
        return False
    index_mtime = path.stat().st_mtime
    for source in _index_sources(root):
        if source.stat().st_mtime > index_mtime:
            return False
    return True


def _index_sources(root: Path) -> list[Path]:
    sources: list[Path] = []
    for folder_name in (".openscribe", "manuscript", "characters", "research", "notes"):
        folder = root / folder_name
        if not folder.exists():
            continue
        if folder.is_file():
            sources.append(folder)
            continue
        sources.extend(path for path in folder.rglob("*") if path.is_file())
    return sources


def _auxiliary_entries(root: Path, documents: list[AuxiliaryDocument]) -> list[dict[str, str]]:
    return [
        {
            "title": document.title,
            "path": str(document.path.relative_to(root)),
        }
        for document in documents
    ]
