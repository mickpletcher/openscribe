from __future__ import annotations

import asyncio
from pathlib import Path

from textual.widgets import Input, Static, TextArea, Tree

from openscribe.board import add_note, list_notes
from openscribe.compile import CompileError
from openscribe.elements import add_element
from openscribe.project import (
    add_scene,
    create_chapter,
    create_part,
    create_source_note,
    create_story_idea,
    init_project,
    list_chapters,
    list_source_notes,
)
from openscribe.proofreading import ProofreadingIssue, ProofreadingResult
from openscribe.tui import OpenScribeApp


def test_tui_search_filters_visible_chapters(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    create_chapter(
        root,
        "Arrival",
        part="Opening",
        synopsis="Eli reaches town.",
        notes="Station callback.",
    )
    create_chapter(
        root,
        "Departure",
        part="Opening",
        synopsis="Nora leaves at dawn.",
    )

    arrival_path = root / "manuscript" / "part-01-opening" / "ch-01-arrival.md"
    arrival_path.write_text(
        arrival_path.read_text(encoding="utf-8") + "The station was almost empty.\n",
        encoding="utf-8",
    )

    app = OpenScribeApp(root)
    assert len(app._visible_chapters()) == 2

    app.search_query = "station"
    matches = app._visible_chapters()

    assert len(matches) == 1
    assert matches[0].title == "Arrival"
    assert "Chapters: 1" in app._search_summary()


def test_tui_chapter_summary_shows_first_class_metadata(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    create_chapter(
        root,
        "Arrival",
        part="Opening",
        status="revised",
        label="setup",
        synopsis="Eli reaches town.",
        pov="Eli",
        word_target=1800,
        notes="Tighten the station scene.",
    )

    chapter = OpenScribeApp(root).chapters[0]
    summary = OpenScribeApp._chapter_summary(root, chapter)

    assert "Status: revised" in summary
    assert "Label: setup" in summary
    assert "POV: Eli" in summary
    assert "Target: 1800" in summary
    assert "Synopsis" in summary
    assert "Eli reaches town." in summary
    assert "Notes" in summary
    assert "Tighten the station scene." in summary


def test_tui_project_sections_cover_library_content(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    create_chapter(root, "Arrival", part="Opening")
    create_story_idea(root, "The Flood Ledger")
    add_element(root, "character", "Eli Harper", notes="Primary point of view")

    character_path = root / "characters" / "eli-harper.md"
    character_path.write_text("# Eli Harper\n\nGuarded and observant.\n", encoding="utf-8")
    research_path = root / "research" / "setting-notes.md"
    research_path.write_text("# Setting Notes\n\nCounty roads and flood plains.\n", encoding="utf-8")
    note_path = root / "notes" / "revision-notes.md"
    note_path.write_text("# Revision Notes\n\nTighten the opening.\n", encoding="utf-8")

    app = OpenScribeApp(root)
    app.auxiliary_lookup = {}
    summary = app._project_summary()

    assert "Template: fiction" in summary
    assert "Index current: False" in summary

    class FakeSection:
        def add_leaf(self, *args, **kwargs) -> None:
            return None

    class FakeNode:
        def add(self, label: str, expand: bool = False) -> FakeSection:
            return FakeSection()

    app._add_auxiliary_section(FakeNode(), "Characters", "characters")
    assert any(document.title == "Eli Harper" for document in app.auxiliary_lookup.values())


def test_tui_board_canvas_summary_and_notes(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    add_note(root, "Station Secret", body="The station master is hiding records.", group="plot", x=10, y=4)

    app = OpenScribeApp(root)
    canvas_summary = app._board_canvas_summary()
    note_summary = app._board_note_summary(
        add_note(root, "Ledger Trail", body="Follow the ledger.", group="plot", x=18, y=8)
    )

    assert "Board Canvas" in canvas_summary
    assert "Notes: 1" in canvas_summary
    assert "Visible: 1" in canvas_summary
    assert "plot" in canvas_summary
    assert "ID: note-002" in note_summary
    assert "Position: (18, 8)" in note_summary


def test_tui_board_actions_and_source_links(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    create_chapter(root, "Arrival", part="Opening", notes="County Archive")
    create_source_note(root, "County Archive", author="Stewart County", year="1987")
    note = add_note(root, "Station Secret", body="Move me.", group="plot", x=10, y=4)

    app = OpenScribeApp(root)

    async def exercise() -> None:
        async with app.run_test():
            app.current_node_data = {"kind": "board-note", "note_id": note.note_id}
            app.action_move_board_note(3, 2)

    asyncio.run(exercise())

    moved_summary = app._board_note_summary(next(item for item in list_notes(root) if item.note_id == note.note_id))
    chapter_summary = app._chapter_summary(root, app.chapters[0])
    source_summary = app._source_summary(list_source_notes(root)[0])

    assert "Position: (13, 6)" in moved_summary
    assert "Sources: County Archive" in chapter_summary
    assert "Linked Chapters: 1" in source_summary


def test_tui_special_views_render_counts(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    create_chapter(root, "Arrival", part="Opening", synopsis="Eli reaches town.", word_target=1500)
    character_path = root / "characters" / "eli-harper.md"
    character_path.write_text("# Eli Harper\n\nGuarded.\n", encoding="utf-8")
    research_path = root / "research" / "archive.md"
    research_path.write_text("# Archive\n\nFlood record.\n", encoding="utf-8")

    app = OpenScribeApp(root)
    corkboard = app._corkboard_summary()
    pair_summary = app._paired_library_summary()
    project_summary = app._project_summary()

    assert "Cards: 1" in corkboard
    assert "Characters: 2" in pair_summary
    assert "Research: 2" in pair_summary
    assert "Draft target:" in project_summary


def test_tui_quick_actions_update_status_and_board_links(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    create_chapter(root, "Arrival", part="Opening", status="draft", label="default", word_target=1000)
    create_chapter(root, "Departure", part="Opening", pov="Nora")
    note = add_note(root, "Station Secret", body="Hidden record.", group="plot")

    app = OpenScribeApp(root)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            app.query_one("#binder-tree", Tree).focus()
            await pilot.pause()
            chapter_key = app.chapters[0].path.as_posix()
            app.current_node_data = chapter_key
            await pilot.press("s", "l", "o", "w", "shift+w")
            app.current_node_data = {"kind": "board-note", "note_id": note.note_id}
            await pilot.press("p")

    asyncio.run(exercise())

    updated_summary = app._chapter_summary(root, app.chapters[0])
    assert "Status: revised" in updated_summary
    assert "Label: setup" in updated_summary
    assert "POV: Nora" in updated_summary
    assert "Target: 1000" in updated_summary
    assert "Quick Actions" in updated_summary

    board_summary = app._board_note_summary(next(item for item in list_notes(root) if item.note_id == note.note_id))
    promoted_id = next(chapter.chapter_id for chapter in list_chapters(root) if chapter.title == "Station Secret")
    assert promoted_id in board_summary


def test_tui_search_runs_in_mounted_event_loop(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    create_chapter(root, "Arrival", part="Opening", synopsis="Station arrival")
    create_chapter(root, "Departure", part="Opening", synopsis="Dawn exit")
    app = OpenScribeApp(root)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            search = app.query_one("#search-box", Input)
            search.value = "arrival"
            await pilot.pause()
            assert [chapter.title for chapter in app._visible_chapters()] == ["Arrival"]
            assert "Chapters: 1" in app._search_summary()

    asyncio.run(exercise())


def test_tui_action_errors_are_visible(tmp_path: Path, monkeypatch) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    create_chapter(root, "Arrival", part="Opening")
    app = OpenScribeApp(root)

    def fail_compile(_root: Path) -> Path:
        raise CompileError("PDF engine unavailable")

    monkeypatch.setattr("openscribe.tui.compile_project", fail_compile)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            app.query_one("#binder-tree", Tree).focus()
            await pilot.pause()
            await pilot.press("c")
            await pilot.pause()
            assert app.last_error == "CompileError: PDF engine unavailable"

    asyncio.run(exercise())


def test_tui_edits_and_saves_chapter_and_scene_text(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    create_chapter(root, "Arrival", part="Opening")
    add_scene(root, "Arrival", "Station", "The platform was empty.")
    app = OpenScribeApp(root)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            chapter = app.chapters[0]
            chapter_key = chapter.path.as_posix()
            app._apply_selection(chapter_key)
            editor = app.query_one("#editor", TextArea)
            assert editor.display
            assert "openscribe-scene-id" not in editor.text
            editor.text = "## Station\n\nThe platform was crowded."
            editor.focus()
            await pilot.press("ctrl+s")

            updated_chapter = app.chapters[0]
            assert updated_chapter.scenes[0].scene_id == chapter.scenes[0].scene_id
            scene_data = {
                "kind": "scene",
                "chapter_id": updated_chapter.chapter_id,
                "scene_id": updated_chapter.scenes[0].scene_id,
            }
            app._apply_selection(scene_data)
            editor.text = "The platform fell silent."
            editor.focus()
            await pilot.press("ctrl+s")

    asyncio.run(exercise())

    chapter = list_chapters(root)[0]
    assert chapter.scenes[0].body == "The platform fell silent."
    assert f"openscribe-scene-id: {chapter.scenes[0].scene_id}" in chapter.body


def test_tui_displays_local_proofreading_findings(tmp_path: Path, monkeypatch) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    create_chapter(root, "Arrival", part="Opening")
    app = OpenScribeApp(root)
    app.config["proofreading"]["enabled"] = True

    def fake_check(text, settings):
        assert text == "This are wrong."
        return ProofreadingResult(
            issues=(
                ProofreadingIssue(
                    message="Use 'is' instead.",
                    short_message="Agreement",
                    offset=5,
                    length=3,
                    replacements=("is",),
                    rule_id="THIS_NNS",
                    category="Grammar",
                    issue_type="grammar",
                    context=text,
                ),
            ),
            language="en-US",
            software_version="test",
            incomplete_results=False,
        )

    monkeypatch.setattr("openscribe.tui.check_text", fake_check)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            app._apply_selection(app.chapters[0].path.as_posix())
            editor = app.query_one("#editor", TextArea)
            editor.text = "This are wrong."
            editor.focus()
            await pilot.press("ctrl+g")
            findings = str(app.query_one("#proofreading", Static).content)
            assert "THIS_NNS" in findings
            assert "Suggestions: is" in findings

    asyncio.run(exercise())


def test_tui_blocks_hosted_proofreading_with_visible_disclosure(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    create_chapter(root, "Arrival", part="Opening")
    app = OpenScribeApp(root)
    app.config["proofreading"].update({"enabled": True, "endpoint": "https://proofreading.example.test/v2/check"})

    async def exercise() -> None:
        async with app.run_test() as pilot:
            app._apply_selection(app.chapters[0].path.as_posix())
            editor = app.query_one("#editor", TextArea)
            editor.text = "Private manuscript text."
            editor.focus()
            await pilot.press("ctrl+g")
            findings = str(app.query_one("#proofreading", Static).content)
            assert "Hosted proofreading is blocked" in findings
            assert "--allow-data-transfer" in findings
            assert app.last_error.startswith("LanguageToolError:")

    asyncio.run(exercise())
