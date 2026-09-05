# openscribe

Open source desktop, CLI, and TUI writing environment for long form projects

## Current Status

- Status: Active pre-release alpha
- Version: 0.1.0
- Project tier: 1
- Primary technologies: Python, PySide6, Typer, Textual, Markdown, and YAML

For current repository health, see [assessment.md](./assessment.md).

## Documentation

The single authority for each documentation responsibility is mapped in [PROJECT-STANDARD.md](./PROJECT-STANDARD.md).

Use [getting-started.md](./getting-started.md) for the shortest setup path, [VALIDATION.md](./VALIDATION.md) for verification procedures, and [docs/ai-setup.md](./docs/ai-setup.md) for optional AI setup.

The files under `specs/` are development milestone plans. They are not contractual requirements.

## What it is

`openscribe` is a writing tool for books and other long form work.
It stores everything as plain Markdown files with YAML frontmatter.
You can use the optional desktop writing app, the command line, the Textual interface, or an external editor.

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
* project templates for fiction, nonfiction, technical writing, screenwriting, and research
* user defined project templates
* part creation
* chapter creation
* scene creation with immutable inline IDs
* preview-first scene move, split, and merge within and across chapters
* batch chapter metadata updates
* chapter search and query
* project reports
* derived project index rebuild and search
* folder import for existing manuscript projects
* story idea capture for future books
* snapshots with checkpoint and git based modes, exact preview-first restore, automatic backup, and interruption recovery
* planning board notes, layout, visual board view, and promotion
* element, alias, relation, and appears in tracking
* nonfiction section and screenplay scene workflow helpers
* nonfiction source notes and citation tracking workflows
* citation insertion helpers for chapter and scene sections
* project goals, draft targets, and deadline tracking
* research paper section scaffolding
* conference material, timed talk, poster revision, and submission status scaffolding
* Word document export
* PDF export
* EPUB export
* manuscript outline view
* detailed outliner view with metadata, scenes, word totals, and filters
* manuscript status view
* chapter and part reordering commands
* compile profiles for print, ebook, submission, and research paper output
* citation aware research compile settings with bibliography controls
* wider Textual TUI views for manuscript, corkboard cards, source links, board canvas, characters, research, notes, story ideas, and elements
* editable chapter and scene text in the TUI with explicit save behavior
* richer TUI chapter metadata quick actions for status, label, point of view, and word target
* snapshot restore and diff helpers
* editor launch helpers for chapters, parts, and search results
* conference schedule import and session checklist automation
* optional LanguageTool grammar and style checks in the CLI and TUI
* optional read-only AI summary, rewrite, outline, focused review, metadata, brainstorming, and project-query commands
* ordered, automatically backed up project-format migrations

This build does not yet include venue specific bibliography styles, richer scene metadata, or drag based board editing. Word round trips are experimental and require real host validation before production use.

## Desktop writing

From a repository checkout:

```powershell
python -m pip install -e ".[desktop]"
openscribe desktop
openscribe desktop --project "C:\Writing\My Novel"
```

Create or open a project, add chapters and scenes, and select them in the binder. Research, character, and note views are read only. The editor keeps drafts when navigating. Local recovery drafts are written every second and on navigation. `Ctrl+S` saves with a checkpoint; a changed disk baseline blocks saving instead of overwriting newer work. Reload discards a draft only after confirmation. Quit offers Save, Discard, and Cancel.

The chapter editor allows prose edits while keeping scene headings unchanged. Use scene commands for structural changes. Do not delete or replace IDs in an external editor. Missing IDs can be repaired explicitly with `openscribe migrate repair`; duplicate IDs must be resolved manually.

Proofread runs local LanguageTool in the background. Select a finding and replacement, preview it, then apply it to the draft. Undo reverses the replacement. Any intervening text change invalidates the suggestion. Export, Checkpoint, Restore, Word export, and Word import are available from the toolbar overflow when the window is narrow.

This is an alpha interface. Keep an independent backup. Draft recovery is not a guarantee against losing the last second of typing after an abrupt failure.

## Experimental Word round trips

Ordinary `compile --format docx` remains one way. Use the distinct round-trip path:

```powershell
openscribe word export --output build\roundtrip.docx
openscribe word import build\roundtrip.docx
openscribe word import build\roundtrip.docx --apply
```

Export writes tagged content controls and a private baseline under `.openscribe/word-roundtrip/`. Use a new output filename for every export. Edit inside the existing controls. Import previews changes, preserves current Markdown-only edits, and blocks conflicting edits, missing or duplicate controls, structural changes, and unresolved tracked changes. Apply checks the preview baseline again and installs a validated staged result with a backup. Markdown remains canonical. Rich Word formatting, drawings, tables, and arbitrary DOCX import are not supported.

For the task-pane prototype, use a fixed local port and a locally trusted certificate valid for `127.0.0.1`:

```powershell
openscribe word bridge --port 8765 --certificate C:\Certificates\localhost.crt --key C:\Certificates\localhost.key --manifest build\openscribe-addin.xml
```

