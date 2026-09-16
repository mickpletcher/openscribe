from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from openscribe.ai import (
    AIConfigurationError,
    load_ai_settings,
    run_ai_task,
    summarize_text,
)
from openscribe.ai import (
    requires_data_transfer_consent as ai_requires_data_transfer_consent,
)
from openscribe.board import (
    add_chapter_link,
    add_link,
    add_note,
    apply_board_outline,
    auto_layout,
    list_notes,
    move_note,
    outline_plan_text,
    plan_board_outline,
    promote_note_to_chapter,
    remove_chapter_link,
    render_board,
    set_group,
)
from openscribe.compile import PROFILE_PRESETS, CompileError, assemble_manuscript_text, compile_project
from openscribe.elements import (
    add_alias,
    add_element,
    add_relation,
    appears_in,
    batch_update_elements,
    get_element,
    list_element_records,
    remove_relation,
    update_element,
)
from openscribe.index import index_is_current, load_project_index, rebuild_project_index
from openscribe.migrations import MigrationError, migrate_project, plan_project_migration
from openscribe.project import (
    SceneOperation,
    add_scene,
    add_screenplay_scene,
    apply_scene_operation,
    batch_update_chapters,
    built_in_templates,
    chapter_deadline_status,
    chapter_report,
    create_chapter,
    create_conference_materials,
    create_nonfiction_section,
    create_part,
    create_research_paper_structure,
    create_source_note,
    create_story_idea,
    ensure_citation_tracking_files,
    find_chapter,
    find_chapters,
    find_scenes,
    find_story_idea,
    import_conference_schedule,
    import_folder_project,
    init_project_from_template,
    insert_citation_reference,
    list_chapters,
    list_source_notes,
    list_story_ideas,
    load_part_metadata,
    load_project_config,
    open_in_editor,
    plan_merge_scene,
    plan_reorder_scene,
    plan_split_scene,
    project_root,
    reorder_chapter,
    reorder_part,
    resolve_editor_target,
    save_project_template,
    scene_operation_diff,
    scene_report,
    strip_scene_markers,
    template_library_path,
    update_chapter_metadata,
    update_goals,
    update_part_title,
    update_research_compile_settings,
)
from openscribe.proofreading import (
    LanguageToolError,
    check_text,
    line_and_column,
    load_languagetool_settings,
)
from openscribe.proofreading import (
    requires_data_transfer_consent as proofreading_requires_data_transfer_consent,
)
from openscribe.snapshots import (
    create_snapshot,
    diff_snapshot,
    list_snapshots,
    preview_snapshot_restore,
    restore_snapshot,
)
from openscribe.tui import OpenScribeApp

app = typer.Typer(help="CLI and TUI writing environment for long form projects.")
new_app = typer.Typer(help="Create manuscript content.")
ai_app = typer.Typer(help="Optional AI helpers for manuscript work.")
proofread_app = typer.Typer(help="LanguageTool grammar and style checks.")
set_app = typer.Typer(help="Update project metadata.")
show_app = typer.Typer(help="Show project metadata.")
find_app = typer.Typer(help="Find project content.")
report_app = typer.Typer(help="Project reports.")
board_app = typer.Typer(help="Board mode workflows.")
board_note_app = typer.Typer(help="Board note workflows.")
board_link_app = typer.Typer(help="Board link workflows.")
board_chapter_app = typer.Typer(help="Board note to chapter link workflows.")
board_group_app = typer.Typer(help="Board grouping workflows.")
board_layout_app = typer.Typer(help="Board layout workflows.")
element_app = typer.Typer(help="Element and relation workflows.")
element_alias_app = typer.Typer(help="Element alias workflows.")
idea_app = typer.Typer(help="Story idea workflows.")
snapshot_app = typer.Typer(help="Snapshot workflows.")
index_app = typer.Typer(help="Derived index workflows.")
template_app = typer.Typer(help="Project template workflows.")
import_app = typer.Typer(help="Import workflows.")
workflow_app = typer.Typer(help="Format specific workflow helpers.")
move_app = typer.Typer(help="Reordering workflows.")
scene_app = typer.Typer(help="Previewable scene restructuring workflows.")
migrate_app = typer.Typer(help="Project format migration workflows.")
word_app = typer.Typer(help="Previewable local Word round trips.")
open_app = typer.Typer(help="Open project files in your editor.")
app.add_typer(new_app, name="new")
app.add_typer(ai_app, name="ai")
app.add_typer(proofread_app, name="proofread")
app.add_typer(set_app, name="set")
app.add_typer(show_app, name="show")
app.add_typer(find_app, name="find")
app.add_typer(report_app, name="report")
app.add_typer(board_app, name="board")
app.add_typer(element_app, name="element")
app.add_typer(idea_app, name="idea")
app.add_typer(snapshot_app, name="snapshot")
app.add_typer(index_app, name="index")
app.add_typer(template_app, name="template")
app.add_typer(import_app, name="import")
app.add_typer(workflow_app, name="workflow")
app.add_typer(move_app, name="move")
app.add_typer(scene_app, name="scene")
app.add_typer(migrate_app, name="migrate")
app.add_typer(word_app, name="word")


