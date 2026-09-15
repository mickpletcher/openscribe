from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QFont, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from openscribe.ai import (
    AI_PROVIDERS,
    AISettings,
    generate_draft,
    has_api_key,
    load_ai_settings,
    provider_definition,
    save_api_key,
    test_ai_connection,
)
from openscribe.ai import (
    requires_data_transfer_consent as ai_requires_data_transfer_consent,
)
from openscribe.compile import compile_project
from openscribe.editing import EditSession
from openscribe.project import (
    add_scene,
    apply_scene_operation,
    create_chapter,
    create_part,
    init_project,
    list_auxiliary_documents,
    list_chapters,
    load_project_config,
    plan_reorder_scene,
    save_project_config,
    scene_operation_diff,
)
from openscribe.proofreading import (
    check_text,
    load_languagetool_settings,
    preview_replacement,
)
from openscribe.proofreading import (
    requires_data_transfer_consent as proofreading_requires_data_transfer_consent,
)
from openscribe.snapshots import create_snapshot, list_snapshots, preview_snapshot_restore, restore_snapshot

AI_INSERTION_MARKER = "[OPENSCRIBE INSERT THE NEW PAGE HERE]"


def _ai_writing_context(text: str, scope: str, cursor_position: int) -> str:
    if scope != "page":
        return text
    encoded = text.encode("utf-16-le")
    byte_position = cursor_position * 2
    if byte_position < 0 or byte_position > len(encoded):
        raise ValueError("The editor cursor position is invalid. Generate the draft again.")
    try:
        python_position = len(encoded[:byte_position].decode("utf-16-le"))
    except UnicodeDecodeError as exc:
        raise ValueError("The editor cursor position splits a Unicode character. Generate the draft again.") from exc
    return text[:python_position] + f"\n\n{AI_INSERTION_MARKER}\n\n" + text[python_position:]


class ProofreadingWorker(QThread):
    completed = Signal(object, str, object)
    failed = Signal(str)

    def __init__(self, text, settings, session, parent=None):
        super().__init__(parent)
        self.text, self.settings, self.session = text, settings, session

    def run(self):
        try:
            self.completed.emit(check_text(self.text, self.settings), self.text, self.session)
        except (OSError, RuntimeError, ValueError) as exc:
            self.failed.emit(str(exc))


class AIWritingWorker(QThread):
    completed = Signal(str, str, str, int, object)
    failed = Signal(str)

    def __init__(self, text, settings, context_label, scope, description, cursor_position, session, consent, parent=None):
        super().__init__(parent)
        self.text = text
        self.settings = settings
        self.context_label = context_label
        self.scope = scope
        self.description = description
        self.cursor_position = cursor_position
        self.session = session
        self.consent = consent

    def run(self):
        try:
            result = generate_draft(
                _ai_writing_context(self.text, self.scope, self.cursor_position),
                self.settings,
                self.context_label,
                self.scope,
                self.description,
                allow_data_transfer=self.consent,
            )
            self.completed.emit(result, self.scope, self.text, self.cursor_position, self.session)
        except (OSError, RuntimeError, ValueError) as exc:
            self.failed.emit(str(exc))


