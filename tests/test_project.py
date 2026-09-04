from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from openscribe.board import add_chapter_link, add_note, list_notes, render_board
from openscribe.index import index_is_current, rebuild_project_index
from openscribe.project import (
    add_scene,
    add_screenplay_scene,
    create_chapter,
    create_nonfiction_section,
    create_part,
    create_story_idea,
    import_folder_project,
    init_project,
    init_project_from_template,
    list_auxiliary_documents,
    list_chapters,
    list_story_ideas,
    parse_frontmatter,
    reorder_chapter,
    save_project_template,
    update_chapter_metadata,
)
from openscribe.schema import SchemaValidationError
from openscribe.snapshots import (
    create_snapshot,
    diff_snapshot,
    list_snapshots,
    preview_snapshot_restore,
    restore_snapshot,
)


def test_init_project_creates_expected_structure(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")

    assert root == tmp_path.resolve()
    assert (root / ".openscribe" / "project.yaml").exists()
    assert (root / ".openscribe" / "templates").is_dir()
    assert (root / "manuscript").is_dir()
    assert (root / "research").is_dir()
    assert (root / "characters").is_dir()
    assert (root / "notes").is_dir()
    config = yaml.safe_load((root / ".openscribe" / "project.yaml").read_text(encoding="utf-8"))
    assert config["proofreading"] == {
        "enabled": False,
        "endpoint": "http://127.0.0.1:8081/v2/check",
        "language": "en-US",
        "timeout_seconds": 30,
    }


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
        chapter_path.read_text(encoding="utf-8") + "Eli stepped off the bus into wet summer heat.\n",
        encoding="utf-8",
    )

    chapters = list_chapters(root)

    assert len(chapters) == 1
    assert (root / "manuscript" / "part-01-opening" / "part.yaml").exists()
    chapter = chapters[0]
    assert chapter.part == "Opening"
    assert chapter.part_id == "part-01-opening"
    assert chapter.chapter_id.startswith("chapter-")
    assert chapter.title == "Arrival"
    assert chapter.status == "draft"
    assert chapter.label == "scene"
    assert chapter.pov == "Eli"
    assert chapter.word_target == 1800
    assert chapter.synopsis == "Eli arrives in town."
    assert chapter.notes == "Tighten the second paragraph."
    assert chapter.word_count == 9


