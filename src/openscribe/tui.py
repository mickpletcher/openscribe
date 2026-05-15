from __future__ import annotations

from pathlib import Path

from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Static, Tree

from openscribe.project import (
    ChapterDocument,
    find_chapters,
    list_chapters,
    load_part_metadata,
    load_project_config,
)


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

    #search-box {
        height: auto;
        padding: 0 1;
        border-bottom: solid #666666;
    }

    #search-status {
        padding: 0 1 1 1;
        color: #aaaaaa;
    }

    #binder-tree {
        height: 1fr;
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

    BINDINGS = [("q", "quit", "Quit"), ("ctrl+f", "focus_search", "Search")]

    def __init__(self, root: Path) -> None:
        super().__init__()
        self.root = root
        self.config = load_project_config(root)
        self.chapters = list_chapters(root)
        self.search_query = ""
        self.chapter_lookup: dict[str, ChapterDocument] = {
            chapter.path.as_posix(): chapter for chapter in self.chapters
        }

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="body"):
            with Vertical(id="binder"):
                yield Input(placeholder="Search title, synopsis, notes, or body text", id="search-box")
                yield Static(self._search_summary(), id="search-status")
                yield Tree("Manuscript", id="binder-tree")
            yield Static("Select a chapter from the binder.", id="preview")
            yield Static(self._project_summary(), id="meta")
        yield Footer()

    def on_mount(self) -> None:
        self._rebuild_tree()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        node_data = event.node.data
        if not node_data:
            return

        preview = self.query_one("#preview", Static)
        metadata = self.query_one("#meta", Static)
        if isinstance(node_data, dict) and node_data.get("kind") == "part":
            preview.update("Select a chapter in this part to preview its text.")
            part_metadata = load_part_metadata(self.root, node_data["part_id"])
            metadata.update(self._part_summary(part_metadata))
            return

        if node_data not in self.chapter_lookup:
            return
        chapter = self.chapter_lookup[node_data]
        body = chapter.body.strip() or "[Empty chapter]"
        preview.update(Syntax(body, "markdown", word_wrap=True, line_numbers=False))
        metadata.update(self._chapter_summary(chapter))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search-box":
            return
        self.search_query = event.value.strip()
        self.query_one("#search-status", Static).update(self._search_summary())
        self._rebuild_tree()

    def action_focus_search(self) -> None:
        self.query_one("#search-box", Input).focus()

    def _rebuild_tree(self) -> None:
        binder = self.query_one("#binder-tree", Tree)
        binder.clear()
        root_node = binder.root
        root_node.label = "Manuscript"
        parts: dict[str, object] = {}
        for chapter in self._visible_chapters():
            part_node = parts.get(chapter.part_id)
            if part_node is None:
                part_node = root_node.add(
                    chapter.part,
                    expand=True,
                    data={"kind": "part", "part_id": chapter.part_id},
                )
                parts[chapter.part_id] = part_node
            part_node.add_leaf(chapter.title, data=chapter.path.as_posix())
        root_node.expand()

    def _visible_chapters(self) -> list[ChapterDocument]:
        if not self.search_query:
            return self.chapters
        return find_chapters(self.root, text=self.search_query)

    def _project_summary(self) -> str:
        compile_config = self.config.get("compile", {})
        return "\n".join(
            [
                f"Title: {self.config.get('title', 'Untitled Project')}",
                f"Chapters: {len(self.chapters)}",
                f"Words: {sum(chapter.word_count for chapter in self.chapters)}",
                "",
                "Compile",
                f"Format: {compile_config.get('default_format', 'docx')}",
                f"Template: {compile_config.get('default_template', 'novel')}",
                f"Title page: {compile_config.get('include_title_page', True)}",
                f"Part headings: {compile_config.get('include_part_headings', True)}",
                f"Chapter headings: {compile_config.get('chapter_heading_style', 'title-only')}",
                "",
                "Keys",
                "q  Quit",
                "Ctrl+F  Focus search",
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

    @staticmethod
    def _part_summary(metadata: dict) -> str:
        return "\n".join(
            [
                f"Title: {metadata.get('title', 'n/a')}",
                f"Part ID: {metadata.get('part_id', 'n/a')}",
                f"Path: {metadata.get('path', 'n/a')}",
            ]
        )

    def _search_summary(self) -> str:
        if not self.search_query:
            return f"Search is empty. Showing all chapters: {len(self.chapters)}"
        match_count = len(find_chapters(self.root, text=self.search_query))
        return f"Search: {self.search_query} | Matches: {match_count}"