@word_app.command("export")
def word_export(output: Path = typer.Option(..., "--output")) -> None:
    from openscribe.word import export_word

    try:
        console.print(f"Round-trip export: {export_word(project_root(), output)}")
    except (OSError, RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@word_app.command("bridge")
def word_bridge(
    port: int = typer.Option(0, "--port", min=0, max=65535),
    certificate: Path | None = typer.Option(None, "--certificate"),
    key: Path | None = typer.Option(None, "--key"),
    manifest: Path | None = typer.Option(None, "--manifest", help="Write a sideload manifest for an HTTPS bridge."),
) -> None:
    from openscribe.word_bridge import WordBridge, write_addin_manifest

    try:
        with WordBridge(project_root(), port, certificate=certificate, key=key) as bridge:
            if manifest:
                write_addin_manifest(bridge, manifest)
            console.print(f"Local Word bridge: {bridge.origin}")
            console.print(f"Session token: {bridge.token}")
            console.print("Keep this token private. Ctrl+C stops the bridge. The task pane requires HTTPS.")
            bridge.serve_forever()
    except KeyboardInterrupt:
        console.print("Word bridge stopped.")
    except (OSError, RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@word_app.command("import")
def word_import(document: Path, apply: bool = typer.Option(False, "--apply")) -> None:
    from openscribe.word import apply_word_import, preview_word_import

    root = project_root()
    try:
        plan = preview_word_import(root, document.read_bytes())
        for review in plan.reviews:
            console.print(f"{review.identity}: {review.status}")
        console.print(f"Unresolved tracked changes: {plan.tracked_changes}")
        if plan.diff:
            console.print(Syntax(plan.diff, "diff"))
        for warning in plan.warnings:
            console.print(warning)
        if apply:
            backup = apply_word_import(root, plan)
            console.print(f"Applied. Backup: {backup}" if backup else "No changes to apply.")
        else:
            console.print("Preview only. Use --apply after reviewing the changes.")
    except (OSError, RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command("desktop")
def desktop(project: Path | None = typer.Option(None, "--project", help="Project folder to open.")) -> None:
    if getattr(sys, "frozen", False):
        packaged_desktop = Path(sys.executable).with_name("OpenScribe.exe")
        if packaged_desktop.is_file():
            arguments = [str(packaged_desktop)]
            if project is not None:
                arguments.extend(["--project", str(project)])
            subprocess.Popen(arguments)
            return
    try:
        from openscribe.desktop import launch
    except ImportError as exc:
        raise typer.BadParameter("Install the desktop extra: pip install 'openscribe[desktop]'.") from exc
    launch(project)
app.add_typer(open_app, name="open")
board_app.add_typer(board_note_app, name="note")
board_app.add_typer(board_link_app, name="link")
board_app.add_typer(board_chapter_app, name="chapter")
board_app.add_typer(board_group_app, name="group")
board_app.add_typer(board_layout_app, name="layout")
element_app.add_typer(element_alias_app, name="alias")
console = Console()


@app.command()
def init(
    title: str = typer.Argument(..., help="Project title."),
    path: Path = typer.Option(Path("."), "--path", help="Target directory."),
    template_name: str = typer.Option(
        "fiction",
        "--template",
        help="Project template. Use fiction, nonfiction, technical, screenwriting, or research.",
    ),
    template_file: Path | None = typer.Option(None, "--template-file", help="Path to a user defined template file."),
) -> None:
    project_path = init_project_from_template(path, title, template_name=template_name, template_file=template_file)
    console.print(f"Initialized openscribe project at {project_path}")


@new_app.command("part")
def new_part(title: str = typer.Argument(..., help="Part title.")) -> None:
    root = project_root()
    part_path = create_part(root, title)
    console.print(f"Created part {part_path.name}")


@new_app.command("chapter")
def new_chapter(
    title: str = typer.Argument(..., help="Chapter title."),
    part: str | None = typer.Option(None, "--part", help="Part name or slug."),
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


@new_app.command("scene")
def new_scene(
    title: str = typer.Argument(..., help="Scene title."),
    chapter: str = typer.Option(..., "--chapter", help="Chapter title or slug."),
    body: str = typer.Option("", "--body", help="Optional scene body text."),
) -> None:
    root = project_root()
    chapter_path = add_scene(root, chapter, title, body=body)
    console.print(f"Added scene to {chapter_path.relative_to(root)}")


@new_app.command("section")
def new_section(
    title: str = typer.Argument(..., help="Section title."),
    part: str | None = typer.Option(None, "--part", help="Part name or slug."),
    synopsis: str = typer.Option("", "--synopsis", help="Section synopsis."),
    notes: str = typer.Option("", "--notes", help="Section notes."),
) -> None:
    root = project_root()
    chapter_path = create_nonfiction_section(root, title, part=part, synopsis=synopsis, notes=notes)
    console.print(f"Created section {chapter_path.relative_to(root)}")


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
def outliner(
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    label: str | None = typer.Option(None, "--label", help="Filter by label."),
    pov: str | None = typer.Option(None, "--pov", help="Filter by point of view."),
    part: str | None = typer.Option(None, "--part", help="Filter by part title or slug."),
) -> None:
    root = project_root()
    chapters = find_chapters(root, status=status, label=label, pov=pov, part=part)
    config = load_project_config(root)
    console.print(f"Project: {config.get('title', 'Untitled Project')}")
    current_part_id = None
    part_total_words = 0
    part_total_scenes = 0
    part_title = ""

    for chapter in [*chapters, None]:
        if chapter is None or chapter.part_id != current_part_id:
            if current_part_id is not None:
                console.print(f"  Part Total Words: {part_total_words}")
                console.print(f"  Part Total Scenes: {part_total_scenes}")
                console.print("")
            if chapter is None:
                break
            current_part_id = chapter.part_id
            part_total_words = 0
            part_total_scenes = 0
            part_title = chapter.part
            console.print(f"{part_title}")
        part_total_words += chapter.word_count
        part_total_scenes += chapter.scene_count
        console.print(
            f"  {chapter.title} | status={chapter.status} | label={chapter.label} | pov={chapter.pov or 'n/a'} | "
            f"words={chapter.word_count} | target={chapter.word_target or 0} | scenes={chapter.scene_count}"
        )
        if chapter.synopsis:
            console.print(f"    Synopsis: {chapter.synopsis}")
        if chapter.scenes:
            console.print(f"    Scenes: {', '.join(scene.title for scene in chapter.scenes)}")


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
    format_name: str | None = typer.Option(None, "--format", help="Output format. Use docx, pdf, or epub."),
    profile_name: str | None = typer.Option(
        None, "--profile", help="Compile profile. Use print, ebook, submission, or research-paper."
    ),
    template_name: str | None = typer.Option(
        None, "--template", help="Compile template. Use novel, manuscript, minimal, or academic."
    ),
    output: Path | None = typer.Option(None, "--output", help="Output document path."),
) -> None:
    root = project_root()
    try:
        output_path = compile_project(root, format_name, profile_name, template_name, output)
    except CompileError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"Compiled manuscript to {output_path}")


@app.command()
def read(
    template_name: str | None = typer.Option(
        None, "--template", help="Reading template. Use novel, manuscript, or minimal."
    ),
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
    title: str | None = typer.Option(None, "--title", help="New chapter title."),
    status: str | None = typer.Option(None, "--status", help="New status."),
    label: str | None = typer.Option(None, "--label", help="New label."),
    synopsis: str | None = typer.Option(None, "--synopsis", help="New synopsis."),
    pov: str | None = typer.Option(None, "--pov", help="New point of view."),
    word_target: int | None = typer.Option(None, "--word-target", help="New word target."),
    notes: str | None = typer.Option(None, "--notes", help="New notes."),
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


@set_app.command("goals")
def set_goals(
    draft_word_target: int | None = typer.Option(None, "--draft-word-target", help="Project draft word target."),
    session_word_target: int | None = typer.Option(None, "--session-word-target", help="Session writing target."),
    deadline: str | None = typer.Option(None, "--deadline", help="Project deadline text."),
) -> None:
    root = project_root()
    config_path = update_goals(
        root,
        draft_word_target=draft_word_target,
        session_word_target=session_word_target,
        deadline=deadline,
    )
    console.print(f"Updated project goals at {config_path.relative_to(root)}")


@set_app.command("compile-research")
def set_compile_research(
    citation_style: str | None = typer.Option(
        None, "--citation-style", help="Citation style such as APA, MLA, or Chicago."
    ),
    include_bibliography: bool | None = typer.Option(
        None, "--include-bibliography/--no-include-bibliography", help="Toggle bibliography output."
    ),
    include_reference_heading: bool | None = typer.Option(
        None, "--include-reference-heading/--no-include-reference-heading", help="Toggle the bibliography heading."
    ),
    bibliography_title: str | None = typer.Option(None, "--bibliography-title", help="Bibliography section title."),
) -> None:
    root = project_root()
    config_path = update_research_compile_settings(
        root,
        citation_style=citation_style,
        include_bibliography=include_bibliography,
        include_reference_heading=include_reference_heading,
        bibliography_title=bibliography_title,
    )
    console.print(f"Updated research compile settings at {config_path.relative_to(root)}")


@set_app.command("chapters")
def set_chapters(
    match_status: str | None = typer.Option(None, "--match-status", help="Match status."),
    match_label: str | None = typer.Option(None, "--match-label", help="Match label."),
    match_pov: str | None = typer.Option(None, "--match-pov", help="Match point of view."),
    match_part: str | None = typer.Option(None, "--match-part", help="Match part title or slug."),
    match_text: str | None = typer.Option(None, "--match-text", help="Match text in title, synopsis, notes, or body."),
    title: str | None = typer.Option(None, "--title", help="New chapter title."),
    status: str | None = typer.Option(None, "--status", help="New status."),
    label: str | None = typer.Option(None, "--label", help="New label."),
    synopsis: str | None = typer.Option(None, "--synopsis", help="New synopsis."),
    pov: str | None = typer.Option(None, "--pov", help="New point of view."),
    word_target: int | None = typer.Option(None, "--word-target", help="New word target."),
    notes: str | None = typer.Option(None, "--notes", help="New notes."),
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
        "chapter_id": document.chapter_id,
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
        "scene_count": document.scene_count,
        "scenes": [scene.title for scene in document.scenes],
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
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    label: str | None = typer.Option(None, "--label", help="Filter by label."),
    pov: str | None = typer.Option(None, "--pov", help="Filter by point of view."),
    part: str | None = typer.Option(None, "--part", help="Filter by part title or slug."),
    text: str | None = typer.Option(None, "--text", help="Search title, synopsis, notes, and body text."),
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


@find_app.command("scenes")
def find_scene_matches(
    status: str | None = typer.Option(None, "--status", help="Filter chapter status."),
    label: str | None = typer.Option(None, "--label", help="Filter chapter label."),
    pov: str | None = typer.Option(None, "--pov", help="Filter chapter point of view."),
    part: str | None = typer.Option(None, "--part", help="Filter by part title or slug."),
    text: str | None = typer.Option(None, "--text", help="Search scene title, scene body, and chapter context."),
) -> None:
    root = project_root()
    matches = find_scenes(root, status=status, label=label, pov=pov, part=part, text=text)
    table = Table(title="Scene Matches")
    table.add_column("Part")
    table.add_column("Chapter")
    table.add_column("Scene")
    table.add_column("Preview")
    for match in matches:
        table.add_row(match.part, match.chapter_title, match.scene_title, " ".join(match.scene_body.split())[:60])
    console.print(table)
    console.print(f"Matches: {len(matches)}")


@report_app.command("project")
def report_project() -> None:
    root = project_root()
    summary = chapter_report(root)
    console.print(f"Chapters: {summary['chapter_count']}")
    console.print(f"Scenes: {summary['scene_count']}")
    console.print(f"Words: {summary['word_count']}")
    console.print(f"Index current: {index_is_current(root)}")
    console.print(f"Draft target: {summary['goals']['draft_word_target']}")
    console.print(f"Session target: {summary['goals']['session_word_target']}")
    console.print(f"Deadline: {summary['goals']['deadline'] or 'n/a'}")
    deadline_status = chapter_deadline_status(root)
    if deadline_status["days_remaining"] is not None:
        console.print(f"Days remaining: {deadline_status['days_remaining']}")
    console.print(f"Progress: {summary['goals']['progress_percent']}%")

    _print_counter_table("By Status", summary["by_status"])
    _print_counter_table("By Label", summary["by_label"])
    _print_counter_table("By POV", summary["by_pov"])
    _print_counter_table("By Part", summary["by_part"])
    _print_counter_table("Part Word Totals", summary["part_word_totals"], value_header="Words")
    _print_counter_table("Scene Titles", summary["scene_title_counts"])


@report_app.command("scenes")
def report_scenes(
    text: str | None = typer.Option(None, "--text", help="Optional scene text filter."),
) -> None:
    root = project_root()
    summary = scene_report(root, text=text)
    console.print(f"Scene matches: {summary['scene_matches']}")
    _print_counter_table("Scenes By Chapter", summary["by_chapter"])
    _print_counter_table("Scenes By Part", summary["by_part"])


@index_app.command("rebuild")
def index_rebuild() -> None:
    root = project_root()
    path = rebuild_project_index(root)
    console.print(f"Rebuilt project index at {path.relative_to(root)}")


@index_app.command("show")
def index_show() -> None:
    root = project_root()
    data = load_project_index(root)
    console.print(Panel(_yaml_dump(data), title="Project Index", border_style="cyan"))


@index_app.command("search")
def index_search(text: str = typer.Argument(..., help="Search text.")) -> None:
    root = project_root()
    if not index_is_current(root):
        raise typer.BadParameter("Project index is missing or stale. Run `openscribe index rebuild`.")
    data = load_project_index(root)
    needle = text.strip().lower()
    table = Table(title="Index Search")
    table.add_column("Kind")
    table.add_column("Title")
    table.add_column("Path")

    matches = 0
    for chapter in data.get("chapters", []):
        haystack = str(chapter.get("search_text", "")).lower()
        if needle in haystack:
            table.add_row("chapter", str(chapter.get("title", "")), str(chapter.get("path", "")))
            matches += 1

    for bucket_name in ("story_ideas", "characters", "research", "notes"):
        for item in data.get(bucket_name, []):
            haystack = f"{item.get('title', '')} {item.get('path', '')}".lower()
            if needle in haystack:
                table.add_row(bucket_name.rstrip("s"), str(item.get("title", "")), str(item.get("path", "")))
                matches += 1

    console.print(table)
    console.print(f"Matches: {matches}")


@snapshot_app.command("save")
def snapshot_save(
    label: str = typer.Argument(..., help="Snapshot label."),
    mode: str = typer.Option("checkpoint", "--mode", help="Snapshot mode. Use checkpoint or git."),
) -> None:
    root = project_root()
    path = create_snapshot(root, label, mode=mode)
    console.print(f"Created snapshot at {path.relative_to(root)}")


@snapshot_app.command("list")
def snapshot_list() -> None:
    root = project_root()
    records = list_snapshots(root)
    table = Table(title="Snapshots")
    table.add_column("Label")
    table.add_column("Mode")
    table.add_column("Created")
    table.add_column("Path")
    for record in records:
        table.add_row(
            str(record.get("label", "")),
            str(record.get("mode", "")),
            str(record.get("created_at", "")),
            str(record.get("path", "")),
        )
    console.print(table)
    console.print(f"Snapshots: {len(records)}")


@snapshot_app.command("restore")
def snapshot_restore(
    snapshot_ref: str = typer.Argument(..., help="Snapshot folder name or partial match."),
    apply: bool = typer.Option(False, "--apply", help="Apply the exact restore after reviewing the preview."),
) -> None:
    root = project_root()
    preview = preview_snapshot_restore(root, snapshot_ref)
    _print_restore_preview(preview)
    if not apply:
        console.print("Preview only. Run again with --apply to restore this exact state.")
        return
    result = restore_snapshot(root, snapshot_ref)
    console.print(f"Restored snapshot {result.snapshot_path.relative_to(root)}")
    console.print(f"Automatic backup: {result.backup_path.relative_to(root)}")


@snapshot_app.command("diff")
def snapshot_diff(snapshot_ref: str = typer.Argument(..., help="Snapshot folder name or partial match.")) -> None:
    root = project_root()
    console.print(diff_snapshot(root, snapshot_ref))


@app.command("templates")
def templates_list() -> None:
    table = Table(title="Project Templates")
    table.add_column("Template")
    table.add_column("Compile Default")
    for name, template in sorted(built_in_templates().items()):
        table.add_row(name, str(template["compile"].get("default_template", "")))
    try:
        root = project_root()
        for path in sorted(template_library_path(root).glob("*.yaml")):
            table.add_row(path.stem, "user-defined")
    except FileNotFoundError:
        pass
    console.print(table)
    profile_table = Table(title="Compile Profiles")
    profile_table.add_column("Profile")
    profile_table.add_column("Format")
    profile_table.add_column("Template")
    for name, profile in sorted(PROFILE_PRESETS.items()):
        profile_table.add_row(name, str(profile.get("format_name", "")), str(profile.get("template_name", "")))
    console.print(profile_table)


@template_app.command("save")
def template_save(name: str = typer.Argument(..., help="Template name.")) -> None:
    root = project_root()
    path = save_project_template(root, name)
    console.print(f"Saved project template to {path.relative_to(root)}")


@workflow_app.command("screenplay-scene")
def workflow_screenplay_scene(
    slugline: str = typer.Argument(..., help="Screenplay slugline, for example INT. KITCHEN - NIGHT."),
    chapter: str = typer.Option(..., "--chapter", help="Chapter title or slug."),
    body: str = typer.Option("", "--body", help="Optional scene body text."),
) -> None:
    root = project_root()
    chapter_path = add_screenplay_scene(root, chapter, slugline, body=body)
    console.print(f"Added screenplay scene to {chapter_path.relative_to(root)}")


@workflow_app.command("nonfiction-section")
def workflow_nonfiction_section(
    title: str = typer.Argument(..., help="Section title."),
    part: str | None = typer.Option(None, "--part", help="Part title or slug."),
    synopsis: str = typer.Option("", "--synopsis", help="Section synopsis."),
    notes: str = typer.Option("", "--notes", help="Section notes."),
) -> None:
    root = project_root()
    chapter_path = create_nonfiction_section(root, title, part=part, synopsis=synopsis, notes=notes)
    console.print(f"Created nonfiction section {chapter_path.relative_to(root)}")


@workflow_app.command("research-paper")
def workflow_research_paper(
    part: str = typer.Option("Paper", "--part", help="Part title for the paper structure."),
    include_appendix: bool = typer.Option(False, "--include-appendix", help="Add an appendix section."),
) -> None:
    root = project_root()
    chapter_paths = create_research_paper_structure(root, part=part, include_appendix=include_appendix)
    console.print(f"Created research paper sections: {len(chapter_paths)}")
    for path in chapter_paths:
        console.print(str(path.relative_to(root)))


@workflow_app.command("conference-materials")
def workflow_conference_materials(
    title: str = typer.Argument(..., help="Conference submission or talk title."),
    venue: str = typer.Option("", "--venue", help="Conference or venue name."),
    include_poster: bool = typer.Option(True, "--include-poster/--no-poster", help="Create poster support files."),
) -> None:
    root = project_root()
    paths = create_conference_materials(root, title, venue=venue, include_poster=include_poster)
    console.print(f"Created conference materials: {len(paths)}")
    for path in paths:
        console.print(str(path.relative_to(root)))


@workflow_app.command("conference-schedule-import")
def workflow_conference_schedule_import(
    schedule_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Conference schedule file. Use csv, tsv, json, yaml, or yml.",
    ),
    venue: str = typer.Option("", "--venue", help="Conference or venue name override."),
    create_checklists: bool = typer.Option(
        True, "--create-checklists/--no-create-checklists", help="Create session checklist files."
    ),
) -> None:
    root = project_root()
    try:
        paths = import_conference_schedule(root, schedule_path, venue=venue, create_checklists=create_checklists)
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"Imported conference schedule: {len(paths)}")
    for path in paths:
        console.print(str(path.relative_to(root)))


@workflow_app.command("source-note")
def workflow_source_note(
    title: str = typer.Argument(..., help="Source title."),
    source_type: str = typer.Option(
        "article", "--type", help="Source type, for example article, book, web, or interview."
    ),
    author: str = typer.Option("", "--author", help="Source author."),
    year: str = typer.Option("", "--year", help="Source year."),
    url: str = typer.Option("", "--url", help="Source URL."),
    notes: str = typer.Option("", "--notes", help="Initial notes."),
) -> None:
    root = project_root()
    path = create_source_note(
        root,
        title,
        source_type=source_type,
        author=author,
        year=year,
        url=url,
        notes=notes,
    )
    console.print(f"Created source note {path.relative_to(root)}")


@workflow_app.command("citation-pack")
def workflow_citation_pack(
    style: str = typer.Option("APA", "--style", help="Citation style, for example APA, MLA, Chicago, or IEEE."),
) -> None:
    root = project_root()
    paths = ensure_citation_tracking_files(root, style=style)
    console.print(f"Created citation tracking files: {len(paths)}")
    for path in paths:
        console.print(str(path.relative_to(root)))
    existing_sources = list_source_notes(root)
    if existing_sources:
        console.print(f"Tracked sources: {len(existing_sources)}")


@workflow_app.command("cite")
def workflow_cite(
    chapter: str = typer.Option(..., "--chapter", help="Chapter title or slug."),
    source: str = typer.Option(..., "--source", help="Source title or slug."),
    scene: str | None = typer.Option(None, "--scene", help="Optional scene title or slug."),
    style: str = typer.Option("APA", "--style", help="Citation style text."),
) -> None:
    root = project_root()
    path = insert_citation_reference(root, chapter, source, scene_ref=scene, citation_style=style)
    console.print(f"Inserted citation into {path.relative_to(root)}")


@import_app.command("folder")
def import_folder(
    source_path: Path = typer.Argument(..., help="Existing folder based manuscript path."),
    title: str = typer.Option(..., "--title", help="Imported project title."),
    template_name: str = typer.Option("fiction", "--template", help="Project template to initialize first."),
    template_file: Path | None = typer.Option(None, "--template-file", help="Path to a user defined template file."),
    path: Path = typer.Option(Path("."), "--path", help="Target directory for the imported project."),
) -> None:
    project_path = import_folder_project(
        path, source_path, title, template_name=template_name, template_file=template_file
    )
    console.print(f"Imported project to {project_path}")


@move_app.command("part")
def move_part(
    part: str = typer.Argument(..., help="Part title or slug."),
    position: int = typer.Option(..., "--position", help="New 1 based position."),
) -> None:
    root = project_root()
    parts = reorder_part(root, part, position)
    console.print(f"Moved part to position {position}")
    for index, part_path in enumerate(parts, start=1):
        console.print(f"{index}. {load_part_metadata(root, part_path.name)['title']}")


@move_app.command("chapter")
def move_chapter(
    chapter: str = typer.Argument(..., help="Chapter title or slug."),
    position: int = typer.Option(..., "--position", help="New 1 based position in the target part."),
    part: str | None = typer.Option(None, "--part", help="Optional target part title or slug."),
) -> None:
    root = project_root()
    chapters = reorder_chapter(root, chapter, position, part=part)
    console.print(f"Moved chapter to position {position}")
    for index, chapter_path in enumerate(chapters, start=1):
        console.print(f"{index}. {chapter_path.name}")


@scene_app.command("move")
def scene_move(
    scene: str = typer.Argument(..., help="Scene ID, title, or slug."),
    chapter: str = typer.Option(..., "--chapter", help="Source chapter title, ID, or slug."),
    position: int = typer.Option(..., "--position", help="New 1 based scene position."),
    to_chapter: str | None = typer.Option(None, "--to-chapter", help="Optional target chapter."),
    apply: bool = typer.Option(False, "--apply", help="Apply the previewed scene move."),
) -> None:
    root = project_root()
    try:
        operation = plan_reorder_scene(root, chapter, scene, position, target_chapter_ref=to_chapter)
        _run_scene_operation(root, operation, apply)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@scene_app.command("split")
def scene_split(
    scene: str = typer.Argument(..., help="Scene ID, title, or slug."),
    chapter: str = typer.Option(..., "--chapter", help="Chapter title, ID, or slug."),
    at_text: str = typer.Option(..., "--at-text", help="Text that starts the new scene."),
    new_title: str = typer.Option(..., "--new-title", help="Title for the new scene."),
    apply: bool = typer.Option(False, "--apply", help="Apply the previewed scene split."),
) -> None:
    root = project_root()
    try:
        operation = plan_split_scene(root, chapter, scene, at_text, new_title)
        _run_scene_operation(root, operation, apply)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@scene_app.command("merge")
def scene_merge(
    scene: str = typer.Argument(..., help="Destination scene ID, title, or slug."),
    other_scene: str = typer.Option(..., "--with", help="Scene to consume."),
    chapter: str = typer.Option(..., "--chapter", help="Destination chapter title, ID, or slug."),
    other_chapter: str | None = typer.Option(None, "--other-chapter", help="Optional source chapter."),
    apply: bool = typer.Option(False, "--apply", help="Apply the previewed scene merge."),
) -> None:
    root = project_root()
    try:
        operation = plan_merge_scene(
            root,
            chapter,
            scene,
            other_scene,
            other_chapter_ref=other_chapter,
        )
        _run_scene_operation(root, operation, apply)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@migrate_app.command("status")
def migrate_status() -> None:
    root = project_root()
    try:
        plan = plan_project_migration(root)
    except MigrationError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"Project format: {plan.current_version}. Supported format: {plan.target_version}.")
    if not plan.steps:
        console.print("No migration is required.")
        return
    for step in plan.steps:
        console.print(f"v{step.from_version} -> v{step.to_version}: {step.name}")


@migrate_app.command("apply")
def migrate_apply() -> None:
    root = project_root()
    try:
        result = migrate_project(root)
    except MigrationError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if not result.plan.steps:
        console.print("No migration is required.")
        return
    console.print(
        f"Migrated project from v{result.plan.current_version} to v{result.plan.target_version}. "
        f"Backup: {result.backup_path.relative_to(root) if result.backup_path else 'none'}"
    )


@migrate_app.command("repair")
def migrate_repair() -> None:
    from openscribe.migrations import repair_project_identities

    root = project_root()
    try:
        backup = repair_project_identities(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"Repaired missing or malformed IDs and legacy board links. Backup: {backup.relative_to(root)}")


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
def board_note_list(group: str | None = typer.Option(None, "--group", help="Filter by group.")) -> None:
    root = project_root()
    notes = list_notes(root)
    table = Table(title="Board Notes")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Group")
    table.add_column("Links")
    table.add_column("Chapters")
    table.add_column("Body")
    for note in notes:
        if group and note.group.strip().lower() != group.strip().lower():
            continue
        table.add_row(
            note.note_id,
            note.title,
            note.group or "",
            ", ".join(note.links),
            ", ".join(note.chapter_links),
            note.body or "",
        )
    console.print(table)


@board_note_app.command("move")
def board_note_move(
    note_id: str = typer.Argument(..., help="Board note id."),
    x: int = typer.Option(..., "--x", help="New x position."),
    y: int = typer.Option(..., "--y", help="New y position."),
) -> None:
    root = project_root()
    move_note(root, note_id, x, y)
    console.print(f"Moved {note_id} to ({x}, {y})")


@board_link_app.command("add")
def board_link_add(
    from_id: str = typer.Argument(..., help="Source note id."),
    to_id: str = typer.Argument(..., help="Target note id."),
) -> None:
    root = project_root()
    add_link(root, from_id, to_id)
    console.print(f"Linked {from_id} to {to_id}")


@board_chapter_app.command("add")
def board_chapter_link_add(
    note_id: str = typer.Argument(..., help="Board note id."),
    chapter: str = typer.Argument(..., help="Chapter title or slug."),
) -> None:
    root = project_root()
    chapter_doc = find_chapter(root, chapter)
    note = add_chapter_link(root, note_id, chapter_doc.chapter_id)
    console.print(f"Linked {note.note_id} to chapter {chapter_doc.title}")


@board_chapter_app.command("remove")
def board_chapter_link_remove(
    note_id: str = typer.Argument(..., help="Board note id."),
    chapter: str = typer.Argument(..., help="Chapter title or slug."),
) -> None:
    root = project_root()
    chapter_doc = find_chapter(root, chapter)
    note = remove_chapter_link(root, note_id, chapter_doc.chapter_id)
    console.print(f"Removed chapter link from {note.note_id}")


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
    chapter: str | None = typer.Option(None, "--chapter", help="New chapter title."),
    part: str | None = typer.Option(None, "--part", help="Target part title or slug."),
) -> None:
    root = project_root()
    note_title = next((note.title for note in list_notes(root) if note.note_id == note_id), note_id)
    chapter_path = promote_note_to_chapter(root, note_id, chapter_title=chapter, part=part)
    promoted_title = chapter or note_title
    console.print(f"Promoted board note into chapter {promoted_title} at {chapter_path.relative_to(root)}")


