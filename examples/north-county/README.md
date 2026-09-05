# North County sample project

North County is a complete synthetic OpenScribe project. It contains no private manuscript data.

Use it to inspect project structure and try commands without creating a project from scratch.

## Before using the sample

Complete [Getting started](../../getting-started.md) and activate the OpenScribe Python environment.

The checked-in sample is part of the source repository. Start with read-only commands. Copy it before trying commands that save, move, restore, import, or create files.

## What is included

- project configuration under `.openscribe`
- one planning board
- one element record
- one manuscript part with two chapters and scene headings
- a character note
- a research note
- revision notes
- a story idea
- compile defaults

## Inspect the sample without changing it

From the OpenScribe source folder:

```powershell
Set-Location .\examples\north-county
python -m openscribe outline
python -m openscribe status
python -m openscribe outliner
python -m openscribe read
python -m openscribe report project
python -m openscribe find chapters --text station
python -m openscribe find scenes --text station
```

These commands do not change manuscript, settings, or planning data. OpenScribe may create an ignored `.openscribe\.write.lock` coordination file.

Expected highlights include:

- project title `North County`
- part title `Opening`
- chapters `Arrival` and `The Call`
- a `Bus Stop` scene
- matches for `station`

Return to the source folder when finished:

```powershell
Set-Location ..\..\
```

## Make a safe working copy

Run this from the OpenScribe source folder. Choose an unused destination path:

```powershell
$sampleCopy = Join-Path $env:USERPROFILE "Documents\OpenScribe\north-county-sample"
New-Item -ItemType Directory -Force -Path (Split-Path $sampleCopy) | Out-Null
Copy-Item -Recurse -LiteralPath .\examples\north-county -Destination $sampleCopy
Set-Location $sampleCopy
python -m openscribe status
```

If `north-county-sample` already exists, choose a different name. Do not overwrite a prior working copy that contains writing you want to keep.

All remaining examples in this guide change the copied project.

Rebuild and search the copied index:

```powershell
python -m openscribe index rebuild
python -m openscribe index search station
```

## Open the copied project

Desktop:

```powershell
python -m openscribe desktop --project .
```

Terminal interface:

```powershell
python -m openscribe tui
```

Select chapters and scenes in the binder. Use `Ctrl+S` to save. See the [desktop guide](../../docs/desktop-guide.md) for the full workflow.

## Try a checkpoint and restore preview

```powershell
python -m openscribe snapshot save "sample-checkpoint"
python -m openscribe snapshot list
python -m openscribe snapshot diff "sample-checkpoint"
python -m openscribe snapshot restore "sample-checkpoint"
```

The restore command is a preview because `--apply` is absent.

## Try project changes

Add a board note:

```powershell
python -m openscribe board note add "Sheriff rumor" --body "A deputy hints that the sheriff knew about the ledger." --group plot
python -m openscribe board note list
python -m openscribe board layout auto
python -m openscribe board view
```

Add an element:

```powershell
python -m openscribe element add character "Nora Bell" --notes "County archivist"
python -m openscribe element list
python -m openscribe element appears-in "Eli Harper"
```

Add a source note and citation files:

```powershell
python -m openscribe workflow source-note "County Archive" --type archive --author "Example Author" --year 1987
python -m openscribe workflow citation-pack --style Chicago
```

## Preview scene structure changes

These commands show a diff without changing the project:

```powershell
python -m openscribe scene move "Bus Stop" --chapter "Arrival" --position 2
python -m openscribe scene split "Bus Stop" --chapter "Arrival" --at-text "Eli" --new-title "The Decision"
```

Add `--apply` only in the copied project and only after reviewing the preview.

## Export the copied manuscript

```powershell
python -m openscribe compile --format docx
python -m openscribe compile --format pdf
python -m openscribe compile --format epub
Get-ChildItem -LiteralPath .\build
```

The exported files appear under `build`.

## LanguageTool

The sample configuration contains proofreading settings, but the feature requires a running LanguageTool-compatible server and `proofreading.enabled: true`.

After configuring a local server:

```powershell
python -m openscribe proofread chapter "Arrival"
```

The CLI reports findings without changing the chapter. See [Troubleshooting](../../docs/troubleshooting.md#languagetool-does-not-connect).

## Files worth opening

- `.openscribe\project.yaml` shows project and compile settings.
- `manuscript\part-01-opening\part.yaml` shows part metadata.
- `manuscript\part-01-opening\ch-01-arrival.md` shows chapter frontmatter and scene identity.
- `.openscribe\boards` shows planning-board storage.
- `.openscribe\elements` shows element storage.
- `characters`, `research`, and `notes` show supporting Markdown files.

Do not copy or edit chapter IDs or scene identity comments by hand. See [Safety and recovery](../../docs/safety-and-recovery.md).
