from __future__ import annotations

import hashlib
import heapq
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from openscribe.project import create_chapter, create_part, list_chapters
from openscribe.schema import atomic_write_text, load_yaml, validate_board

BOARD_DIR = ".openscribe/boards"
BOARD_FILE = "default.yaml"


@dataclass(slots=True)
class BoardNote:
    note_id: str
    title: str
    body: str
    group: str
    links: list[str]
    x: int
    y: int
    hidden: bool
    chapter_links: list[str]


@dataclass(frozen=True, slots=True)
class OutlineChapter:
    note_id: str
    title: str
    synopsis: str


@dataclass(frozen=True, slots=True)
class OutlinePart:
    title: str
    chapters: tuple[OutlineChapter, ...]


@dataclass(frozen=True, slots=True)
class BoardOutlinePlan:
    board_digest: str
    parts: tuple[OutlinePart, ...]
    linked_notes: int


def board_path(root: Path) -> Path:
    return root / BOARD_DIR / BOARD_FILE


def load_board(root: Path) -> dict[str, Any]:
    path = board_path(root)
    if not path.exists():
        return {"notes": []}
    board = validate_board(load_yaml(path, default={"notes": []}), f"Board '{path}'")
    return board


def migrate_chapter_links(root: Path, repaired_ids: dict[str, str] | None = None) -> bool:
    path = board_path(root)
    if not path.exists():
        return False
    board = validate_board(load_yaml(path, default={"notes": []}), f"Board '{path}'")
    changed = _migrate_chapter_links(root, board, repaired_ids)
    if changed:
        save_board(root, board)
    return changed


def save_board(root: Path, board: dict[str, Any]) -> Path:
    path = board_path(root)
    validate_board(board, f"Board '{path}'")
    atomic_write_text(path, yaml.safe_dump(board, sort_keys=False))
    return path


def list_notes(root: Path) -> list[BoardNote]:
    board = load_board(root)
    notes: list[BoardNote] = []
    for item in board.get("notes", []):
        notes.append(
            BoardNote(
                note_id=str(item.get("id", "")),
                title=str(item.get("title", "")),
                body=str(item.get("body", "")),
                group=str(item.get("group", "")),
                links=[str(link) for link in item.get("links", [])],
                x=int(item.get("x", 0) or 0),
                y=int(item.get("y", 0) or 0),
                hidden=bool(item.get("hidden", False)),
                chapter_links=[str(value) for value in item.get("chapter_links", [])],
            )
        )
    return notes


def add_note(root: Path, title: str, body: str = "", group: str = "", x: int = 0, y: int = 0) -> BoardNote:
    if not title.strip() or "\n" in title or "\r" in title:
        raise ValueError("Board note titles must be nonempty single lines.")
    board = load_board(root)
    next_id = _next_note_id(board)
    note = {
        "id": next_id,
        "title": title,
        "body": body,
        "group": group,
        "links": [],
        "x": x,
        "y": y,
        "hidden": False,
        "chapter_links": [],
    }
    board.setdefault("notes", []).append(note)
    save_board(root, board)
    return BoardNote(
        note_id=next_id, title=title, body=body, group=group, links=[], x=x, y=y, hidden=False, chapter_links=[]
    )


def update_note(root: Path, note_id: str, *, title: str, body: str, group: str) -> BoardNote:
    if not title.strip() or "\n" in title or "\r" in title:
        raise ValueError("Board note titles must be nonempty single lines.")
    board = load_board(root)
    note = _require_note(board, note_id)
    note["title"] = title.strip()
    note["body"] = body.strip()
    note["group"] = group.strip()
    save_board(root, board)
    return _note_from_dict(note)


def delete_note(root: Path, note_id: str) -> None:
    board = load_board(root)
    _require_note(board, note_id)
    board["notes"] = [item for item in board.get("notes", []) if str(item.get("id", "")) != note_id]
    for item in board["notes"]:
        item["links"] = [str(link) for link in item.get("links", []) if str(link) != note_id]
    save_board(root, board)


def add_link(root: Path, from_id: str, to_id: str) -> None:
    if from_id == to_id:
        raise ValueError("A brainstorming idea cannot link to itself.")
    board = load_board(root)
    note = _require_note(board, from_id)
    _require_note(board, to_id)
    links = [str(link) for link in note.get("links", [])]
    if to_id not in links:
        links.append(to_id)
    note["links"] = links
    save_board(root, board)


def remove_link(root: Path, from_id: str, to_id: str) -> None:
    board = load_board(root)
    note = _require_note(board, from_id)
    _require_note(board, to_id)
    note["links"] = [str(link) for link in note.get("links", []) if str(link) != to_id]
    save_board(root, board)


