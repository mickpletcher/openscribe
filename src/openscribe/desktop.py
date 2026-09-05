from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
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
    scene_operation_diff,
)
from openscribe.proofreading import (
    check_text,
    load_languagetool_settings,
    preview_replacement,
    requires_data_transfer_consent,
)
from openscribe.snapshots import create_snapshot, list_snapshots, preview_snapshot_restore, restore_snapshot


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


class AuthorWindow(QMainWindow):
    def __init__(self, root: Path | None = None):
        super().__init__()
        self.root = None
        self.config = {}
        self.sessions = {}
        self.active_session = None
        self.worker = None
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
            self.open_project(init_project(Path(folder), title.strip()))

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
        if requires_data_transfer_consent(settings):
            raise ValueError("Desktop proofreading is local only. Use the CLI consent flow for hosted services.")
        self.worker = ProofreadingWorker(self.editor.toPlainText(), settings, self.active_session, self)
        self.worker.completed.connect(self.proofreading_complete)
        self.worker.failed.connect(self.show_error)
        self.statusBar().showMessage("Checking with local LanguageTool...")
        self.worker.start()

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
