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