def set_group(root: Path, note_id: str, group: str) -> None:
    board = load_board(root)
    note = _require_note(board, note_id)
    note["group"] = group
    save_board(root, board)


def move_note(root: Path, note_id: str, x: int, y: int) -> None:
    board = load_board(root)
    note = _require_note(board, note_id)
    note["x"] = x
    note["y"] = y
    save_board(root, board)


def move_note_by_delta(root: Path, note_id: str, dx: int, dy: int) -> BoardNote:
    board = load_board(root)
    note = _require_note(board, note_id)
    note["x"] = int(note.get("x", 0) or 0) + dx
    note["y"] = int(note.get("y", 0) or 0) + dy
    save_board(root, board)
    return _note_from_dict(note)


def set_note_hidden(root: Path, note_id: str, hidden: bool) -> BoardNote:
    board = load_board(root)
    note = _require_note(board, note_id)
    note["hidden"] = hidden
    save_board(root, board)
    return _note_from_dict(note)


def add_chapter_link(root: Path, note_id: str, chapter_id: str) -> BoardNote:
    board = load_board(root)
    note = _require_note(board, note_id)
    chapter_links = [str(value) for value in note.get("chapter_links", [])]
    if chapter_id not in chapter_links:
        chapter_links.append(chapter_id)
    note["chapter_links"] = chapter_links
    save_board(root, board)
    return _note_from_dict(note)


def remove_chapter_link(root: Path, note_id: str, chapter_id: str) -> BoardNote:
    board = load_board(root)
    note = _require_note(board, note_id)
    note["chapter_links"] = [str(value) for value in note.get("chapter_links", []) if str(value) != chapter_id]
    save_board(root, board)
    return _note_from_dict(note)


def auto_layout(root: Path, column_width: int = 22) -> None:
    board = load_board(root)
    grouped = sorted(board.get("notes", []), key=lambda item: (str(item.get("group", "")), str(item.get("id", ""))))
    current_group = None
    row = 0
    column = 0
    for item in grouped:
        group_name = str(item.get("group", ""))
        if current_group is None:
            current_group = group_name
        elif group_name != current_group:
            current_group = group_name
            row += 4
            column = 0
        item["x"] = column * column_width
        item["y"] = row
        column += 1
        if column >= 3:
            column = 0
            row += 4
    save_board(root, board)


def render_board(root: Path, width: int = 72, height: int = 18) -> str:
    notes = list_notes(root)
    canvas = [[" " for _ in range(width)] for _ in range(height)]

    for note in notes:
        if note.hidden:
            continue
        x = max(0, min(width - 8, note.x))
        y = max(0, min(height - 1, note.y))
        label = f"[{note.note_id}]"
        for index, character in enumerate(label):
            if x + index < width:
                canvas[y][x + index] = character
        title = note.title[: min(18, max(0, width - x))]
        if y + 1 < height:
            for index, character in enumerate(title):
                if x + index < width:
                    canvas[y + 1][x + index] = character

    rendered = "\n".join("".join(row).rstrip() for row in canvas).rstrip()
    links = []
    for note in notes:
        for link in note.links:
            links.append(f"{note.note_id} -> {link}")
    if links:
        rendered = rendered + "\n\nLinks\n" + "\n".join(links)
    return rendered or "[Empty board]"


def promote_note_to_chapter(
    root: Path, note_id: str, chapter_title: str | None = None, part: str | None = None
) -> Path:
    board = load_board(root)
    note = _require_note(board, note_id)
    title = chapter_title or str(note.get("title", "")).strip() or f"Board Note {note_id}"
    chapter_path = create_chapter(root, title, part=part, synopsis=str(note.get("body", "")).strip())
    body = str(note.get("body", "")).strip()
    if body:
        atomic_write_text(
            chapter_path,
            chapter_path.read_text(encoding="utf-8") + body + "\n",
        )
    chapter_links = [str(value) for value in note.get("chapter_links", [])]
    chapter_id = next(chapter.chapter_id for chapter in list_chapters(root) if chapter.path == chapter_path)
    if chapter_id not in chapter_links:
        chapter_links.append(chapter_id)
    note["chapter_links"] = chapter_links
    save_board(root, board)
    return chapter_path


