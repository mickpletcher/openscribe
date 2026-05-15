from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from openscribe.ai import AIConfigurationError, load_ai_settings, summarize_text
from openscribe.compile import CompileError, assemble_manuscript_text, compile_project
from openscribe.project import (
    create_chapter,
    create_part,
    find_chapter,
    find_chapters,
    init_project,
    list_chapters,
    load_part_metadata,
    load_project_config,
    project_root,
    update_chapter_metadata,
    update_part_title,
)
from openscribe.tui import OpenScribeApp

app = typer.Typer(help="CLI and TUI writing environment for long form projects.")
new_app = typer.Typer(help="Create manuscript content.")
ai_app = typer.Typer(help="Optional AI helpers for manuscript work.")
set_app = typer.Typer(help="Update project metadata.")
show_app = typer.Typer(help="Show project metadata.")
find_app = typer.Typer(help="Find project content.")
app.add_typer(new_app, name="new")
app.add_typer(ai_app, name="ai")
app.add_typer(set_app, name="set")
app.add_typer(show_app, name="show")
app.add_typer(find_app, name="find")
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
        part_node = nodes.get(chapter.part_id)
        if part_node is None:
            part_node = tree.add(chapter.part)
            nodes[chapter.part_id] = part_node
        part_node.add(Text(f"{chapter.title} [{chapter.status}]"))

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
def compile(
    format_name: str = typer.Option("docx", "--format", help="Output format. Use docx, pdf, or epub."),
    template_name: Optional[str] = typer.Option(None, "--template", help="Compile template. Use novel, manuscript, or minimal."),
    output: Optional[Path] = typer.Option(None, "--output", help="Output document path."),
) -> None:
    root = project_root()
    try:
        output_path = compile_project(root, format_name, template_name, output)
    except CompileError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"Compiled manuscript to {output_path}")


@app.command()
def read(
    template_name: Optional[str] = typer.Option(None, "--template", help="Reading template. Use novel, manuscript, or minimal."),
) -> None:
    root = project_root()
    try:
        manuscript_text = assemble_manuscript_text(root, template_name)
    except CompileError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(manuscript_text)


@app.command()
def tui() -> None:
    root = project_root()
    OpenScribeApp(root).run()


@set_app.command("part")
def set_part(
    part: str = typer.Argument(..., help="Part title or slug."),
    title: str = typer.Option(..., "--title", help="New part title."),
) -> None:
    root = project_root()
    part_path = update_part_title(root, part, title)
    console.print(f"Updated part {part_path.name}")


@set_app.command("chapter")
def set_chapter(
    chapter: str = typer.Argument(..., help="Chapter title or slug."),
    title: Optional[str] = typer.Option(None, "--title", help="New chapter title."),
    status: Optional[str] = typer.Option(None, "--status", help="New status."),
    label: Optional[str] = typer.Option(None, "--label", help="New label."),
    synopsis: Optional[str] = typer.Option(None, "--synopsis", help="New synopsis."),
    pov: Optional[str] = typer.Option(None, "--pov", help="New point of view."),
    word_target: Optional[int] = typer.Option(None, "--word-target", help="New word target."),
    notes: Optional[str] = typer.Option(None, "--notes", help="New notes."),
) -> None:
    root = project_root()
    chapter_path = update_chapter_metadata(
        root,
        chapter,
        title=title,
        status=status,
        label=label,
        synopsis=synopsis,
        pov=pov,
        word_target=word_target,
        notes=notes,
    )
    console.print(f"Updated chapter {chapter_path.relative_to(root)}")


@show_app.command("part")
def show_part(part: str = typer.Argument(..., help="Part title or slug.")) -> None:
    root = project_root()
    metadata = load_part_metadata(root, part)
    console.print(Panel(_yaml_dump(metadata), title="Part Metadata", border_style="cyan"))


@show_app.command("chapter")
def show_chapter(chapter: str = typer.Argument(..., help="Chapter title or slug.")) -> None:
    root = project_root()
    document = find_chapter(root, chapter)
    metadata = {
        "title": document.title,
        "status": document.status,
        "label": document.label,
        "synopsis": document.synopsis,
        "pov": document.pov,
        "word_target": document.word_target,
        "notes": document.notes,
        "part": document.part,
        "part_id": document.part_id,
        "path": str(document.path),
        "word_count": document.word_count,
    }
    console.print(Panel(_yaml_dump(metadata), title="Chapter Metadata", border_style="cyan"))


@find_app.command("chapters")
def find_chapter_matches(
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status."),
    label: Optional[str] = typer.Option(None, "--label", help="Filter by label."),
    pov: Optional[str] = typer.Option(None, "--pov", help="Filter by point of view."),
    part: Optional[str] = typer.Option(None, "--part", help="Filter by part title or slug."),
    text: Optional[str] = typer.Option(None, "--text", help="Search title, synopsis, notes, and body text."),
) -> None:
    root = project_root()
    matches = find_chapters(root, status=status, label=label, pov=pov, part=part, text=text)
    table = Table(title="Chapter Matches")
    table.add_column("Part")
    table.add_column("Chapter")
    table.add_column("Status")
    table.add_column("POV")
    table.add_column("Path")

    for chapter in matches:
        table.add_row(
            chapter.part,
            chapter.title,
            chapter.status,
            chapter.pov or "",
            str(chapter.path.relative_to(root)),
        )

    console.print(table)
    console.print(f"Matches: {len(matches)}")


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


def _yaml_dump(data: dict) -> str:
    import yaml

    return yaml.safe_dump(data, sort_keys=False).strip()
