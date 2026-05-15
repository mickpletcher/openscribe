from __future__ import annotations

from pathlib import Path

from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Static, Tree

from openscribe.elements import get_element, list_element_records
from openscribe.index import index_is_current
from openscribe.project import (
    AuxiliaryDocument,
    ChapterDocument,
    find_chapters,
    find_story_idea,
    list_auxiliary_documents,
    list_chapters,
    list_story_ideas,
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
        self.auxiliary_lookup: dict[str, AuxiliaryDocument] = {}

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

        if isinstance(node_data, dict) and node_data.get("kind") == "element":
            record = get_element(self.root, str(node_data["element_id"]))
            preview.update(record.notes or "[Empty element notes]")
            metadata.update(self._element_summary(record))
            return

        if isinstance(node_data, dict) and node_data.get("kind") == "story-idea":
            idea = find_story_idea(self.root, str(node_data["idea_ref"]))
            preview.update(Syntax(idea.body.strip() or "[Empty story idea]", "markdown", word_wrap=True, line_numbers=False))
            metadata.update(self._story_idea_summary(idea))
            return

        if isinstance(node_data, dict) and node_data.get("kind") == "aux":
            document = self.auxiliary_lookup.get(str(node_data["path"]))
            if document is None:
                return
            preview.update(Syntax(document.body.strip() or "[Empty document]", "markdown", word_wrap=True, line_numbers=False))
            metadata.update(self._auxiliary_summary(document))
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
        root_node.label = "Project"
        manuscript_root = root_node.add("Manuscript", expand=True)
        parts: dict[str, object] = {}
        for chapter in self._visible_chapters():
            part_node = parts.get(chapter.part_id)
            if part_node is None:
                part_node = manuscript_root.add(
                    chapter.part,
                    expand=True,
                    data={"kind": "part", "part_id": chapter.part_id},
                )
                parts[chapter.part_id] = part_node
            part_node.add_leaf(chapter.title, data=chapter.path.as_posix())

        self.auxiliary_lookup = {}
        self._add_auxiliary_section(root_node, "Characters", "characters")
        self._add_auxiliary_section(root_node, "Research", "research")
        self._add_auxiliary_section(root_node, "Notes", "notes")
        self._add_story_ideas_section(root_node)
        self._add_elements_section(root_node)
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
                f"Template: {self.config.get('template', 'fiction')}",
                f"Chapters: {len(self.chapters)}",
                f"Scenes: {sum(chapter.scene_count for chapter in self.chapters)}",
                f"Words: {sum(chapter.word_count for chapter in self.chapters)}",
                "",
                "Compile",
                f"Format: {compile_config.get('default_format', 'docx')}",
                f"Template: {compile_config.get('default_template', 'novel')}",
                f"Title page: {compile_config.get('include_title_page', True)}",
                f"Part headings: {compile_config.get('include_part_headings', True)}",
                f"Chapter headings: {compile_config.get('chapter_heading_style', 'title-only')}",
                f"Index current: {index_is_current(self.root)}",
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
                f"Scenes: {chapter.scene_count}",
                "",
                "Synopsis",
                chapter.synopsis or "n/a",
                "",
                "Notes",
                chapter.notes or "n/a",
                "",
                "Scene Titles",
                ", ".join(scene.title for scene in chapter.scenes) or "n/a",
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

    @staticmethod
    def _auxiliary_summary(document: AuxiliaryDocument) -> str:
        return "\n".join(
            [
                f"Title: {document.title}",
                f"Category: {document.category}",
                f"Path: {document.path}",
            ]
        )

    @staticmethod
    def _story_idea_summary(idea) -> str:
        return "\n".join(
            [
                f"Title: {idea.title}",
                f"Status: {idea.status}",
                f"Genre: {idea.genre or 'n/a'}",
                f"Tone: {idea.tone or 'n/a'}",
                "",
                "Premise",
                idea.premise or "n/a",
            ]
        )

    @staticmethod
    def _element_summary(record) -> str:
        return "\n".join(
            [
                f"Name: {record.name}",
                f"Type: {record.type_name}",
                f"Aliases: {', '.join(record.aliases) or 'n/a'}",
                f"Tags: {', '.join(record.tags) or 'n/a'}",
                "",
                "Relations",
                ", ".join(f"{relation['type']}:{relation['target']}" for relation in record.relations) or "n/a",
            ]
        )

    def _search_summary(self) -> str:
        if not self.search_query:
            return f"Search is empty. Showing all chapters: {len(self.chapters)}"
        match_count = len(find_chapters(self.root, text=self.search_query))
        return f"Search: {self.search_query} | Matches: {match_count}"

    def _add_auxiliary_section(self, root_node: Tree, label: str, category: str) -> None:
        documents = list_auxiliary_documents(self.root, category)
        section = root_node.add(label, expand=False)
        for document in documents:
            path_key = document.path.as_posix()
            self.auxiliary_lookup[path_key] = document
            section.add_leaf(document.title, data={"kind": "aux", "path": path_key})

    def _add_story_ideas_section(self, root_node: Tree) -> None:
        ideas = list_story_ideas(self.root)
        section = root_node.add("Story Ideas", expand=False)
        for idea in ideas:
            section.add_leaf(idea.title, data={"kind": "story-idea", "idea_ref": idea.slug})

    def _add_elements_section(self, root_node: Tree) -> None:
        section = root_node.add("Elements", expand=False)
        for record in list_element_records(self.root):
            section.add_leaf(record.name, data={"kind": "element", "element_id": record.element_id})
