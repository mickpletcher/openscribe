from typer.testing import CliRunner

from openscribe.cli import app
from openscribe.project import create_chapter, create_part, init_project, list_chapters


def test_word_cli_export_preview_apply_and_invalid_file(tmp_path, monkeypatch):
    root = init_project(tmp_path, "CLI validation")
    create_part(root, "Opening")
    create_chapter(root, "Arrival")
    monkeypatch.chdir(root)
    runner = CliRunner()
    output = root / "build" / "roundtrip.docx"
    exported = runner.invoke(app, ["word", "export", "--output", str(output)])
    assert exported.exit_code == 0, exported.output
    preview = runner.invoke(app, ["word", "import", str(output)])
    assert preview.exit_code == 0, preview.output
    assert "Preview" in preview.output
    applied = runner.invoke(app, ["word", "import", str(output), "--apply"])
    assert applied.exit_code == 0, applied.output
    output.write_bytes(b"not a docx")
    assert runner.invoke(app, ["word", "import", str(output)]).exit_code != 0


def test_explicit_repair_cli_and_desktop_launcher(tmp_path, monkeypatch):
    root = init_project(tmp_path, "CLI validation")
    create_part(root, "Opening")
    create_chapter(root, "Arrival")
    chapter = list_chapters(root)[0]
    chapter.path.write_text(chapter.path.read_text(encoding="utf-8") + "## External scene\n\nSynthetic prose", encoding="utf-8")
    monkeypatch.chdir(root)
    runner = CliRunner()
    result = runner.invoke(app, ["migrate", "repair"])
    assert result.exit_code == 0, result.output
    assert list_chapters(root)[0].scenes[0].scene_id
    launches = []
    monkeypatch.setattr("openscribe.desktop.launch", launches.append)
    result = runner.invoke(app, ["desktop", "--project", str(root)])
    assert result.exit_code == 0, result.output
    assert launches == [root]