@board_layout_app.command("auto")
def board_layout_auto(
    column_width: int = typer.Option(22, "--column-width", help="Column width for the auto layout."),
) -> None:
    root = project_root()
    auto_layout(root, column_width=column_width)
    console.print("Applied board auto layout")


@board_app.command("view")
def board_view(
    width: int = typer.Option(72, "--width", help="Board canvas width."),
    height: int = typer.Option(18, "--height", help="Board canvas height."),
) -> None:
    root = project_root()
    console.print(Panel(render_board(root, width=width, height=height), title="Board View", border_style="cyan"))


@board_app.command("outline")
def board_outline(apply: bool = typer.Option(False, "--apply", help="Create parts and chapters from the preview.")) -> None:
    root = project_root()
    plan = plan_board_outline(root)
    console.print(Panel(outline_plan_text(plan), title="Brainstorming Outline", border_style="cyan"))
    if not apply:
        console.print("Preview only. Use --apply after reviewing the outline.")
        return
    backup, created = apply_board_outline(root, plan)
    console.print(f"Created outline chapters: {len(created)}")
    console.print(f"Backup: {backup.relative_to(root)}")


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
def element_list(type_name: str | None = typer.Option(None, "--type", help="Filter by element type.")) -> None:
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


@element_app.command("set")
def element_set(
    element_ref: str = typer.Argument(..., help="Element id or name."),
    name: str | None = typer.Option(None, "--name", help="New element name."),
    notes: str | None = typer.Option(None, "--notes", help="New element notes."),
    tags: str | None = typer.Option(None, "--tags", help="Comma separated tags."),
) -> None:
    root = project_root()
    tag_values = None if tags is None else [value.strip() for value in tags.split(",") if value.strip()]
    record = update_element(root, element_ref, name=name, notes=notes, tags=tag_values)
    console.print(f"Updated element {record.element_id}")