def plan_board_outline(root: Path) -> BoardOutlinePlan:
    notes = [note for note in list_notes(root) if not note.hidden]
    if not notes:
        raise ValueError("Add at least one visible brainstorming idea before creating an outline.")

    notes_by_id = {note.note_id: note for note in notes}
    if len(notes_by_id) != len(notes):
        raise ValueError("The brainstorming board contains duplicate note IDs.")
    all_note_ids = {note.note_id for note in list_notes(root)}
    for note in notes:
        unknown = [link for link in note.links if link not in all_note_ids]
        if unknown:
            raise ValueError(f"Idea '{note.note_id}' links to missing idea '{unknown[0]}'.")

    ordered = _ordered_notes_by_group(notes_by_id)
    chapter_ids = {chapter.chapter_id for chapter in list_chapters(root)}
    linked_notes = 0
    grouped: dict[str, list[OutlineChapter]] = {}
    group_titles: dict[str, str] = {}
    group_order: list[str] = []
    for note in ordered:
        resolved_links = [chapter_id for chapter_id in note.chapter_links if chapter_id in chapter_ids]
        if note.chapter_links and not resolved_links:
            raise ValueError(
                f"Idea '{note.note_id}' has an unresolved chapter link. Run `openscribe migrate repair` first."
            )
        if resolved_links:
            linked_notes += 1
            continue
        group = note.group.strip() or "Outline"
        group_key = group.casefold()
        if group_key not in grouped:
            grouped[group_key] = []
            group_titles[group_key] = group
            group_order.append(group_key)
        grouped[group_key].append(OutlineChapter(note.note_id, note.title.strip(), note.body.strip()))

    parts = tuple(
        OutlinePart(group_titles[group], tuple(grouped[group])) for group in group_order if grouped[group]
    )
    if not parts:
        raise ValueError("Every visible brainstorming idea is already linked to a chapter.")
    return BoardOutlinePlan(_board_digest(root), parts, linked_notes)


def outline_plan_text(plan: BoardOutlinePlan) -> str:
    lines = ["Book outline from brainstorming flowchart", ""]
    for part in plan.parts:
        lines.append(f"Part: {part.title}")
        for index, chapter in enumerate(part.chapters, start=1):
            lines.append(f"  {index}. {chapter.title} [{chapter.note_id}]")
            if chapter.synopsis:
                lines.append(f"     {chapter.synopsis}")
        lines.append("")
    if plan.linked_notes:
        lines.append(f"Already linked ideas skipped: {plan.linked_notes}")
    lines.append("Applying this plan creates parts and empty draft chapters. Idea details become chapter synopses.")
    return "\n".join(lines).rstrip()


def apply_board_outline(root: Path, plan: BoardOutlinePlan) -> tuple[Path, list[Path]]:
    from openscribe.editing import transform_project

    if _board_digest(root) != plan.board_digest:
        raise ValueError("The brainstorming flowchart changed after preview. Preview the outline again.")

    def apply_to_stage(stage: Path) -> list[Path]:
        if _board_digest(stage) != plan.board_digest:
            raise ValueError("The brainstorming flowchart changed after preview. Preview the outline again.")
        board = load_board(stage)
        created: list[Path] = []
        for part in plan.parts:
            try:
                from openscribe.project import resolve_part_path

                resolve_part_path(stage, part.title)
            except FileNotFoundError:
                create_part(stage, part.title)
            for chapter in part.chapters:
                chapter_path = create_chapter(
                    stage,
                    chapter.title,
                    part=part.title,
                    synopsis=chapter.synopsis,
                )
                created.append(chapter_path)
                chapter_id = next(item.chapter_id for item in list_chapters(stage) if item.path == chapter_path)
                note = _require_note(board, chapter.note_id)
                links = [str(value) for value in note.get("chapter_links", [])]
                if chapter_id not in links:
                    links.append(chapter_id)
                note["chapter_links"] = links
        save_board(stage, board)
        return created

    backup, created_paths = transform_project(root, "automatic backup before creating outline", apply_to_stage)
    return backup, created_paths


def _board_digest(root: Path) -> str:
    path = board_path(root)
    return hashlib.sha256(path.read_bytes() if path.exists() else b"").hexdigest()


def _topological_notes(notes_by_id: dict[str, BoardNote]) -> list[BoardNote]:
    indegree = {note_id: 0 for note_id in notes_by_id}
    outgoing = {note_id: [] for note_id in notes_by_id}
    for note in notes_by_id.values():
        for target in set(note.links):
            if target not in notes_by_id:
                continue
            outgoing[note.note_id].append(target)
            indegree[target] += 1

    def sort_key(note_id: str) -> tuple[int, int, str]:
        note = notes_by_id[note_id]
        return note.y, note.x, note.note_id

    available = [(sort_key(note_id), note_id) for note_id, count in indegree.items() if count == 0]
    heapq.heapify(available)
    ordered: list[BoardNote] = []
    while available:
        _, note_id = heapq.heappop(available)
        ordered.append(notes_by_id[note_id])
        for target in sorted(outgoing[note_id], key=sort_key):
            indegree[target] -= 1
            if indegree[target] == 0:
                heapq.heappush(available, (sort_key(target), target))
    if len(ordered) != len(notes_by_id):
        cycle_ids = ", ".join(sorted(note_id for note_id, count in indegree.items() if count > 0))
        raise ValueError(f"The brainstorming flowchart contains a cycle involving: {cycle_ids}.")
    return ordered


