# North County example project

This folder is a checked in sample `openscribe` project.

Use it when you want to see:

* the folder layout
* project config
* chapter frontmatter
* manuscript ordering
* supporting notes outside the manuscript

## What is included

This example includes:

* `.openscribe/project.yaml`
* one board data file under `.openscribe/boards/`
* one element data file under `.openscribe/elements/`
* one manuscript part
* one `part.yaml` part metadata file
* two chapter files
* one character note
* one research note
* one revision note
* one story idea note

The sample project config also includes compile defaults you can edit to test template, profile, and export behavior.
It also includes scene headings inside the sample chapters so scene level support has real data to inspect.
You can also save user templates from this project and reuse them when you initialize another one.

## How to inspect it

From the repo root:

```powershell
Set-Location .\examples\north-county
py -3.11 -m openscribe outline
py -3.11 -m openscribe report project
py -3.11 -m openscribe index rebuild
py -3.11 -m openscribe index search station
py -3.11 -m openscribe find chapters --text station
py -3.11 -m openscribe find scenes --text station
py -3.11 -m openscribe outliner
py -3.11 -m openscribe outliner --status draft
py -3.11 -m openscribe move chapter "Town Hall" --position 1
py -3.11 -m openscribe compile --profile submission
py -3.11 -m openscribe workflow source-note "County Archive" --type archive --author "Stewart County" --year 1987
py -3.11 -m openscribe workflow citation-pack --style Chicago
py -3.11 -m openscribe workflow cite --chapter "Arrival" --scene "Bus Stop" --source "County Archive" --style Chicago
py -3.11 -m openscribe workflow conference-schedule-import .\energyconf-schedule.csv --venue "EnergyConf"
py -3.11 -m openscribe set compile-research --citation-style Chicago --include-bibliography --bibliography-title "Works Cited"
py -3.11 -m openscribe set goals --draft-word-target 85000 --session-word-target 1200 --deadline 2026-09-01
py -3.11 -m openscribe board note add "Sheriff rumor" --body "A deputy hints the sheriff knew about the ledger." --group plot
py -3.11 -m openscribe board note list
py -3.11 -m openscribe board chapter add note-001 "Arrival"
py -3.11 -m openscribe board layout auto
py -3.11 -m openscribe board view
py -3.11 -m openscribe idea list
py -3.11 -m openscribe show idea "The Flood Ledger"
py -3.11 -m openscribe element add character "Eli Harper" --notes "Primary point of view"
py -3.11 -m openscribe element appears-in Eli
py -3.11 -m openscribe snapshot save "sample-checkpoint"
py -3.11 -m openscribe snapshot diff sample-checkpoint
py -3.11 -m openscribe snapshot restore sample-checkpoint
py -3.11 -m openscribe snapshot restore sample-checkpoint --apply
py -3.11 -m openscribe proofread chapter "Arrival"
py -3.11 -m openscribe open chapter "Arrival"
py -3.11 -m openscribe template save "north-county-custom"
py -3.11 -m openscribe read
py -3.11 -m openscribe status
py -3.11 -m openscribe tui
```

Inside the TUI you can now use the search box to filter chapters, sources, board notes, and library content.
Select a chapter or scene to edit it. Press `Ctrl+S` to save and `Ctrl+G` to run the configured local LanguageTool check.
You can inspect part metadata, open the board canvas section, review corkboard cards, browse source links, use keyboard board note movement with saved positions, and cycle selected chapter metadata from the keyboard.

The board commands store freeform planning notes under `.openscribe/boards/`.

The element commands store element, alias, and relation data under `.openscribe/elements/`.

The source note and citation workflows store nonfiction research support files under `research/sources/` and `research/`.
Citation insertion can target the whole chapter or a named scene section.
Conference schedule import can generate session overview and checklist files from a schedule export.

The goal and deadline settings live in `.openscribe/project.yaml` and show up in `report project` and the TUI.

The story idea commands store structured new book ideas under `notes/story-ideas/`.

The snapshot commands store checkpoint and git based snapshot records under `.openscribe/snapshots/`.
Restore previews by default. `--apply` creates an automatic backup, restores the exact managed state, and removes managed files that were not in the snapshot.

The template commands store saved user templates under `.openscribe/templates/`.

The proofreading command requires a running LanguageTool server and `proofreading.enabled: true` in `.openscribe/project.yaml`. It reports suggestions without editing the chapter.

Scene restructuring previews a unified diff unless `--apply` is present:

```powershell
py -3.11 -m openscribe scene move "Bus Stop" --chapter "Arrival" --position 2
py -3.11 -m openscribe scene split "Bus Stop" --chapter "Arrival" --at-text "Eli" --new-title "The Decision"
```

The move commands renumber parts and chapters so manuscript order stays stable on disk.

You can also open the Markdown files directly in your editor and compare them with the command output.
