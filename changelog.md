# changelog

## 2026-05-15

### Getting started guide

* added root `getting-started.md` as the fastest beginner setup path for install, first project creation, TUI use, and export
* linked `getting-started.md` from `README.md`
* updated `assessment.md` so the guide is treated as part of the repo source of truth documentation set

### Assessment and quality

* added `assessment.md` with a current project review, risks, and next priority recommendations
* fixed the outline status rendering bug so chapter status displays literally in the tree output
* added a basic pytest suite for project initialization, chapter parsing, outline output, and compile output

### Example project

* added `examples/north-county/` as a checked in sample project
* added sample manuscript chapters, project config, character notes, research notes, and revision notes
* linked the sample project and assessment from `README.md`

### Compile workflow

* added `openscribe compile`
* added manuscript export to Microsoft Word `.docx`
* added manuscript export to `.pdf`
* added manuscript export to `.epub`
* added compile output defaults under the project `build/` folder
* added `--format` and `--output` support for compile exports

### Dependencies and docs

* added `python-docx` for Word export
* added `reportlab` for PDF export
* added `EbookLib` for EPUB export
* updated `README.md` to document the example project, compile command, and all supported export formats

### AI provider parity

* added Anthropic, Gemini, and Mistral provider support to `openscribe ai summarize`
* added `openai-compatible-local` provider support for local model servers such as LM Studio, Ollama compatibility mode, vLLM, and LocalAI
* changed AI provider SDK loading to lazy imports so non AI installs stay clean
* moved AI SDKs into an optional `ai` extras group in `pyproject.toml`
* updated `README.md` so the AI setup and provider list match the current code
* added provider routing tests for OpenAI, Azure OpenAI, Anthropic, Gemini, and Mistral

### AI documentation

* added `docs/ai-setup.md` with separate AI setup guidance
* documented cloud API key providers and on prem or local model server setup in one guide
* linked the new AI setup guide from the root `README.md`

### Part display titles

* added `part.yaml` metadata files inside manuscript part folders
* separated part display titles from part folder names in the project model
* updated outline, status, TUI, and compile exports to show part titles instead of storage folder ids
* updated the sample project and README files to document the new part metadata file

### Compile settings

* added configurable compile settings in `.openscribe/project.yaml`
* added built in compile templates named `novel`, `manuscript`, and `minimal`
* added support for compile output filename override, title page toggle, part heading toggle, and chapter heading style
* added `--template` support to `openscribe compile`
* added tests that verify compile settings change the generated output

### Continuous manuscript view

* added `openscribe read` to print the manuscript as one continuous reading view
* reused the compile assembly path so reading order and template behavior stay aligned with exports
* added tests and README updates for the new reading command

### Metadata commands

* added `openscribe set part` and `openscribe set chapter` for metadata updates without hand editing YAML
* added `openscribe show part` and `openscribe show chapter` for metadata inspection
* added tests and README updates for the new metadata command surface

### Search and query

* added `openscribe find chapters` for chapter lookup by status, label, POV, part, and text
* added tests for metadata filtering and text search
* updated the README and sample project guide for the new query workflow

### TUI improvements

* added a TUI search box for filtering chapters by title, synopsis, notes, and body text
* added part metadata inspection from binder part nodes
* added project compile setting visibility in the TUI metadata panel
* added TUI tests for search filtering behavior

### Reports and batch updates

* added `openscribe report project` for chapter counts, word totals, and grouped metadata summaries
* added `openscribe set chapters` for batch chapter metadata updates using the same filters as chapter search
* added tests for reporting output and batch metadata updates

### Board mode

* added CLI first board note storage under `.openscribe/boards/`
* added board note creation, listing, grouping, linking, and promotion into manuscript chapters
* aligned board promotion with the current part and chapter metadata model
* added tests for board note workflows and chapter promotion

### Elements and relations

* added element storage under `.openscribe/elements/`
* added element records for characters, settings, and items
* added alias support, relation tracking, and chapter appearance lookup derived from manuscript text and metadata
* added tests for element creation, relation output, and appears in queries

