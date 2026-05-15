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
* one manuscript part
* one `part.yaml` part metadata file
* two chapter files
* one character note
* one research note
* one revision note

The sample project config also includes compile defaults you can edit to test template and export behavior.

## How to inspect it

From the repo root:

```powershell
Set-Location .\examples\north-county
py -3.11 -m openscribe outline
py -3.11 -m openscribe find chapters --text station
py -3.11 -m openscribe read
py -3.11 -m openscribe status
py -3.11 -m openscribe tui
```

Inside the TUI you can now use the search box to filter chapters and inspect part metadata from the binder.

You can also open the Markdown files directly in your editor and compare them with the command output.
