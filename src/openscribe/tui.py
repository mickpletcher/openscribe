from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Static, Tree

from openscribe.board import auto_layout, list_notes, load_board, move_note_by_delta, promote_note_to_chapter, render_board, set_note_hidden
from openscribe.compile import compile_project
from openscribe.elements import get_element, list_element_records
from openscribe.index import index_is_current
from openscribe.project import (
    AuxiliaryDocument,
    ChapterDocument,
    SourceDocument,
    adjust_chapter_word_target,
    chapter_report,
    cycle_chapter_label,
    cycle_chapter_pov,
    find_chapters,
    find_story_idea,
    linked_sources_for_chapter,
    list_auxiliary_documents,
    list_chapters,
    list_source_notes,
    list_story_ideas,
    load_part_metadata,
    load_project_config,
    manuscript_goal_stats,
    source_link_map,
    update_chapter_metadata,
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
        width: 32%;
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
        width: 43%;
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

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+f", "focus_search", "Search"),
        ("ctrl+left", "move_board_note(-2,0)", "Board left"),
        ("ctrl+right", "move_board_note(2,0)", "Board right"),
        ("ctrl+up", "move_board_note(0,-1)", "Board up"),
        ("ctrl+down", "move_board_note(0,1)", "Board down"),
        ("v", "toggle_board_note_visibility", "Toggle board note"),
        ("b", "auto_layout_board", "Auto layout"),
        ("s", "cycle_chapter_status", "Cycle status"),
        ("l", "cycle_chapter_label", "Cycle label"),
        ("o", "cycle_chapter_pov", "Cycle POV"),
        ("w", "increase_chapter_target", "Increase target"),
        ("W", "decrease_chapter_target", "Decrease target"),
        ("p", "promote_selected_board_note", "Promote note"),
        ("c", "compile_project_quick", "Compile"),
    ]

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
        self.source_lookup: dict[str, SourceDocument] = {}
        self.current_node_data: Any = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="body"):
            with Vertical(id="binder"):
                yield Input(placeholder="Filter chapters, notes, sources, or elements", id="search-box")
                yield Static(self._search_summary(), id="search-status")
                yield Tree("Manuscript", id="binder-tree")
            yield Static("Select a node from the binder.", id="preview")
            yield Static(self._project_summary(), id="meta")
        yield Footer()

    def on_mount(self) -> None:
        self._rebuild_tree()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        self._apply_selection(event.node.data)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search-box":
            return
        self.search_query = event.value.strip()
        self.query_one("#search-status", Static).update(self._search_summary())
        self._rebuild_tree()

    def action_focus_search(self) -> None:
        self.query_one("#search-box", Input).focus()

    def action_move_board_note(self, dx: int, dy: int) -> None:
        if not isinstance(self.current_node_data, dict) or self.current_node_data.get("kind") != "board-note":
            return
        note = move_note_by_delta(self.root, str(self.current_node_data["note_id"]), dx, dy)
        try:
            self._rebuild_tree()
            self._apply_selection({"kind": "board-note", "note_id": note.note_id})
        except Exception:
            self.current_node_data = {"kind": "board-note", "note_id": note.note_id}

    def action_toggle_board_note_visibility(self) -> None:
        if not isinstance(self.current_node_data, dict) or self.current_node_data.get("kind") != "board-note":
            return
        note = next((item for item in list_notes(self.root) if item.note_id == str(self.current_node_data["note_id"])), None)
        if note is None:
            return
        updated = set_note_hidden(self.root, note.note_id, not note.hidden)
        try:
            self._rebuild_tree()
            self._apply_selection({"kind": "board-note", "note_id": updated.note_id})
        except Exception:
            self.current_node_data = {"kind": "board-note", "note_id": updated.note_id}

    def action_auto_layout_board(self) -> None:
        auto_layout(self.root)
        if isinstance(self.current_node_data, dict) and self.current_node_data.get("kind") in {"board-canvas", "board-note"}:
            try:
                self._rebuild_tree()
                self._apply_selection(self.current_node_data)
            except Exception:
                pass

    def action_cycle_chapter_status(self) -> None:
        if not isinstance(self.current_node_data, str) or self.current_node_data not in self.chapter_lookup:
            return
        chapter = self.chapter_lookup[self.current_node_data]
        status_order = ["draft", "revised", "done"]
        try:
            next_index = (status_order.index(chapter.status) + 1) % len(status_order)
        except ValueError:
            next_index = 0
        update_chapter_metadata(self.root, chapter.slug, status=status_order[next_index])
        self._refresh_chapter_selection(chapter.path.as_posix())

    def action_cycle_chapter_label(self) -> None:
        if not isinstance(self.current_node_data, str) or self.current_node_data not in self.chapter_lookup:
            return
        chapter = self.chapter_lookup[self.current_node_data]
        cycle_chapter_label(self.root, chapter.slug)
        self._refresh_chapter_selection(chapter.path.as_posix())

    def action_cycle_chapter_pov(self) -> None:
        if not isinstance(self.current_node_data, str) or self.current_node_data not in self.chapter_lookup:
            return
        chapter = self.chapter_lookup[self.current_node_data]
        cycle_chapter_pov(self.root, chapter.slug)
        self._refresh_chapter_selection(chapter.path.as_posix())

    def action_increase_chapter_target(self) -> None:
        self._adjust_selected_chapter_target(250)

    def action_decrease_chapter_target(self) -> None:
        self._adjust_selected_chapter_target(-250)

    def action_promote_selected_board_note(self) -> None:
        if not isinstance(self.current_node_data, dict) or self.current_node_data.get("kind") != "board-note":
            return
        chapter_path = promote_note_to_chapter(self.root, str(self.current_node_data["note_id"]))
        self.chapters = list_chapters(self.root)
        self.chapter_lookup = {item.path.as_posix(): item for item in self.chapters}
        try:
            self._rebuild_tree()
            self._apply_selection(chapter_path.as_posix())
        except Exception:
            self.current_node_data = chapter_path.as_posix()

    def action_compile_project_quick(self) -> None:
        output_path = compile_project(self.root)
        preview = self.query_one("#preview", Static)
        metadata = self.query_one("#meta", Static)
        preview.update(f"Compiled manuscript to {output_path}")
        metadata.update(self._project_summary())

    def _adjust_selected_chapter_target(self, delta: int) -> None:
        if not isinstance(self.current_node_data, str) or self.current_node_data not in self.chapter_lookup:
            return
        chapter = self.chapter_lookup[self.current_node_data]
        adjust_chapter_word_target(self.root, chapter.slug, delta)
        self._refresh_chapter_selection(chapter.path.as_posix())

    def _refresh_chapter_selection(self, chapter_key: str) -> None:
        self.chapters = list_chapters(self.root)
        self.chapter_lookup = {item.path.as_posix(): item for item in self.chapters}
        try:
            self._rebuild_tree()
            self._apply_selection(chapter_key)
        except Exception:
            self.current_node_data = chapter_key

    def _apply_selection(self, node_data: Any) -> None:
        self.current_node_data = node_data
        if not node_data:
            return

        preview = self.query_one("#preview", Static)
        metadata = self.query_one("#meta", Static)

        if isinstance(node_data, dict) and node_data.get("kind") == "part":
            preview.update("Select a chapter in this part to preview its text.")
            metadata.update(self._part_summary(load_part_metadata(self.root, node_data["part_id"])))
            return

        if isinstance(node_data, dict) and node_data.get("kind") == "element":
            record = get_element(self.root, str(node_data["element_id"]))
            preview.update(record.notes or "[Empty element notes]")
            metadata.update(self._element_summary(record))
            return

        if isinstance(node_data, dict) and node_data.get("kind") == "board-canvas":
            preview.update(Syntax(render_board(self.root, width=72, height=18), "text", word_wrap=False, line_numbers=False))
            metadata.update(self._board_canvas_summary())
            return

        if isinstance(node_data, dict) and node_data.get("kind") == "board-note":
            note = next((item for item in list_notes(self.root) if item.note_id == str(node_data["note_id"])), None)
            if note is None:
                return
            preview.update(Syntax(note.body.strip() or "[Empty board note]", "markdown", word_wrap=True, line_numbers=False))
            metadata.update(self._board_note_summary(note))
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

        if isinstance(node_data, dict) and node_data.get("kind") == "source":
            source = self.source_lookup.get(str(node_data["path"]))
            if source is None:
                return
            preview.update(Syntax(source.body.strip() or "[Empty source note]", "markdown", word_wrap=True, line_numbers=False))
            metadata.update(self._source_summary(source))
            return

        if isinstance(node_data, dict) and node_data.get("kind") == "corkboard":
            preview.update(Syntax(self._corkboard_preview(), "markdown", word_wrap=True, line_numbers=False))
            metadata.update(self._corkboard_summary())
            return

        if isinstance(node_data, dict) and node_data.get("kind") == "library-pair":
            preview.update(Syntax(self._paired_library_preview(), "markdown", word_wrap=True, line_numbers=False))
            metadata.update(self._paired_library_summary())
            return

        if node_data not in self.chapter_lookup:
            return
        chapter = self.chapter_lookup[node_data]
        preview.update(Syntax(chapter.body.strip() or "[Empty chapter]", "markdown", word_wrap=True, line_numbers=False))
        metadata.update(self._chapter_summary(self.root, chapter))

    def _rebuild_tree(self) -> None:
        binder = self.query_one("#binder-tree", Tree)
        binder.clear()
        root_node = binder.root
        root_node.label = "Project"
        self.auxiliary_lookup = {}
        self.source_lookup = {}

        manuscript_root = root_node.add("Manuscript", expand=True)
        parts: dict[str, Any] = {}
        for chapter in self._visible_chapters():
            part_node = parts.get(chapter.part_id)
            if part_node is None:
                part_node = manuscript_root.add(chapter.part, expand=True, data={"kind": "part", "part_id": chapter.part_id})
                parts[chapter.part_id] = part_node
            chapter_node = part_node.add(chapter.title, data=chapter.path.as_posix())
            linked_sources = linked_sources_for_chapter(self.root, chapter)
            if linked_sources:
                source_branch = chapter_node.add("Sources", expand=False)
                for source in linked_sources:
                    source_branch.add_leaf(source.title, data={"kind": "source", "path": source.path.as_posix()})
            linked_notes = [note for note in list_notes(self.root) if chapter.slug in note.chapter_links]
            if linked_notes:
                note_branch = chapter_node.add("Board Notes", expand=False)
                for note in linked_notes:
                    note_branch.add_leaf(note.title, data={"kind": "board-note", "note_id": note.note_id})

        self._add_views_section(root_node)
        self._add_auxiliary_section(root_node, "Characters", "characters")
        self._add_auxiliary_section(root_node, "Research", "research")
        self._add_auxiliary_section(root_node, "Notes", "notes")
        self._add_story_ideas_section(root_node)
        self._add_source_links_section(root_node)
        self._add_board_section(root_node)
        self._add_elements_section(root_node)
        root_node.expand()

    def _visible_chapters(self) -> list[ChapterDocument]:
        if not self.search_query:
            return self.chapters
        return find_chapters(self.root, text=self.search_query)

    def _project_summary(self) -> str:
        compile_config = self.config.get("compile", {})
        goal_stats = manuscript_goal_stats(self.chapters, self.config.get("goals", {}))
        research_compile = compile_config.get("research", {})
        return "\n".join(
            [
                f"Title: {self.config.get('title', 'Untitled Project')}",
                f"Template: {self.config.get('template', 'fiction')}",
                f"Chapters: {len(self.chapters)}",
                f"Scenes: {sum(chapter.scene_count for chapter in self.chapters)}",
                f"Words: {sum(chapter.word_count for chapter in self.chapters)}",
                "",
                "Goals",
                f"Draft target: {goal_stats['draft_word_target']}",
                f"Chapter targets: {goal_stats['chapter_word_target_total']}",
                f"Session target: {goal_stats['session_word_target']}",
                f"Deadline: {goal_stats['deadline'] or 'n/a'}",
                f"Progress: {goal_stats['progress_percent']}%",
                "",
                "Compile",
                f"Format: {compile_config.get('default_format', 'docx')}",
                f"Template: {compile_config.get('default_template', 'novel')}",
                f"Profile: {compile_config.get('default_profile', '') or 'none'}",
                f"Title page: {compile_config.get('include_title_page', True)}",
                f"Part headings: {compile_config.get('include_part_headings', True)}",
                f"Chapter headings: {compile_config.get('chapter_heading_style', 'title-only')}",
                f"Citation style: {research_compile.get('citation_style', 'APA')}",
                f"Bibliography: {research_compile.get('include_bibliography', False)}",
                f"Index current: {index_is_current(self.root)}",
                "",
                "Keys",
                "q  Quit",
                "Ctrl+F  Focus search",
                "Ctrl+Arrows  Move board note",
                "v  Toggle board note",
                "b  Auto layout board",
                "s  Cycle chapter status",
                "l  Cycle chapter label",
                "o  Cycle chapter POV",
                "w  Increase target by 250",
                "W  Decrease target by 250",
                "p  Promote selected board note",
                "c  Compile project",
            ]
        )

    @staticmethod
    def _chapter_summary(root: Path, chapter: ChapterDocument) -> str:
        linked_sources = linked_sources_for_chapter(root, chapter)
        linked_notes = [note.title for note in list_notes(root) if chapter.slug in note.chapter_links]
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
                f"Sources: {', '.join(source.title for source in linked_sources) or 'n/a'}",
                f"Board Notes: {', '.join(linked_notes) or 'n/a'}",
                "",
                "Synopsis",
                chapter.synopsis or "n/a",
                "",
                "Notes",
                chapter.notes or "n/a",
                "",
                "Scene Titles",
                ", ".join(scene.title for scene in chapter.scenes) or "n/a",
                "",
                "Quick Actions",
                "s status  l label  o POV  w target+250  W target-250",
            ]
        )

    @staticmethod
    def _part_summary(metadata: dict[str, Any]) -> str:
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

    def _board_canvas_summary(self) -> str:
        notes = list_notes(self.root)
        groups = sorted({note.group for note in notes if note.group})
        visible_count = len([note for note in notes if not note.hidden])
        hidden_count = len(notes) - visible_count
        link_count = sum(len(note.links) for note in notes)
        return "\n".join(
            [
                "Board Canvas",
                f"Notes: {len(notes)}",
                f"Visible: {visible_count}",
                f"Hidden: {hidden_count}",
                f"Groups: {', '.join(groups) or 'n/a'}",
                f"Links: {link_count}",
                "",
                "Use Ctrl+Arrows to move the selected board note.",
            ]
        )

    @staticmethod
    def _board_note_summary(note) -> str:
        return "\n".join(
            [
                f"ID: {note.note_id}",
                f"Title: {note.title}",
                f"Group: {note.group or 'n/a'}",
                f"Links: {', '.join(note.links) or 'n/a'}",
                f"Chapters: {', '.join(note.chapter_links) or 'n/a'}",
                f"Position: ({note.x}, {note.y})",
                f"Hidden: {note.hidden}",
            ]
        )

    def _source_summary(self, source: SourceDocument) -> str:
        linked_map = source_link_map(self.root)
        linked = linked_map.get(source.slug, [])
        return "\n".join(
            [
                f"Title: {source.title}",
                f"Type: {source.source_type}",
                f"Author: {source.author or 'n/a'}",
                f"Year: {source.year or 'n/a'}",
                f"URL: {source.url or 'n/a'}",
                f"Linked Chapters: {len(linked)}",
                "",
                "Chapters",
                ", ".join(chapter.title for chapter in linked) or "n/a",
            ]
        )

    def _corkboard_preview(self) -> str:
        cards = []
        for chapter in self._visible_chapters():
            cards.append(
                "\n".join(
                    [
                        f"# {chapter.title}",
                        f"Part: {chapter.part}",
                        f"Status: {chapter.status}",
                        f"POV: {chapter.pov or 'n/a'}",
                        f"Synopsis: {chapter.synopsis or 'n/a'}",
                    ]
                )
            )
        return "\n\n".join(cards) or "[No visible chapters]"

    def _corkboard_summary(self) -> str:
        chapters = self._visible_chapters()
        return "\n".join(
            [
                "Corkboard",
                f"Cards: {len(chapters)}",
                f"Words: {sum(chapter.word_count for chapter in chapters)}",
                f"Scenes: {sum(chapter.scene_count for chapter in chapters)}",
            ]
        )

    def _paired_library_preview(self) -> str:
        characters = list_auxiliary_documents(self.root, "characters")
        research = list_auxiliary_documents(self.root, "research")
        left = ["# Characters", *[document.title for document in characters]] or ["# Characters", "n/a"]
        right = ["# Research", *[document.title for document in research]] or ["# Research", "n/a"]
        return "\n".join(left) + "\n\n" + "\n".join(right)

    def _paired_library_summary(self) -> str:
        characters = list_auxiliary_documents(self.root, "characters")
        research = list_auxiliary_documents(self.root, "research")
        return "\n".join(
            [
                "Library Pair",
                f"Characters: {len(characters)}",
                f"Research: {len(research)}",
                "",
                "Use this view to cross check profiles and support material.",
            ]
        )

    def _search_summary(self) -> str:
        if not self.search_query:
            return f"Filter is empty. Showing all chapters: {len(self.chapters)}"
        source_matches = len([source for source in list_source_notes(self.root) if self.search_query.lower() in f'{source.title} {source.author} {source.body}'.lower()])
        note_matches = len([note for note in list_notes(self.root) if self.search_query.lower() in f'{note.title} {note.body} {note.group}'.lower()])
        chapter_matches = len(find_chapters(self.root, text=self.search_query))
        return f"Filter: {self.search_query} | Chapters: {chapter_matches} | Sources: {source_matches} | Board: {note_matches}"

    def _add_auxiliary_section(self, root_node: Tree, label: str, category: str) -> None:
        documents = list_auxiliary_documents(self.root, category)
        section = root_node.add(label, expand=False)
        for document in documents:
            if self.search_query and self.search_query.lower() not in f"{document.title} {document.body}".lower():
                continue
            path_key = document.path.as_posix()
            self.auxiliary_lookup[path_key] = document
            section.add_leaf(document.title, data={"kind": "aux", "path": path_key})

    def _add_story_ideas_section(self, root_node: Tree) -> None:
        ideas = list_story_ideas(self.root)
        section = root_node.add("Story Ideas", expand=False)
        for idea in ideas:
            if self.search_query and self.search_query.lower() not in f"{idea.title} {idea.premise} {idea.body}".lower():
                continue
            section.add_leaf(idea.title, data={"kind": "story-idea", "idea_ref": idea.slug})

    def _add_source_links_section(self, root_node: Tree) -> None:
        section = root_node.add("Source Links", expand=False)
        link_map = source_link_map(self.root)
        for source in list_source_notes(self.root):
            if self.search_query and self.search_query.lower() not in f"{source.title} {source.author} {source.body}".lower():
                continue
            path_key = source.path.as_posix()
            self.source_lookup[path_key] = source
            source_node = section.add(source.title, expand=False, data={"kind": "source", "path": path_key})
            for chapter in link_map.get(source.slug, []):
                source_node.add_leaf(chapter.title, data=chapter.path.as_posix())

    def _add_board_section(self, root_node: Tree) -> None:
        board = load_board(self.root)
        section = root_node.add("Board", expand=False)
        section.add_leaf("Canvas", data={"kind": "board-canvas"})
        for item in board.get("notes", []):
            haystack = f"{item.get('title', '')} {item.get('body', '')} {item.get('group', '')}".lower()
            if self.search_query and self.search_query.lower() not in haystack:
                continue
            hidden_marker = " [hidden]" if item.get("hidden", False) else ""
            section.add_leaf(
                str(item.get("title", "")) + hidden_marker,
                data={"kind": "board-note", "note_id": str(item.get("id", ""))},
            )

    def _add_elements_section(self, root_node: Tree) -> None:
        section = root_node.add("Elements", expand=False)
        for record in list_element_records(self.root):
            haystack = f"{record.name} {' '.join(record.aliases)} {' '.join(record.tags)} {record.notes}".lower()
            if self.search_query and self.search_query.lower() not in haystack:
                continue
            section.add_leaf(record.name, data={"kind": "element", "element_id": record.element_id})

    def _add_views_section(self, root_node: Tree) -> None:
        section = root_node.add("Views", expand=False)
        section.add_leaf("Corkboard", data={"kind": "corkboard"})
        section.add_leaf("Characters + Research", data={"kind": "library-pair"})
