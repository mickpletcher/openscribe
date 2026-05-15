from __future__ import annotations

from pathlib import Path

from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Static, Tree

from openscribe.project import ChapterDocument, list_chapters, load_project_config


class OpenScribeApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
    }

    #body {
        height: 1fr;
    }

    #binder {
        width: 34%;
        border: solid #666666;
    }

    #preview {
        width: 41%;
        border: solid #666666;
        padding: 1 2;
        overflow: auto;
    }

    #meta {
        width: 25%;
        border: solid #666666;
        padding: 1 2;
        overflow: auto;
    }
    """

    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, root: Path) -> None:
        super().__init__()
        self.root = root
        self.config = load_project_config(root)
        self.chapters = list_chapters(root)
        self.chapter_lookup: dict[str, ChapterDocument] = {
            chapter.path.as_posix(): chapter for chapter in self.chapters
        }

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="body"):
            yield Tree("Manuscript", id="binder")
            yield Static("Select a chapter from the binder.", id="preview")
            yield Static(self._project_summary(), id="meta")
        yield Footer()

    def on_mount(self) -> None:
        binder = self.query_one("#binder", Tree)
        root_node = binder.root
        parts: dict[str, object] = {}
        for chapter in self.chapters:
            part_node = parts.get(chapter.part_id)
            if part_node is None:
                part_node = root_node.add(chapter.part, expand=True)
                parts[chapter.part_id] = part_node
            part_node.add_leaf(chapter.title, data=chapter.path.as_posix())
        root_node.expand()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        node_data = event.node.data
        if not node_data or node_data not in self.chapter_lookup:
            return
        chapter = self.chapter_lookup[node_data]
        preview = self.query_one("#preview", Static)
        metadata = self.query_one("#meta", Static)
        body = chapter.body.strip() or "[Empty chapter]"
        preview.update(Syntax(body, "markdown", word_wrap=True, line_numbers=False))
        metadata.update(self._chapter_summary(chapter))

    def _project_summary(self) -> str:
        return "\n".join(
            [
                f"Title: {self.config.get('title', 'Untitled Project')}",
                f"Chapters: {len(self.chapters)}",
                f"Words: {sum(chapter.word_count for chapter in self.chapters)}",
                "",
                "Keys",
                "q  Quit",
            ]
        )

    @staticmethod
    def _chapter_summary(chapter: ChapterDocument) -> str:
        return "\n".join(
            [
                f"Title: {chapter.title}",
                f"Part: {chapter.part}",
                f"Status: {chapter.status}",
                f"Label: {chapter.label}",
                f"POV: {chapter.pov or 'n/a'}",
                f"Words: {chapter.word_count}",
                f"Target: {chapter.word_target or 0}",
                "",
                "Synopsis",
                chapter.synopsis or "n/a",
                "",
                "Notes",
                chapter.notes or "n/a",
            ]
        )
