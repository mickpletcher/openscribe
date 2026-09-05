from __future__ import annotations

import shutil
from pathlib import Path

from typer.testing import CliRunner

from openscribe.cli import app

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


def invoke(arguments: list[str]):
    result = runner.invoke(app, arguments)
    assert result.exit_code == 0, result.output
    return result


def user_files(project: Path) -> dict[Path, bytes]:
    return {
        path.relative_to(project): path.read_bytes()
        for path in project.rglob("*")
        if path.is_file() and path.relative_to(project).as_posix() != ".openscribe/.write.lock"
    }


def test_documented_first_project_sequence(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "my-novel-cli"
    invoke(["init", "My Novel", "--path", str(project), "--template", "fiction"])
    monkeypatch.chdir(project)

    assert "No migration is required" in invoke(["migrate", "status"]).output
    invoke(["new", "part", "Opening"])
    invoke(["new", "chapter", "Arrival", "--part", "Opening"])
    invoke(
        [
            "new",
            "scene",
            "Bus Stop",
            "--chapter",
            "Arrival",
            "--body",
            "The bus doors closed behind her.",
        ]
    )
    assert "Arrival" in invoke(["outline"]).output
    assert "Bus Stop" in invoke(["outliner"]).output
    assert "Chapters: 1" in invoke(["status"]).output
    assert "The bus doors closed behind her." in invoke(["read"]).output
    invoke(["snapshot", "save", "first-pass"])
    assert "first-pass" in invoke(["snapshot", "list"]).output
    assert "Preview only" in invoke(["snapshot", "restore", "first-pass"]).output
    invoke(["compile", "--format", "docx"])

    assert (project / "build" / "my-novel.docx").is_file()


def test_documented_research_project_sequence(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "grid-study"
    invoke(["init", "Grid Study", "--path", str(project), "--template", "research"])
    monkeypatch.chdir(project)

    invoke(["workflow", "research-paper", "--part", "Paper"])
    abstract = project / "manuscript" / "part-01-paper" / "ch-01-abstract.md"
    abstract.write_text(
        abstract.read_text(encoding="utf-8") + "\nThis paper examines resilient rural energy systems.\n",
        encoding="utf-8",
    )
    invoke(
        [
            "workflow",
            "source-note",
            "River Ledger Study",
            "--type",
            "article",
            "--author",
            "J. Harper",
            "--year",
            "2024",
        ]
    )
    invoke(["workflow", "citation-pack", "--style", "Chicago"])
    invoke(["compile", "--profile", "research-paper"])

    assert (project / "build" / "grid-study-research-paper.docx").is_file()


def test_documented_sample_inspection_is_read_only(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "north-county"
    shutil.copytree(ROOT / "examples" / "north-county", project)
    before = user_files(project)
    monkeypatch.chdir(project)

    for arguments in (
        ["outline"],
        ["status"],
        ["outliner"],
        ["read"],
        ["report", "project"],
        ["find", "chapters", "--text", "station"],
        ["find", "scenes", "--text", "station"],
    ):
        invoke(arguments)

    assert user_files(project) == before
