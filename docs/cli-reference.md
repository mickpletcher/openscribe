# OpenScribe CLI reference

This document maps the complete command-line interface by workflow.

For the exact options supported by the installed version, run:

```powershell
openscribe --help
openscribe COMMAND --help
openscribe COMMAND SUBCOMMAND --help
```

Most commands must run from a project folder or one of its subfolders. A project folder contains `.openscribe\project.yaml`.

## Top-level commands

| Command | Purpose |
|---|---|
| `openscribe desktop` | Open the desktop writing application |
| `openscribe init` | Initialize a project in a selected folder |
| `openscribe outline` | Show the part and chapter outline |
| `openscribe outliner` | Show detailed structure and metadata |
| `openscribe status` | Show project progress and status |
| `openscribe compile` | Export DOCX, PDF, or EPUB |
| `openscribe read` | Print the assembled manuscript |
| `openscribe tui` | Open the terminal interface |
| `openscribe templates` | List project templates and compile profiles |
| `openscribe new` | Create manuscript content |
| `openscribe set` | Update project metadata |
| `openscribe show` | Display stored metadata |
| `openscribe find` | Find chapters or scenes |
| `openscribe report` | Produce project or scene reports |
| `openscribe move` | Reorder parts or chapters |
| `openscribe scene` | Preview or apply scene restructuring |
| `openscribe migrate` | Inspect, apply, or repair project format data |
| `openscribe snapshot` | Save, list, compare, or restore checkpoints |
| `openscribe index` | Manage the derived search index |
| `openscribe board` | Manage planning-board notes and links |
| `openscribe element` | Manage characters, settings, items, aliases, and relations |
| `openscribe idea` | Manage story ideas |
| `openscribe template` | Save user-defined project templates |
| `openscribe import` | Import a folder-based manuscript |
| `openscribe workflow` | Run research, citation, conference, and format helpers |
| `openscribe open` | Open project files in the configured editor |
| `openscribe proofread` | Run LanguageTool checks |
| `openscribe ai` | Run optional AI review commands |
| `openscribe word` | Run experimental tagged Word round trips |

## Project setup

### Initialize a project

```powershell
openscribe init "My Novel" --path "C:\Writing\my-novel" --template fiction
```

Supported built-in templates are `fiction`, `nonfiction`, `technical`, `screenwriting`, and `research`.

If `--path` is omitted, the current directory is initialized. OpenScribe does not automatically create a folder from the title.

Use a saved template file:

```powershell
openscribe init "My Novel" --path "C:\Writing\my-novel" --template-file "C:\Templates\novel.yaml"
```

### List templates

```powershell
openscribe templates
```

### Open the interfaces

```powershell
openscribe desktop
openscribe desktop --project "C:\Writing\my-novel"
openscribe tui
```

See [Desktop guide](desktop-guide.md) for the visual workflow.

## Project migrations

Check without changing files:

```powershell
openscribe migrate status
```

Apply an ordered migration with an automatic checkpoint:

```powershell
openscribe migrate apply
```

Explicitly add missing identities and update legacy board links:

```powershell
openscribe migrate repair
```

Duplicate or ambiguous identities require manual review.

## Manuscript structure

### Create a part

```powershell
openscribe new part "Opening"
```

### Create a chapter

```powershell
openscribe new chapter "Arrival" --part "Opening"
openscribe new chapter "The Call" --part "Opening" --status draft --label scene --pov Eli --word-target 2200
```

### Create a scene

```powershell
openscribe new scene "Bus Stop" --chapter "Arrival"
openscribe new scene "Bus Stop" --chapter "Arrival" --body "The bus doors closed behind her."
```

### Create a generic section

```powershell
openscribe new section "Background" --part "Research"
```

Use `openscribe new section --help` for section type, synopsis, and notes options.

### Reorder parts and chapters

```powershell
openscribe move part "Opening" --position 2
openscribe move chapter "Arrival" --position 1
openscribe move chapter "Arrival" --part "Act Two" --position 1
```

Movement renumbers storage names while immutable IDs preserve relationships.

## Scene structure

Scene structure commands preview a unified diff by default. Add `--apply` only after reviewing it.

Move a scene:

```powershell
openscribe scene move "Bus Stop" --chapter "Arrival" --position 2
openscribe scene move "Bus Stop" --chapter "Arrival" --to-chapter "The Call" --position 1
openscribe scene move "Bus Stop" --chapter "Arrival" --position 2 --apply
```

Split a scene at matching text:

```powershell
openscribe scene split "Bus Stop" --chapter "Arrival" --at-text "The phone rang" --new-title "The Call"
openscribe scene split "Bus Stop" --chapter "Arrival" --at-text "The phone rang" --new-title "The Call" --apply
```

Merge two scenes:

```powershell
openscribe scene merge "Bus Stop" --with "The Call" --chapter "Arrival"
openscribe scene merge "Bus Stop" --with "The Call" --chapter "Arrival" --apply
```

Applied operations create checkpoints.

## Reading and project views

```powershell
openscribe outline
openscribe outliner
openscribe outliner --status draft
openscribe outliner --label scene
openscribe status
openscribe read
```

Use `openscribe read --help` for compile-template options that affect assembly.

## Chapter and part metadata

Update metadata:

```powershell
openscribe set part "Opening" --title "Act One"
openscribe set chapter "Arrival" --status revised --label scene --pov Eli --word-target 1800
openscribe set chapter "Arrival" --synopsis "Eli returns to town." --notes "Tighten the final paragraph."
```

Inspect metadata:

```powershell
openscribe show part "Act One"
openscribe show chapter "Arrival"
```

Update matching chapters in a batch:

```powershell
openscribe set chapters --match-status draft --status revised
openscribe set chapters --match-label scene --pov Eli
```

Review `openscribe set chapters --help` before applying a batch update.

## Goals and research compile settings

```powershell
openscribe set goals --draft-word-target 85000 --session-word-target 1200 --deadline 2026-12-01
openscribe set compile-research --citation-style Chicago --include-bibliography --bibliography-title "Works Cited"
```

## Find and report

Find chapters:

```powershell
openscribe find chapters --status draft
openscribe find chapters --pov Eli
openscribe find chapters --text station
```

Find scenes:

```powershell
openscribe find scenes --text station
openscribe find scenes --status draft
```

Reports:

```powershell
openscribe report project
openscribe report scenes
openscribe report scenes --text station
```

## Open files in an editor

```powershell
openscribe open chapter "Arrival"
openscribe open part "Opening"
openscribe open search --text station
```

The launcher uses the platform's configured file or folder opener.

## Compile and export

Use project defaults:

```powershell
openscribe compile
```

Choose a format or output path:

```powershell
openscribe compile --format docx
openscribe compile --format pdf
openscribe compile --format epub
openscribe compile --output .\build\review-copy.docx
```

Use a built-in profile:

```powershell
openscribe compile --profile print
openscribe compile --profile ebook
openscribe compile --profile submission
openscribe compile --profile research-paper
```

Use `openscribe compile --help` for backend, template, profile, and output precedence.

## Snapshots

Create and list checkpoints:

```powershell
openscribe snapshot save "end-of-session"
openscribe snapshot save "git-checkpoint" --mode git
openscribe snapshot list
```

Compare a checkpoint:

```powershell
openscribe snapshot diff "end-of-session"
```

Preview and apply an exact restore:

```powershell
openscribe snapshot restore "end-of-session"
openscribe snapshot restore "end-of-session" --apply
```

Restore can remove managed files that were created after the checkpoint. Review the preview first. See [Safety and recovery](safety-and-recovery.md).

## Derived index

```powershell
openscribe index rebuild
openscribe index show
openscribe index search "station"
```

Source hashes make the index stale after a source edit, addition, or deletion. Rebuild it when requested.

## Project templates and folder import

Save the current project structure as a reusable template:

```powershell
openscribe template save "my-novel-template"
```

Import a folder-based manuscript into the current OpenScribe project:

```powershell
openscribe import folder "C:\Writing\existing-manuscript" --title "Imported Manuscript" --path "C:\Writing\imported-project"
```

Use `openscribe import folder --help` and make a backup before importing.

## Planning board

Create and list notes:

```powershell
openscribe board note add "Ledger clue" --body "Eli finds the ledger." --group plot
openscribe board note list
openscribe board note list --group plot
```

Move and group notes:

```powershell
openscribe board note move note-001 --x 10 --y 4
openscribe board group set note-001 plot
openscribe board layout auto
openscribe board view
```

Link board notes:

```powershell
openscribe board link add note-001 note-002
openscribe board chapter add note-001 "Arrival"
openscribe board chapter remove note-001 "Arrival"
```

Promote a note into a chapter:

```powershell
openscribe board promote note-001 --part "Opening" --chapter "Ledger Clue"
```

Run each nested `--help` command for required IDs and options.

## Elements and relations

Create and list elements:

```powershell
openscribe element add character "Eli Harper" --notes "Main point of view"
openscribe element add setting "North County"
openscribe element list
openscribe element list --type character
```

Inspect and update:

```powershell
openscribe element show "Eli Harper"
openscribe element set "Eli Harper" --notes "Returns after ten years."
openscribe element set-many --match-tag lead --notes "Needs arc review."
```

Aliases and relations:

```powershell
openscribe element alias add "Eli Harper" "Eli"
openscribe element relate "Eli Harper" "North County" --type "returns to"
openscribe element unrelate "Eli Harper" "North County"
openscribe element appears-in "Eli Harper"
```

Use the nested help before relation or batch operations.

## Story ideas

```powershell
openscribe idea add "The Flood Ledger" --premise "A clerk finds a ledger that predicts deaths."
openscribe idea list
openscribe show idea "The Flood Ledger"
```

Use `openscribe idea add --help` for genre, tone, status, premise, and notes options.

## Writing workflow helpers

Screenplay scene:

```powershell
openscribe workflow screenplay-scene "EXT. ROAD - NIGHT" --chapter "Arrival"
```

Nonfiction section:

```powershell
openscribe workflow nonfiction-section "Background" --part "Part One"
```

Research paper structure:

```powershell
openscribe workflow research-paper --part "Paper"
openscribe workflow research-paper --part "Paper" --include-appendix
```

Research sources and citations:

```powershell
openscribe workflow source-note "County Archive" --type archive --author "Example Author" --year 1987
openscribe workflow citation-pack --style Chicago
openscribe workflow cite --chapter "Arrival" --source "County Archive" --style Chicago
openscribe workflow cite --chapter "Arrival" --scene "Bus Stop" --source "County Archive" --style Chicago
```

Conference materials:

```powershell
openscribe workflow conference-materials "Grid Study" --venue "Example Conference"
openscribe workflow conference-schedule-import .\schedule.csv --venue "Example Conference"
```

Schedule import supports CSV, TSV, JSON, YAML, and YML. The source schedule file must exist.

## LanguageTool proofreading

After configuring an enabled endpoint:

```powershell
openscribe proofread chapter "Arrival"
openscribe proofread chapter "Arrival" --language en-US
```

An approved licensed hosted endpoint also requires:

```powershell
openscribe proofread chapter "Arrival" --allow-data-transfer
```

The CLI reports findings without changing manuscript files. The free public LanguageTool endpoint is rejected for automated use.

## Optional AI commands

Available command groups:

```powershell
openscribe ai summarize "Arrival"
openscribe ai rewrite "Arrival"
openscribe ai outline "Arrival"
openscribe ai analyze "Arrival" --focus pacing
openscribe ai metadata "Arrival"
openscribe ai brainstorm "Arrival" --question "Three complications for the midpoint"
openscribe ai query "Where does Eli first mention the ledger?"
```

Use each command's `--help` for its exact arguments. Hosted destinations require `--allow-data-transfer` on every invocation after reviewing the disclosure.

See [AI setup](ai-setup.md).

## Experimental Word commands

Export a tagged Word document:

```powershell
openscribe word export --output .\build\roundtrip.docx
```

Preview and apply changes:

```powershell
openscribe word import .\build\roundtrip.docx
openscribe word import .\build\roundtrip.docx --apply
```

Start the project-bound loopback bridge for task-pane diagnostics:

```powershell
openscribe word bridge --port 8765 --certificate C:\Certificates\localhost.crt --key C:\Certificates\localhost.key --manifest .\build\openscribe-addin.xml
```

Word round trips are experimental. Real Word save and reopen behavior, task-pane sideloading, and certificate setup remain release gates. See [Safety and recovery](safety-and-recovery.md#experimental-word-round-trips).
