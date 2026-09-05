from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from openscribe.project import ChapterDocument, list_chapters, slugify
from openscribe.schema import atomic_write_text, load_yaml, validate_elements

ELEMENTS_DIR = ".openscribe/elements"
ELEMENTS_FILE = "elements.yaml"
SUPPORTED_ELEMENT_TYPES = {"character", "setting", "item"}


@dataclass(slots=True)
class ElementRecord:
    element_id: str
    type_name: str
    name: str
    aliases: list[str]
    tags: list[str]
    notes: str
    relations: list[dict[str, str]]


def elements_path(root: Path) -> Path:
    return root / ELEMENTS_DIR / ELEMENTS_FILE


def load_elements(root: Path) -> dict[str, Any]:
    path = elements_path(root)
    if not path.exists():
        return {"elements": []}
    return validate_elements(load_yaml(path, default={"elements": []}), f"Elements '{path}'")


def save_elements(root: Path, data: dict[str, Any]) -> Path:
    path = elements_path(root)
    validate_elements(data, f"Elements '{path}'")
    atomic_write_text(path, yaml.safe_dump(data, sort_keys=False))
    return path


def add_element(root: Path, type_name: str, name: str, notes: str = "", tags: list[str] | None = None) -> ElementRecord:
    normalized_type = type_name.strip().lower()
    if normalized_type not in SUPPORTED_ELEMENT_TYPES:
        supported = ", ".join(sorted(SUPPORTED_ELEMENT_TYPES))
        raise ValueError(f"Unsupported element type '{type_name}'. Use {supported}.")

    data = load_elements(root)
    element_id = _next_element_id(data, normalized_type, name)
    record = {
        "id": element_id,
        "type": normalized_type,
        "name": name,
        "aliases": [],
        "tags": tags or [],
        "notes": notes,
        "relations": [],
    }
    data.setdefault("elements", []).append(record)
    save_elements(root, data)
    return _record_from_dict(record)


def list_element_records(root: Path, type_name: str | None = None) -> list[ElementRecord]:
    data = load_elements(root)
    results: list[ElementRecord] = []
    for item in data.get("elements", []):
        if type_name and str(item.get("type", "")).strip().lower() != type_name.strip().lower():
            continue
        results.append(_record_from_dict(item))
    return results


def get_element(root: Path, element_ref: str) -> ElementRecord:
    data = load_elements(root)
    item = _require_element(data, element_ref)
    return _record_from_dict(item)


def add_alias(root: Path, element_ref: str, alias: str) -> ElementRecord:
    data = load_elements(root)
    item = _require_element(data, element_ref)
    aliases = [str(value) for value in item.get("aliases", [])]
    if alias not in aliases:
        aliases.append(alias)
    item["aliases"] = aliases
    save_elements(root, data)
    return _record_from_dict(item)


def add_relation(root: Path, from_ref: str, to_ref: str, relation_type: str) -> ElementRecord:
    data = load_elements(root)
    source = _require_element(data, from_ref)
    target = _require_element(data, to_ref)
    relations = [
        {"target": str(item.get("target", "")), "type": str(item.get("type", ""))}
        for item in source.get("relations", [])
    ]
    relation = {"target": str(target.get("id", "")), "type": relation_type}
    if relation not in relations:
        relations.append(relation)
    source["relations"] = relations
    save_elements(root, data)
    return _record_from_dict(source)


def update_element(
    root: Path,
    element_ref: str,
    *,
    name: str | None = None,
    notes: str | None = None,
    tags: list[str] | None = None,
) -> ElementRecord:
    data = load_elements(root)
    item = _require_element(data, element_ref)
    if name is not None:
        item["name"] = name
    if notes is not None:
        item["notes"] = notes
    if tags is not None:
        item["tags"] = tags
    save_elements(root, data)
    return _record_from_dict(item)