@element_app.command("set-many")
def element_set_many(
    match_type: str | None = typer.Option(None, "--match-type", help="Match element type."),
    match_tag: str | None = typer.Option(None, "--match-tag", help="Match an existing tag."),
    match_text: str | None = typer.Option(None, "--match-text", help="Match text in name, aliases, tags, or notes."),
    notes: str | None = typer.Option(None, "--notes", help="Replacement notes."),
    add_tags: str | None = typer.Option(None, "--add-tags", help="Comma separated tags to add."),
) -> None:
    root = project_root()
    updated = batch_update_elements(
        root,
        match_type=match_type,
        match_tag=match_tag,
        match_text=match_text,
        notes=notes,
        add_tags=[value.strip() for value in add_tags.split(",") if value.strip()] if add_tags else None,
    )
    console.print(f"Updated elements: {len(updated)}")


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


@element_app.command("unrelate")
def element_unrelate(
    source: str = typer.Argument(..., help="Source element id or name."),
    target: str = typer.Argument(..., help="Target element id or name."),
    relation_type: str | None = typer.Option(None, "--type", help="Optional relation type to remove."),
) -> None:
    root = project_root()
    record = remove_relation(root, source, target, relation_type)
    console.print(f"Removed relation for {record.element_id}")


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


@open_app.command("chapter")
def open_chapter(chapter: str = typer.Argument(..., help="Chapter title or slug.")) -> None:
    root = project_root()
    path = resolve_editor_target(root, "chapter", chapter)
    open_in_editor(path)
    console.print(f"Opened {path.relative_to(root)}")


