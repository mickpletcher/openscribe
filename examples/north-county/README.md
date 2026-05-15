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

## How to inspect it

From the repo root:

```powershell
Set-Location .\examples\north-county
py -3.11 -m openscribe outline
py -3.11 -m openscribe status
py -3.11 -m openscribe tui
```

You can also open the Markdown files directly in your editor and compare them with the command output.
