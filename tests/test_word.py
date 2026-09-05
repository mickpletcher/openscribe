from __future__ import annotations

import io
import json
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import pytest

from openscribe.editing import EditConflictError
from openscribe.index import index_is_current
from openscribe.project import add_scene, create_chapter, create_part, init_project, list_chapters, update_scene_body
from openscribe.snapshots import _current_file_bytes
from openscribe.word import W, WordImportError, apply_word_import, export_word, preview_word_import


@pytest.fixture
def exported(tmp_path):
    root = init_project(tmp_path, "Synthetic Word project")
    create_part(root, "Opening")
    create_chapter(root, "Arrival")
    add_scene(root, "Arrival", "Station", "Original text.")
    output = export_word(root, root / "build" / "roundtrip.docx")
    return root, output.read_bytes()


def modify_package(payload, modify):
    with ZipFile(io.BytesIO(payload)) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    document = ET.fromstring(parts["word/document.xml"])
    modify(document)
    parts["word/document.xml"] = ET.tostring(document)
    result = io.BytesIO()
    with ZipFile(result, "w") as archive:
        for name, content in parts.items():
            archive.writestr(name, content)
    return result.getvalue()


def word_edit(payload, text="Word text."):
    def edit(document):
        for node in document.iter(f"{{{W}}}t"):
            if node.text == "Original text.":
                node.text = text
    return modify_package(payload, edit)


@pytest.mark.parametrize(("markdown", "word", "status"), [
    ("Original text.", "Original text.", "unchanged"),
    ("Original text.", "Word text.", "import"),
    ("Markdown text.", "Original text.", "keep-markdown"),
    ("Same edit.", "Same edit.", "converged"),
    ("Markdown text.", "Word text.", "conflict"),
])
def test_word_three_way_classification_and_safe_apply(exported, markdown, word, status):
    root, payload = exported
    chapter = list_chapters(root)[0]
    scene_id = chapter.scenes[0].scene_id
    if markdown != "Original text.":
        update_scene_body(root, chapter.chapter_id, scene_id, markdown)
    payload = word_edit(payload, word)
    before = _current_file_bytes(root)
    plan = preview_word_import(root, payload)
    assert _current_file_bytes(root) == before
    assert next(review.status for review in plan.reviews if review.identity == scene_id) == status
    if status == "conflict":
        with pytest.raises(WordImportError, match="conflicts"):
            apply_word_import(root, plan)
        assert _current_file_bytes(root) == before
    else:
        backup = apply_word_import(root, plan)
        assert list_chapters(root)[0].scenes[0].body == (word if status == "import" else markdown)
        if status == "import":
            assert backup.exists()
            assert index_is_current(root)


def test_word_identity_deletion_duplication_and_malformed_tags(exported):
    root, payload = exported
    def remove(document):
        body = document.find(f"{{{W}}}body")
        body.remove(body.find(f"{{{W}}}sdt"))
    with pytest.raises(WordImportError, match="added, removed"):
        preview_word_import(root, modify_package(payload, remove))

    def duplicate(document):
        body = document.find(f"{{{W}}}body")
        body.append(ET.fromstring(ET.tostring(body.find(f"{{{W}}}sdt"))))
    with pytest.raises(WordImportError, match="duplicate"):
        preview_word_import(root, modify_package(payload, duplicate))

    def malformed(document):
        document.find(f".//{{{W}}}tag").set(f"{{{W}}}val", "untrusted-id")
    with pytest.raises(WordImportError, match="identity"):
        preview_word_import(root, modify_package(payload, malformed))


def test_tracked_changes_block_apply(exported):
    root, payload = exported
    def tracking(document):
        paragraph = document.find(f".//{{{W}}}p")
        insertion = ET.SubElement(paragraph, f"{{{W}}}ins")
        run = ET.SubElement(insertion, f"{{{W}}}r")
        ET.SubElement(run, f"{{{W}}}t").text = "Unresolved change"
    plan = preview_word_import(root, modify_package(payload, tracking))
    assert plan.tracked_changes == 1
    assert plan.blocked
    with pytest.raises(WordImportError, match="tracked changes"):
        apply_word_import(root, plan)


def test_word_stale_preview_and_failed_apply_preserve_files(exported, monkeypatch):
    root, payload = exported
    plan = preview_word_import(root, word_edit(payload))
    note = root / "notes" / "new.md"
    note.write_text("New work", encoding="utf-8")
    with pytest.raises(EditConflictError, match="Preview again"):
        apply_word_import(root, plan)
    plan = preview_word_import(root, word_edit(payload))
    before = _current_file_bytes(root)
    def fail_index(stage):
        raise RuntimeError("Synthetic index failure")
    monkeypatch.setattr("openscribe.word.rebuild_project_index", fail_index)
    with pytest.raises(RuntimeError, match="index failure"):
        apply_word_import(root, plan)
    assert _current_file_bytes(root) == before


def test_word_requires_baseline_and_never_overwrites_export(exported):
    root, payload = exported
    with pytest.raises(FileExistsError):
        export_word(root, root / "build" / "roundtrip.docx")
    with pytest.raises(WordImportError, match="under build"):
        export_word(root, root / "notes" / "document.docx")
    baseline_path = next((root / ".openscribe" / "word-roundtrip").glob("*/baseline.json"))
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline["texts"][next(iter(baseline["texts"]))] = "Corrupt baseline"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    with pytest.raises(WordImportError, match="hash verification"):
        preview_word_import(root, payload)
    baseline_path.unlink()
    with pytest.raises(WordImportError, match="baseline is missing"):
        preview_word_import(root, payload)


def test_invalid_word_package(exported):
    root, _ = exported
    with pytest.raises(WordImportError, match="malformed"):
        preview_word_import(root, b"not a docx")
