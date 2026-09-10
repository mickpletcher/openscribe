from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QDialog, QFileDialog, QInputDialog, QLineEdit, QMessageBox

from openscribe.desktop import (
    AI_INSERTION_MARKER,
    AISetupDialog,
    AIWritingDialog,
    AuthorWindow,
    ReviewDialog,
    _ai_writing_context,
)
from openscribe.project import add_scene, create_chapter, create_part, init_project, list_chapters, load_project_config
from openscribe.proofreading import ProofreadingIssue, ProofreadingResult
from openscribe.snapshots import list_snapshots


@pytest.fixture
def window(qtbot, tmp_path, monkeypatch):
    root = init_project(tmp_path, "Writing desk")
    create_part(root, "Opening")
    create_chapter(root, "Arrival")
    create_chapter(root, "Departure")
    add_scene(root, "Arrival", "Station", "This are wrong.")
    settings = QSettings(str(tmp_path / "app-settings.ini"), QSettings.Format.IniFormat)
    app = AuthorWindow(root, show_ai_onboarding=False, app_settings=settings)
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
    window.app_settings.setValue("ai/provider", "openai-compatible-local")
    window.app_settings.setValue("ai/model", "local-test-default")
    window.app_settings.setValue("ai/endpoint", "http://127.0.0.1:11434/v1/")
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(new_root))
    monkeypatch.setattr(QInputDialog, "getText", lambda *args: ("Another project", True))
    window.new_project()
    assert window.root == new_root
    assert load_project_config(new_root)["ai"] == {
        "enabled": True,
        "provider": "openai-compatible-local",
        "model": "local-test-default",
        "endpoint": "http://127.0.0.1:11434/v1/",
    }
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


def test_ai_setup_dialog_masks_key_and_accepts_editable_model(qtbot):
    dialog = AISetupDialog("anthropic", "custom-model", "", {"anthropic": False})
    qtbot.addWidget(dialog)
    assert dialog.api_key.echoMode() == QLineEdit.EchoMode.Password
    assert dialog.model.isEditable()
    assert dialog.provider_id() == "anthropic"
    assert dialog.model_id() == "custom-model"
    assert not dialog.endpoint.isEnabled()
    providers = {dialog.provider.itemData(index) for index in range(dialog.provider.count())}
    assert {"openai", "anthropic", "gemini", "mistral", "xai", "deepseek", "azure-openai", "lm-studio"} <= providers


def test_ai_setup_dialog_has_lm_studio_preset(qtbot):
    dialog = AISetupDialog("lm-studio", "", "", {})
    qtbot.addWidget(dialog)
    assert dialog.provider_id() == "lm-studio"
    assert dialog.model_id() == "openai/gpt-oss-20b"
    assert dialog.endpoint_url() == "http://127.0.0.1:1234/v1/"
    assert dialog.endpoint.isEnabled()
    assert "optional" in dialog.key_label.text().lower()


def test_ai_writing_dialog_collects_scope_and_description(qtbot):
    dialog = AIWritingDialog()
    qtbot.addWidget(dialog)
    dialog.scope.setCurrentIndex(1)
    dialog.description.setPlainText("Draft the confrontation in a restrained tone.")
    assert dialog.scope_id() == "chapter"
    assert dialog.writing_description() == "Draft the confrontation in a restrained tone."


def test_ai_page_context_marks_utf16_editor_cursor_without_saving_marker():
    text = "Before 😀 after"
    cursor_position = len("Before 😀".encode("utf-16-le")) // 2
    context = _ai_writing_context(text, "page", cursor_position)
    assert context == f"Before 😀\n\n{AI_INSERTION_MARKER}\n\n after"
    assert _ai_writing_context(text, "chapter", cursor_position) == text


def test_ai_page_draft_is_previewed_and_added_to_unsaved_editor(window, monkeypatch):
    window.binder.setCurrentItem(scene_item(window))
    cursor = window.editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    window.editor.setTextCursor(cursor)
    before = window.editor.toPlainText()
    monkeypatch.setattr(ReviewDialog, "exec", lambda self: QDialog.DialogCode.Accepted)

    window.ai_writing_complete("Generated next page.", "page", before, cursor.position(), window.active_session)

    assert window.editor.toPlainText() == before + "\n\nGenerated next page."
    assert window.active_session.dirty
    assert list_chapters(window.root)[0].scenes[0].body == "This are wrong."


def test_ai_chapter_draft_is_previewed_and_replaces_only_unsaved_draft(window, monkeypatch):
    window.binder.setCurrentItem(window.binder.topLevelItem(0).child(0))
    before = window.editor.toPlainText()
    monkeypatch.setattr(ReviewDialog, "exec", lambda self: QDialog.DialogCode.Accepted)

    window.ai_writing_complete("A complete generated chapter.", "chapter", before, 0, window.active_session)

    assert window.editor.toPlainText() == "A complete generated chapter."
    assert window.active_session.dirty
    assert "A complete generated chapter." not in list_chapters(window.root)[0].body


