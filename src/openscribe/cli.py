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
from openscribe.board import add_link, add_note, list_notes, promote_note_to_chapter, set_group
from openscribe.compile import CompileError, assemble_manuscript_text, compile_project
from openscribe.elements import add_alias, add_element, add_relation, appears_in, get_element, list_element_records
from openscribe.project import (
    batch_update_chapters,
    chapter_report,
    create_chapter,
    create_part,
    create_story_idea,
    find_chapter,
    find_chapters,
    find_story_idea,
    init_project,
    list_chapters,
    list_story_ideas,
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
report_app = typer.Typer(help="Project reports.")
board_app = typer.Typer(help="Board mode workflows.")
board_note_app = typer.Typer(help="Board note workflows.")
board_link_app = typer.Typer(help="Board link workflows.")
board_group_app = typer.Typer(help="Board grouping workflows.")
element_app = typer.Typer(help="Element and relation workflows.")
element_alias_app = typer.Typer(help="Element alias workflows.")
idea_app = typer.Typer(help="Story idea workflows.")
app.add_typer(new_app, name="new")
app.add_typer(ai_app, name="ai")
app.add_typer(set_app, name="set")
app.add_typer(show_app, name="show")
app.add_typer(find_app, name="find")
app.add_typer(report_app, name="report")
app.add_typer(board_app, name="board")
app.add_typer(element_app, name="element")
app.add_typer(idea_app, name="idea")
board_app.add_typer(board_note_app, name="note")
board_app.add_typer(board_link_app, name="link")
board_app.add_typer(board_group_app, name="group")
element_app.add_typer(element_alias_app, name="alias")
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


@idea_app.command("add")
def idea_add(
    title: str = typer.Argument(..., help="Story idea title."),
    premise: str = typer.Option("", "--premise", help="Short story premise."),
    genre: str = typer.Option("", "--genre", help="Story genre."),
    tone: str = typer.Option("", "--tone", help="Story tone."),
    status: str = typer.Option("seed", "--status", help="Idea status."),
    notes: str = typer.Option("", "--notes", help="Longer idea notes."),
) -> None:
    root = project_root()
    idea_path = create_story_idea(
        root,
        title,
        premise=premise,
        genre=genre,
        tone=tone,
        status=status,
        notes=notes,
    )
    console.print(f"Added story idea {idea_path.relative_to(root)}")


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


@set_app.command("chapters")
def set_chapters(
    match_status: Optional[str] = typer.Option(None, "--match-status", help="Match status."),
    match_label: Optional[str] = typer.Option(None, "--match-label", help="Match label."),
    match_pov: Optional[str] = typer.Option(None, "--match-pov", help="Match point of view."),
    match_part: Optional[str] = typer.Option(None, "--match-part", help="Match part title or slug."),
    match_text: Optional[str] = typer.Option(None, "--match-text", help="Match text in title, synopsis, notes, or body."),
    title: Optional[str] = typer.Option(None, "--title", help="New chapter title."),
    status: Optional[str] = typer.Option(None, "--status", help="New status."),
    label: Optional[str] = typer.Option(None, "--label", help="New label."),
    synopsis: Optional[str] = typer.Option(None, "--synopsis", help="New synopsis."),
    pov: Optional[str] = typer.Option(None, "--pov", help="New point of view."),
    word_target: Optional[int] = typer.Option(None, "--word-target", help="New word target."),
    notes: Optional[str] = typer.Option(None, "--notes", help="New notes."),
) -> None:
    root = project_root()
    updated_paths = batch_update_chapters(
        root,
        match_status=match_status,
        match_label=match_label,
        match_pov=match_pov,
        match_part=match_part,
        match_text=match_text,
        title=title,
        status=status,
        label=label,
        synopsis=synopsis,
        pov=pov,
        word_target=word_target,
        notes=notes,
    )
    console.print(f"Updated chapters: {len(updated_paths)}")


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


@show_app.command("idea")
def show_idea(idea: str = typer.Argument(..., help="Story idea title or slug.")) -> None:
    root = project_root()
    record = find_story_idea(root, idea)
    metadata = {
        "title": record.title,
        "premise": record.premise,
        "genre": record.genre,
        "tone": record.tone,
        "status": record.status,
        "path": str(record.path),
        "notes": record.body,
    }
    console.print(Panel(_yaml_dump(metadata), title="Story Idea", border_style="cyan"))


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


@report_app.command("project")
def report_project() -> None:
    root = project_root()
    summary = chapter_report(root)
    console.print(f"Chapters: {summary['chapter_count']}")
    console.print(f"Words: {summary['word_count']}")

    _print_counter_table("By Status", summary["by_status"])
    _print_counter_table("By Label", summary["by_label"])
    _print_counter_table("By POV", summary["by_pov"])
    _print_counter_table("By Part", summary["by_part"])
    _print_counter_table("Part Word Totals", summary["part_word_totals"], value_header="Words")


@idea_app.command("list")
def idea_list() -> None:
    root = project_root()
    ideas = list_story_ideas(root)
    table = Table(title="Story Ideas")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Genre")
    table.add_column("Tone")
    table.add_column("Premise")
    table.add_column("Path")
    for idea in ideas:
        table.add_row(
            idea.title,
            idea.status,
            idea.genre,
            idea.tone,
            idea.premise,
            str(idea.path.relative_to(root)),
        )
    console.print(table)
    console.print(f"Ideas: {len(ideas)}")


@board_note_app.command("add")
def board_note_add(
    title: str = typer.Argument(..., help="Board note title."),
    body: str = typer.Option("", "--body", help="Board note body."),
    group: str = typer.Option("", "--group", help="Board note group."),
    x: int = typer.Option(0, "--x", help="Optional x position."),
    y: int = typer.Option(0, "--y", help="Optional y position."),
) -> None:
    root = project_root()
    note = add_note(root, title, body=body, group=group, x=x, y=y)
    console.print(f"Added board note {note.note_id}")


@board_note_app.command("list")
def board_note_list(group: Optional[str] = typer.Option(None, "--group", help="Filter by group.")) -> None:
    root = project_root()
    notes = list_notes(root)
    table = Table(title="Board Notes")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Group")
    table.add_column("Links")
    table.add_column("Body")
    for note in notes:
        if group and note.group.strip().lower() != group.strip().lower():
            continue
        table.add_row(note.note_id, note.title, note.group or "", ", ".join(note.links), note.body or "")
    console.print(table)


@board_link_app.command("add")
def board_link_add(
    from_id: str = typer.Argument(..., help="Source note id."),
    to_id: str = typer.Argument(..., help="Target note id."),
) -> None:
    root = project_root()
    add_link(root, from_id, to_id)
    console.print(f"Linked {from_id} to {to_id}")


@board_group_app.command("set")
def board_group_set(
    note_id: str = typer.Argument(..., help="Board note id."),
    group: str = typer.Argument(..., help="Group name."),
) -> None:
    root = project_root()
    set_group(root, note_id, group)
    console.print(f"Updated group for {note_id}")


@board_app.command("promote")
def board_promote(
    note_id: str = typer.Argument(..., help="Board note id."),
    chapter: Optional[str] = typer.Option(None, "--chapter", help="New chapter title."),
    part: Optional[str] = typer.Option(None, "--part", help="Target part title or slug."),
) -> None:
    root = project_root()
    note_title = next((note.title for note in list_notes(root) if note.note_id == note_id), note_id)
    chapter_path = promote_note_to_chapter(root, note_id, chapter_title=chapter, part=part)
    promoted_title = chapter or note_title
    console.print(f"Promoted board note into chapter {promoted_title} at {chapter_path.relative_to(root)}")


@element_app.command("add")
def element_add(
    type_name: str = typer.Argument(..., help="Element type. Use character, setting, or item."),
    name: str = typer.Argument(..., help="Primary element name."),
    notes: str = typer.Option("", "--notes", help="Element notes."),
    tags: str = typer.Option("", "--tags", help="Comma separated tags."),
) -> None:
    root = project_root()
    tag_values = [value.strip() for value in tags.split(",") if value.strip()]
    record = add_element(root, type_name, name, notes=notes, tags=tag_values)
    console.print(f"Added element {record.element_id}")


@element_app.command("list")
def element_list(type_name: Optional[str] = typer.Option(None, "--type", help="Filter by element type.")) -> None:
    root = project_root()
    records = list_element_records(root, type_name=type_name)
    table = Table(title="Elements")
    table.add_column("ID")
    table.add_column("Type")
    table.add_column("Name")
    table.add_column("Aliases")
    table.add_column("Tags")
    for record in records:
        table.add_row(
            record.element_id,
            record.type_name,
            record.name,
            ", ".join(record.aliases),
            ", ".join(record.tags),
        )
    console.print(table)


@element_app.command("show")
def element_show(element_ref: str = typer.Argument(..., help="Element id or name.")) -> None:
    root = project_root()
    record = get_element(root, element_ref)
    data = {
        "id": record.element_id,
        "type": record.type_name,
        "name": record.name,
        "aliases": record.aliases,
        "tags": record.tags,
        "notes": record.notes,
        "relations": record.relations,
    }
    console.print(Panel(_yaml_dump(data), title="Element", border_style="cyan"))


@element_alias_app.command("add")
def element_alias_add(
    element_ref: str = typer.Argument(..., help="Element id or name."),
    alias: str = typer.Argument(..., help="Alias text."),
) -> None:
    root = project_root()
    record = add_alias(root, element_ref, alias)
    console.print(f"Added alias to {record.element_id}")


@element_app.command("relate")
def element_relate(
    source: str = typer.Argument(..., help="Source element id or name."),
    target: str = typer.Argument(..., help="Target element id or name."),
    relation_type: str = typer.Option(..., "--type", help="Relation type."),
) -> None:
    root = project_root()
    record = add_relation(root, source, target, relation_type)
    console.print(f"Added relation for {record.element_id}")


@element_app.command("appears-in")
def element_appears_in(element_ref: str = typer.Argument(..., help="Element id or name.")) -> None:
    root = project_root()
    matches = appears_in(root, element_ref)
    table = Table(title="Element Appearances")
    table.add_column("Part")
    table.add_column("Chapter")
    table.add_column("Path")
    for chapter in matches:
        table.add_row(chapter.part, chapter.title, str(chapter.path.relative_to(root)))
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


def _print_counter_table(title: str, data: dict[str, int], value_header: str = "Count") -> None:
    table = Table(title=title)
    table.add_column("Name")
    table.add_column(value_header, justify="right")
    for name, value in sorted(data.items()):
        table.add_row(name, str(value))
    console.print(table)
