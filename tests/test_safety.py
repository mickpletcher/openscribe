from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
import yaml
from textual.widgets import Static, TextArea, Tree

from openscribe import ai, snapshots
from openscribe.editing import EditConflictError, EditSession
from openscribe.migrations import repair_project_identities
from openscribe.project import (
    add_scene,
    create_chapter,
    create_part,
    init_project,
    list_chapters,
    load_project_config,
    parse_scenes,
    update_chapter_body,
)
from openscribe.proofreading import ProofreadingIssue, ProofreadingResult
from openscribe.tui import OpenScribeApp, UnsavedDialog


def make_project(tmp_path):
    root = init_project(tmp_path, "Synthetic assessment")
    create_part(root, "Opening")
    create_chapter(root, "Arrival", part="Opening")
    return root


def test_typed_draft_survives_navigation_and_quit_cancel(tmp_path):
    root = make_project(tmp_path)
    create_chapter(root, "Departure", part="Opening")
    app = OpenScribeApp(root)

    async def exercise():
        async with app.run_test() as pilot:
            binder = app.query_one("#binder-tree", Tree)
            chapters = binder.root.children[0].children[0].children
            binder.select_node(chapters[0])
            await pilot.pause()
            editor = app.query_one("#editor", TextArea)
            editor.focus()
            await pilot.press("x", "y", "z")
            binder.select_node(chapters[1])
            await pilot.pause()
            binder.select_node(chapters[0])
            await pilot.pause()
            assert "xyz" in editor.text
            binder.focus()
            await pilot.press("q")
            assert isinstance(app.screen, UnsavedDialog)
            await pilot.click("#cancel")
            assert editor.text == "xyz"

    asyncio.run(exercise())
    recovered = EditSession.open(root, list_chapters(root)[0].chapter_id)
    assert recovered.text == "xyz"
    assert recovered.dirty


def test_stale_editor_save_refuses_without_losing_draft(tmp_path):
    root = make_project(tmp_path)
    chapter = list_chapters(root)[0]
    session = EditSession.open(root, chapter.chapter_id)
    session.text = "New draft"
    session.stash()
    chapter.path.write_bytes(chapter.path.read_bytes() + b"External edit\n")
    before = chapter.path.read_bytes()
    with pytest.raises(EditConflictError, match="changed on disk"):
        session.save()
    assert chapter.path.read_bytes() == before
    assert session.text == "New draft"
    assert session.draft_path.exists()


def test_chapter_editor_refuses_ambiguous_rename_and_reorder(tmp_path):
    root = make_project(tmp_path)
    add_scene(root, "Arrival", "Alpha", "ALPHA BODY")
    add_scene(root, "Arrival", "Beta", "BETA BODY")
    chapter = list_chapters(root)[0]
    before = chapter.path.read_bytes()
    with pytest.raises(ValueError, match="cannot infer scene identity"):
        update_chapter_body(root, "Arrival", "## Beta renamed\n\nBETA BODY\n\n## Alpha renamed\n\nALPHA BODY")
    assert chapter.path.read_bytes() == before


def test_listing_is_read_only_and_identity_repair_is_explicit(tmp_path):
    root = make_project(tmp_path)
    path = list_chapters(root)[0].path
    path.write_bytes(path.read_bytes() + b"## New scene\n\nA hard break.  \nNext line.\n")
    before = path.read_bytes()
    assert list_chapters(root)[0].scenes[0].scene_id == ""
    assert path.read_bytes() == before
    backup = repair_project_identities(root)
    assert backup.exists()
    assert list_chapters(root)[0].scenes[0].scene_id.startswith("scene-")
    assert "A hard break.  \nNext line." in path.read_text(encoding="utf-8")


def test_fenced_headings_are_not_scenes():
    body = "## Real scene\n\n```markdown\n## Code example\n```\n\n~~~\n## Another example\n~~~"
    assert [scene.title for scene in parse_scenes(body)] == ["Real scene"]


@pytest.mark.parametrize("endpoint", ["https://hosted.example.test/v1", "http://192.0.2.1/v1"])
def test_nonlocal_ai_endpoint_cannot_bypass_consent(monkeypatch, endpoint):
    calls = []

    class FakeClient:
        def __init__(self, **kwargs):
            calls.append(kwargs)
            self.responses = self

        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(output_text="Synthetic response")

    monkeypatch.setenv("OPENAI_COMPATIBLE_LOCAL_BASE_URL", endpoint)
    monkeypatch.setattr(ai, "_load_dependency", lambda *args: SimpleNamespace(OpenAI=FakeClient))
    settings = ai.AISettings(enabled=True, provider="openai-compatible-local", model="synthetic")
    with pytest.raises(ai.AIConfigurationError):
        ai.run_ai_task("SYNTHETIC", settings, "chapter", "summarize")
    assert calls == []