def _ordered_notes_by_group(notes_by_id: dict[str, BoardNote]) -> list[BoardNote]:
    groups: dict[str, dict[str, BoardNote]] = {}
    group_titles: dict[str, str] = {}
    note_groups: dict[str, str] = {}
    for note_id, note in notes_by_id.items():
        title = note.group.strip() or "Outline"
        group = title.casefold()
        groups.setdefault(group, {})[note_id] = note
        group_titles.setdefault(group, title)
        note_groups[note_id] = group

    outgoing = {group: set() for group in groups}
    indegree = {group: 0 for group in groups}
    for note in notes_by_id.values():
        source_group = note_groups[note.note_id]
        for target_id in set(note.links):
            if target_id not in notes_by_id:
                continue
            target_group = note_groups[target_id]
            if source_group == target_group or target_group in outgoing[source_group]:
                continue
            outgoing[source_group].add(target_group)
            indegree[target_group] += 1

    def group_sort_key(group: str) -> tuple[int, int, str]:
        note = min(groups[group].values(), key=lambda item: (item.y, item.x, item.note_id))
        return note.y, note.x, group

    available = [(group_sort_key(group), group) for group, count in indegree.items() if count == 0]
    heapq.heapify(available)
    group_order: list[str] = []
    while available:
        _, group = heapq.heappop(available)
        group_order.append(group)
        for target in sorted(outgoing[group], key=group_sort_key):
            indegree[target] -= 1
            if indegree[target] == 0:
                heapq.heappush(available, (group_sort_key(target), target))
    if len(group_order) != len(groups):
        cycle = ", ".join(
            group_titles[group] for group, count in sorted(indegree.items()) if count > 0
        )
        raise ValueError(f"The brainstorming flowchart contains a cycle between book parts: {cycle}.")

    return [note for group in group_order for note in _topological_notes(groups[group])]


def _next_note_id(board: dict[str, Any]) -> str:
    existing = []
    for item in board.get("notes", []):
        raw = str(item.get("id", ""))
        if raw.startswith("note-"):
            try:
                existing.append(int(raw.split("-", 1)[1]))
            except ValueError:
                continue
    next_number = (max(existing) + 1) if existing else 1
    return f"note-{next_number:03d}"


def _migrate_chapter_links(
    root: Path,
    board: dict[str, Any],
    repaired_ids: dict[str, str] | None = None,
) -> bool:
    chapters = list_chapters(root)
    identities = {chapter.chapter_id.lower(): chapter.chapter_id for chapter in chapters}
    references: dict[str, set[str]] = {}
    for chapter in chapters:
        for reference in (chapter.slug, chapter.title, chapter.path.stem):
            references.setdefault(reference.strip().lower(), set()).add(chapter.chapter_id)
    for reference, chapter_id in (repaired_ids or {}).items():
        references.setdefault(reference.strip().lower(), set()).add(chapter_id)

    changed = False
    for item in board.get("notes", []):
        original_links = [str(value) for value in item.get("chapter_links", [])]
        migrated_links: list[str] = []
        for value in original_links:
            normalized = value.strip().lower()
            resolved = identities.get(normalized)
            if resolved is None and normalized in references:
                matches = references[normalized]
                if len(matches) > 1:
                    choices = ", ".join(sorted(matches))
                    raise ValueError(
                        f"Legacy board chapter reference '{value}' is ambiguous. "
                        f"Replace it with an immutable chapter ID: {choices}."
                    )
                resolved = next(iter(matches))
            if resolved is None:
                resolved = value
            if resolved not in migrated_links:
                migrated_links.append(resolved)
        if migrated_links != original_links:
            item["chapter_links"] = migrated_links
            changed = True
    return changed


def _require_note(board: dict[str, Any], note_id: str) -> dict[str, Any]:
    for item in board.get("notes", []):
        if str(item.get("id", "")) == note_id:
            return item
    raise FileNotFoundError(f"Board note '{note_id}' was not found.")


def _note_from_dict(item: dict[str, Any]) -> BoardNote:
    return BoardNote(
        note_id=str(item.get("id", "")),
        title=str(item.get("title", "")),
        body=str(item.get("body", "")),
        group=str(item.get("group", "")),
        links=[str(link) for link in item.get("links", [])],
        x=int(item.get("x", 0) or 0),
        y=int(item.get("y", 0) or 0),
        hidden=bool(item.get("hidden", False)),
        chapter_links=[str(value) for value in item.get("chapter_links", [])],
    )
