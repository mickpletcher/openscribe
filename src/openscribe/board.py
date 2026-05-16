from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from openscribe.project import create_chapter, project_root

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


def board_path(root: Path) -> Path:
    return root / BOARD_DIR / BOARD_FILE


def load_board(root: Path) -> dict[str, Any]:
    path = board_path(root)
    if not path.exists():
        return {"notes": []}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"notes": []}


def save_board(root: Path, board: dict[str, Any]) -> Path:
    path = board_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(board, sort_keys=False), encoding="utf-8")
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
            )
        )
    return notes


def add_note(root: Path, title: str, body: str = "", group: str = "", x: int = 0, y: int = 0) -> BoardNote:
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
    }
    board.setdefault("notes", []).append(note)
    save_board(root, board)
    return BoardNote(note_id=next_id, title=title, body=body, group=group, links=[], x=x, y=y, hidden=False)


def add_link(root: Path, from_id: str, to_id: str) -> None:
    board = load_board(root)
    note = _require_note(board, from_id)
    _require_note(board, to_id)
    links = [str(link) for link in note.get("links", [])]
    if to_id not in links:
        links.append(to_id)
    note["links"] = links
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


def promote_note_to_chapter(root: Path, note_id: str, chapter_title: str | None = None, part: str | None = None) -> Path:
    board = load_board(root)
    note = _require_note(board, note_id)
    title = chapter_title or str(note.get("title", "")).strip() or f"Board Note {note_id}"
    chapter_path = create_chapter(root, title, part=part, synopsis=str(note.get("body", "")).strip())
    body = str(note.get("body", "")).strip()
    if body:
        chapter_path.write_text(
            chapter_path.read_text(encoding="utf-8") + body + "\n",
            encoding="utf-8",
        )
    return chapter_path


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
    )