def batch_update_elements(
    root: Path,
    *,
    match_type: str | None = None,
    match_tag: str | None = None,
    match_text: str | None = None,
    notes: str | None = None,
    add_tags: list[str] | None = None,
) -> list[ElementRecord]:
    data = load_elements(root)
    updated: list[ElementRecord] = []
    tag_filter = (match_tag or "").strip().lower()
    text_filter = (match_text or "").strip().lower()
    type_filter = (match_type or "").strip().lower()
    for item in data.get("elements", []):
        if type_filter and str(item.get("type", "")).strip().lower() != type_filter:
            continue
        tags = [str(value) for value in item.get("tags", [])]
        if tag_filter and tag_filter not in {value.strip().lower() for value in tags}:
            continue
        if text_filter:
            haystack = " ".join(
                [
                    str(item.get("name", "")),
                    str(item.get("notes", "")),
                    " ".join(str(value) for value in item.get("aliases", [])),
                    " ".join(tags),
                ]
            ).lower()
            if text_filter not in haystack:
                continue
        if notes is not None:
            item["notes"] = notes
        if add_tags:
            merged = tags[:]
            for tag in add_tags:
                if tag not in merged:
                    merged.append(tag)
            item["tags"] = merged
        updated.append(_record_from_dict(item))
    save_elements(root, data)
    return updated


def remove_relation(root: Path, from_ref: str, to_ref: str, relation_type: str | None = None) -> ElementRecord:
    data = load_elements(root)
    source = _require_element(data, from_ref)
    target = _require_element(data, to_ref)
    filtered = []
    for item in source.get("relations", []):
        current_target = str(item.get("target", ""))
        current_type = str(item.get("type", ""))
        if current_target != str(target.get("id", "")):
            filtered.append({"target": current_target, "type": current_type})
            continue
        if relation_type and current_type != relation_type:
            filtered.append({"target": current_target, "type": current_type})
    source["relations"] = filtered
    save_elements(root, data)
    return _record_from_dict(source)


def appears_in(root: Path, element_ref: str) -> list[ChapterDocument]:
    element = get_element(root, element_ref)
    search_terms = [element.name, *element.aliases]
    matches: list[ChapterDocument] = []
    for chapter in list_chapters(root):
        haystacks = [chapter.title, chapter.synopsis, chapter.notes, chapter.body]
        if any(term.strip() and any(term.lower() in text.lower() for text in haystacks) for term in search_terms):
            matches.append(chapter)
    return matches


def _require_element(data: dict[str, Any], element_ref: str) -> dict[str, Any]:
    normalized = element_ref.strip().lower()
    for item in data.get("elements", []):
        element_id = str(item.get("id", ""))
        name = str(item.get("name", ""))
        aliases = [str(value).strip().lower() for value in item.get("aliases", [])]
        if element_id.lower() == normalized or name.strip().lower() == normalized or normalized in aliases:
            return item
    raise FileNotFoundError(f"Element '{element_ref}' was not found.")


def _record_from_dict(item: dict[str, Any]) -> ElementRecord:
    return ElementRecord(
        element_id=str(item.get("id", "")),
        type_name=str(item.get("type", "")),
        name=str(item.get("name", "")),
        aliases=[str(value) for value in item.get("aliases", [])],
        tags=[str(value) for value in item.get("tags", [])],
        notes=str(item.get("notes", "")),
        relations=[
            {"target": str(value.get("target", "")), "type": str(value.get("type", ""))}
            for value in item.get("relations", [])
        ],
    )


def _next_element_id(data: dict[str, Any], type_name: str, name: str) -> str:
    stem = type_name[:3]
    slug = slugify(name)
    existing_ids = {str(item.get("id", "")) for item in data.get("elements", [])}
    candidate = f"{stem}-{slug}"
    if candidate not in existing_ids:
        return candidate
    suffix = 2
    while f"{candidate}-{suffix}" in existing_ids:
        suffix += 1
    return f"{candidate}-{suffix}"