@open_app.command("part")
def open_part(part: str = typer.Argument(..., help="Part title or slug.")) -> None:
    root = project_root()
    path = resolve_editor_target(root, "part", part)
    open_in_editor(path)
    console.print(f"Opened {path.relative_to(root)}")


@open_app.command("search")
def open_search(
    text: str = typer.Option(..., "--text", help="Search text."),
    index: int = typer.Option(1, "--index", help="1 based match index."),
) -> None:
    root = project_root()
    path = resolve_editor_target(root, "search", text=text, index=index)
    open_in_editor(path)
    console.print(f"Opened {path.relative_to(root)}")


@proofread_app.command("chapter")
def proofread_chapter(
    chapter: str = typer.Argument(..., help="Chapter title, ID, or slug."),
    language: str | None = typer.Option(None, "--language", help="Override the configured LanguageTool language."),
    allow_data_transfer: bool = typer.Option(
        False,
        "--allow-data-transfer",
        help="Approve sending the complete chapter text to a hosted LanguageTool endpoint.",
    ),
) -> None:
    root = project_root()
    config = load_project_config(root)
    settings = load_languagetool_settings(config)
    document = find_chapter(root, chapter)
    if not document.body.strip():
        raise typer.BadParameter("The chapter body is empty.")

    try:
        if settings.enabled and proofreading_requires_data_transfer_consent(settings) and allow_data_transfer:
            console.print(
                f"Sending {len(document.body)} characters of chapter text to "
                f"hosted LanguageTool endpoint '{settings.endpoint}'."
            )
        result = check_text(
            document.body,
            settings,
            language=language,
            allow_data_transfer=allow_data_transfer,
        )
    except LanguageToolError as exc:
        raise typer.BadParameter(str(exc)) from exc

    table = Table(title=f"LanguageTool: {document.title}")
    table.add_column("Location")
    table.add_column("Rule")
    table.add_column("Category")
    table.add_column("Message")
    table.add_column("Suggestions")
    for issue in result.issues:
        line, column = line_and_column(document.body, issue.offset)
        table.add_row(
            f"{line}:{column}",
            issue.rule_id,
            issue.category,
            issue.message,
            ", ".join(issue.replacements[:5]) or "none",
        )
    if not result.issues:
        table.add_row("", "", "", "No findings.", "")
    console.print(table)
    console.print(
        f"Language: {result.language}. Server version: {result.software_version}. Findings: {len(result.issues)}."
    )
    if result.incomplete_results:
        console.print("LanguageTool reported incomplete results.", style="yellow")


