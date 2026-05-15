from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from docx import Document
from typer.testing import CliRunner

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