class ReviewDialog(QDialog):
    def __init__(self, title: str, text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(760, 540)
        layout = QVBoxLayout(self)
        view = QPlainTextEdit()
        view.setReadOnly(True)
        view.setPlainText(text)
        layout.addWidget(view)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class AIWritingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Write with AI")
        self.resize(620, 430)
        layout = QVBoxLayout(self)
        heading = QLabel("Describe what should happen next")
        heading.setObjectName("documentTitle")
        layout.addWidget(heading)
        guidance = QLabel(
            "Include the events, characters, setting, tone, point of view, and constraints the draft should follow. "
            "The result is previewed before it is added to your unsaved draft."
        )
        guidance.setWordWrap(True)
        layout.addWidget(guidance)
        layout.addWidget(QLabel("Draft scope"))
        self.scope = QComboBox()
        self.scope.addItem("Page, about 250 to 350 words", "page")
        self.scope.addItem("Complete chapter", "chapter")
        self.scope.setAccessibleName("AI writing scope")
        layout.addWidget(self.scope)
        layout.addWidget(QLabel("Writing description"))
        self.description = QPlainTextEdit()
        self.description.setAccessibleName("AI writing description")
        self.description.setPlaceholderText(
            "Example: Mara enters the abandoned station at dusk, finds evidence that her brother was here, "
            "and hears someone approaching. Keep the tone tense and stay in close third person."
        )
        layout.addWidget(self.description)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Generate draft")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def scope_id(self) -> str:
        return str(self.scope.currentData())

    def writing_description(self) -> str:
        return self.description.toPlainText().strip()


class AISetupDialog(QDialog):
    def __init__(
        self,
        provider: str,
        model: str,
        endpoint: str,
        available_keys: dict[str, bool],
        parent=None,
    ):
        super().__init__(parent)
        self.available_keys = available_keys
        self.setWindowTitle("Connect an AI model")
        self.resize(620, 440)
        layout = QVBoxLayout(self)
        heading = QLabel("Connect an AI model")
        heading.setObjectName("documentTitle")
        layout.addWidget(heading)
        self.disclosure = QLabel(
            "Connecting tests the API key and model without sending manuscript text. "
            "Later AI commands require explicit approval before sending manuscript text to a hosted endpoint."
        )
        self.disclosure.setWordWrap(True)
        layout.addWidget(self.disclosure)
        layout.addWidget(QLabel("Provider"))
        self.provider = QComboBox()
        for definition in AI_PROVIDERS:
            self.provider.addItem(definition.label, definition.provider_id)
        self.provider.setAccessibleName("AI provider")
        layout.addWidget(self.provider)
        self.account_link = QLabel()
        self.account_link.setOpenExternalLinks(True)
        layout.addWidget(self.account_link)
        layout.addWidget(QLabel("Model ID"))
        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.setAccessibleName("AI model ID")
        layout.addWidget(self.model)
        layout.addWidget(QLabel("API endpoint"))
        self.endpoint = QLineEdit()
        self.endpoint.setAccessibleName("AI API endpoint")
        layout.addWidget(self.endpoint)
        self.key_label = QLabel("API key")
        layout.addWidget(self.key_label)
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setAccessibleName("AI API key")
        layout.addWidget(self.api_key)
        self.storage = QLabel(
            "A pasted key is stored in your operating system credential store. "
            "It is never written to the project or shown again. The provider's environment variable takes priority."
        )
        self.storage.setWordWrap(True)
        layout.addWidget(self.storage)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Connect")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Not now")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        provider_index = self.provider.findData(provider)
        self.provider.setCurrentIndex(provider_index if provider_index >= 0 else 0)
        self.provider.currentIndexChanged.connect(lambda: self._provider_changed())
        self._provider_changed(model, endpoint)

    def _provider_changed(self, model: str = "", endpoint: str = "") -> None:
        definition = provider_definition(self.provider_id())
        if definition.provider_id == "freellmapi":
            routing_disclosure = (
                " FreeLLMAPI accepts the request locally, then forwards it to hosted model providers. "
                "Every manuscript request requires separate approval."
            )
        else:
            routing_disclosure = " A loopback local endpoint normally keeps requests on this computer."
        self.disclosure.setText(
            "Connecting tests the API key and model without sending manuscript text. "
            "Later AI commands require explicit approval before sending manuscript text to a hosted endpoint."
            + routing_disclosure
        )
        self.model.clear()
        self.model.addItems(definition.models)
        self.model.setCurrentText(model or definition.models[0])
        self.endpoint.setEnabled(definition.endpoint_required)
        self.endpoint.setText(endpoint or definition.default_endpoint)
        self.endpoint.setPlaceholderText("Not required" if not definition.endpoint_required else definition.default_endpoint)
        self.account_link.setText(f'<a href="{definition.account_url}">Provider setup and API key instructions</a>')
        if definition.api_key_optional:
            self.key_label.setText("API key (optional)")
            placeholder = "Optional saved key available" if self.available_keys.get(definition.provider_id) else "Optional"
        else:
            self.key_label.setText("API key")
            placeholder = "Saved key available" if self.available_keys.get(definition.provider_id) else "Paste an API key"
        self.api_key.clear()
        self.api_key.setPlaceholderText(placeholder)

    def provider_id(self) -> str:
        return str(self.provider.currentData())

    def model_id(self) -> str:
        return self.model.currentText().strip()

    def entered_api_key(self) -> str:
        return self.api_key.text().strip()

    def endpoint_url(self) -> str:
        return self.endpoint.text().strip() if self.endpoint.isEnabled() else ""


