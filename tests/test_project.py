from __future__ import annotations

from pathlib import Path

from openscribe.index import rebuild_project_index
from openscribe.project import (
    add_scene,
    create_chapter,
    create_part,
    create_story_idea,
    init_project,
    init_project_from_template,
    list_auxiliary_documents,
    list_chapters,
    list_story_ideas,
)
from openscribe.snapshots import create_snapshot


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
    assert (root / "manuscript" / "part-01-opening" / "part.yaml").exists()
    chapter = chapters[0]
    assert chapter.part == "Opening"
    assert chapter.part_id == "part-01-opening"
    assert chapter.title == "Arrival"
    assert chapter.status == "draft"
    assert chapter.label == "scene"
    assert chapter.pov == "Eli"
    assert chapter.word_target == 1800
    assert chapter.synopsis == "Eli arrives in town."
    assert chapter.notes == "Tighten the second paragraph."
    assert chapter.word_count == 9


def test_create_story_idea_creates_structured_note(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")

    idea_path = create_story_idea(
        root,
        "The Flood Ledger",
        premise="A county clerk finds a ledger that predicts deaths.",
        genre="Southern Gothic",
        tone="Uneasy",
        status="seed",
        notes="Tie the flood history to the missing records plot.",
    )

    assert idea_path.exists()
    ideas = list_story_ideas(root)

    assert len(ideas) == 1
    assert ideas[0].title == "The Flood Ledger"
    assert ideas[0].premise == "A county clerk finds a ledger that predicts deaths."
    assert ideas[0].genre == "Southern Gothic"
    assert ideas[0].tone == "Uneasy"
    assert ideas[0].status == "seed"
    assert "missing records plot" in ideas[0].body


def test_template_init_applies_template_defaults(tmp_path: Path) -> None:
    root = init_project_from_template(tmp_path, "North County", template_name="technical")

    config_text = (root / ".openscribe" / "project.yaml").read_text(encoding="utf-8")
    assert "template: technical" in config_text
    assert "default_template: minimal" in config_text
    assert (root / "notes" / "implementation-notes.md").exists()


def test_scene_support_and_index_rebuild(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    create_chapter(root, "Arrival", part="Opening")
    add_scene(root, "Arrival", "Bus Stop", body="Eli arrives in town.")
    add_scene(root, "Arrival", "Porch Watchers", body="Three men stop talking.")
    create_story_idea(root, "The Flood Ledger")

    chapters = list_chapters(root)
    assert chapters[0].scene_count == 2
    assert chapters[0].scenes[0].title == "Bus Stop"

    index_path = rebuild_project_index(root)
    assert index_path.exists()
    index_text = index_path.read_text(encoding="utf-8")
    assert "scene_count: 2" in index_text
    assert "story_idea_count: 1" in index_text


def test_list_auxiliary_documents_reads_titles(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    document_path = root / "research" / "field-notes.md"
    document_path.write_text("# Field Notes\n\nTown square is too quiet.\n", encoding="utf-8")

    documents = list_auxiliary_documents(root, "research")
    titles = {document.title for document in documents}
    assert "Field Notes" in titles


def test_create_git_snapshot_writes_commit_metadata(tmp_path: Path, monkeypatch) -> None:
    root = init_project(tmp_path, "North County")

    class Result:
        def __init__(self, stdout: str, returncode: int = 0) -> None:
            self.stdout = stdout
            self.returncode = returncode

    calls: list[list[str]] = []

    def fake_run(command: list[str], cwd: Path, capture_output: bool, text: bool, check: bool):
        calls.append(command)
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return Result("abc123\n")
        return Result(" M manuscript/ch-01-arrival.md\n")

    monkeypatch.setattr("openscribe.snapshots.subprocess.run", fake_run)

    snapshot_dir = create_snapshot(root, "before-rewrite", mode="git")
    metadata = (snapshot_dir / "snapshot.yaml").read_text(encoding="utf-8")

    assert snapshot_dir.exists()
    assert "commit: abc123" in metadata
    assert "dirty: true" in metadata
    assert any(command[:3] == ["git", "rev-parse", "HEAD"] for command in calls)