@ai_app.command("summarize")
def ai_summarize(
    chapter: str = typer.Argument(..., help="Chapter title or slug."),
    allow_data_transfer: bool = typer.Option(
        False,
        "--allow-data-transfer",
        help="Approve sending the complete chapter text to a hosted AI provider.",
    ),
) -> None:
    root = project_root()
    config = load_project_config(root)
    settings = load_ai_settings(config)
    document = find_chapter(root, chapter)
    if not document.body.strip():
        raise typer.BadParameter("The chapter body is empty.")

    try:
        if settings.enabled and ai_requires_data_transfer_consent(settings) and allow_data_transfer:
            console.print(
                f"Sending {len(document.body)} characters of chapter text to "
                f"hosted provider '{settings.provider}' using model '{settings.model}'."
            )
        summary = summarize_text(
            document.body,
            settings,
            "chapter",
            allow_data_transfer=allow_data_transfer,
        )
    except AIConfigurationError as exc:
        raise typer.BadParameter(str(exc)) from exc

    console.print(
        Panel(
            summary,
            title=f"AI Summary: {document.title}",
            border_style="cyan",
        )
    )


@ai_app.command("rewrite")
def ai_rewrite(
    chapter: str = typer.Argument(..., help="Chapter title, ID, or slug."),
    allow_data_transfer: bool = typer.Option(False, "--allow-data-transfer"),
) -> None:
    _run_ai_chapter_task(chapter, "rewrite", "AI Rewrite Suggestion", allow_data_transfer)


