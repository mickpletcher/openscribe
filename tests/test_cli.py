from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from docx import Document
from typer.testing import CliRunner
import yaml

from openscribe.cli import app
import openscribe.compile as compile_module


runner = CliRunner()


def test_outline_shows_literal_status_text(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "North County"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["new", "part", "Opening"])
    assert result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "new",
            "chapter",
            "Arrival",
            "--part",
            "Opening",
            "--status",
            "draft",
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(app, ["outline"])
    assert result.exit_code == 0
    assert "Opening" in result.stdout
    assert "part-01-opening" not in result.stdout
    assert "Arrival [draft]" in result.stdout


def test_compile_writes_docx_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["init", "North County"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Opening"]).exit_code == 0
    assert (
        runner.invoke(
            app,
            ["new", "chapter", "Arrival", "--part", "Opening", "--status", "draft"],
        ).exit_code
        == 0
    )

    chapter_path = (
        tmp_path / "manuscript" / "part-01-opening" / "ch-01-arrival.md"
    )
    chapter_path.write_text(
        chapter_path.read_text(encoding="utf-8")
        + "Eli stepped off the bus into wet summer heat.\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["compile"])
    assert result.exit_code == 0

    output_path = tmp_path / "build" / "north-county.docx"
    assert output_path.exists()

    document = Document(output_path)
    paragraph_text = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
    assert "North County" in paragraph_text
    assert "Opening" in paragraph_text
    assert "Arrival" in paragraph_text
    assert "Eli stepped off the bus into wet summer heat." in paragraph_text


def test_compile_writes_pdf_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["init", "North County"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Opening"]).exit_code == 0
    assert (
        runner.invoke(
            app,
            ["new", "chapter", "Arrival", "--part", "Opening", "--status", "draft"],
        ).exit_code
        == 0
    )

    chapter_path = tmp_path / "manuscript" / "part-01-opening" / "ch-01-arrival.md"
    chapter_path.write_text(
        chapter_path.read_text(encoding="utf-8")
        + "Eli stepped off the bus into wet summer heat.\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["compile", "--format", "pdf"])
    assert result.exit_code == 0

    output_path = tmp_path / "build" / "north-county.pdf"
    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"%PDF")


def test_compile_writes_epub_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["init", "North County"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Opening"]).exit_code == 0
    assert (
        runner.invoke(
            app,
            ["new", "chapter", "Arrival", "--part", "Opening", "--status", "draft"],
        ).exit_code
        == 0
    )

    chapter_path = tmp_path / "manuscript" / "part-01-opening" / "ch-01-arrival.md"
    chapter_path.write_text(
        chapter_path.read_text(encoding="utf-8")
        + "Eli stepped off the bus into wet summer heat.\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["compile", "--format", "epub"])
    assert result.exit_code == 0

    output_path = tmp_path / "build" / "north-county.epub"
    assert output_path.exists()

    with ZipFile(output_path) as archive:
        names = set(archive.namelist())

    assert "mimetype" in names
    assert "EPUB/content.opf" in names
    assert "EPUB/nav.xhtml" in names


def test_compile_respects_project_compile_settings(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["init", "North County"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Opening"]).exit_code == 0
    assert (
        runner.invoke(
            app,
            ["new", "chapter", "Arrival", "--part", "Opening", "--status", "draft"],
        ).exit_code
        == 0
    )

    config_path = tmp_path / ".openscribe" / "project.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["compile"]["output_filename"] = "review-copy"
    config["compile"]["include_title_page"] = False
    config["compile"]["include_part_headings"] = False
    config["compile"]["chapter_heading_style"] = "chapter-number-title"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    chapter_path = tmp_path / "manuscript" / "part-01-opening" / "ch-01-arrival.md"
    chapter_path.write_text(
        chapter_path.read_text(encoding="utf-8")
        + "Eli stepped off the bus into wet summer heat.\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["compile"])
    assert result.exit_code == 0

    output_path = tmp_path / "build" / "review-copy.docx"
    assert output_path.exists()

    document = Document(output_path)
    paragraph_text = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
    assert "North County" not in paragraph_text
    assert "Opening" not in paragraph_text
    assert "Chapter 1: Arrival" in paragraph_text


def test_compile_prefers_pandoc_when_available(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["init", "North County"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Opening"]).exit_code == 0
    assert runner.invoke(app, ["new", "chapter", "Arrival", "--part", "Opening"]).exit_code == 0

    chapter_path = tmp_path / "manuscript" / "part-01-opening" / "ch-01-arrival.md"
    chapter_path.write_text(
        chapter_path.read_text(encoding="utf-8") + "Eli stepped off the bus into wet summer heat.\n",
        encoding="utf-8",
    )

    command_log: list[list[str]] = []

    def fake_run(command: list[str], capture_output: bool, text: bool, check: bool):
        command_log.append(command)
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_text("pandoc output", encoding="utf-8")

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return Result()

    monkeypatch.setattr(compile_module.shutil, "which", lambda name: "pandoc.exe" if name == "pandoc" else None)
    monkeypatch.setattr(compile_module.subprocess, "run", fake_run)

    result = runner.invoke(app, ["compile"])
    assert result.exit_code == 0

    output_path = tmp_path / "build" / "north-county.docx"
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == "pandoc output"
    assert command_log
    assert command_log[0][0] == "pandoc.exe"
    assert "--to" in command_log[0]
    assert "docx" in command_log[0]


def test_read_outputs_continuous_manuscript_using_template(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["init", "North County"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Opening"]).exit_code == 0
    assert (
        runner.invoke(
            app,
            ["new", "chapter", "Arrival", "--part", "Opening", "--status", "draft"],
        ).exit_code
        == 0
    )

    chapter_path = tmp_path / "manuscript" / "part-01-opening" / "ch-01-arrival.md"
    chapter_path.write_text(
        chapter_path.read_text(encoding="utf-8")
        + "Eli stepped off the bus into wet summer heat.\n\nHe kept walking toward Willow Lane.\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["read", "--template", "manuscript"])
    assert result.exit_code == 0
    assert "North County" in result.stdout
    assert "Opening" not in result.stdout
    assert "Chapter 1: Arrival" in result.stdout
    assert "He kept walking toward Willow Lane." in result.stdout


def test_set_and_show_chapter_metadata(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["init", "North County"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Opening"]).exit_code == 0
    assert runner.invoke(app, ["new", "chapter", "Arrival", "--part", "Opening"]).exit_code == 0

    result = runner.invoke(
        app,
        [
            "set",
            "chapter",
            "Arrival",
            "--status",
            "revised",
            "--label",
            "action",
            "--pov",
            "Eli",
            "--word-target",
            "2500",
            "--synopsis",
            "Eli reaches town.",
            "--notes",
            "Tighten the station scene.",
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(app, ["show", "chapter", "Arrival"])
    assert result.exit_code == 0
    assert "status: revised" in result.stdout
    assert "label: action" in result.stdout
    assert "pov: Eli" in result.stdout
    assert "word_target: 2500" in result.stdout
    assert "synopsis: Eli reaches town." in result.stdout
    assert "notes: Tighten the station scene." in result.stdout


def test_set_and_show_part_metadata(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["init", "North County"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Opening"]).exit_code == 0

    result = runner.invoke(app, ["set", "part", "Opening", "--title", "Cold Open"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["show", "part", "Cold Open"])
    assert result.exit_code == 0
    assert "title: Cold Open" in result.stdout


def test_story_idea_commands(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["init", "North County"]).exit_code == 0

    result = runner.invoke(
        app,
        [
            "idea",
            "add",
            "The Flood Ledger",
            "--premise",
            "A county clerk finds a ledger that predicts deaths.",
            "--genre",
            "Southern Gothic",
            "--tone",
            "Uneasy",
            "--status",
            "seed",
            "--notes",
            "Tie the flood history to the missing records plot.",
        ],
    )
    assert result.exit_code == 0
    assert "notes\\story-ideas\\the-flood-ledger.md" in result.stdout

    result = runner.invoke(app, ["idea", "list"])
    assert result.exit_code == 0
    assert "The Flood" in result.stdout
    assert "Southern" in result.stdout
    assert "Ideas: 1" in result.stdout

    result = runner.invoke(app, ["show", "idea", "The Flood Ledger"])
    assert result.exit_code == 0
    assert "premise: A county clerk finds a ledger that predicts deaths." in result.stdout
    assert "genre: Southern Gothic" in result.stdout
    assert "tone: Uneasy" in result.stdout
    assert "status: seed" in result.stdout


def test_find_chapters_filters_by_metadata_and_text(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["init", "North County"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Opening"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Ending"]).exit_code == 0
    assert (
        runner.invoke(
            app,
            [
                "new",
                "chapter",
                "Arrival",
                "--part",
                "Opening",
                "--status",
                "draft",
                "--label",
                "setup",
                "--pov",
                "Eli",
                "--synopsis",
                "Eli reaches town.",
            ],
        ).exit_code
        == 0
    )
    assert (
        runner.invoke(
            app,
            [
                "new",
                "chapter",
                "Departure",
                "--part",
                "Ending",
                "--status",
                "revised",
                "--label",
                "finale",
                "--pov",
                "Nora",
                "--notes",
                "Need stronger station callback.",
            ],
        ).exit_code
        == 0
    )

    arrival_path = tmp_path / "manuscript" / "part-01-opening" / "ch-01-arrival.md"
    arrival_path.write_text(
        arrival_path.read_text(encoding="utf-8") + "The station was almost empty.\n",
        encoding="utf-8",
    )
    departure_path = tmp_path / "manuscript" / "part-02-ending" / "ch-01-departure.md"
    departure_path.write_text(
        departure_path.read_text(encoding="utf-8") + "Nora left before sunrise.\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["find", "chapters", "--status", "revised"])
    assert result.exit_code == 0
    assert "Departure" in result.stdout
    assert "Arrival" not in result.stdout
    assert "Matches: 1" in result.stdout

    result = runner.invoke(app, ["find", "chapters", "--part", "Opening", "--pov", "Eli"])
    assert result.exit_code == 0
    assert "Arrival" in result.stdout
    assert "Departure" not in result.stdout

    result = runner.invoke(app, ["find", "chapters", "--text", "station"])
    assert result.exit_code == 0
    assert "Arrival" in result.stdout
    assert "Departure" in result.stdout
    assert "Matches: 2" in result.stdout


def test_report_project_and_batch_update(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["init", "North County"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Opening"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Ending"]).exit_code == 0
    assert (
        runner.invoke(
            app,
            ["new", "chapter", "Arrival", "--part", "Opening", "--status", "draft", "--label", "setup", "--pov", "Eli"],
        ).exit_code
        == 0
    )
    assert (
        runner.invoke(
            app,
            ["new", "chapter", "Departure", "--part", "Ending", "--status", "draft", "--label", "finale", "--pov", "Nora"],
        ).exit_code
        == 0
    )

    result = runner.invoke(app, ["report", "project"])
    assert result.exit_code == 0
    assert "By Status" in result.stdout
    assert "draft" in result.stdout
    assert "By POV" in result.stdout
    assert "Eli" in result.stdout

    result = runner.invoke(app, ["set", "chapters", "--match-status", "draft", "--status", "revised"])
    assert result.exit_code == 0
    assert "Updated chapters: 2" in result.stdout

    result = runner.invoke(app, ["find", "chapters", "--status", "revised"])
    assert result.exit_code == 0
    assert "Matches: 2" in result.stdout


def test_board_note_workflow_and_promote(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["init", "North County"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Opening"]).exit_code == 0

    result = runner.invoke(app, ["board", "note", "add", "Station Secret", "--body", "The station master is hiding records.", "--group", "plot"])
    assert result.exit_code == 0
    assert "note-001" in result.stdout

    result = runner.invoke(app, ["board", "note", "add", "Eli Clue", "--body", "Eli finds a ledger."])
    assert result.exit_code == 0
    assert "note-002" in result.stdout

    assert runner.invoke(app, ["board", "link", "add", "note-001", "note-002"]).exit_code == 0
    assert runner.invoke(app, ["board", "group", "set", "note-002", "plot"]).exit_code == 0

    result = runner.invoke(app, ["board", "note", "list", "--group", "plot"])
    assert result.exit_code == 0
    assert "Station Secret" in result.stdout
    assert "Eli Clue" in result.stdout

    result = runner.invoke(app, ["board", "promote", "note-001", "--part", "Opening", "--chapter", "Station Secret"])
    assert result.exit_code == 0
    assert "Station Secret" in result.stdout

    result = runner.invoke(app, ["find", "chapters", "--text", "hiding records"])
    assert result.exit_code == 0
    assert "Station Secret" in result.stdout


def test_element_workflow_and_appears_in(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["init", "North County"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Opening"]).exit_code == 0
    assert runner.invoke(app, ["new", "chapter", "Arrival", "--part", "Opening"]).exit_code == 0

    chapter_path = tmp_path / "manuscript" / "part-01-opening" / "ch-01-arrival.md"
    chapter_path.write_text(
        chapter_path.read_text(encoding="utf-8") + "Marcus Vale met the station keeper at dawn.\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["element", "add", "character", "Marcus Vale", "--notes", "Main investigator", "--tags", "lead,viewpoint"])
    assert result.exit_code == 0
    assert "cha-marcus-vale" in result.stdout

    assert runner.invoke(app, ["element", "alias", "add", "cha-marcus-vale", "Marcus"]).exit_code == 0
    assert runner.invoke(app, ["element", "add", "setting", "North Station"]).exit_code == 0
    assert runner.invoke(app, ["element", "relate", "cha-marcus-vale", "set-north-station", "--type", "visits"]).exit_code == 0

    result = runner.invoke(app, ["element", "show", "cha-marcus-vale"])
    assert result.exit_code == 0
    assert "Marcus Vale" in result.stdout
    assert "Main investigator" in result.stdout
    assert "visits" in result.stdout

    result = runner.invoke(app, ["element", "appears-in", "Marcus"])
    assert result.exit_code == 0
    assert "Arrival" in result.stdout
    assert "Matches: 1" in result.stdout


def test_multi_part_read_and_export_regression(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["init", "North County"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Opening"]).exit_code == 0
    assert runner.invoke(app, ["new", "part", "Ending"]).exit_code == 0
    assert runner.invoke(app, ["new", "chapter", "Arrival", "--part", "Opening"]).exit_code == 0
    assert runner.invoke(app, ["new", "chapter", "Reckoning", "--part", "Ending"]).exit_code == 0

    arrival_path = tmp_path / "manuscript" / "part-01-opening" / "ch-01-arrival.md"
    arrival_path.write_text(arrival_path.read_text(encoding="utf-8") + "Opening text.\n", encoding="utf-8")
    reckoning_path = tmp_path / "manuscript" / "part-02-ending" / "ch-01-reckoning.md"
    reckoning_path.write_text(reckoning_path.read_text(encoding="utf-8") + "Ending text.\n", encoding="utf-8")

    read_result = runner.invoke(app, ["read"])
    assert read_result.exit_code == 0
    assert read_result.stdout.index("Opening") < read_result.stdout.index("Arrival")
    assert read_result.stdout.index("Ending") < read_result.stdout.index("Reckoning")
    assert read_result.stdout.index("Arrival") < read_result.stdout.index("Reckoning")

    compile_result = runner.invoke(app, ["compile"])
    assert compile_result.exit_code == 0

    output_path = tmp_path / "build" / "north-county.docx"
    document = Document(output_path)
    paragraph_text = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
    assert paragraph_text.index("Opening") < paragraph_text.index("Arrival")
    assert paragraph_text.index("Ending") < paragraph_text.index("Reckoning")
