# openscribe getting started

This is the fastest path to a working `openscribe` project.

Use this guide if you want to:

* install the tool
* create your first project
* make a part, chapter, and scene
* open the TUI
* export to Word, PDF, or EPUB

If you want AI later, use [docs/ai-setup.md](./docs/ai-setup.md).
You do not need AI to use `openscribe`.

## What `openscribe` is

`openscribe` is a CLI first writing tool for long form projects.
Your manuscript stays in normal Markdown files.
Project settings live in YAML.
You can edit the files directly in your editor, use the CLI, or use the TUI.

## What you need

You need:

* Windows with PowerShell
* Python 3.11 or newer

Optional:

* Pandoc if you want `openscribe compile` to prefer Pandoc output

## Install

From the repo root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Check that the command works:

```powershell
py -3.11 -m openscribe --help
```

If `openscribe` is already on your `PATH`, you can also run:

```powershell
openscribe --help
```

## Create your first project

Make a new fiction project:

```powershell
openscribe init "My Novel" --template fiction
Set-Location .\my-novel
```

That creates:

* `.openscribe\project.yaml` for project settings
* `manuscript\` for parts and chapters
* `characters\`, `research\`, and `notes\` for support material
* `build\` for export output

## Create manuscript structure

Add a part, chapter, and scene:

```powershell
openscribe new part "Opening"
openscribe new chapter "Arrival" --part "Opening"
openscribe new scene "Bus Stop" --chapter "Arrival"
```

Check the manuscript structure:

```powershell
openscribe outline
openscribe outliner
openscribe status
```

## Read and inspect the manuscript

Use the continuous reading view:

```powershell
openscribe read
```

Open the TUI:

```powershell
openscribe tui
```

The TUI can show:

* manuscript structure
* chapter metadata
* corkboard style synopsis cards
* board canvas notes
* character, research, notes, story idea, and element views

## Export the manuscript

Default export:

```powershell
openscribe compile
```

Export specific formats:

```powershell
openscribe compile --format docx
openscribe compile --format pdf
openscribe compile --format epub
```

Use a compile profile:

```powershell
openscribe compile --profile print
openscribe compile --profile ebook
openscribe compile --profile submission
```

Output goes to the project `build\` folder unless you pass `--output`.

## Useful next commands

Update chapter metadata:

```powershell
openscribe set chapter "Arrival" --status draft --label scene --pov Eli
```

Find chapters:

```powershell
openscribe find chapters --status draft
openscribe find chapters --text station
```

Find scenes:

```powershell
openscribe find scenes --text station
```

Save a checkpoint:

```powershell
openscribe snapshot save "first-pass"
openscribe snapshot list
```

Create a board note:

```powershell
openscribe board note add "Opening image"
openscribe board view
```

## Research and nonfiction

If you are writing a paper or research driven project, start with:

```powershell
openscribe init "Grid Study" --template research
Set-Location .\grid-study
openscribe workflow research-paper --part "Paper"
openscribe workflow source-note "River Ledger Study" --type article --author "J. Harper" --year 2024
openscribe workflow citation-pack --style Chicago
openscribe compile --profile research-paper
```

## AI is optional

Normal `openscribe` use does not require AI.

If you want AI provider support later:

```powershell
python -m pip install -e ".[ai]"
```

Then use the separate guide:

* [AI setup guide](./docs/ai-setup.md)

## Sample project

If you want a real example project, start here:

* [North County example project](./examples/north-county/README.md)

## Keep this guide current

This file should be updated when the repo changes in ways that affect:

* install steps
* first run setup
* the normal command sequence
* export setup
* beginner workflow guidance
