from __future__ import annotations

from pathlib import Path

from openscribe.elements import add_element
from openscribe.project import create_chapter, create_part, create_story_idea, init_project
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
    assert "Matches: 1" in app._search_summary()


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
    summary = OpenScribeApp._chapter_summary(chapter)

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