### Larger manuscript regression coverage

* added multi part read regression coverage for binder order across larger sample manuscripts
* added export regression coverage that verifies compiled `.docx` output preserves multi part chapter order
* updated the README and sample project guide for reports, board mode, and element tracking

### Pandoc compile backend

* updated `openscribe compile` to prefer Pandoc for `docx`, `pdf`, and `epub` when `pandoc` is available on `PATH`
* kept the native export path as a fallback when Pandoc is not installed
* added compile backend settings so projects can choose `auto`, `pandoc`, or `native`
* added tests for the Pandoc compile path and TUI metadata coverage

### Upgrade tracking

* added tracked `completed-upgrades.md` for shipped roadmap items
* updated `README.md` to link `completed-upgrades.md` and clarify that `future-upgrades.md` stays local
* refreshed `future-upgrades.md` so completed items move out and new ideas replace them

### Assessment maintenance

* refreshed `assessment.md` so it reflects the current CLI, TUI, compile, board, and element feature set
* established `assessment.md` as a file that should be updated whenever repo changes materially affect project status or priorities

### Story ideas

* added `openscribe idea add` for capturing structured new book ideas under `notes/story-ideas/`
* added `openscribe idea list` and `openscribe show idea` for inspecting stored story ideas
* added model and CLI tests for story idea creation and listing
* updated the README, sample project, completed upgrades log, future upgrades file, and assessment for the new idea workflow

### Templates, snapshots, scenes, index, and TUI library views

* added built in project templates for fiction, nonfiction, and technical writing through `openscribe init --template`
* added `openscribe new scene` and scene parsing inside chapter files
* added `openscribe index rebuild`, `openscribe index show`, and `openscribe index search`
* added `openscribe snapshot save` and `openscribe snapshot list` for checkpoint and git based snapshots
* expanded the TUI so it can browse characters, research, notes, story ideas, and elements
* updated the sample project, README, assessment, completed upgrades log, and future upgrades file for the new workflow surface

### Custom templates, import, screenwriting or nonfiction helpers, and richer board visuals

* added user defined template saving through `openscribe template save` and reuse through `openscribe init --template-file`
* added `openscribe import folder` for existing folder based manuscript projects
* added nonfiction section and screenplay scene workflow helpers
* added board note movement, board auto layout, and a terminal board view command
* updated tests, README, sample project guide, completed upgrades log, future upgrades file, and assessment for the expanded workflow support

## 2026-05-14

### Initial scaffold

* created the Python package structure for `openscribe`
* added `pyproject.toml` with CLI entrypoint and core dependencies
* added the `openscribe` CLI with `init`, `new part`, `new chapter`, `outline`, `status`, and `tui`
* added project initialization and manuscript file management
* added a lightweight Textual TUI for binder style manuscript browsing

### Documentation

* rewrote `README.md` into a detailed usage guide
* documented installation, project setup, command usage, frontmatter fields, workflow, and current limitations
* added a root link to this changelog from `README.md`

### Repo planning

* added a root `future-upgrades.md` planning file for local roadmap tracking
* updated `.gitignore` so `future-upgrades.md` stays local only

### Specification

* added `specs/001-compile-pipeline/` for the first GitHub Spec package
* defined requirements, scope, plan, and tasks for the first compile milestone
* linked the spec package from `README.md`

### Feature planning refresh

* updated `future-upgrades.md` to reflect the current MVP feature order based on Scrivener style gaps
* updated the compile spec so it stays focused on compile while preserving room for a later Scrivenings style feature
* added a second spec package for a lightweight planning board mode inspired by Scapple style freeform note mapping
* updated board planning to absorb the useful LivingWriter board ideas without taking on cloud, AI, or collaboration scope
* added a third spec package for elements, aliases, relations, and appears in tracking

### AI integration

* added an optional `openscribe ai summarize` command for chapter review
* added project level AI settings in `.openscribe/project.yaml`
* added provider routing for `openai` and `azure-openai`
* expanded `README.md` with setup guidance for OpenAI, Azure OpenAI, Anthropic, Gemini, and Mistral
* clarified in `README.md` that AI is not required for normal `openscribe` setup or usage

