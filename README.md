# openscribe

Open source CLI and TUI writing environment for long form projects

## Project docs

See [changelog.md](./changelog.md) for the repo change history.
See [assessment.md](./assessment.md) for the current project assessment.
See [docs/ai-setup.md](./docs/ai-setup.md) for AI setup with cloud API keys and local model servers.
See [Spec 001](./specs/001-compile-pipeline/README.md) for the compile milestone definition.
See [Spec 002](./specs/002-board-mode/README.md) for the planning board milestone definition.
See [Spec 003](./specs/003-elements-and-relations/README.md) for the elements and relations milestone definition.
See the [North County example project](./examples/north-county/README.md) for a concrete sample project.

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
* Word document export
* PDF export
* EPUB export
* manuscript outline view
* manuscript status view
* lightweight Textual TUI
* optional AI summary command for chapter review

This build does not yet include snapshots, editor launch commands, or search indexing.

## Requirements

You need:

* Python 3.11 or newer
* PowerShell on Windows if you want to follow the examples exactly

You do not need any AI provider, API key, or AI SDK setup to use the normal project, CLI, or TUI features.

## Install

Clone the repo, create a virtual environment, activate it, then install in editable mode.

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

```powershell
py -3.11 -m openscribe --help
openscribe init "My Novel"
openscribe new part "Opening"
openscribe new chapter "The Beginning" --part "Opening"
openscribe compile
openscribe compile --format pdf
openscribe compile --format epub
openscribe outline
openscribe status
openscribe tui
```

If you only want the writing tool, you can stop there.
You can ignore the rest of the AI section completely.

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

Current AI command:

```powershell
openscribe ai summarize "The Beginning"
```

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

### Recommended command layout

Keep AI features separate from the core writing commands.

Good examples:

* `openscribe ai summarize`
* `openscribe ai rewrite`
* `openscribe ai outline`
* `openscribe ai analyze`
* `openscribe ai brainstorm`

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

## Recommended build order for AI

Do not build every AI feature at once.

Use this order:

1. `ai summarize`
2. `ai rewrite`
3. `ai outline`
4. `ai analyze`
5. board aware prompts
6. element aware prompts

That keeps the AI layer useful without letting it overtake the writing workflow.

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

## Exporting your project

You can export the current manuscript to Word or PDF.
You can export the current manuscript to Word, PDF, or EPUB.

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
* chapter text is written into a real output file

Right now `docx`, `pdf`, and `epub` are implemented.

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

### `openscribe compile`

Exports the current manuscript to a document file.

```powershell
openscribe compile
openscribe compile --format pdf
openscribe compile --format epub
openscribe compile --output .\build\my-novel.docx
openscribe compile --format pdf --output .\build\my-novel.pdf
openscribe compile --format epub --output .\build\my-novel.epub
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
openscribe compile
openscribe compile --format pdf
openscribe compile --format epub
openscribe outline
openscribe status
openscribe tui
```

After that, open the chapter files in your editor and start writing.

## Example project

If you want to inspect a real sample project instead of creating one from scratch, use the checked in example at `examples/north-county/`.

It includes:

* a real `.openscribe/project.yaml`
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

This project does not currently add snapshot commands on top of git.

## Current limitations

Right now:

* the TUI is for browsing, not editing
* word counts only reflect the chapter body text
* part names are shown from folder names
* chapter ordering is based on numbered filenames and folders
* compile currently exports to Word, PDF, and EPUB only
* no query or search command exists yet

## Roadmap

Planned next:

* compile pipeline with Pandoc
* project templates
* snapshots
* derived search index
* editor integration
