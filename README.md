# OpenScribe

Open source desktop, terminal, and command-line writing software for books and other long-form projects.

**Status:** Active pre-release alpha

**Version:** 0.1.0

**Supported Python:** 3.11, 3.12, and 3.13

OpenScribe keeps your manuscript in ordinary Markdown files with YAML metadata. The files remain readable without OpenScribe and can be backed up with normal file tools or Git.

This is alpha software. Keep an independent backup of your manuscript. Real Microsoft Word round trips, native accessibility, and physical power-loss recovery are not fully validated.

## Start here

If this is your first time using OpenScribe, follow the [Windows getting-started guide](getting-started.md). The packaged installer does not require Python or Git.

Choose the interface that fits your work:

| Interface | Best for | Start command |
|---|---|---|
| Desktop | Most writers and first-time users | **OpenScribe** in the Start menu |
| TUI | Keyboard-focused terminal writing | `openscribe tui` in **OpenScribe command line** |
| CLI | Automation and detailed project management | `openscribe --help` in **OpenScribe command line** |
| External editor | Direct Markdown editing in VSCode or another editor | `openscribe open chapter "Title"` |

All interfaces use the same project files and safety rules.

## Install on Windows

For a packaged release:

1. Open the [OpenScribe releases page](https://github.com/mickpletcher/openscribe/releases).
2. Download `OpenScribe-Setup-VERSION-x64.exe` and `SHA256SUMS.txt` from the release.
3. Run the setup file. It installs for your Windows account and does not require administrator access.
4. Open **OpenScribe** from the Start menu.

The installer includes the desktop application and command-line tools. Python and Git are not required. Release packages are not digitally signed yet, so Windows may show an unrecognized-app warning. Confirm that the file came from this repository and that its SHA-256 value matches `SHA256SUMS.txt` before continuing.

The portable ZIP is an alternative for users who do not want an installer. Extract the entire ZIP before opening `OpenScribe.exe`. Do not run it from inside the ZIP.

### Install from source

Use this route for development or when no packaged release is available. Install [Git for Windows](https://git-scm.com/download/win) and [Python 3.11 or newer](https://www.python.org/downloads/windows/) first.

Then run these commands in PowerShell:

```powershell
Set-Location $env:USERPROFILE\Documents
git clone https://github.com/mickpletcher/openscribe.git
Set-Location .\openscribe
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[desktop]"
openscribe --help
```

If activation or command discovery fails, use [Troubleshooting](docs/troubleshooting.md).

## Create a project

The easiest route is:

```powershell
openscribe desktop
```

With the packaged installer, open **OpenScribe** from the Start menu instead.

Select **New project**, choose an empty folder, enter a title, add a chapter and scene, and start writing.

To create the same project from PowerShell:

```powershell
$projectPath = Join-Path $env:USERPROFILE "Documents\OpenScribe\my-novel"
openscribe init "My Novel" --path $projectPath --template fiction
Set-Location $projectPath
openscribe desktop --project .
```

OpenScribe creates this structure:

```text
my-novel/
  .openscribe/
    project.yaml
  manuscript/
  characters/
  research/
  notes/
  build/
```

Do not run `openscribe init` in the OpenScribe source checkout unless you intend to turn that folder into a writing project. Use `--path` or choose an empty folder in the desktop application.

## Normal writing workflow

1. Open the project in the desktop application, TUI, or your text editor.
2. Add chapters and scenes.
3. Write and press `Ctrl+S` to save.
4. Create a checkpoint before major structural changes.
5. Review your outline and word counts.
6. Export a review copy to DOCX, PDF, or EPUB.
7. Keep a separate backup outside the project folder.

Common commands:

```powershell
openscribe new part "Opening"
openscribe new chapter "Arrival" --part "Opening"
openscribe new scene "Bus Stop" --chapter "Arrival"
openscribe outline
openscribe status
openscribe snapshot save "end-of-session"
openscribe compile --format docx
```

See the [complete CLI reference](docs/cli-reference.md) for every command group.

## Data safety

OpenScribe protects writing in several ways:

- unsaved desktop and TUI drafts survive navigation
- closing with unsaved text requires a Save, Discard, or Cancel decision
- saving checks whether another program changed the chapter on disk
- saves and structural changes create checkpoints
- snapshot restore previews changes before `--apply`
- restore creates an automatic backup and uses a recovery journal
- migrations and identity repair are explicit operations, not ordinary reads
- duplicate chapter or scene titles require immutable IDs instead of ambiguous aliases
- hosted AI and proofreading require a disclosure and explicit transfer approval

These controls reduce risk. They do not replace an independent backup. Read [Safety and recovery](docs/safety-and-recovery.md) before using OpenScribe for important work.

## Main capabilities

- fiction, nonfiction, technical, screenwriting, and research templates
- desktop binder, editor, search, research views, export, checkpoints, and restore
- Textual TUI with manuscript editing, planning views, and keyboard actions
- immutable chapter and scene identities
- chapter and scene creation, movement, splitting, merging, and metadata
- outlines, project status, search, reports, and derived indexes
- planning boards, story ideas, characters, settings, items, aliases, and relations
- research notes, citations, paper structure, and conference material workflows
- DOCX, PDF, and EPUB export
- optional local LanguageTool proofreading
- optional AI review with explicit hosted-transfer consent
- experimental tagged Word export and import
- per-user Windows installer and portable Windows package

## Optional LanguageTool proofreading

LanguageTool is not required. OpenScribe defaults to a disabled local endpoint at `http://127.0.0.1:8081/v2/check`.

After starting a self-hosted LanguageTool server and enabling it in `.openscribe\project.yaml`, run:

```powershell
openscribe proofread chapter "Arrival"
```

The desktop and TUI can preview and apply suggestions to the current draft with undo support. They do not use hosted endpoints. Licensed hosted endpoints require HTTPS and explicit `--allow-data-transfer` approval in the CLI. Automated use of LanguageTool's free public endpoint is rejected.

See [LanguageTool setup and troubleshooting](docs/troubleshooting.md#languagetool-does-not-connect).

## Optional AI review

AI is not required for project creation, writing, saving, searching, recovery, or export.

Install provider support only if you need it:

```powershell
python -m pip install -e ".[ai]"
```

OpenScribe shows the provider, model, endpoint, and character count before manuscript text is sent to a hosted service. Each hosted command requires `--allow-data-transfer`. Local loopback endpoints do not require that flag.

See [AI setup](docs/ai-setup.md).

## Experimental Word round trips

Normal `openscribe compile --format docx` creates a review or submission document. It does not import changes back.

The separate Word round-trip workflow adds identity tags and a local baseline:

```powershell
openscribe word export --output build\roundtrip.docx
openscribe word import build\roundtrip.docx
openscribe word import build\roundtrip.docx --apply
```

The first import is a preview. Apply is blocked for conflicts, missing or duplicate identity controls, structural changes, and unresolved tracked changes. Markdown remains canonical.

This workflow is experimental. Use synthetic or copied writing until real Word validation is complete. See [Safety and recovery](docs/safety-and-recovery.md#experimental-word-round-trips).

## Documentation

| Document | Use it for |
|---|---|
| [Getting started](getting-started.md) | First installation and first writing session |
| [Desktop guide](docs/desktop-guide.md) | Binder, editor, proofreading, export, checkpoints, and recovery |
| [CLI reference](docs/cli-reference.md) | Every command group and practical examples |
| [Troubleshooting](docs/troubleshooting.md) | Installation, project, save, export, LanguageTool, and Word errors |
| [Safety and recovery](docs/safety-and-recovery.md) | Backups, drafts, conflicts, snapshots, migrations, AI, and Word boundaries |
| [AI setup](docs/ai-setup.md) | Optional local and hosted AI providers |
| [North County sample](examples/north-county/README.md) | Safe exploration of a complete example project |
| [Validation](VALIDATION.md) | Developer and release validation commands |
| [Current assessment](assessment.md) | Current health, risks, and priorities |
| [Future upgrades](future-upgrades.md) | Planned and proposed work |
| [Changelog](changelog.md) | Shipped changes |

Files under `specs/` are development plans, not user instructions or contractual requirements.

## Command help

The built-in help is always the exact reference for the installed version:

```powershell
openscribe --help
openscribe COMMAND --help
openscribe COMMAND SUBCOMMAND --help
```

Examples:

```powershell
openscribe snapshot --help
openscribe scene split --help
openscribe word import --help
```

Most project commands must run from the project folder or one of its subfolders. A valid project contains `.openscribe\project.yaml`.

## Development and validation

Development setup:

```powershell
python -m pip install -e ".[dev]"
python -m ruff check src tests scripts/check-secrets.py scripts/check_markdown_links.py
python -m pytest --cov=openscribe --cov-report=term-missing --cov-fail-under=80
python scripts/check_markdown_links.py
pwsh -File scripts/docs-check.ps1 -FailOnGap
```

Windows package build:

```powershell
python -m pip install -e ".[packaging]"
pwsh -File scripts/build-windows.ps1
```

See [VALIDATION.md](VALIDATION.md) for supported Python versions, package checks, security checks, and known validation limitations.

## Current limitations

- The project is pre-release alpha software.
- Windows release packages are not digitally signed.
- Native desktop and TUI accessibility are not fully verified.
- Physical power-loss durability is not proven.
- Licensed hosted LanguageTool and live hosted AI providers are covered only by limited or mocked contract tests.
- Word round trips and the Office task pane require real-host validation and independent review.
- Rich scene metadata and drag-based planning are not implemented.

Keep independent backups. Do not use the experimental Word workflow on the only copy of a manuscript.

## Project records

- [Current assessment](assessment.md)
- [Technical debt](TECH-DEBT.md)
- [Validation limitations](VALIDATION.md#known-validation-limitations)
- [Decision records](docs/decisions/README.md)
- [Completed upgrades](completed-upgrades.md)
- [Future upgrades](future-upgrades.md)
- [Changelog](changelog.md)
