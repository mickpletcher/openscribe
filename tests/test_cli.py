from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from docx import Document
from typer.testing import CliRunner
import yaml

from openscribe.cli import app


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
    assert "part_id: part-01-opening" in result.stdout


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
