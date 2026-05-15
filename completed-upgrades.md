# completed upgrades

Tracked record of roadmap items that shipped.

## 2026-05-15

### Core writing workflow

* added `openscribe compile` with Pandoc first output for `docx`, `pdf`, and `epub`, with native fallback when Pandoc is not installed
* added default compile templates for book manuscript output
* added `openscribe read` for a Scrivenings style continuous manuscript view
* made status, label, synopsis, point of view, notes, and word target first class in the CLI and TUI

### Supporting coverage

* added tests for project initialization, file creation, frontmatter parsing, and manuscript ordering
* added larger regression coverage for multi part read and export flows

### Planning and idea capture

* added structured story idea capture, listing, and inspection for future books under `notes/story-ideas/`

### Structure and workflow depth

* added snapshots with checkpoint archives and git based commit records
* added scene level support inside chapter files
* added a derived project index for faster search and reporting workflows
* added character, notes, research, story idea, and element views inside the TUI
* added built in project templates for fiction, nonfiction, and technical writing

### Custom templates, import, and expanded workflows

* added user defined project templates that can be saved from a project and reused with `--template-file`
* added import helpers for existing folder based manuscript projects
* added screenwriting and nonfiction specific workflow helpers
* added richer board layout and terminal board view commands