def test_failed_restore_never_replays_against_later_notes(tmp_path, monkeypatch):
    root = make_project(tmp_path)
    (root / "notes" / "snapshot-note.md").write_text("Synthetic", encoding="utf-8")
    checkpoint = snapshots.create_snapshot(root, "synthetic checkpoint")
    (root / "notes").rename(root / "notes-set-aside")
    real_write = snapshots.atomic_write_text
    failed_once = False

    def fail_one_commit(path, text):
        nonlocal failed_once
        if path.name == "journal.yaml" and "state: committed" in text and not failed_once:
            failed_once = True
            raise OSError("Synthetic commit failure")
        return real_write(path, text)

    monkeypatch.setattr(snapshots, "atomic_write_text", fail_one_commit)
    with pytest.raises(RuntimeError, match="automatic backup was restored"):
        snapshots.restore_snapshot(root, checkpoint.name)
    assert failed_once
    (root / "notes").mkdir(exist_ok=True)
    new_note = root / "notes" / "later.md"
    new_note.write_text("Work after rollback", encoding="utf-8")
    load_project_config(root)
    load_project_config(root)
    assert new_note.read_text(encoding="utf-8") == "Work after rollback"


def test_rolled_back_journal_cleanup_failure_is_safe_to_repeat(tmp_path, monkeypatch):
    root = make_project(tmp_path)
    transaction = root / ".openscribe" / ".restore-transaction-residue"
    transaction.mkdir()
    journal = {"version": 1, "state": "rolled_back", "operations": [
        {"path": "notes", "target_existed": False, "staged_existed": True},
    ]}
    (transaction / "journal.yaml").write_text(yaml.safe_dump(journal), encoding="utf-8")
    note = root / "notes" / "later.md"
    note.write_text("New work", encoding="utf-8")
    monkeypatch.setattr(snapshots, "_cleanup_restore_transaction", lambda path: None)
    snapshots.recover_interrupted_restores(root)
    snapshots.recover_interrupted_restores(root)
    assert note.read_text(encoding="utf-8") == "New work"


def test_invalid_journal_is_validated_before_any_rollback(tmp_path):
    root = make_project(tmp_path)
    transaction = root / ".openscribe" / ".restore-transaction-invalid"
    transaction.mkdir()
    journal = {"version": 1, "state": "applying", "operations": [
        {"path": "notes", "target_existed": False, "staged_existed": True},
        {"path": "manuscript", "target_existed": "yes", "staged_existed": True},
    ]}
    (transaction / "journal.yaml").write_text(yaml.safe_dump(journal), encoding="utf-8")
    with pytest.raises(RuntimeError, match="booleans"):
        snapshots.recover_interrupted_restores(root)
    assert (root / "notes").exists()


def test_session_save_has_a_checkpoint(tmp_path):
    root = make_project(tmp_path)
    chapter = list_chapters(root)[0]
    session = EditSession.open(root, chapter.chapter_id)
    session.text = "Saved writing"
    session.save()
    assert not session.dirty
    assert snapshots.list_snapshots(root)
    assert "Saved writing" in chapter.path.read_text(encoding="utf-8")


@pytest.mark.parametrize("choice", ["save", "discard"])
def test_tui_quit_save_and_discard_are_explicit(tmp_path, choice):
    root = make_project(tmp_path)
    app = OpenScribeApp(root)

    async def exercise():
        async with app.run_test() as pilot:
            app._apply_selection(app.chapters[0].path.as_posix())
            editor = app.query_one("#editor", TextArea)
            editor.focus()
            await pilot.press("d", "r", "a", "f", "t")
            app.query_one("#binder-tree", Tree).focus()
            await pilot.press("q")
            assert isinstance(app.screen, UnsavedDialog)
            await pilot.click(f"#{choice}")

    asyncio.run(exercise())
    chapter = list_chapters(root)[0]
    assert ("draft" in chapter.body) == (choice == "save")
    assert not EditSession.open(root, chapter.chapter_id).dirty


def test_tui_background_proofreading_preview_apply_undo_and_stale_error(tmp_path, monkeypatch):
    root = make_project(tmp_path)
    update_chapter_body(root, "Arrival", "This are wrong.")
    issue = ProofreadingIssue("Use is", "", 5, 3, ("is",), "GRAMMAR", "Grammar", "grammar", "This are wrong.")
    monkeypatch.setattr("openscribe.tui.check_text", lambda *args: ProofreadingResult((issue,), "en-US", "synthetic", False))
    app = OpenScribeApp(root)

    async def check(pilot):
        await pilot.press("ctrl+g")
        await app.workers.wait_for_complete()
        await pilot.pause()

    async def exercise():
        async with app.run_test(size=(140, 45)) as pilot:
            app._apply_selection(app.chapters[0].path.as_posix())
            editor = app.query_one("#editor", TextArea)
            editor.focus()
            await check(pilot)
            original = editor.text
            assert original == "This are wrong.\n"
            await pilot.press("ctrl+j", "ctrl+k", "ctrl+shift+r")
            assert app.suggestion_preview is not None
            assert editor.text == original
            await pilot.press("ctrl+shift+a")
            assert editor.text == "This is wrong.\n"
            await pilot.press("ctrl+z")
            assert editor.text == original
            await check(pilot)
            await pilot.press("ctrl+shift+r")
            editor.insert("changed")
            await pilot.press("ctrl+shift+a")
            assert "Text changed" in str(app.query_one("#proofreading", Static).content)
            await pilot.press("ctrl+shift+i")
            assert not app.findings

    asyncio.run(exercise())