Sideload the generated manifest in Windows desktop Word using your approved Office add-in process. Enter the session token printed by the running bridge into the pane. Preview and Apply are separate actions. The pane communicates only with the selected local project; Microsoft supplies the Office JavaScript runtime. The bridge does not install or trust certificates for you. Without a certificate, it supports local HTTP diagnostics but does not generate a task-pane manifest.

Real Word UI and certificate/sideload validation remain unverified. See [VL-004](VALIDATION.md#vl-004-real-word-and-desktop-ui-validation-is-incomplete) and [ADR-006](docs/decisions/ADR-006-experimental-word-round-trip-availability.md).

## Requirements

You need:

* Python 3.11, 3.12, or 3.13
* PowerShell on Windows if you want to follow the examples exactly

You do not need any AI provider, API key, or AI SDK setup to use the normal project, CLI, or TUI features.

## Validation

Use the commands and change-class matrix in [VALIDATION.md](./VALIDATION.md).

## Install

Clone the repo, create a virtual environment, activate it, then install in editable mode.

If you want the shortest setup path first, use [getting-started.md](./getting-started.md).

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

If you want AI provider support, install the optional AI extras too:

```powershell
python -m pip install -e ".[ai]"
```

If `openscribe` is not on your `PATH`, run it with:

```powershell
py -3.11 -m openscribe --help
```

## Standard setup

This is the normal setup path.
It does not require AI.

If you are brand new to the repo, [getting-started.md](./getting-started.md) is the better first read.

```powershell
py -3.11 -m openscribe --help
openscribe init "My Novel" --template fiction
openscribe new part "Opening"
openscribe new chapter "The Beginning" --part "Opening"
openscribe new scene "Cold Open" --chapter "The Beginning"
openscribe workflow screenplay-scene "EXT. ROAD - NIGHT" --chapter "The Beginning"
openscribe workflow research-paper --part "Paper"
openscribe compile
openscribe compile --format pdf
openscribe compile --format epub
openscribe compile --profile submission
openscribe index rebuild
openscribe snapshot save "first-pass"
openscribe board view
openscribe read
openscribe outline
openscribe outliner
openscribe status
openscribe tui
```

If you only want the writing tool, you can stop there.
You can ignore the rest of the AI section completely.

## LanguageTool proofreading

`openscribe` can send one chapter at a time to a LanguageTool compatible `/v2/check` endpoint and display grammar, spelling, and style findings. It does not apply replacements or change manuscript files.

The default is disabled and points to a local server:

```yaml
proofreading:
  enabled: true
  endpoint: http://127.0.0.1:8081/v2/check
  language: en-US
  timeout_seconds: 30
```

Start a self hosted server by following the [official LanguageTool HTTP server guide](https://dev.languagetool.org/http-server), then run:

```powershell
openscribe proofread chapter "The Beginning"
openscribe proofread chapter "The Beginning" --language en-GB
```

Local loopback endpoints can use HTTP. Nonlocal endpoints must use HTTPS and require explicit approval for every command:

```powershell
openscribe proofread chapter "The Beginning" --allow-data-transfer
```

Before an approved hosted request, `openscribe` reports the endpoint and number of chapter characters being sent. The free public LanguageTool endpoint is intentionally rejected because its [published access policy](https://dev.languagetool.org/public-http-api) prohibits automated requests. Use a local server or a licensed hosted endpoint instead.

Inside `openscribe tui`, select a chapter or scene and press `Ctrl+G` to check in the background. Use `Ctrl+J` and `Ctrl+K` to navigate findings, `Ctrl+Shift+R` to preview the first suggestion, `Ctrl+Shift+A` to apply that preview to the draft, and `Ctrl+Shift+I` to ignore a finding. `Ctrl+Z` undoes a replacement. Changed text invalidates a preview. The TUI runs local endpoints only. Hosted endpoints require the CLI disclosure flow with `--allow-data-transfer`.

This integration uses the LanguageTool HTTP API. It does not copy or distribute LanguageTool source code. See the [LanguageTool repository](https://github.com/languagetool-org/languagetool) for its server, source, and license details. The self hosted server does not include LanguageTool's cloud only AI rules.

## Research workflow

If you are using `openscribe` for papers or conference work:

```powershell
openscribe init "Grid Study" --template research
openscribe workflow research-paper --part "Paper" --include-appendix
openscribe workflow source-note "River Ledger Study" --type article --author "J. Harper" --year 2024
openscribe workflow citation-pack --style Chicago
openscribe set compile-research --citation-style Chicago --include-bibliography --bibliography-title "Works Cited"
openscribe workflow cite --chapter "Introduction" --source "River Ledger Study" --style Chicago
openscribe workflow conference-materials "Grid Study 2026" --venue "EnergyConf"
openscribe compile --profile research-paper
openscribe compile --profile research-paper --format pdf
```

Use this when you want a section based paper draft, source tracking files, and presentation support files.

## AI setup

`openscribe` treats AI as an optional helper layer.
The manuscript files stay the source of truth.
AI should assist review and drafting work, not become a requirement for normal writing.

If you do not want AI:

* leave `ai.enabled` set to `false`
* do not set any AI environment variables
* do not run `openscribe ai ...` commands

Nothing else in the project depends on AI being enabled.

Use the separate setup guide for full provider instructions:

* [AI setup guide](./docs/ai-setup.md)

That guide covers:

* AI install extras
* cloud API key setup
* on prem or local model setup
* project config examples
* troubleshooting

Current AI commands:

```powershell
openscribe ai summarize "The Beginning" --allow-data-transfer
openscribe ai rewrite "The Beginning" --allow-data-transfer
openscribe ai outline "The Beginning" --allow-data-transfer
openscribe ai analyze "The Beginning" --focus pacing --allow-data-transfer
openscribe ai analyze "The Beginning" --focus continuity --allow-data-transfer
openscribe ai analyze "The Beginning" --focus pov --allow-data-transfer
openscribe ai analyze "The Beginning" --focus prose --allow-data-transfer
openscribe ai metadata "The Beginning" --allow-data-transfer
openscribe ai brainstorm "The Beginning" --question "What could fail next?" --allow-data-transfer
openscribe ai query "Where was the ledger last seen?" --allow-data-transfer
```

For hosted providers, `openscribe` refuses to send manuscript text unless that
command includes `--allow-data-transfer`. Before each request, it reports the
provider, model, and number of characters being sent. Only a loopback endpoint
is exempt, regardless of the provider name. A nonlocal OpenAI-compatible endpoint
requires HTTPS and the flag. These commands print suggestions and never write them to manuscript files.

## AI architecture

The current code uses a small provider adapter layer in `src/openscribe/ai.py`.

The design is simple:

1. load provider settings from `.openscribe/project.yaml`
2. normalize the manuscript text that will be sent to the model
3. route the request through the configured provider adapter
4. return plain text back to the CLI
5. avoid silent writes into manuscript files

That keeps the AI layer replaceable.
It also means the same command surface can work across multiple vendors.

### Command layout

Keep AI features separate from the core writing commands.

Available commands:

* `openscribe ai summarize`
* `openscribe ai rewrite`
* `openscribe ai outline`
* `openscribe ai analyze`
* `openscribe ai brainstorm`
* `openscribe ai metadata`
* `openscribe ai query`

### Safe behavior

AI output should not overwrite chapters automatically.

Safer pattern:

1. generate output
2. show it in the terminal
3. let the user decide whether to copy it into the manuscript or notes

## How to implement major AI providers

The clean way is to keep one provider interface and one adapter per platform.

Suggested internal shape:

```python
class ProviderAdapter:
    def summarize(self, text: str, model: str, context_label: str) -> str:
        raise NotImplementedError
```

Then implement one adapter per vendor and keep the CLI unaware of vendor details.

### OpenAI

Use the Responses API for new work.

Minimal Python pattern:

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5.5",
    input="Summarize this chapter in five bullet points:\n\n" + chapter_text,
)

print(response.output_text)
```

Suggested config:

```yaml
ai:
  enabled: true
  provider: openai
  model: gpt-5.5
```

This is a good first provider for `openscribe` because the current code already supports it.

### Azure OpenAI

Azure OpenAI can use the same OpenAI Python client with a different `base_url`.

Minimal Python pattern:

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.environ["AZURE_OPENAI_BASE_URL"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)

response = client.responses.create(
    model="gpt-4.1",
    input="Summarize this chapter in five bullet points:\n\n" + chapter_text,
)

print(response.output_text)
```

Suggested config:

```yaml
ai:
  enabled: true
  provider: azure-openai
  model: gpt-4.1
```

In Azure, the `model` value should match your deployment name if that is how your environment is configured.

### OpenAI compatible local

This provider is for local servers that expose an OpenAI compatible API.

Examples:

* LM Studio
* Ollama with OpenAI compatibility enabled
* vLLM
* LocalAI

Suggested config:

```yaml
ai:
  enabled: true
  provider: openai-compatible-local
  model: qwen3-8b
```

Set the local base URL before running:

```powershell
$env:OPENAI_COMPATIBLE_LOCAL_BASE_URL="http://localhost:1234/v1"
```

If your local server expects a token, also set:

```powershell
$env:OPENAI_COMPATIBLE_LOCAL_API_KEY="local"
```

This provider uses the same OpenAI Python client as the hosted OpenAI path, but points it at your local server instead.

### Anthropic

Anthropic fits well as a second direct provider adapter.

Minimal Python pattern:

```python
import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Summarize this chapter in five bullet points:\n\n" + chapter_text,
        }
    ],
)

print(message.content)
```

Suggested config:

```yaml
ai:
  enabled: true
  provider: anthropic
  model: claude-sonnet-4-5
```

The current code already supports this provider.

### Google Gemini

Gemini is a good fit for a separate adapter with its own request shape.

REST shape:

```text
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
```

Python adapter shape:

```python
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Summarize this chapter in five bullet points:\n\n" + chapter_text,
)

print(response.text)
```

Suggested config:

```yaml
ai:
  enabled: true
  provider: gemini
  model: gemini-2.5-flash
```

The current code already supports this provider.

### Mistral

Mistral works well as another simple adapter for text generation features.

Minimal Python pattern:

```python
import os
from mistralai import Mistral

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

response = client.chat.complete(
    model="mistral-large-latest",
    messages=[
        {
            "role": "user",
            "content": "Summarize this chapter in five bullet points:\n\n" + chapter_text,
        }
    ],
)

print(response.choices[0].message.content)
```

Suggested config:

```yaml
ai:
  enabled: true
  provider: mistral
  model: mistral-large-latest
```

## Remaining AI work

Board-aware and element-aware prompts remain deferred. The current command set scopes every request to one chapter or the assembled project manuscript and keeps all output read only.

## Adding more providers to the codebase

When you are ready to add the next provider:

1. add the SDK dependency to `pyproject.toml`
2. add one adapter function or class in `src/openscribe/ai.py`
3. add provider specific environment validation
4. normalize the response into plain text
5. keep the CLI command surface the same
6. document the provider in this README

## Current AI scope

`openai`, `azure-openai`, `openai-compatible-local`, `anthropic`, `gemini`, and `mistral` are all wired into the CLI.
AI is still optional.
The base writing workflow works without any provider configuration or AI SDK install.

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

`notes/story-ideas/`

Use this for structured new book ideas that are not part of the current manuscript yet.

`.openscribe/templates/`

Use this for saved user defined project templates.

`.openscribe/index/`

Use this for the derived project index built from manuscript, note, research, and element data.
The index stores a SHA-256 source manifest. Search stops and asks for a rebuild
after any indexed source is edited, added, or deleted.

`.openscribe/snapshots/`

Use this for checkpoint archives and git based snapshot records.

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
Each part folder also gets a `part.yaml` file that stores the display title.

Example:

```text
manuscript/
  part-01-opening/
    part.yaml
  part-02-act-two/
    part.yaml
  part-03-ending/
    part.yaml
```

Example `part.yaml`:

```yaml
title: Opening
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
chapter_id: chapter-8f2c486b47e149f7a26dc2b3df3244fb
status: draft
label: default
synopsis: Hero meets mentor for the first time.
pov: Marcus
word_target: 2500
notes: Tighten the middle scene.
---

Marcus stepped off the train into rain and diesel smoke.

## Station Platform
<!-- openscribe-scene-id: scene-2f507e2f0ea04adca93644188df1ac66 -->

The last train pulled away.
```

`chapter_id` is generated once and stays stable when a chapter is renamed,
moved, or renumbered. Board relationships store this ID. Reading a project does
not assign or migrate identities. Use `openscribe migrate status`, followed by
`openscribe migrate apply` for an older format or `openscribe migrate repair` for
missing identities in a current-format project. Both mutation paths create a checkpoint. Metadata commands preserve
frontmatter fields they do not recognize.

Scene IDs are stored in HTML comments immediately after scene headings. They remain stable when scenes move, split, or merge and are removed from reading and compile output. Do not copy one scene ID onto another scene.

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
This is useful for outline review and the current corkboard style TUI views.

`pov`

Point of view character or narrator.

`word_target`

Target word count for the chapter.

`notes`

Internal notes for revision, continuity, or reminders.

## Writing in your editor

`openscribe` creates the files. You can write in the TUI or use an editor of your choice.

A common pattern is:

1. create the chapter with `openscribe`
2. open `manuscript\part-xx-...\ch-xx-....md` in VS Code
3. write below the frontmatter
4. keep the metadata updated as the draft changes

For integrated editing, run `openscribe tui`, select a chapter or scene, edit the middle pane, and press `Ctrl+S`. Chapter editing hides internal scene ID comments. It refuses heading renames or reorders that would make identity ambiguous. Use the scene commands for structural changes.

## Viewing the outline

Run:

```powershell
openscribe outline
```

This prints a tree of the manuscript based on the part folders and chapter files.

Example:

```text
My Novel
`-- Opening
    `-- The Beginning [draft]
```

Use this when you want a quick structural view without opening the TUI.

## Detailed outliner view

Run:

```powershell
openscribe outliner
```

This prints:

* part structure
* chapter metadata
* chapter word counts and targets
* scene counts and scene titles
* part word totals

Use this when `outline` is too light and `status` is too flat.

## Continuous manuscript view

Run:

```powershell
openscribe read
openscribe read --template manuscript
```

This prints the manuscript as one continuous reading view in binder order.
It uses the same part and chapter assembly path as compile.

Use this when you want to review the whole manuscript flow in the terminal without exporting a file first.

## Reordering parts and chapters

You can reorder manuscript structure from the CLI.

Examples:

```powershell
openscribe move part "Ending" --position 2
openscribe move chapter "Reckoning" --position 1
openscribe move chapter "Reckoning" --position 1 --part "Opening"
```

This renumbers part folders and chapter files so binder order, read order, and compile order stay aligned.

## Updating metadata

You can update part and chapter metadata from the CLI instead of hand editing YAML.

Examples:

```powershell
openscribe set part "Opening" --title "Cold Open"
openscribe set chapter "Arrival" --status revised --label action --pov Eli
openscribe set chapter "Arrival" --word-target 2500 --synopsis "Eli reaches town."
openscribe set chapter "Arrival" --notes "Tighten the station scene."
```

## Inspecting metadata

You can also inspect the current metadata directly:

```powershell
openscribe show part "Cold Open"
openscribe show chapter "Arrival"
```

## Finding chapters

You can search chapters by metadata and text.

Examples:

```powershell
openscribe find chapters --status draft
openscribe find chapters --label action --pov Eli
openscribe find chapters --part Opening
openscribe find chapters --text station
```

## Project reports

You can view project level chapter and word summaries:

```powershell
openscribe report project
```

This reports:

* chapter count
* word count
* counts by status
* counts by label
* counts by POV
* counts by part
* part word totals

## Batch updates

You can update multiple chapters at once using the same filters as `find chapters`.

Examples:

```powershell
openscribe set chapters --match-status draft --status revised
openscribe set chapters --match-part Opening --label act-one
openscribe set chapters --match-text station --notes "Needs station revision."
```

## Board mode

Board notes live separately from the manuscript until you promote them.

Examples:

```powershell
openscribe board note add "Station Secret" --body "The station master is hiding records." --group plot
openscribe board note list
openscribe board link add note-001 note-002
openscribe board group set note-002 plot
openscribe board promote note-001 --part Opening --chapter "Station Secret"
```

Board storage is plain YAML under `.openscribe/boards/default.yaml`.

## Elements and relations

You can track characters, settings, and items as structured project elements.

Examples:

```powershell
openscribe element add character "Marcus Vale" --notes "Main investigator" --tags lead,viewpoint
openscribe element alias add cha-marcus-vale "Marcus"
openscribe element add setting "North Station"
openscribe element relate cha-marcus-vale set-north-station --type visits
openscribe element show cha-marcus-vale
openscribe element appears-in Marcus
```

Element storage is plain YAML under `.openscribe/elements/elements.yaml`.

## Exporting your project

You can export the current manuscript to Word, PDF, or EPUB.
Compile behavior also reads defaults from `.openscribe/project.yaml`.

Run:

```powershell
openscribe compile
openscribe compile --format pdf
openscribe compile --format epub
```

Default output paths:

```text
build/<project-title>.docx
build/<project-title>.pdf
build/<project-title>.epub
```

You can also choose the output path:

```powershell
openscribe compile --output .\build\north-county-review.docx
openscribe compile --format pdf --output .\build\north-county-review.pdf
openscribe compile --format epub --output .\build\north-county-review.epub
```

Current behavior:

* chapter order follows numbered folders and files
* empty chapters are skipped
* the project title is added to the document
* Pandoc is used for `docx`, `pdf`, and `epub` when it is available on `PATH`
* native export remains as a fallback when Pandoc is not installed

Right now `docx`, `pdf`, and `epub` are implemented.

### Compile settings

You can control default compile behavior in `.openscribe/project.yaml`:

```yaml
compile:
  default_format: docx
  backend: auto
  default_profile: ""
  default_template: novel
  output_filename: ""
  include_title_page: true
  include_part_headings: true
  chapter_heading_style: title-only
```

Built in templates:

* `novel`
* `manuscript`
* `minimal`
* `academic`

Current settings:

* `default_format` chooses the default export format
* `backend` supports `auto`, `pandoc`, or `native`
* `default_profile` applies a named export preset when you do not pass a CLI override
* `default_template` chooses the built in template preset
* `output_filename` overrides the default build filename
* `include_title_page` turns the title page on or off
* `include_part_headings` turns part headings on or off
* `chapter_heading_style` supports `title-only`, `chapter-number-title`, or `section-number-title`

Built in compile profiles:

* `print` writes a `docx` with book style defaults
* `ebook` writes an `epub` with book style defaults
* `submission` writes a `docx` with manuscript style chapter headings and no part headings
* `research-paper` writes a `docx` with academic style numbered section headings

If you want Pandoc output, install `pandoc` and keep `backend: auto` or set `backend: pandoc`.

You can also override the profile or template from the CLI:

```powershell
openscribe compile --profile print
openscribe compile --profile ebook
openscribe compile --profile submission
openscribe compile --profile research-paper
openscribe compile --template manuscript
openscribe compile --template academic
openscribe compile --format pdf --template minimal
```

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
* chapter or scene editor and proofreading findings in the middle
* metadata summary on the right

What it does:

* reads the part and chapter structure from `manuscript/`
* reads board canvas, corkboard cards, source links, character, research, notes, story idea, and element content into the same browser
* includes a search box for filtering chapters, sources, board notes, and library content
* lets you select and edit a chapter or scene from the binder tree
* lets you select a part node to inspect part metadata
* hides internal scene ID comments while editing chapter text
* saves canonical chapter or scene text only when you press `Ctrl+S`, with a checkpoint and stale-file check
* preserves drafts across navigation and writes local recovery drafts every second
* runs configured local LanguageTool proofreading with `Ctrl+G`
* displays action and proofreading failures beside the active text
* shows chapter status, label, synopsis, point of view, notes, word target, and linked sources in the right panel
* shows part metadata, story idea metadata, element metadata, source note metadata, progress goals, and compile defaults in the right panel
* lets you move board notes with keyboard controls and save new positions immediately
* lets you hide or reveal board notes while reviewing the canvas
* includes a paired character and research view for cross checking support material
* includes quick keys to cycle chapter status, label, and point of view
* includes quick keys to raise or lower chapter word targets
* includes quick keys to promote the selected board note and run compile

The CLI is still broader for metadata editing and compile configuration.
The TUI now includes board editing, corkboard review, source link browsing, and richer library views.

Current keys:

* `q` quits the app
* `Ctrl+F` focuses the search box
* `Ctrl+S` saves the selected chapter or scene text
* `Ctrl+G` runs the configured local LanguageTool check
* `Ctrl+Arrow keys` move the selected board note
* `v` toggles the selected board note visibility
* `b` applies board auto layout
* `s` cycles the selected chapter status
* `l` cycles the selected chapter label
* `o` cycles the selected chapter point of view
* `w` raises the selected chapter word target by `250`
* `W` lowers the selected chapter word target by `250`
* `p` promotes the selected board note into a chapter
* `c` runs compile with project defaults

This is still a lightweight authoring interface. It does not provide rich text formatting or drag based manuscript reordering. Proofreading replacements require a preview and a separate apply action; they are never automatic.

## Command reference

### `openscribe init`

Initializes a new project in the target path.

```powershell
openscribe init "My Novel"
openscribe init "My Novel" --path .\books\my-novel
openscribe init "Field Guide" --template technical
openscribe init "Custom Guide" --template-file .\my-template.yaml
```

Built in project templates:

* `fiction`
* `nonfiction`
* `technical`
* `screenwriting`
* `research`

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

### `openscribe new scene`

Adds a scene heading inside a chapter file.

```powershell
openscribe new scene "Cold Open" --chapter "The Beginning"
openscribe new scene "County Road" --chapter "Arrival" --body "Eli sees the porch men again."
```

### `openscribe scene move`, `split`, and `merge`

Preview structural scene changes by default. Add `--apply` only after reviewing the unified diff. Applied changes create an automatic checkpoint.

```powershell
openscribe scene move "Cold Open" --chapter "The Beginning" --position 2
openscribe scene move "Cold Open" --chapter "The Beginning" --to-chapter "The Turn" --position 1 --apply
openscribe scene split "Cold Open" --chapter "The Beginning" --at-text "The phone rang" --new-title "The Call" --apply
openscribe scene merge "Cold Open" --with "The Call" --chapter "The Beginning" --apply
```

### `openscribe migrate status` and `apply`

Project loading does not migrate files automatically. Inspect and explicitly apply the ordered, backed-up migration path. Current-format projects with missing IDs or legacy board links can use the separate repair command.

```powershell
openscribe migrate status
openscribe migrate apply
openscribe migrate repair
```

### `openscribe new section`

Adds a nonfiction friendly section chapter.

```powershell
openscribe new section "Case Study" --part "Examples" --synopsis "Support the main claim."
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

### `openscribe compile`

Exports the current manuscript to a document file.

```powershell
openscribe compile
openscribe compile --format pdf
openscribe compile --format epub
openscribe compile --profile ebook
openscribe compile --template manuscript
openscribe compile --output .\build\my-novel.docx
openscribe compile --format pdf --output .\build\my-novel.pdf
openscribe compile --format epub --output .\build\my-novel.epub
```

### `openscribe outliner`

Prints a structure plus metadata view.

```powershell
openscribe outliner
```

### `openscribe move part`

Reorders a part in the manuscript binder.

```powershell
openscribe move part "Ending" --position 2
```

### `openscribe move chapter`

Reorders a chapter inside a part or moves it into another part.

```powershell
openscribe move chapter "Reckoning" --position 1
openscribe move chapter "Reckoning" --position 1 --part "Opening"
```

### `openscribe set part`

Updates part metadata.

```powershell
openscribe set part "Opening" --title "Cold Open"
```

### `openscribe set chapter`

Updates chapter metadata.

```powershell
openscribe set chapter "Arrival" --status revised --label action --pov Eli
openscribe set chapter "Arrival" --word-target 2500 --synopsis "Eli reaches town."
openscribe set chapter "Arrival" --notes "Tighten the station scene."
```

### `openscribe show part`

Shows part metadata.

```powershell
openscribe show part "Cold Open"
```

### `openscribe show chapter`

Shows chapter metadata.

```powershell
openscribe show chapter "Arrival"
```

### `openscribe find chapters`

Finds chapters by metadata and text.

```powershell
openscribe find chapters --status draft
openscribe find chapters --label action --pov Eli
openscribe find chapters --part Opening
openscribe find chapters --text station
```

### `openscribe find scenes`

Finds scenes by chapter filters and section text.

```powershell
openscribe find scenes --text station
openscribe find scenes --part Opening --pov Eli
```

### `openscribe report project`

Shows project level chapter and word summaries.

```powershell
openscribe report project
```

### `openscribe report scenes`

Shows scene counts grouped by chapter and part.

```powershell
openscribe report scenes
openscribe report scenes --text station
```

### `openscribe templates`

Lists built in project templates.

```powershell
openscribe templates
```

### `openscribe template save`

Saves the current project as a user defined template file.

```powershell
openscribe template save "Client Report"
```

### `openscribe index rebuild`

Builds the derived project index.

```powershell
openscribe index rebuild
```

### `openscribe index search`

Searches the derived project index.

```powershell
openscribe index search station
```

### `openscribe import folder`

Imports an existing folder based manuscript project.

```powershell
openscribe import folder C:\books\old-draft --title "Imported Draft"
openscribe import folder C:\books\old-draft --title "Imported Screenplay" --template screenwriting
```

### `openscribe snapshot save`

Creates a project snapshot.

```powershell
openscribe snapshot save "first-pass"
openscribe snapshot save "clean-head" --mode git
```

### `openscribe snapshot list`

Lists saved snapshots.

```powershell
openscribe snapshot list
```

### `openscribe snapshot diff`

Shows the current diff against a saved snapshot.

```powershell
openscribe snapshot diff before-rewrite
```

### `openscribe snapshot restore`

Previews an exact restore from a saved snapshot. No files change without
`--apply`.

```powershell
openscribe snapshot restore before-rewrite
openscribe snapshot restore before-rewrite --apply
```

An applied restore first creates an automatic checkpoint. It then restores the
saved managed files and removes managed files that were created after the
snapshot.

### `openscribe workflow screenplay-scene`

Adds an uppercased screenplay slugline scene inside a chapter.

```powershell
openscribe workflow screenplay-scene "INT. DINER - NIGHT" --chapter "Opening"
```

### `openscribe workflow nonfiction-section`

Creates a nonfiction style section chapter.

```powershell
openscribe workflow nonfiction-section "Background" --part "Section One"
```

### `openscribe workflow research-paper`

Creates a standard research paper section scaffold.

```powershell
openscribe workflow research-paper --part "Paper"
openscribe workflow research-paper --part "Paper" --include-appendix
```

### `openscribe workflow conference-materials`

Creates conference submission notes, talk outlines, slide drafts, speaker notes, timed talk plans, poster revision logs, and submission status files.

```powershell
openscribe workflow conference-materials "Grid Study 2026" --venue "EnergyConf"
openscribe workflow conference-materials "Grid Study 2026" --venue "EnergyConf" --no-poster
```

### `openscribe workflow conference-schedule-import`

Imports a conference schedule from `csv`, `tsv`, `json`, `yaml`, or `yml`.
It creates a schedule overview, a session checklist, and per session notes with ready to use review checklists.

```powershell
openscribe workflow conference-schedule-import .\energyconf-schedule.csv --venue "EnergyConf"
openscribe workflow conference-schedule-import .\energyconf-schedule.json --venue "EnergyConf" --no-create-checklists
```

### `openscribe workflow source-note`

Creates a structured nonfiction or research source note.

```powershell
openscribe workflow source-note "River Ledger Study" --type article --author "J. Harper" --year 2024 --url "https://example.com/ledger"
```

### `openscribe workflow citation-pack`

Creates the shared citation tracking files for nonfiction or research projects.

```powershell
openscribe workflow citation-pack --style Chicago
openscribe workflow citation-pack --style APA
```

### `openscribe workflow cite`

Inserts a source citation marker into a chapter or a named scene.

```powershell
openscribe workflow cite --chapter "Introduction" --source "County Archive"
openscribe workflow cite --chapter "Arrival" --scene "Station Watch" --source "County Archive" --style Chicago
```

### `openscribe set goals`

Updates project level draft targets and deadlines.

```powershell
openscribe set goals --draft-word-target 90000 --session-word-target 1200 --deadline 2026-08-01
```

### `openscribe set compile-research`

Updates bibliography and citation related compile settings.

```powershell
openscribe set compile-research --citation-style Chicago --include-bibliography --bibliography-title "Works Cited"
openscribe set compile-research --citation-style APA --no-include-reference-heading
```

### `openscribe set chapters`

Updates multiple chapters at once.

```powershell
openscribe set chapters --match-status draft --status revised
openscribe set chapters --match-part Opening --label act-one
openscribe set chapters --match-text station --notes "Needs station revision."
```

### `openscribe board note add`

Adds a board note.

```powershell
openscribe board note add "Station Secret" --body "The station master is hiding records." --group plot
```

### `openscribe board note list`

Lists board notes.

```powershell
openscribe board note list
```

### `openscribe board chapter add`

Adds an explicit link between a board note and a chapter.

```powershell
openscribe board chapter add note-001 "Arrival"
```

### `openscribe board chapter remove`

Removes an explicit link between a board note and a chapter.

```powershell
openscribe board chapter remove note-001 "Arrival"
```

### `openscribe board note move`

Moves a board note to a saved canvas position.

```powershell
openscribe board note move note-001 --x 24 --y 8
```

### `openscribe board layout auto`

Applies a simple automatic board layout.

```powershell
openscribe board layout auto
```

### `openscribe board view`

Renders a simple board canvas in the terminal.

```powershell
openscribe board view
```

### `openscribe board promote`

Promotes a board note into manuscript structure.

```powershell
openscribe board promote note-001 --part Opening --chapter "Station Secret"
```

### `openscribe idea add`

Adds a structured story idea for a future book.

```powershell
openscribe idea add "The Flood Ledger" --premise "A county clerk finds a ledger that predicts deaths." --genre "Southern Gothic" --tone "Uneasy"
```

### `openscribe idea list`

Lists stored story ideas.

```powershell
openscribe idea list
```

### `openscribe show idea`

Shows one story idea with all stored fields.

```powershell
openscribe show idea "The Flood Ledger"
```

### `openscribe element add`

Adds an element record.

```powershell
openscribe element add character "Marcus Vale" --notes "Main investigator" --tags lead,viewpoint
```

### `openscribe element show`

Shows an element record.

```powershell
openscribe element show cha-marcus-vale
```

### `openscribe element set`

Updates one element record.

```powershell
openscribe element set cha-marcus-vale --notes "Lead investigator" --tags lead,viewpoint
```

### `openscribe element set-many`

Updates multiple element records at once.

```powershell
openscribe element set-many --match-type character --add-tags viewpoint
openscribe element set-many --match-tag lead --notes "Needs arc review."
```

### `openscribe element appears-in`

Shows matching chapters for an element name or alias.

```powershell
openscribe element appears-in Marcus
```

### `openscribe open chapter`

Opens a chapter file in your editor.

```powershell
openscribe open chapter "Arrival"
```

### `openscribe open part`

Opens a part folder in your editor.

```powershell
openscribe open part "Opening"
```

### `openscribe open search`

Opens the first or indexed chapter search result in your editor.

```powershell
openscribe open search --text station
openscribe open search --text station --index 2
```

### `openscribe element unrelate`

Removes a stored relation.

```powershell
openscribe element unrelate cha-marcus-vale set-north-station --type visits
```

### `openscribe read`

Prints the manuscript as one continuous reading view.

```powershell
openscribe read
openscribe read --template manuscript
```

### `openscribe tui`

Opens the Textual interface.

```powershell
openscribe tui
```

### `openscribe proofread chapter`

Runs a read-only LanguageTool check. Hosted endpoints require `--allow-data-transfer`.

```powershell
openscribe proofread chapter "The Beginning"
```

### `openscribe ai`

Runs read-only manuscript review and suggestion tasks. Use `openscribe ai --help` for the full command list. Hosted providers require `--allow-data-transfer` on every invocation.

```powershell
openscribe ai analyze "The Beginning" --focus pacing --allow-data-transfer
openscribe ai query "Which clues remain unresolved?" --allow-data-transfer
```

## Example session

This is a full example from an empty folder.

```powershell
mkdir novel-demo
Set-Location .\novel-demo
openscribe init "North County" --template fiction
openscribe new part "Opening"
openscribe new chapter "Arrival" --part "Opening" --pov "Eli" --word-target 1800
openscribe new scene "Bus Stop" --chapter "Arrival"
openscribe workflow screenplay-scene "EXT. COURTHOUSE - DAY" --chapter "Arrival"
openscribe new chapter "The Call" --part "Opening" --pov "Eli" --word-target 2200
openscribe set chapter "Arrival" --status revised
openscribe find chapters --status revised
openscribe report project
openscribe index rebuild
openscribe index search station
openscribe board note add "Ledger clue" --body "Eli finds the missing ledger." --group plot
openscribe board layout auto
openscribe board view
openscribe board promote note-001 --part Opening --chapter "Ledger clue"
openscribe idea add "The Flood Ledger" --premise "A county clerk finds a ledger that predicts deaths."
openscribe element add character "Eli Harper" --notes "Main point of view"
openscribe snapshot save "after-outline"
openscribe proofread chapter "Arrival"
openscribe compile
openscribe compile --format pdf
openscribe compile --format epub
openscribe read
openscribe show chapter "Arrival"
openscribe outline
openscribe status
openscribe tui
```

After that, open the chapter files in your editor and start writing.

## Example project

If you want to inspect a real sample project instead of creating one from scratch, use the checked in example at `examples/north-county/`.

It includes:

* a real `.openscribe/project.yaml`
* sample board and element storage under `.openscribe/`
* saved user template files under `.openscribe/templates/` when you create them
* a manuscript folder with one part and two chapters
* sample character, research, and notes files

Quick start:

```powershell
Set-Location .\examples\north-county
py -3.11 -m openscribe outline
py -3.11 -m openscribe status
py -3.11 -m openscribe tui
```

## Working with git

`openscribe` works well with git because the source files are plain text.

A simple pattern:

* keep the whole project in a git repo
* commit after major writing sessions
* use diffs to review revisions
* branch if you want to test major structural changes

You can also record snapshots from inside `openscribe`:

* `openscribe snapshot save "label"` creates a checkpoint archive
* `openscribe snapshot save "label" --mode git` records the current git commit and dirty state and includes a restorable archive
* `openscribe snapshot restore "label"` previews an exact restore
* `openscribe snapshot restore "label" --apply` creates a backup and applies it

## Current limitations

See [TECH-DEBT.md](./TECH-DEBT.md) for current compromises and [assessment.md](./assessment.md) for their effect on repository health.

## Roadmap

See [future-upgrades.md](./future-upgrades.md). The current milestone adds shared editing protection, a desktop writing workflow, actionable local proofreading, and an experimental Word round-trip implementation. Real Word host validation, independent review, and broader manual accessibility testing remain release gates.
