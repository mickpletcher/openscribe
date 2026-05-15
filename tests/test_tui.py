from __future__ import annotations

from pathlib import Path

from openscribe.project import create_chapter, create_part, init_project
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