def test_ai_draft_is_not_applied_when_editor_changes(window, monkeypatch):
    window.binder.setCurrentItem(scene_item(window))
    before = window.editor.toPlainText()
    window.editor.insertPlainText(" Local change.")
    monkeypatch.setattr(ReviewDialog, "exec", lambda self: pytest.fail("stale output must not be previewed"))

    window.ai_writing_complete("Stale generated text.", "page", before, 0, window.active_session)

    assert " Local change." in window.editor.toPlainText()
    assert "Stale generated text." not in window.editor.toPlainText()
    assert "not applied" in window.statusBar().currentMessage()


def test_hosted_ai_writing_requires_per_request_consent(window, monkeypatch):
    window.binder.setCurrentItem(scene_item(window))
    window.config["ai"] = {"enabled": True, "provider": "openai", "model": "test-model"}

    class AcceptedWriting:
        def __init__(self, *args):
            return None

        def exec(self):
            return QDialog.DialogCode.Accepted

        def scope_id(self):
            return "page"

        def writing_description(self):
            return "Continue the arrival scene."

    monkeypatch.setattr("openscribe.desktop.AIWritingDialog", AcceptedWriting)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)

    window.write_with_ai()

    assert window.ai_worker is None


def test_local_ai_writing_starts_without_transfer_prompt(window, monkeypatch):
    window.binder.setCurrentItem(scene_item(window))
    window.config["ai"] = {
        "enabled": True,
        "provider": "lm-studio",
        "model": "local-test-model",
        "endpoint": "http://127.0.0.1:1234/v1/",
    }

    class AcceptedWriting:
        def __init__(self, *args):
            return None

        def exec(self):
            return QDialog.DialogCode.Accepted

        def scope_id(self):
            return "page"

        def writing_description(self):
            return "Continue the arrival scene."

    class Connection:
        def connect(self, callback):
            return None

    started = {}

    class FakeWorker:
        def __init__(self, *args):
            started["args"] = args
            self.completed = Connection()
            self.failed = Connection()

        def start(self):
            started["started"] = True

    monkeypatch.setattr("openscribe.desktop.AIWritingDialog", AcceptedWriting)
    monkeypatch.setattr("openscribe.desktop.AIWritingWorker", FakeWorker)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: pytest.fail("local AI must not request transfer"))

    window.write_with_ai()

    assert started["started"]
    assert started["args"][1].provider == "lm-studio"
    assert started["args"][3] == "page"
    assert started["args"][7] is True


def test_ai_setup_dialog_supports_local_endpoint(qtbot):
    dialog = AISetupDialog(
        "openai-compatible-local",
        "qwen-test",
        "http://127.0.0.1:1234/v1/",
        {},
    )
    qtbot.addWidget(dialog)
    assert dialog.provider_id() == "openai-compatible-local"
    assert dialog.model_id() == "qwen-test"
    assert dialog.endpoint.isEnabled()
    assert dialog.endpoint_url() == "http://127.0.0.1:1234/v1/"
    assert "optional" in dialog.key_label.text().lower()


def test_first_run_ai_setup_connects_and_updates_project(window, monkeypatch):
    credential = "synthetic" + "-value"

    class AcceptedSetup:
        def __init__(self, *args):
            return None

        def exec(self):
            return QDialog.DialogCode.Accepted

        def model_id(self):
            return "gpt-test"

        def provider_id(self):
            return "anthropic"

        def endpoint_url(self):
            return ""

        def entered_api_key(self):
            return credential

    checked = {}
    monkeypatch.setattr("openscribe.desktop.AISetupDialog", AcceptedSetup)
    monkeypatch.setattr("openscribe.desktop.has_api_key", lambda provider: False)
    monkeypatch.setattr(
        "openscribe.desktop.test_ai_connection",
        lambda settings, key: checked.update(settings=settings, key=key),
    )
    monkeypatch.setattr(
        "openscribe.desktop.save_api_key",
        lambda provider, key: checked.update(saved_provider=provider, saved=key),
    )

    window.show_ai_onboarding()

    assert checked["settings"].provider == "anthropic"
    assert checked["settings"].model == "gpt-test"
    assert checked["key"] == credential
    assert checked["saved_provider"] == "anthropic"
    assert checked["saved"] == credential
    assert window.app_settings.value("onboarding/ai_prompt_completed", False, type=bool)
    config = load_project_config(window.root)
    assert config["ai"] == {"enabled": True, "provider": "anthropic", "model": "gpt-test"}
    assert credential not in (window.root / ".openscribe" / "project.yaml").read_text(encoding="utf-8")


def test_first_run_ai_setup_can_be_skipped(window, monkeypatch):
    monkeypatch.setattr("openscribe.desktop.AISetupDialog.exec", lambda self: QDialog.DialogCode.Rejected)
    monkeypatch.setattr("openscribe.desktop.has_api_key", lambda provider: False)
    window.show_ai_onboarding()
    assert window.app_settings.value("onboarding/ai_prompt_completed", False, type=bool)