@ai_app.command("outline")
def ai_outline(
    chapter: str = typer.Argument(..., help="Chapter title, ID, or slug."),
    allow_data_transfer: bool = typer.Option(False, "--allow-data-transfer"),
) -> None:
    _run_ai_chapter_task(chapter, "outline", "AI Outline", allow_data_transfer)


@ai_app.command("analyze")
def ai_analyze(
    chapter: str = typer.Argument(..., help="Chapter title, ID, or slug."),
    focus: str = typer.Option(
        "prose",
        "--focus",
        help="Analysis focus: pacing, continuity, point-of-view, or prose.",
    ),
    allow_data_transfer: bool = typer.Option(False, "--allow-data-transfer"),
) -> None:
    normalized_focus = focus.strip().lower()
    aliases = {"pov": "point-of-view", "point of view": "point-of-view"}
    normalized_focus = aliases.get(normalized_focus, normalized_focus)
    if normalized_focus not in {"pacing", "continuity", "point-of-view", "prose"}:
        raise typer.BadParameter("Focus must be pacing, continuity, point-of-view, or prose.")
    _run_ai_chapter_task(
        chapter,
        normalized_focus,
        f"AI {normalized_focus.title()} Review",
        allow_data_transfer,
    )


@ai_app.command("metadata")
def ai_metadata(
    chapter: str = typer.Argument(..., help="Chapter title, ID, or slug."),
    allow_data_transfer: bool = typer.Option(False, "--allow-data-transfer"),
) -> None:
    _run_ai_chapter_task(chapter, "metadata", "AI Metadata Suggestions", allow_data_transfer)


