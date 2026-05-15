from __future__ import annotations

from pathlib import Path

from openscribe.project import create_chapter, create_part, init_project, list_chapters


def test_init_project_creates_expected_structure(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")

    assert root == tmp_path.resolve()
    assert (root / ".openscribe" / "project.yaml").exists()
    assert (root / ".openscribe" / "templates").is_dir()
    assert (root / "manuscript").is_dir()
    assert (root / "research").is_dir()
    assert (root / "characters").is_dir()
    assert (root / "notes").is_dir()


def test_create_chapter_parses_metadata_and_body(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")

    chapter_path = create_chapter(
        root,
        "Arrival",
        part="Opening",
        status="draft",
        label="scene",
        pov="Eli",
        word_target=1800,
        synopsis="Eli arrives in town.",
        notes="Tighten the second paragraph.",
    )
    chapter_path.write_text(
        chapter_path.read_text(encoding="utf-8")
        + "Eli stepped off the bus into wet summer heat.\n",
        encoding="utf-8",
    )

    chapters = list_chapters(root)

    assert len(chapters) == 1
    chapter = chapters[0]
    assert chapter.part == "part-01-opening"
    assert chapter.title == "Arrival"
    assert chapter.status == "draft"
    assert chapter.label == "scene"
    assert chapter.pov == "Eli"
    assert chapter.word_target == 1800
    assert chapter.synopsis == "Eli arrives in town."
    assert chapter.notes == "Tighten the second paragraph."
    assert chapter.word_count == 9