class AuthorWindow(QMainWindow):
    def __init__(self, root: Path | None = None, *, show_ai_onboarding: bool = True, app_settings=None):
        super().__init__()
        self.app_settings = app_settings or QSettings("OpenScribe", "OpenScribe")
        self.root = None
        self.config = {}
        self.sessions = {}
        self.active_session = None
        self.worker = None
        self.ai_worker = None
        self.checked_text = ""
        self.finding_items = []
        self.pending_replacement = None
        self.last_error = ""
        self.setWindowTitle("OpenScribe")
        self.resize(1320, 860)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f5f4ef; color: #252b2d; }
            QPlainTextEdit, QTreeWidget, QListWidget, QLineEdit, QComboBox { background: #fffefa; }
            QToolBar { spacing: 8px; padding: 8px; border-bottom: 1px solid #cfcec6; }
            QPushButton { padding: 7px 10px; }
            QLabel#documentTitle { font-size: 21px; font-weight: 600; padding: 8px 0; }
            QLabel#error { color: #9c2525; padding: 8px; background: #fce6e1; }
        """)
        toolbar = QToolBar("Writing")
        self.addToolBar(toolbar)
        for label, callback, shortcut in (
            ("New project", self.new_project, "Ctrl+N"), ("Open", self.choose_project, "Ctrl+O"),
            ("Save", self.save, "Ctrl+S"), ("Reload", self.reload_selected, ""),
            ("New chapter", self.new_chapter, ""), ("New scene", self.new_scene, ""),
            ("Move up", lambda: self.move_scene(-1), ""), ("Move down", lambda: self.move_scene(1), ""),
            ("Proofread", self.proofread, "Ctrl+G"), ("Export", self.choose_export, ""),
            ("Checkpoint", self.checkpoint, ""), ("Restore", self.choose_restore, ""),
            ("Write with AI", self.write_with_ai, "Ctrl+Shift+G"), ("AI setup", self.configure_ai, ""),
            ("Word export", self.word_export, ""), ("Word import", self.word_import, ""),
        ):
            action = QAction(label, self)
            if shortcut:
                action.setShortcut(shortcut)
            action.triggered.connect(lambda checked=False, fn=callback: self._run(fn))
            toolbar.addAction(action)
        container = QWidget()
        layout = QVBoxLayout(container)
        self.error = QLabel()
        self.error.setObjectName("error")
        self.error.setWordWrap(True)
        self.error.hide()
        layout.addWidget(self.error)
        splitter = QSplitter()
        layout.addWidget(splitter)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("PROJECT BINDER"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search chapters, scenes, and research")
        self.search.setAccessibleName("Search project")
        self.search.textChanged.connect(self.filter_binder)
        left_layout.addWidget(self.search)
        self.binder = QTreeWidget()
        self.binder.setHeaderHidden(True)
        self.binder.setAccessibleName("Project binder")
        self.binder.currentItemChanged.connect(lambda item, previous: self._run(lambda: self.select(item)))
        left_layout.addWidget(self.binder)
        splitter.addWidget(left)
        center = QWidget()
        center_layout = QVBoxLayout(center)
        self.title = QLabel("Your writing, kept in your files")
        self.title.setObjectName("documentTitle")
        center_layout.addWidget(self.title)
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Georgia", 13))
        self.editor.setPlaceholderText("Create or open a project to start writing.")
        self.editor.setAccessibleName("Manuscript editor")
        self.editor.setReadOnly(True)
        self.editor.textChanged.connect(self.text_changed)
        center_layout.addWidget(self.editor, 3)
        self.findings = QListWidget()
        self.findings.setAccessibleName("Proofreading findings")
        self.findings.currentRowChanged.connect(self.select_finding)
        center_layout.addWidget(self.findings, 1)
        controls = QHBoxLayout()
        self.suggestions = QComboBox()
        self.suggestions.setAccessibleName("Replacement suggestions")
        controls.addWidget(self.suggestions)
        for label, handler in (("Preview replacement", self.preview_suggestion), ("Apply preview", self.apply_suggestion),
                               ("Ignore finding", self.ignore_finding), ("Undo", self.editor.undo)):
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, fn=handler: self._run(fn))
            controls.addWidget(button)
        center_layout.addLayout(controls)
        splitter.addWidget(center)
        self.inspector = QPlainTextEdit()
        self.inspector.setReadOnly(True)
        self.inspector.setAccessibleName("Document details")
        splitter.addWidget(self.inspector)
        splitter.setSizes([260, 800, 260])
        self.setCentralWidget(container)
        self.draft_timer = QTimer(self)
        self.draft_timer.setInterval(1000)
        self.draft_timer.timeout.connect(lambda: self._run(self.stash))
        self.draft_timer.start()
        if root is not None:
            self._run(lambda: self.open_project(root))
        if show_ai_onboarding:
            QTimer.singleShot(0, self.show_ai_onboarding)

    def show_ai_onboarding(self):
        if not self.app_settings.value("onboarding/ai_prompt_completed", False, type=bool):
            self._run(lambda: self.configure_ai(first_run=True))

    def configure_ai(self, *, first_run: bool = False):
        project_ai = self.config.get("ai", {})
        current_provider = str(project_ai.get("provider", "")).strip() if project_ai.get("enabled") else ""
        current_model = str(project_ai.get("model", "")).strip() if project_ai.get("enabled") else ""
        current_endpoint = str(project_ai.get("endpoint", "")).strip() if project_ai.get("enabled") else ""
        if not current_provider:
            current_provider = str(self.app_settings.value("ai/provider", "openai"))
        if not current_model:
            current_model = str(self.app_settings.value("ai/model", "gpt-5.6-terra"))
        if not current_endpoint:
            current_endpoint = str(self.app_settings.value("ai/endpoint", ""))
        available_keys = {definition.provider_id: has_api_key(definition.provider_id) for definition in AI_PROVIDERS}
        dialog = AISetupDialog(current_provider, current_model, current_endpoint, available_keys, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            if first_run:
                self.app_settings.setValue("onboarding/ai_prompt_completed", True)
                self.app_settings.sync()
            return
        provider = dialog.provider_id()
        model = dialog.model_id()
        endpoint = dialog.endpoint_url()
        entered_key = dialog.entered_api_key()
        settings = AISettings(True, provider, model, endpoint)
        test_ai_connection(settings, entered_key or None)
        if entered_key:
            save_api_key(provider, entered_key)
        saved_config = {"enabled": True, "provider": provider, "model": model}
        if endpoint:
            saved_config["endpoint"] = endpoint
        provider_label = provider_definition(provider).label
        if self.root is not None:
            self.config["ai"] = saved_config
            save_project_config(self.root, self.config)
            self.statusBar().showMessage(f"Connected {provider_label} model {model} for this project")
        else:
            self.statusBar().showMessage(f"Connected {provider_label} model {model}; new desktop projects will use it")
        self.app_settings.setValue("onboarding/ai_prompt_completed", True)
        self.app_settings.setValue("ai/provider", provider)
        self.app_settings.setValue("ai/model", model)
        self.app_settings.setValue("ai/endpoint", endpoint)
        self.app_settings.sync()

    def apply_saved_ai_default(self, root: Path) -> None:
        provider = str(self.app_settings.value("ai/provider", "")).strip()
        if provider not in {definition.provider_id for definition in AI_PROVIDERS}:
            return
        model = str(self.app_settings.value("ai/model", "")).strip()
        if not model:
            return
        endpoint = str(self.app_settings.value("ai/endpoint", "")).strip()
        config = load_project_config(root)
        config["ai"] = {"enabled": True, "provider": provider, "model": model}
        if endpoint:
            config["ai"]["endpoint"] = endpoint
        save_project_config(root, config)

    def _run(self, callback):
        try:
            return callback()
        except (OSError, RuntimeError, ValueError) as exc:
            self.show_error(str(exc))
            return None

    def show_error(self, message):
        self.last_error = message
        self.error.setText(message)
        self.error.show()
        self.statusBar().showMessage("Action failed. Your draft remains available.")

    def open_project(self, root: Path):
        config = load_project_config(root)
        if self.root and not self.confirm_leave():
            return
        self.root = root.resolve()
        self.config = config
        self.sessions = {}
        self.active_session = None
        self.setWindowTitle(f"{config.get('title', 'Untitled')} | OpenScribe")
        self.rebuild_binder()

    def rebuild_binder(self):
        self.stash()
        self.active_session = None
        self.editor.setReadOnly(True)
        self.editor.clear()
        self.binder.blockSignals(True)
        self.binder.clear()
        self.chapters = list_chapters(self.root)
        manuscript = QTreeWidgetItem(self.binder, ["Manuscript"])
        for chapter in self.chapters:
            item = QTreeWidgetItem(manuscript, [chapter.title])
            item.setData(0, Qt.ItemDataRole.UserRole, ("chapter", chapter.chapter_id, None))
            item.setData(0, Qt.ItemDataRole.UserRole + 1, chapter.title + " " + chapter.body)
            for scene in chapter.scenes:
                child = QTreeWidgetItem(item, [scene.title])
                child.setData(0, Qt.ItemDataRole.UserRole, ("scene", chapter.chapter_id, scene.scene_id))
                child.setData(0, Qt.ItemDataRole.UserRole + 1, scene.title + " " + scene.body)
        for category in ("research", "characters", "notes"):
            section = QTreeWidgetItem(self.binder, [category.title()])
            for note in list_auxiliary_documents(self.root, category):
                item = QTreeWidgetItem(section, [note.title])
                item.setData(0, Qt.ItemDataRole.UserRole, ("aux", str(note.path), None))
                item.setData(0, Qt.ItemDataRole.UserRole + 1, note.title + " " + note.body)
        self.binder.expandAll()
        self.binder.blockSignals(False)

    def filter_binder(self, query):
        def visit(item):
            child_matches = [visit(item.child(index)) for index in range(item.childCount())]
            text = item.data(0, Qt.ItemDataRole.UserRole + 1) or item.text(0)
            visible = not query or query.casefold() in text.casefold() or any(child_matches)
            item.setHidden(not visible)
            return visible
        for index in range(self.binder.topLevelItemCount()):
            visit(self.binder.topLevelItem(index))

    def select(self, item):
        self.stash()
        data = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not data:
            return
        self.active_session = None
        self.findings.clear()
        self.finding_items = []
        self.pending_replacement = None
        self.title.setText(item.text(0))
        if data[0] == "aux":
            self.editor.setReadOnly(True)
            self.editor.setPlainText(Path(data[1]).read_text(encoding="utf-8"))
            self.inspector.setPlainText("Reference document. This view is read only.")
            return
        key = (data[1], data[2])
        if key not in self.sessions:
            self.sessions[key] = EditSession.open(self.root, *key)
        self.editor.setReadOnly(False)
        session = self.sessions[key]
        self.editor.setPlainText(session.text)
        self.active_session = session
        chapter = next(chapter for chapter in self.chapters if chapter.chapter_id == data[1])
        self.inspector.setPlainText(
            f"{chapter.part}\n\nStatus: {chapter.status}\nPOV: {chapter.pov}\n"
            f"Words: {chapter.word_count}\nTarget: {chapter.word_target}\n\n"
            f"Synopsis\n{chapter.synopsis}\n\nNotes\n{chapter.notes}\n\n"
            "Draft recovery is written locally every second. Ctrl+S commits with a backup."
        )
        self.statusBar().showMessage("Recovered unsaved draft" if session.dirty else "Saved version")

    def text_changed(self):
        if self.active_session:
            self.active_session.text = self.editor.toPlainText()
            self.statusBar().showMessage("Unsaved draft" if self.active_session.dirty else "Saved version")

    def stash(self):
        if self.active_session:
            self.active_session.text = self.editor.toPlainText()
            self.active_session.stash()

    def save(self):
        if self.active_session:
            self.stash()
            self.active_session.save()
            self.error.hide()
            self.statusBar().showMessage("Saved with an automatic checkpoint")

    def reload_selected(self):
        if not self.active_session:
            return
        if self.active_session.dirty and QMessageBox.question(
            self, "Reload", "Discard this draft and reload the saved file?"
        ) != QMessageBox.StandardButton.Yes:
            return
        key = (self.active_session.chapter_id, self.active_session.scene_id)
        self.active_session.discard()
        self.active_session = None
        self.sessions.pop(key)
        self.select(self.binder.currentItem())

    def confirm_leave(self):
        self.stash()
        if self.worker and self.worker.isRunning():
            self.show_error("A proofreading check is still running. Wait for it before closing this project.")
            return False
        if not any(session.dirty for session in self.sessions.values()):
            return True
        choice = QMessageBox.question(
            self, "Unsaved writing", "Save all drafts before leaving this project?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Cancel:
            return False
        for session in self.sessions.values():
            if choice == QMessageBox.StandardButton.Save:
                session.save()
            else:
                session.discard()
        return True

    def closeEvent(self, event):
        if self._run(self.confirm_leave):
            event.accept()
        else:
            event.ignore()

    def new_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose an empty project folder")
        if not folder:
            return
        title, accepted = QInputDialog.getText(self, "New project", "Project title")
        if accepted and title.strip():
            root = init_project(Path(folder), title.strip())
            self.apply_saved_ai_default(root)
            self.open_project(root)

    def choose_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Open project folder")
        if folder:
            self.open_project(Path(folder))

    def new_chapter(self):
        if self.root is None:
            return
        title, accepted = QInputDialog.getText(self, "New chapter", "Chapter title")
        if accepted and title.strip():
            if not list((self.root / "manuscript").iterdir()):
                create_part(self.root, "Manuscript")
            create_chapter(self.root, title.strip())
            self.rebuild_binder()

    def new_scene(self):
        if not self.active_session:
            return
        self.save()
        title, accepted = QInputDialog.getText(self, "New scene", "Scene title")
        if accepted and title.strip():
            add_scene(self.root, self.active_session.chapter_id, title.strip())
            self.sessions = {key: session for key, session in self.sessions.items() if session.dirty}
            self.active_session = None
            self.rebuild_binder()

    def move_scene(self, direction):
        if not self.active_session or not self.active_session.scene_id:
            return
        self.save()
        chapter = next(c for c in list_chapters(self.root) if c.chapter_id == self.active_session.chapter_id)
        position = next(i + 1 for i, scene in enumerate(chapter.scenes) if scene.scene_id == self.active_session.scene_id)
        plan = plan_reorder_scene(self.root, chapter.chapter_id, self.active_session.scene_id, position + direction)
        if ReviewDialog("Review scene move", scene_operation_diff(self.root, plan), self).exec():
            apply_scene_operation(self.root, plan)
            self.sessions = {key: session for key, session in self.sessions.items() if session.dirty}
            self.active_session = None
            self.rebuild_binder()

    def proofread(self):
        if not self.active_session or (self.worker and self.worker.isRunning()):
            return
        settings = load_languagetool_settings(self.config)
        if proofreading_requires_data_transfer_consent(settings):
            raise ValueError("Desktop proofreading is local only. Use the CLI consent flow for hosted services.")
        self.worker = ProofreadingWorker(self.editor.toPlainText(), settings, self.active_session, self)
        self.worker.completed.connect(self.proofreading_complete)
        self.worker.failed.connect(self.show_error)
        self.statusBar().showMessage("Checking with local LanguageTool...")
        self.worker.start()

    def write_with_ai(self):
        if not self.active_session or (self.ai_worker and self.ai_worker.isRunning()):
            return
        settings = load_ai_settings(self.config)
        dialog = AIWritingDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        scope = dialog.scope_id()
        description = dialog.writing_description()
        if not description:
            raise ValueError("Describe what the AI should write.")
        if scope == "chapter" and self.active_session.scene_id is not None:
            raise ValueError("Select the chapter in the binder before generating a complete chapter draft.")
        text = self.editor.toPlainText()
        consent = not ai_requires_data_transfer_consent(settings)
        if not consent:
            definition = provider_definition(settings.provider)
            forwarding_disclosure = (
                " FreeLLMAPI will forward it to a hosted model provider."
                if definition.provider_id == "freellmapi"
                else ""
            )
            answer = QMessageBox.question(
                self,
                "Send manuscript context?",
                f"This sends {len(text):,} characters from the selected manuscript text plus your writing "
                f"description to {definition.label}, model {settings.model}.{forwarding_disclosure} "
                "Send it for this request?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            consent = True
        context_label = "chapter" if self.active_session.scene_id is None else "scene"
        self.ai_worker = AIWritingWorker(
            text,
            settings,
            context_label,
            scope,
            description,
            self.editor.textCursor().position(),
            self.active_session,
            consent,
            self,
        )
        self.ai_worker.completed.connect(
            lambda generated, scope, before, cursor_position, session: self._run(
                lambda: self.ai_writing_complete(generated, scope, before, cursor_position, session)
            )
        )
        self.ai_worker.failed.connect(self.show_error)
        self.statusBar().showMessage(f"Generating {scope} draft with {provider_definition(settings.provider).label}...")
        self.ai_worker.start()

    def ai_writing_complete(self, generated, scope, before, cursor_position, session):
        if session is not self.active_session or before != self.editor.toPlainText():
            self.statusBar().showMessage("Text changed while AI was writing. Generated text was not applied.")
            return
        generated = generated.strip()
        if not generated:
            raise ValueError("The AI provider returned an empty draft.")
        if ReviewDialog(f"Review AI {scope} draft", generated, self).exec() != QDialog.DialogCode.Accepted:
            self.statusBar().showMessage("AI draft discarded")
            return
        cursor = self.editor.textCursor()
        if scope == "chapter":
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.insertText(generated)
        else:
            cursor.setPosition(cursor_position)
            prefix = "" if cursor.atStart() else "\n\n"
            suffix = "" if cursor.atEnd() else "\n\n"
            cursor.insertText(prefix + generated + suffix)
        self.stash()
        self.statusBar().showMessage(f"AI {scope} draft added. Review it, then save when ready.")

    def proofreading_complete(self, result, text, session):
        if session is not self.active_session or text != self.editor.toPlainText():
            self.statusBar().showMessage("Text changed. Run proofreading again.")
            return
        self.checked_text = text
        self.finding_items = list(result.issues)
        self.pending_replacement = None
        self.findings.clear()
        self.findings.addItems([f"{issue.rule_id}: {issue.message}" for issue in result.issues])
        if result.issues:
            self.findings.setCurrentRow(0)
        self.statusBar().showMessage(f"{len(result.issues)} findings" + ("; results incomplete" if result.incomplete_results else ""))

    def select_finding(self, index):
        self.pending_replacement = None
        self.suggestions.clear()
        if 0 <= index < len(self.finding_items):
            issue = self.finding_items[index]
            self.suggestions.addItems(issue.replacements)
            if self.editor.toPlainText() == self.checked_text:
                cursor = self.editor.textCursor()
                start = len(self.checked_text[:issue.offset].encode("utf-16-le")) // 2
                end = len(self.checked_text[:issue.offset + issue.length].encode("utf-16-le")) // 2
                cursor.setPosition(start)
                cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
                self.editor.setTextCursor(cursor)

    def preview_suggestion(self):
        index = self.findings.currentRow()
        if index < 0 or not self.suggestions.count():
            return
        preview = preview_replacement(self.checked_text, self.finding_items[index], self.suggestions.currentText())
        preview.apply(self.editor.toPlainText())
        if ReviewDialog("Review replacement", preview.diff, self).exec():
            self.pending_replacement = preview
            self.statusBar().showMessage("Preview approved. Use Apply preview to change the draft.")

    def apply_suggestion(self):
        preview = self.pending_replacement
        if preview is None:
            return
        preview.apply(self.editor.toPlainText())
        cursor = self.editor.textCursor()
        cursor.setPosition(len(preview.before[:preview.offset].encode("utf-16-le")) // 2)
        cursor.setPosition(len(preview.before[:preview.offset + preview.length].encode("utf-16-le")) // 2,
                           QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(preview.replacement)
        self.pending_replacement = None
        self.findings.clear()
        self.finding_items = []
        self.stash()

    def ignore_finding(self):
        index = self.findings.currentRow()
        if index >= 0:
            self.finding_items.pop(index)
            self.findings.takeItem(index)
            self.pending_replacement = None

    def choose_export(self):
        if self.root is None:
            return
        self.save()
        format_name, accepted = QInputDialog.getItem(self, "Export", "Format", ["docx", "pdf", "epub"], editable=False)
        if accepted:
            output, _ = QFileDialog.getSaveFileName(self, "Export manuscript", str(self.root / "build" / f"manuscript.{format_name}"))
            if output:
                compile_project(self.root, format_name=format_name, output_path=Path(output))
                self.statusBar().showMessage(f"Exported {format_name.upper()}")

    def checkpoint(self):
        if self.root is not None:
            self.save()
            backup = create_snapshot(self.root, "Writer checkpoint")
            self.statusBar().showMessage(f"Checkpoint: {backup.name}")

    def choose_restore(self):
        if self.root is None or not self.confirm_leave():
            return
        records = list_snapshots(self.root)
        choices = [Path(record["path"]).name for record in records]
        selected, accepted = QInputDialog.getItem(self, "Restore checkpoint", "Checkpoint", choices, editable=False)
        if accepted and selected:
            preview = preview_snapshot_restore(self.root, selected)
            text = "\n".join([*("Add: " + p for p in preview.added), *("Modify: " + p for p in preview.modified),
                              *("Delete: " + p for p in preview.deleted)])
            if ReviewDialog("Review exact restore", text or "No changes", self).exec():
                restore_snapshot(self.root, selected)
                self.sessions = {}
                self.active_session = None
                self.rebuild_binder()

    def word_export(self):
        from openscribe.word import export_word

        if self.root is None:
            return
        self.save()
        output, _ = QFileDialog.getSaveFileName(self, "Word round-trip export", str(self.root / "build" / "roundtrip.docx"))
        if output:
            export_word(self.root, Path(output))
            self.statusBar().showMessage("Word round-trip document and local baseline created")

    def word_import(self):
        from openscribe.word import apply_word_import, preview_word_import

        if self.root is None or not self.confirm_leave():
            return
        source, _ = QFileDialog.getOpenFileName(self, "Preview Word document", str(self.root / "build"), "Word (*.docx)")
        if source:
            plan = preview_word_import(self.root, Path(source).read_bytes())
            if plan.blocked:
                raise ValueError("Word import is blocked by conflicts or tracked changes. Review with `openscribe word import`.")
            summary = "\n".join(f"{review.identity}: {review.status}" for review in plan.reviews)
            if ReviewDialog("Review Word import", summary + "\n\n" + plan.diff, self).exec():
                apply_word_import(self.root, plan)
                self.sessions = {}
                self.active_session = None
                self.rebuild_binder()


def launch(root: Path | None = None) -> None:
    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = AuthorWindow(root)
    window.show()
    app.exec()