### Structure management and compile intent

* added `openscribe outliner` to show structure, metadata, scenes, chapter targets, and part word totals together
* added `openscribe move part` and `openscribe move chapter` so manuscript order can be changed without hand renaming folders or files
* added compile profiles named `print`, `ebook`, and `submission`
* updated compile resolution so profiles can choose default format, template, and output naming unless the CLI overrides them
* added `default_profile` support in `.openscribe/project.yaml`
* fixed the continuous read path so it uses the current compile option resolver
* added regression tests for outliner output, reordering commands, and compile profiles
* updated the sample project, `README.md`, `assessment.md`, `completed-upgrades.md`, and local `future-upgrades.md`

### Research and conference workflows

* added a built in `research` project template
* added an `academic` compile template and a `research-paper` compile profile
* added support for `section-number-title` academic style headings in compile output
* added `openscribe workflow research-paper` to scaffold standard paper sections
* added `openscribe workflow conference-materials` to create conference abstracts, submission checklists, talk outlines, slide drafts, speaker notes, and poster outlines
* added regression tests for research paper compile output and conference material generation
* updated `README.md`, `assessment.md`, `completed-upgrades.md`, and local `future-upgrades.md`

### Roadmap review refresh

* moved snapshot restore and diff helpers up to the top roadmap tier
* added roadmap items for scene aware search and reporting, TUI quick actions, and chapter split or merge helpers
* refreshed `assessment.md` so the next priorities match the revised roadmap

### Nonfiction source tracking and TUI board canvas

* added `openscribe workflow source-note` for structured nonfiction or research source notes
* added `openscribe workflow citation-pack` for shared citation tracking files
* updated nonfiction and research templates to include citation log and bibliography note scaffolds
* added board canvas preview and board note inspection inside the TUI binder
* added regression coverage for the new source tracking workflows and board canvas summaries
* updated `README.md`, the sample project guide, `assessment.md`, `completed-upgrades.md`, and local `future-upgrades.md`

### TUI board editing, source links, goal stats, and research compile controls

* added TUI board note movement with keyboard controls and saved position updates
* added TUI board note visibility toggles, richer canvas summaries, and stronger board preview metadata
* added source to chapter link views in the binder and chapter metadata panels
* added corkboard style synopsis cards and a paired character plus research library view in the TUI
* added project goal tracking for draft targets, session targets, deadlines, and progress reporting
* added `openscribe set goals` and `openscribe set compile-research` to manage progress and bibliography settings
* added batch element updates and relation removal commands under `openscribe element`
* added bibliography aware research compile output controls for `docx`, `pdf`, `epub`, and continuous read assembly
* added regression coverage for the new TUI views, board editing, element batch updates, relation removal, and research compile behavior
* updated `README.md`, the sample project guide, `assessment.md`, `completed-upgrades.md`, and local `future-upgrades.md`

### Recovery, editor launch, scene search, and explicit board links

* added `openscribe snapshot diff` and `openscribe snapshot restore` for checkpoint and git based snapshot workflows
* added `openscribe open chapter`, `openscribe open part`, and `openscribe open search` to launch files and folders in the editor
* added outliner filters by status, label, part, and point of view
* added `openscribe find scenes` and `openscribe report scenes` for scene aware search and reporting across chapter sections
* added TUI quick actions for chapter status cycling, board note promotion, and compile runs
* expanded conference material generation with timed talk plans, poster revision logs, and submission status files
* added `openscribe workflow cite` for source citation insertion into chapters and named scenes
* added explicit board note to chapter link commands plus TUI chapter and binder visibility for those links
* added regression coverage for snapshot restore and diff, editor launch helpers, outliner filters, scene search, conference support, citation insertion, board chapter links, and TUI quick actions
* updated `README.md`, the sample project guide, `assessment.md`, `completed-upgrades.md`, and local `future-upgrades.md`
