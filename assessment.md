# openscribe assessment

## current state

`openscribe` is now a real manuscript workflow tool.
It is past the early scaffold stage.
The repo supports project setup, manuscript structure, metadata editing, search, reporting, planning notes, board layout, element tracking, import, continuous reading, and export.

The product shape is clear now.
Markdown and YAML remain the source of truth.
The CLI is the primary surface.
The TUI is a read and inspection surface with metadata visibility and search.

## what is working now

The manuscript path is real and usable:

1. initialize a project
2. create parts and chapters
3. edit chapter metadata from the CLI
4. query chapters by status, label, point of view, part, or text
5. inspect reports and word totals
6. capture structured story ideas for future books
7. work with scene headings inside chapter files
8. rebuild a derived project index for search and reporting
9. save snapshots as checkpoints or git based records
10. save and reuse user defined project templates
11. import an existing folder based manuscript into a new project
12. use nonfiction, screenplay, and research paper workflow helpers
13. create conference submission notes, slide drafts, and talk outlines
14. read the manuscript as one continuous document
15. reorder parts and chapters from the CLI
16. inspect a richer outliner view with scene counts and part totals
17. export to `docx`, `pdf`, and `epub` with print, ebook, submission, and research paper profiles

The planning and tracking layer is also real:

1. board notes can be added, grouped, linked, and promoted into chapters
2. board notes can be moved, auto laid out, and rendered in a terminal board view
3. elements can be tracked as characters, settings, and items
4. aliases and relations are stored explicitly
5. chapter appearance lookup works across chapter text and metadata
6. story ideas can be stored separately from the active manuscript
7. the TUI can browse characters, research, notes, story ideas, and elements

The quality baseline is better than it was at the start.
There is now regression coverage across compile, read, metadata, query, board, element, and TUI behaviors.

## strengths

### clear file first model

The strongest part of the repo is still the storage model.
Project data is readable on disk.
That keeps the tool compatible with git, backups, and outside editors.

### better manuscript model

The app has moved past raw folder browsing.
Parts have display titles.
Chapters have first class metadata.
Exports, status views, read mode, and queries all reuse the same ordered manuscript model.

### practical feature layering

The feature order has mostly been good.
Compile, read, metadata editing, and search landed before heavier visual features.
That kept the core writing path ahead of the novelty layer.

### healthier test position

This is no longer a no test repo.
There is still room to grow, but the project now has enough coverage to change the core model with less risk.

## current issues

### 1. the TUI still lags behind the CLI

The CLI is now the real control surface.
The TUI is useful, but it is still mostly inspection and navigation.
Board workflows, reports, element editing, and metadata updates are still command first.

### 2. compile formatting is broader, but still fairly shallow

Pandoc support improves the backend story, but the formatting model is still small.
The current templates and profiles are useful, not rich.
The export intent is clearer now, but the formatting depth is still limited.

### 3. board mode is more useful now, but still early

The board model has improved.
It now supports saved positions, automatic layout, and a terminal board view.
It still does not have a dedicated TUI canvas or richer interaction model.

### 4. import and template flows are practical, not yet deep

The repo can now import simple folder based manuscripts and reuse user templates.
That is a real workflow gain.
It is still early compared with a mature importer or a broader template marketplace.

### 5. snapshot restore is still missing

The repo can now save snapshots.
It cannot yet restore them through first class commands.
That means the safety story is stronger than before, but still one sided.

### 6. element appearance tracking is still heuristic

The current appears in model is derived from name and alias matches in chapter text and metadata.
That is acceptable for now.
It will eventually need scene awareness or explicit tagging if the repo grows into denser manuscripts.

### 7. roadmap discipline depends on keeping the docs current

The repo now has several source of truth files:

1. `assessment.md`
2. `changelog.md`
3. `completed-upgrades.md`
4. local `future-upgrades.md`

That is the right structure.
It only works if those files stay synchronized every time the repo changes.

## delivery assessment

The repo now feels like a strong CLI first alpha rather than a prototype.

That matters.
The tool can already support a real writing loop:

1. plan with notes or board items
2. create or promote manuscript structure
3. write in Markdown
4. inspect metadata and progress
5. read continuously
6. export to common output formats

That is enough to validate the product direction with actual use.

## what to do next

### priority 1

Add snapshot restore and project recovery helpers.

Checkpoint creation is useful.
Recovery needs the other half of the workflow.

### priority 2

Deepen scene workflows.

The repo has scene support and the outliner now exposes scene counts and titles.
The next step is stronger scene reordering, scene metadata, scene aware search or reporting, and better split or merge helpers for large chapters.

### priority 3

Deepen compile formatting beyond the current profile layer.

The repo now separates export intent with:

1. print
2. ebook
3. submission
4. research paper

The next step is richer profile level formatting, citation handling, and bibliography aware outputs.

### priority 4

Deepen the board, element, and TUI integration.

The board and element features exist now.
The next value is tighter connection between them and the manuscript:

1. chapter links to related elements
2. chapter links to board notes
3. board canvas behavior inside the TUI
4. quick TUI actions for metadata edits, chapter promotion, and compile runs

## bottom line

The repo has crossed the important threshold.
It is no longer proving that the app can exist.
It is now proving that the workflow can hold together.

The next stage should focus on tightening the surfaces that already exist instead of adding broad new domains too early.
