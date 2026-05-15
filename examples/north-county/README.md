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

The sample project config also includes compile defaults you can edit to test template and export behavior.
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
py -3.11 -m openscribe board note add "Sheriff rumor" --body "A deputy hints the sheriff knew about the ledger." --group plot
py -3.11 -m openscribe board note list
py -3.11 -m openscribe board layout auto
py -3.11 -m openscribe board view
py -3.11 -m openscribe idea list
py -3.11 -m openscribe show idea "The Flood Ledger"
py -3.11 -m openscribe element add character "Eli Harper" --notes "Primary point of view"
py -3.11 -m openscribe element appears-in Eli
py -3.11 -m openscribe snapshot save "sample-checkpoint"
py -3.11 -m openscribe template save "north-county-custom"
py -3.11 -m openscribe read
py -3.11 -m openscribe status
py -3.11 -m openscribe tui
```

Inside the TUI you can now use the search box to filter chapters and inspect part metadata from the binder.

The board commands store freeform planning notes under `.openscribe/boards/`.

The element commands store element, alias, and relation data under `.openscribe/elements/`.

The story idea commands store structured new book ideas under `notes/story-ideas/`.

The snapshot commands store checkpoint and git based snapshot records under `.openscribe/snapshots/`.

The template commands store saved user templates under `.openscribe/templates/`.

You can also open the Markdown files directly in your editor and compare them with the command output.
