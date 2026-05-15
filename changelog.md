# changelog

## 2026-05-15

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
