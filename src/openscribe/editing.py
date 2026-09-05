from __future__ import annotations

import base64
import difflib
import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from functools import wraps
from hashlib import sha256
from pathlib import Path

from openscribe.locking import project_lock, project_locked


class EditConflictError(ValueError):
    pass


def content_hash(content: bytes) -> str:
    return sha256(content).hexdigest()


@dataclass(frozen=True, slots=True)
class FileEdit:
    path: Path
    before: bytes | None
    after: bytes | None


@project_locked
def apply_edits(root: Path, edits: tuple[FileEdit, ...], label: str) -> Path:
    from openscribe.project import load_project_config
    from openscribe.snapshots import (
        _apply_exact_snapshot,
        _validate_snapshot_relative_path,
        create_snapshot,
        recover_interrupted_restores,
    )

    recover_interrupted_restores(root)
    load_project_config(root)
    paths: list[str] = []
    for edit in edits:
        resolved = edit.path.resolve()
        relative = resolved.relative_to(root.resolve()).as_posix()
        _validate_snapshot_relative_path(relative)
        if edit.path.is_symlink() or resolved != edit.path.absolute():
            raise ValueError("Editing linked files or directories is not supported.")
        if relative.casefold() in {path.casefold() for path in paths}:
            raise ValueError("An edit plan contains duplicate paths.")
        paths.append(relative)
        current = edit.path.read_bytes() if edit.path.exists() else None
        if current != edit.before:
            raise EditConflictError(f"'{relative}' changed on disk. Reload and review before saving.")
    if not edits:
        raise ValueError("There are no changes to apply.")
    backup = create_snapshot(root, label)
    # Recheck after the backup, because an external editor does not honor our lock.
    for edit in edits:
        current = edit.path.read_bytes() if edit.path.exists() else None
        if current != edit.before:
            raise EditConflictError("Project files changed while preparing the backup. Nothing was applied.")
    files = {path: edit.after for path, edit in zip(paths, edits, strict=True) if edit.after is not None}
    _apply_exact_snapshot(root, files, set(files), paths=tuple(paths))
    return backup


@project_locked
def transform_project(root: Path, label: str, transform, *, allow_legacy: bool = False):
    from openscribe.project import load_project_config
    from openscribe.snapshots import (
        MANAGED_PATHS,
        _apply_exact_snapshot,
        _current_file_bytes,
        create_snapshot,
        recover_interrupted_restores,
    )

    recover_interrupted_restores(root)
    if not allow_legacy:
        load_project_config(root)
    before = _current_file_bytes(root)
    backup = create_snapshot(root, label)
    with tempfile.TemporaryDirectory(prefix="openscribe-transform-") as directory:
        stage = Path(directory)
        for relative in MANAGED_PATHS:
            source = root / relative
            if source.is_dir():
                shutil.copytree(source, stage / relative)
            elif source.is_file():
                (stage / relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, stage / relative)
        result = transform(stage)
        after = _current_file_bytes(stage)
        if _current_file_bytes(root) != before:
            raise EditConflictError("Project changed while preparing the operation. Nothing was applied.")
        present = {relative for relative in MANAGED_PATHS if (stage / relative).exists()}
        directories = {p.relative_to(stage).as_posix() for relative in present
                       for p in (stage / relative).rglob("*") if p.is_dir()}
        _apply_exact_snapshot(root, after, present | directories)
        if isinstance(result, list) and all(isinstance(item, Path) for item in result):
            result = [root / item.relative_to(stage) for item in result]
        return backup, result


def staged_operation(label: str):
    def decorate(function):
        @wraps(function)
        def staged(root: Path, *args, **kwargs):
            return transform_project(root, label, lambda stage: function(stage, *args, **kwargs))[1]
        return staged
    return decorate


@dataclass(slots=True)
class EditSession:
    root: Path
    chapter_id: str
    scene_id: str | None
    baseline: bytes
    original: str
    text: str
    draft_baseline: bytes | None = None

    @property
    def dirty(self) -> bool:
        return self.text != self.original

    @classmethod
    def open(cls, root: Path, chapter_id: str, scene_id: str | None = None):
        from openscribe.project import find_chapter, find_scene, strip_scene_markers

        with project_lock(root):
            chapter = find_chapter(root, chapter_id)
            if not chapter.chapter_id:
                raise ValueError("Chapter identity is missing. Run `openscribe migrate repair` first.")
            baseline = chapter.path.read_bytes()
            text = find_scene(chapter, scene_id).body if scene_id else strip_scene_markers(chapter.body)
            session = cls(root, chapter.chapter_id, scene_id, baseline, text, text)
            if session.draft_path.exists():
                session.draft_baseline = session.draft_path.read_bytes()
                data = json.loads(session.draft_baseline)
                if (
                    not isinstance(data, dict) or data.get("version") != 1
                    or any(not isinstance(data.get(key), str) for key in ("baseline", "original", "text"))
                ):
                    raise ValueError("Recovery draft is invalid. Preserve it and inspect before editing.")
                session.baseline = base64.b64decode(data["baseline"], validate=True)
                session.original = data["original"]
                session.text = data["text"]
            return session

    @property
    def draft_path(self) -> Path:
        identity = self.chapter_id + ("_" + self.scene_id if self.scene_id else "")
        if not re.fullmatch(r"chapter-[a-f0-9]{32}(?:_scene-[a-f0-9]{32})?", identity):
            raise ValueError("Invalid identity for an editing session.")
        return self.root / ".openscribe" / "drafts" / f"{identity}.json"

    def stash(self) -> None:
        from openscribe.schema import atomic_write_text

        with project_lock(self.root):
            current = self.draft_path.read_bytes() if self.draft_path.exists() else None
            if current != self.draft_baseline:
                raise EditConflictError("Recovery draft changed in another window. Keep this window open and save a copy.")
            if self.dirty:
                encoded = json.dumps({
                    "version": 1, "baseline": base64.b64encode(self.baseline).decode("ascii"),
                    "original": self.original, "text": self.text,
                })
                if current != encoded.encode("utf-8"):
                    atomic_write_text(self.draft_path, encoded)
                self.draft_baseline = encoded.encode("utf-8")
            elif current is not None:
                self.draft_path.unlink()
                self.draft_baseline = None

    def discard(self) -> None:
        with project_lock(self.root):
            current = self.draft_path.read_bytes() if self.draft_path.exists() else None
            if current != self.draft_baseline:
                raise EditConflictError("Recovery draft changed in another window. It has not been removed.")
            self.text = self.original
            self.draft_path.unlink(missing_ok=True)
            self.draft_baseline = None

    def save(self) -> None:
        from openscribe.project import find_chapter, update_chapter_body, update_scene_body

        if not self.dirty:
            return
        with project_lock(self.root):
            self.stash()
            if self.scene_id:
                update_scene_body(self.root, self.chapter_id, self.scene_id, self.text, expected=self.baseline)
            else:
                update_chapter_body(self.root, self.chapter_id, self.text, expected=self.baseline)
            self.baseline = find_chapter(self.root, self.chapter_id).path.read_bytes()
            self.original = self.text
            self.draft_path.unlink(missing_ok=True)
            self.draft_baseline = None

    def diff(self) -> str:
        return "\n".join(difflib.unified_diff(
            self.original.splitlines(), self.text.splitlines(), fromfile="saved", tofile="draft", lineterm=""
        ))