@ai_app.command("brainstorm")
def ai_brainstorm(
    chapter: str = typer.Argument(..., help="Chapter title, ID, or slug."),
    question: str = typer.Option("Possible next developments", "--question", help="Brainstorming direction."),
    allow_data_transfer: bool = typer.Option(False, "--allow-data-transfer"),
) -> None:
    _run_ai_chapter_task(
        chapter,
        "brainstorm",
        "AI Brainstorm",
        allow_data_transfer,
        question=question,
    )


@ai_app.command("query")
def ai_query(
    question: str = typer.Argument(..., help="Question to answer from the manuscript."),
    allow_data_transfer: bool = typer.Option(False, "--allow-data-transfer"),
) -> None:
    root = project_root()
    chapters = list_chapters(root)
    manuscript_text = "\n\n".join(
        f"# {chapter.title}\n\n{strip_scene_markers(chapter.body).strip()}" for chapter in chapters
    )
    if not manuscript_text.strip():
        raise typer.BadParameter("The project manuscript is empty.")
    _run_ai_task(
        root,
        manuscript_text,
        "project manuscript",
        "query",
        "AI Project Query",
        allow_data_transfer,
        question=question,
    )


def _run_ai_chapter_task(
    chapter_ref: str,
    task: str,
    panel_title: str,
    allow_data_transfer: bool,
    *,
    question: str = "",
) -> None:
    root = project_root()
    document = find_chapter(root, chapter_ref)
    text = strip_scene_markers(document.body)
    if not text.strip():
        raise typer.BadParameter("The chapter body is empty.")
    _run_ai_task(
        root,
        text,
        "chapter",
        task,
        f"{panel_title}: {document.title}",
        allow_data_transfer,
        question=question,
    )


def _run_ai_task(
    root: Path,
    text: str,
    context_label: str,
    task: str,
    panel_title: str,
    allow_data_transfer: bool,
    *,
    question: str = "",
) -> None:
    settings = load_ai_settings(load_project_config(root))
    try:
        if settings.enabled and ai_requires_data_transfer_consent(settings) and allow_data_transfer:
            console.print(
                f"Sending {len(text)} characters of {context_label} text to "
                f"hosted provider '{settings.provider}' using model '{settings.model}'."
            )
        output = run_ai_task(
            text,
            settings,
            context_label,
            task,
            question=question,
            allow_data_transfer=allow_data_transfer,
        )
    except AIConfigurationError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(Panel(output, title=panel_title, border_style="cyan"))


def _yaml_dump(data: dict) -> str:
    import yaml

    return yaml.safe_dump(data, sort_keys=False).strip()


def _run_scene_operation(root: Path, operation: SceneOperation, apply: bool) -> None:
    console.print(Panel(scene_operation_diff(root, operation), title=operation.summary, border_style="cyan"))
    if not apply:
        console.print("Preview only. Rerun with --apply to modify the manuscript.")
        return
    backup_path = apply_scene_operation(root, operation)
    console.print(f"Applied scene operation. Backup: {backup_path.relative_to(root)}")


def _print_restore_preview(preview) -> None:
    table = Table(title="Snapshot Restore Preview")
    table.add_column("Action")
    table.add_column("Path")
    for path in preview.added:
        table.add_row("restore missing", path)
    for path in preview.modified:
        table.add_row("overwrite", path)
    for path in preview.deleted:
        table.add_row("delete", path)
    if not preview.has_changes:
        table.add_row("none", "Project already matches the snapshot")
    console.print(table)


def _print_counter_table(title: str, data: dict[str, int], value_header: str = "Count") -> None:
    table = Table(title=title)
    table.add_column("Name")
    table.add_column(value_header, justify="right")
    for name, value in sorted(data.items()):
        table.add_row(name, str(value))
    console.print(table)
