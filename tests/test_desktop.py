from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QDialog, QFileDialog, QInputDialog, QMessageBox

from openscribe.desktop import AuthorWindow, ReviewDialog
from openscribe.project import add_scene, create_chapter, create_part, init_project, list_chapters
from openscribe.proofreading import ProofreadingIssue, ProofreadingResult
from openscribe.snapshots import list_snapshots


@pytest.fixture
def window(qtbot, tmp_path, monkeypatch):
    root = init_project(tmp_path, "Writing desk")
    create_part(root, "Opening")
    create_chapter(root, "Arrival")
    create_chapter(root, "Departure")
    add_scene(root, "Arrival", "Station", "This are wrong.")
    app = AuthorWindow(root)
    qtbot.addWidget(app)
    app.show()
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Discard)
    yield app
    if app.worker:
        app.worker.wait(2000)
    for session in app.sessions.values():
        session.discard()
    app.active_session = None


def scene_item(window):
    return window.binder.topLevelItem(0).child(0).child(0)


def test_desktop_typing_navigation_save_and_conflict(window, qtbot):
    item = scene_item(window)
    window.binder.setCurrentItem(item)
    window.editor.selectAll()
    qtbot.keyClicks(window.editor, "A revised scene.")
    window.binder.setCurrentItem(window.binder.topLevelItem(0).child(1))
    window.binder.setCurrentItem(item)
    assert window.editor.toPlainText() == "A revised scene."
    window.save()
    assert list_chapters(window.root)[0].scenes[0].body == "A revised scene."
    assert list_snapshots(window.root)
    window.editor.insertPlainText("More writing")
    chapter = list_chapters(window.root)[0]
    chapter.path.write_bytes(chapter.path.read_bytes() + b"External edit")
    window._run(window.save)
    assert "changed on disk" in window.last_error
    assert "External edit" in chapter.path.read_text(encoding="utf-8")


def test_desktop_proofreading_preview_apply_undo_and_stale_refusal(window, monkeypatch):
    window.binder.setCurrentItem(scene_item(window))
    issue = ProofreadingIssue("Use is", "", 5, 3, ("is",), "GRAMMAR", "Grammar", "grammar", "This are wrong.")
    result = ProofreadingResult((issue,), "en-US", "synthetic", False)
    window.proofreading_complete(result, window.editor.toPlainText(), window.active_session)
    monkeypatch.setattr(ReviewDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    window.preview_suggestion()
    window.apply_suggestion()
    assert window.editor.toPlainText() == "This is wrong."
    window.editor.undo()
    assert window.editor.toPlainText() == "This are wrong."
    window.proofreading_complete(result, window.editor.toPlainText(), window.active_session)
    window.preview_suggestion()
    window.editor.insertPlainText("changed")
    window._run(window.apply_suggestion)
    assert "Text changed" in window.last_error
    window.ignore_finding()
    assert not window.finding_items


def test_desktop_async_proofreading_and_hosted_refusal(window, qtbot, monkeypatch):
    window.binder.setCurrentItem(scene_item(window))
    monkeypatch.setattr("openscribe.desktop.check_text", lambda *args: ProofreadingResult((), "en-US", "fake", False))
    window.proofread()
    qtbot.waitUntil(lambda: window.statusBar().currentMessage() == "0 findings")
    qtbot.waitUntil(lambda: not window.worker.isRunning())
    window.config["proofreading"]["endpoint"] = "https://example.test/v2/check"
    window._run(window.proofread)
    assert "local only" in window.last_error


def test_desktop_empty_search_reference_and_close_cancel(window, monkeypatch):
    window.filter_binder("nothing matches")
    assert window.binder.topLevelItem(0).isHidden()
    window.filter_binder("")
    assert not window.binder.topLevelItem(0).isHidden()
    window.binder.setCurrentItem(window.binder.topLevelItem(1).child(0))
    assert window.editor.isReadOnly()
    window.binder.setCurrentItem(scene_item(window))
    window.editor.insertPlainText("draft")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Cancel)
    assert not window.confirm_leave()
    window.close()
    assert window.isVisible()


def test_desktop_create_scene_move_export_and_restore(window, monkeypatch):
    monkeypatch.setattr(QInputDialog, "getText", lambda *args: ("New writing", True))
    window.new_chapter()
    assert any(c.title == "New writing" for c in list_chapters(window.root))
    window.binder.setCurrentItem(scene_item(window))
    window.new_scene()
    assert len(list_chapters(window.root)[0].scenes) == 2
    window.binder.setCurrentItem(scene_item(window))
    monkeypatch.setattr(ReviewDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    window.move_scene(1)
    assert list_chapters(window.root)[0].scenes[1].title == "Station"
    window.binder.setCurrentItem(scene_item(window))
    window.checkpoint()
    output = window.root / "build" / "manuscript.docx"
    monkeypatch.setattr(QInputDialog, "getItem", lambda *args, **kwargs: ("docx", True))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(output), ""))
    window.choose_export()
    assert output.exists()
    checkpoint = Path(list_snapshots(window.root)[0]["path"]).name
    monkeypatch.setattr(QInputDialog, "getItem", lambda *args, **kwargs: (checkpoint, True))
    window.choose_restore()
    assert len(list_chapters(window.root)) == 3


def test_desktop_reload_and_project_dialogs(window, monkeypatch, tmp_path):
    window.binder.setCurrentItem(scene_item(window))
    window.editor.insertPlainText("unsaved")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    window.reload_selected()
    assert window.editor.toPlainText() == "This are wrong."
    new_root = tmp_path / "another"
    new_root.mkdir()
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(new_root))
    monkeypatch.setattr(QInputDialog, "getText", lambda *args: ("Another project", True))
    window.new_project()
    assert window.root == new_root
    window.choose_project()
    assert window.config["title"] == "Another project"


def test_desktop_word_export_and_import_preview(window, monkeypatch):
    output = window.root / "build" / "roundtrip.docx"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(output), ""))
    window.word_export()
    assert output.exists()
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(output), ""))
    dialogs = []

    def reject(self):
        dialogs.append(self.windowTitle())
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(ReviewDialog, "exec", reject)
    before = [chapter.path.read_bytes() for chapter in list_chapters(window.root)]
    window.word_import()
    assert dialogs == ["Review Word import"]
    assert [chapter.path.read_bytes() for chapter in list_chapters(window.root)] == before
