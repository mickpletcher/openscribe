# completed upgrades

Tracked record of roadmap items that shipped.

## 2026-09-04

### Data integrity baseline

* preserved unknown metadata and introduced immutable chapter IDs with automatic migration
* moved board chapter links to chapter IDs and migrated legacy references
* made snapshot restore exact, preview first, staged, automatically backed up, and rollback protected
* validated all persisted YAML structures and restricted template files to safe project paths
* replaced index modification time freshness with SHA-256 source manifests

### Test, package, and user safety baseline

* added CI coverage for Python 3.11, 3.12, and 3.13
* enforced an 80 percent test coverage floor plus Ruff, package build, and CLI smoke checks
* added mounted TUI interaction tests and visible mutation and compile errors
* required an explicit manuscript data transfer flag before hosted AI requests

### Versioned migrations and recoverable restore

* resolved TD-001 with a project format version, ordered migration registry, automatic pre-migration checkpoint, and rollback tests
* added immutable inline scene IDs without exposing those IDs in compiled or continuous-reading output
* resolved TD-002 with a durable restore transaction journal and automatic startup recovery at both replacement boundaries
* completed a byte-for-byte restore drill against a disposable copy of the checked-in sample project

### Scene authoring, proofreading, and AI review

* added preview-first scene move, split, and merge commands within and across chapters with automatic checkpoints on apply
* added an editable chapter and scene surface to the TUI with explicit save behavior
* displayed local LanguageTool findings beside TUI manuscript text and visibly blocked hosted proofreading from that surface
* added read-only AI rewrite, outline, pacing, continuity, point-of-view, prose, metadata, brainstorming, and project-query commands under the existing hosted-transfer approval boundary

### Word round-trip design

* defined content-control identity, a DOCX manifest, local baselines, three-way conflicts, tracked-change refusal, preview, backup, rollback, local-bridge security, and real Word validation in `specs/004-word-round-trip/`

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

### Structure management and export intent

* added a detailed outliner view that combines structure, metadata, scenes, and word counts
* added chapter and part reordering commands that renumber manuscript storage cleanly
* added compile profiles for print, ebook, and submission exports

### Research and conference workflow

* added compile support for research papers with an academic template and a `research-paper` profile
* added research project templates and paper section scaffolding helpers
* added conference material and presentation draft workflows for abstracts, slide drafts, talk outlines, speaker notes, and poster outlines

### Nonfiction source tracking and board canvas

* added nonfiction source note creation and citation tracking pack workflows
* added board canvas preview and board note inspection inside the TUI

### TUI board editing, progress goals, source links, and research compile controls

* added board note movement and visibility editing inside the TUI with saved positions
* added source to chapter link views in the binder and chapter metadata panels
* added corkboard style synopsis cards plus richer TUI filtering, previews, and library pair views
* added project goals and progress stats for targets and deadlines in reports and the TUI
* added batch element updates, relation removal commands, and citation aware research compile settings with bibliography controls

### Snapshot restore, editor launch, scene search, and conference support

* added snapshot restore and snapshot diff helpers for checkpoint and git based project snapshots
* added editor launch helpers for chapters, parts, and chapter search results
* added outliner filters plus scene aware search and reporting across chapter sections
* added TUI quick actions for status changes, board note promotion, and compile runs
* added richer conference output support for timed talks, poster revision logs, and submission status tracking
* added citation insertion helpers for chapters and named scenes
* added explicit board note to chapter link commands and views

### TUI metadata quick actions and conference schedule import

* added richer TUI quick actions for chapter label, point of view, and word target updates
* added conference schedule import for `csv`, `tsv`, `json`, and `yaml`
* added automated session schedule and checklist file generation from imported conference data

## 2026-09-05

### Recovery, editing, and privacy corrections

* added terminal rollback states, full journal prevalidation, empty-directory preservation, and cross-process project locks
* added child-process termination coverage at both manuscript replacement boundaries; physical power-loss behavior remains unverified under VL-005
* removed identity assignment and board migration from ordinary reads; explicit migration and repair stage changes behind a checkpoint
* refused ambiguous scene identity changes in chapter editing and retained Markdown hard breaks during explicit identity repair
* added shared stale-baseline checks, checkpointed editor saves, recoverable drafts, and Save, Discard, and Cancel navigation controls
* made AI consent depend on the actual destination rather than the provider label

### Authoring surfaces and experimental Word support

* added an optional PySide6 authoring window with binder, draft editor, research views, scene movement, compile, checkpoint, and restore actions
* completed FU-012 with background local LanguageTool checks, finding navigation, ignore, replacement preview, separate apply, stale-text refusal, and undo in the TUI and desktop
* implemented experimental tagged DOCX export, local baselines, three-way import review, tracked-change refusal, checkpointed apply, index refresh, a loopback bridge, and an Office task-pane prototype
* retained real Word, native accessibility, and independent-review gates under VL-004 and VL-006; FU-004 remains open
* resolved TD-004's missing scan configuration with dependency audit, Bandit, and reviewed-baseline secret scanning in CI; new hosted runs remain unverified
