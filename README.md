# openscribe

Open source CLI and TUI writing environment for long form projects

## Project docs

See [changelog.md](./changelog.md) for the repo change history.

## What it is

`openscribe` is a writing tool for books and other long form work.
It stores everything as plain Markdown files with YAML frontmatter.
You can work from the command line, open the Textual interface, or edit files directly in your editor.

The source files stay readable without the app.
That matters if you want your manuscript under git, want full control of backups, or want to move between tools later.

## Why it exists

Most long form writing tools hide your project behind a desktop interface.
That works until you want automation, version control, or direct access to your files.

`openscribe` takes the opposite approach.

* Markdown files are the source of truth
* project structure is visible on disk
* metadata lives in frontmatter
* the CLI handles project setup and manuscript structure
* the TUI gives you a binder style view without taking ownership of the files

## Current scope

This first build includes:

* project initialization
* part creation
* chapter creation
* manuscript outline view
* manuscript status view
* lightweight Textual TUI

This build does not yet include compile, snapshots, editor launch commands, or search indexing.

## Requirements

You need:

* Python 3.11 or newer
* PowerShell on Windows if you want to follow the examples exactly

## Install

Clone the repo, create a virtual environment, activate it, then install in editable mode.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

If `openscribe` is not on your `PATH`, run it with:

```powershell
py -3.11 -m openscribe --help
```

## First project

Create a folder for your book, move into it, then initialize the project.

```powershell
mkdir my-book
Set-Location .\my-book
openscribe init "My Novel"
```

That creates this structure:

```text
my-book/
  .openscribe/
    project.yaml
    templates/
  manuscript/
  research/
  characters/
  notes/
```

### What each folder is for

`manuscript/`

This is the main writing area.
Each part becomes a folder.
Each chapter becomes a Markdown file inside a part folder.

`.openscribe/project.yaml`

This is the project config file.
It stores the project title and future compile settings.

`research/`

Put background material here.
Examples include references, links, excerpts, and notes that are not part of the manuscript draft itself.

`characters/`

Use this for character profiles, timelines, arcs, and relationship notes.

`notes/`

Use this for loose ideas, outline fragments, revision notes, and planning.

## Basic workflow

The normal writing flow looks like this:

1. Initialize a project.
2. Create a part.
3. Create chapters inside that part.
4. Open the Markdown files in your editor and write.
5. Use `outline` and `status` to inspect progress.
6. Use `tui` when you want a binder style view of the manuscript.

## Creating parts

Use this when you want a top level section of the book.

```powershell
openscribe new part "Opening"
openscribe new part "Act Two"
openscribe new part "Ending"
```

Each part gets a numbered folder name so the manuscript keeps a stable order on disk.

Example:

```text
manuscript/
  part-01-opening/
  part-02-act-two/
  part-03-ending/
```

## Creating chapters

Use `new chapter` to create a Markdown file with frontmatter already filled in.

```powershell
openscribe new chapter "The Beginning" --part "Opening"
```

You can also set metadata when the chapter is created.

```powershell
openscribe new chapter "The Chase" `
  --part "Opening" `
  --status "draft" `
  --label "action" `
  --pov "Marcus" `
  --word-target 2500 `
  --synopsis "Marcus runs after the courier and loses the package." `
  --notes "Need stronger tension in the middle section."
```

If you leave out `--part`, `openscribe` uses the most recent part folder.

## Chapter file format

Each chapter is a Markdown file.
It starts with YAML frontmatter, then the body text.

Example:

```markdown
---
title: The Beginning
status: draft
label: default
synopsis: Hero meets mentor for the first time.
pov: Marcus
word_target: 2500
notes: Tighten the middle scene.
---

Marcus stepped off the train into rain and diesel smoke.
```

### Frontmatter fields

`title`

The display title for the chapter.

`status`

Current workflow state.
Right now this is just a text value.
Common values might be `draft`, `revised`, or `final`.

`label`

A free form label for classification.
You can use this for things like `action`, `research`, `needs-work`, or `final-pass`.

`synopsis`

A short summary of the chapter.
This is useful for outline review and later corkboard style views.

`pov`

Point of view character or narrator.

`word_target`

Target word count for the chapter.

`notes`

Internal notes for revision, continuity, or reminders.

## Writing in your editor

`openscribe` creates the files.
You still write the actual manuscript in your editor of choice.

A common pattern is:

1. create the chapter with `openscribe`
2. open `manuscript\part-xx-...\ch-xx-....md` in VS Code
3. write below the frontmatter
4. keep the metadata updated as the draft changes

## Viewing the outline

Run:

```powershell
openscribe outline
```

This prints a tree of the manuscript based on the part folders and chapter files.

Example:

```text
My Novel
`-- part-01-opening
    `-- The Beginning [draft]
```

Use this when you want a quick structural view without opening the TUI.

## Viewing status

Run:

```powershell
openscribe status
```

This shows:

* project title
* chapter count
* total word count
* table of chapters with status, point of view, current word count, and target word count

This is the quickest way to see how much has been written and which chapters still need work.

## Using the TUI

Run:

```powershell
openscribe tui
```

The current TUI has three areas:

* binder tree on the left
* chapter preview in the middle
* metadata summary on the right

What it does:

* reads the part and chapter structure from `manuscript/`
* lets you select a chapter from the binder tree
* shows the chapter body in the preview pane
* shows chapter metadata in the right panel

Current key:

* `q` quits the app

This is a read focused interface right now.
It is meant for navigation and review, not inline editing yet.

## Command reference

### `openscribe init`

Initializes a new project in the target path.

```powershell
openscribe init "My Novel"
openscribe init "My Novel" --path .\books\my-novel
```

Arguments and options:

* `title` is required
* `--path` defaults to the current directory

### `openscribe new part`

Creates a numbered part folder under `manuscript/`.

```powershell
openscribe new part "Opening"
```

Arguments:

* `title` is required

### `openscribe new chapter`

Creates a chapter file inside a part folder.

```powershell
openscribe new chapter "The Beginning" --part "Opening"
```

Arguments:

* `title` is required

Options:

* `--part` sets the part by title or slug
* `--status` defaults to `draft`
* `--label` defaults to `default`
* `--pov` sets point of view
* `--word-target` sets the target word count
* `--synopsis` sets the chapter summary
* `--notes` sets internal notes

### `openscribe outline`

Prints the manuscript tree.

```powershell
openscribe outline
```

### `openscribe status`

Prints project totals and a chapter table.

```powershell
openscribe status
```

### `openscribe tui`

Opens the Textual interface.

```powershell
openscribe tui
```

## Example session

This is a full example from an empty folder.

```powershell
mkdir novel-demo
Set-Location .\novel-demo
openscribe init "North County"
openscribe new part "Opening"
openscribe new chapter "Arrival" --part "Opening" --pov "Eli" --word-target 1800
openscribe new chapter "The Call" --part "Opening" --pov "Eli" --word-target 2200
openscribe outline
openscribe status
openscribe tui
```

After that, open the chapter files in your editor and start writing.

## Working with git

`openscribe` works well with git because the source files are plain text.

A simple pattern:

* keep the whole project in a git repo
* commit after major writing sessions
* use diffs to review revisions
* branch if you want to test major structural changes

This project does not currently add snapshot commands on top of git.

## Current limitations

Right now:

* the TUI is for browsing, not editing
* word counts only reflect the chapter body text
* part names are shown from folder names
* chapter ordering is based on numbered filenames and folders
* compile output is not built yet
* no query or search command exists yet

## Roadmap

Planned next:

* compile pipeline with Pandoc
* project templates
* snapshots
* derived search index
* editor integration