def test_chapter_metadata_updates_preserve_unknown_fields_and_id(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    chapter_path = create_chapter(root, "Arrival", part="Opening")
    metadata, body = parse_frontmatter(chapter_path.read_text(encoding="utf-8"))
    chapter_id = metadata["chapter_id"]
    metadata["custom_field"] = {"owner": "writer", "locked": True}
    chapter_path.write_text(
        f"---\n{yaml.safe_dump(metadata, sort_keys=False).strip()}\n---\n\n{body}",
        encoding="utf-8",
    )

    update_chapter_metadata(root, "Arrival", status="revised")

    updated, _ = parse_frontmatter(chapter_path.read_text(encoding="utf-8"))
    assert updated["chapter_id"] == chapter_id
    assert updated["custom_field"] == {"owner": "writer", "locked": True}


def test_board_chapter_links_migrate_to_stable_ids_and_survive_reorder(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    create_chapter(root, "Arrival", part="Opening")
    second_path = create_chapter(root, "Departure", part="Opening")
    chapter_id = next(chapter.chapter_id for chapter in list_chapters(root) if chapter.title == "Departure")
    note = add_note(root, "Ending")

    board_path = root / ".openscribe" / "boards" / "default.yaml"
    board = yaml.safe_load(board_path.read_text(encoding="utf-8"))
    board["notes"][0]["chapter_links"] = [second_path.stem]
    board_path.write_text(yaml.safe_dump(board, sort_keys=False), encoding="utf-8")

    assert list_notes(root)[0].chapter_links == [chapter_id]
    reorder_chapter(root, "Departure", 1)
    reordered = next(chapter for chapter in list_chapters(root) if chapter.title == "Departure")
    assert reordered.chapter_id == chapter_id
    assert list_notes(root)[0].chapter_links == [chapter_id]

    add_chapter_link(root, note.note_id, chapter_id)
    assert list_notes(root)[0].chapter_links == [chapter_id]


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


def test_template_paths_cannot_escape_project(tmp_path: Path) -> None:
    template_path = tmp_path / "unsafe-template.yaml"
    template_path.write_text(
        yaml.safe_dump(
            {
                "name": "unsafe",
                "compile": {},
                "files": {"../escaped.txt": "outside project"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(SchemaValidationError, match="Unsafe template path"):
        init_project_from_template(tmp_path / "target", "Unsafe", template_file=template_path)

    assert not (tmp_path / "target").exists()
    assert not (tmp_path / "escaped.txt").exists()


def test_invalid_chapter_schema_has_a_clear_error(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    chapter_path = create_chapter(root, "Arrival", part="Opening")
    metadata, body = parse_frontmatter(chapter_path.read_text(encoding="utf-8"))
    metadata["word_target"] = "many"
    chapter_path.write_text(
        f"---\n{yaml.safe_dump(metadata, sort_keys=False).strip()}\n---\n\n{body}",
        encoding="utf-8",
    )

    with pytest.raises(SchemaValidationError, match="word_target must be an integer"):
        list_chapters(root)


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


def test_index_manifest_detects_changes_additions_and_deletions(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    first_path = create_chapter(root, "Arrival", part="Opening")
    rebuild_project_index(root)
    assert index_is_current(root)

    first_path.write_text(first_path.read_text(encoding="utf-8") + "Changed.\n", encoding="utf-8")
    assert not index_is_current(root)

    rebuild_project_index(root)
    second_path = create_chapter(root, "Departure", part="Opening")
    assert not index_is_current(root)

    rebuild_project_index(root)
    second_path.unlink()
    assert not index_is_current(root)


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


def test_checkpoint_snapshot_diff_and_restore(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    chapter_path = create_chapter(root, "Arrival", part="Opening")
    chapter_path.write_text(chapter_path.read_text(encoding="utf-8") + "Original text.\n", encoding="utf-8")
    template_path = root / ".openscribe" / "templates" / "custom.yaml"
    template_path.write_text("name: original\n", encoding="utf-8")

    snapshot_dir = create_snapshot(root, "before-change")

    chapter_path.write_text(chapter_path.read_text(encoding="utf-8") + "Changed text.\n", encoding="utf-8")
    added_path = create_chapter(root, "Added Later", part="Opening")
    template_path.write_text("name: changed\n", encoding="utf-8")
    diff_text = diff_snapshot(root, snapshot_dir.name)
    assert "Changed text." in diff_text

    preview = preview_snapshot_restore(root, snapshot_dir.name)
    assert str(added_path.relative_to(root)).replace("\\", "/") in preview.deleted
    assert str(template_path.relative_to(root)).replace("\\", "/") in preview.modified

    result = restore_snapshot(root, snapshot_dir.name)
    restored_text = chapter_path.read_text(encoding="utf-8")
    assert "Original text." in restored_text
    assert "Changed text." not in restored_text
    assert not added_path.exists()
    assert template_path.read_text(encoding="utf-8") == "name: original\n"
    assert result.backup_path.exists()


def test_snapshot_restore_rolls_back_when_staged_replacement_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    chapter_path = create_chapter(root, "Arrival", part="Opening")
    chapter_path.write_text(
        chapter_path.read_text(encoding="utf-8") + "Snapshot text.\n",
        encoding="utf-8",
    )
    snapshot_dir = create_snapshot(root, "before-change")
    chapter_path.write_text(
        chapter_path.read_text(encoding="utf-8") + "Current text.\n",
        encoding="utf-8",
    )

    original_replace = Path.replace
    failed = False

    def fail_first_manuscript_install(path: Path, target: Path) -> Path:
        nonlocal failed
        if not failed and path.name == "manuscript" and path.parent.name == "stage":
            failed = True
            raise OSError("injected replacement failure")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_first_manuscript_install)

    with pytest.raises(RuntimeError, match="automatic backup was restored"):
        restore_snapshot(root, snapshot_dir.name)

    current_text = chapter_path.read_text(encoding="utf-8")
    assert "Snapshot text." in current_text
    assert "Current text." in current_text
    assert any(str(record["label"]).startswith("automatic backup before restoring") for record in list_snapshots(root))


def test_save_project_template_and_reuse_it(tmp_path: Path) -> None:
    source_root = init_project(tmp_path / "source", "North County")
    custom_notes = source_root / "notes" / "field-outline.md"
    custom_notes.write_text("# Field Outline\n\nBullet list.\n", encoding="utf-8")

    template_path = save_project_template(source_root, "Field Guide")
    target_root = init_project_from_template(tmp_path / "target", "West County", template_file=template_path)

    assert template_path.exists()
    assert (target_root / "notes" / "field-outline.md").exists()
    config_text = (target_root / ".openscribe" / "project.yaml").read_text(encoding="utf-8")
    assert "template: field-guide" in config_text


def test_import_folder_project_preserves_parts_and_metadata(tmp_path: Path) -> None:
    source_root = tmp_path / "source-manuscript"
    (source_root / "act-one").mkdir(parents=True)
    (source_root / "draft.md").write_text("# Root Draft\n\nOpening body.\n", encoding="utf-8")
    (source_root / "act-one" / "arrival.md").write_text(
        "---\ntitle: Arrival\nstatus: revised\nlabel: setup\n---\n\nTown entry.\n",
        encoding="utf-8",
    )

    imported_root = import_folder_project(tmp_path / "imported", source_root, "Imported Book")
    chapters = list_chapters(imported_root)
    titles = {chapter.title for chapter in chapters}

    assert "Arrival" in titles
    assert "Root Draft" in titles
    assert any(chapter.status == "revised" for chapter in chapters if chapter.title == "Arrival")


def test_nonfiction_and_screenplay_helpers(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    create_part(root, "Opening")
    section_path = create_nonfiction_section(root, "Case Study", part="Opening", synopsis="A supporting example.")
    add_screenplay_scene(root, "Case Study", "int. courthouse - day", body="Lawyers cross the hall.")
    chapters = list_chapters(root)

    assert section_path.exists()
    assert chapters[0].label == "section"
    assert chapters[0].scenes[0].title == "INT. COURTHOUSE - DAY"


def test_render_board_includes_note_titles(tmp_path: Path) -> None:
    root = init_project(tmp_path, "North County")
    add_note(root, "Clue", group="plot", x=2, y=1)
    add_note(root, "Threat", group="plot", x=25, y=1)

    board_text = render_board(root, width=60, height=8)
    assert "note-001" in board_text
    assert "Clue" in board_text
    assert "Threat" in board_text
