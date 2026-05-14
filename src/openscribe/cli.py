from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from openscribe.ai import AIConfigurationError, load_ai_settings, summarize_text
from openscribe.project import (
    create_chapter,
    create_part,
    find_chapter,
    init_project,
    list_chapters,
    load_project_config,
    project_root,
)
from openscribe.tui import OpenScribeApp

app = typer.Typer(help="CLI and TUI writing environment for long form projects.")
new_app = typer.Typer(help="Create manuscript content.")
ai_app = typer.Typer(help="Optional AI helpers for manuscript work.")
app.add_typer(new_app, name="new")
app.add_typer(ai_app, name="ai")
console = Console()


@app.command()
def init(
    title: str = typer.Argument(..., help="Project title."),
    path: Path = typer.Option(Path("."), "--path", help="Target directory."),
) -> None:
    project_path = init_project(path, title)
    console.print(f"Initialized openscribe project at {project_path}")


@new_app.command("part")
def new_part(title: str = typer.Argument(..., help="Part title.")) -> None:
    root = project_root()
    part_path = create_part(root, title)
    console.print(f"Created part {part_path.name}")


@new_app.command("chapter")
def new_chapter(
    title: str = typer.Argument(..., help="Chapter title."),
    part: Optional[str] = typer.Option(None, "--part", help="Part name or slug."),
    status: str = typer.Option("draft", "--status", help="Document status."),
    label: str = typer.Option("default", "--label", help="Document label."),
    pov: str = typer.Option("", "--pov", help="Point of view."),
    word_target: int = typer.Option(0, "--word-target", help="Word target."),
    synopsis: str = typer.Option("", "--synopsis", help="Synopsis text."),
    notes: str = typer.Option("", "--notes", help="Notes text."),
) -> None:
    root = project_root()
    chapter_path = create_chapter(
        root=root,
        title=title,
        part=part,
        status=status,
        label=label,
        pov=pov,
        word_target=word_target,
        synopsis=synopsis,
        notes=notes,
    )
    console.print(f"Created chapter {chapter_path.relative_to(root)}")


@app.command()
def outline() -> None:
    root = project_root()
    chapters = list_chapters(root)
    config = load_project_config(root)
    tree = Tree(config.get("title", "Untitled Project"))
    nodes: dict[str, Tree] = {}

    for chapter in chapters:
        part_node = nodes.get(chapter.part)
        if part_node is None:
            part_node = tree.add(chapter.part)
            nodes[chapter.part] = part_node
        part_node.add(f"{chapter.title} [{chapter.status}]")

    console.print(tree)


@app.command()
def status() -> None:
    root = project_root()
    chapters = list_chapters(root)
    config = load_project_config(root)

    console.print(f"Project: {config.get('title', 'Untitled Project')}")
    console.print(f"Chapters: {len(chapters)}")
    console.print(f"Words: {sum(chapter.word_count for chapter in chapters)}")

    table = Table(title="Manuscript")
    table.add_column("Part")
    table.add_column("Chapter")
    table.add_column("Status")
    table.add_column("POV")
    table.add_column("Words", justify="right")
    table.add_column("Target", justify="right")

    for chapter in chapters:
        table.add_row(
            chapter.part,
            chapter.title,
            chapter.status,
            chapter.pov or "",
            str(chapter.word_count),
            str(chapter.word_target or 0),
        )

    console.print(table)


@app.command()
def tui() -> None:
    root = project_root()
    OpenScribeApp(root).run()


@ai_app.command("summarize")
def ai_summarize(
    chapter: str = typer.Argument(..., help="Chapter title or slug."),
) -> None:
    root = project_root()
    config = load_project_config(root)
    settings = load_ai_settings(config)
    document = find_chapter(root, chapter)
    if not document.body.strip():
        raise typer.BadParameter("The chapter body is empty.")

    try:
        summary = summarize_text(document.body, settings, "chapter")
    except AIConfigurationError as exc:
        raise typer.BadParameter(str(exc)) from exc

    console.print(
        Panel(
            summary,
            title=f"AI Summary: {document.title}",
            border_style="cyan",
        )
    )
