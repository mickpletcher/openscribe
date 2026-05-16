# openscribe assessment

## current state

`openscribe` is now a real manuscript workflow tool.
It is past the early scaffold stage.
The repo supports project setup, manuscript structure, metadata editing, search, reporting, planning notes, board layout, element tracking, source tracking, snapshots, editor launch, continuous reading, TUI inspection, import, and export.

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
13. create source notes and citation tracking files for nonfiction or research work
14. compile research drafts with bibliography and reference formatting controls
15. insert source citations into chapters or named scenes from the CLI
16. create conference submission notes, slide drafts, timed talk plans, poster revision logs, and talk outlines
17. read the manuscript as one continuous document
18. reorder parts and chapters from the CLI
19. inspect a richer outliner view with scene counts, part totals, and metadata filters
20. export to `docx`, `pdf`, and `epub` with print, ebook, submission, and research paper profiles

The planning and tracking layer is also real:

1. board notes can be added, grouped, linked, explicitly attached to chapters, and promoted into chapters
2. board notes can be moved, auto laid out, rendered in a terminal board view, and repositioned inside the TUI
3. elements can be tracked as characters, settings, and items
4. aliases and relations are stored explicitly
5. chapter appearance lookup works across chapter text and metadata
6. story ideas can be stored separately from the active manuscript
7. the TUI can browse the board canvas, corkboard cards, source links, characters, research, notes, story ideas, and elements
8. project goals, deadlines, and progress stats are visible in reports and the TUI
9. snapshots can now be listed, diffed, and restored
10. editor launch helpers can open chapters, parts, and search matches directly
11. the TUI can now cycle chapter label, point of view, and word target in addition to status
12. conference schedule files can now be imported into session schedule and checklist documents

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

### 1. the TUI is much stronger, but freeform editing is still selective

The TUI now does more than browse.
It can move board notes, hide them, render corkboard cards, show source links, cycle chapter status, label, and point of view, adjust word targets, promote notes, and run compile.
The CLI is still the broader control surface for freeform metadata editing, relation authoring, and compile configuration.

### 2. compile formatting is broader, but still fairly shallow

Pandoc support improves the backend story, but the formatting model is still small.
The current templates and profiles are useful, not rich.
The export intent is clearer now, and research compile settings now cover bibliography output, but the formatting depth is still limited.

### 3. board mode is more useful now, but still early

The board model has improved.
It now supports saved positions, automatic layout, a terminal board view, and TUI note movement.
It still does not have denser canvas controls, drag gestures, or richer visual grouping behavior.

### 4. import and template flows are practical, not yet deep

The repo can now import simple folder based manuscripts and reuse user templates.
That is a real workflow gain.
It is still early compared with a mature importer or a broader template marketplace.

### 5. snapshot safety is better, but still not complete

The repo can now save, diff, and restore snapshots.
That is a meaningful improvement.
It still needs more guided recovery flow and clearer restore previews.

### 6. element appearance tracking is still heuristic

The current appears in model is derived from name and alias matches in chapter text and metadata.
That is acceptable for now.
It will eventually need scene awareness or explicit tagging if the repo grows into denser manuscripts.

### 7. roadmap discipline depends on keeping the docs current

The repo now has several source of truth files:

1. `assessment.md`
2. `changelog.md`
3. `completed-upgrades.md`
4. `getting-started.md`
5. local `future-upgrades.md`

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

Deepen project recovery and chapter split workflows.

The recovery story is now real.
The next step is safer restore previews, snapshot comparison summaries, and stronger restructuring helpers for large drafts.

### priority 2

Deepen scene workflows.

The repo has scene support, scene aware search, and scene reporting.
The next step is stronger scene reordering, scene metadata, and better split or merge helpers for large chapters.

### priority 3

Deepen compile formatting beyond the current profile layer.

The repo now separates export intent with:

1. print
2. ebook
3. submission
4. research paper

The next step is richer profile level formatting, venue specific bibliography styles, and stronger citation insertion helpers.

### priority 4

Deepen the board, element, and TUI integration.

The board and element features exist now.
The next value is tighter connection between them and the manuscript:

1. chapter links to related elements, board notes, and source notes should deepen beyond the current basics
2. synopsis and notes editing should move into the TUI next
3. richer compare views and deeper binder filtering should continue
4. stronger canvas controls beyond the current keyboard movement should land next

### priority 5

Deepen the AI layer with review and suggestion workflows.

The provider layer is broader than the current command surface.
The next value is not generic chat.
It is workflow specific review and drafting support:

1. chapter analysis for pacing, continuity, and point of view drift
2. scoped rewrite suggestions that never overwrite manuscript files silently
3. metadata, outline, and project query assistance on top of the current manuscript model
4. compile review and conference material refinement once the earlier AI review path is stable

## bottom line

The repo has crossed the important threshold.
It is no longer proving that the app can exist.
It is now proving that the workflow can hold together.

The next stage should focus on tightening the surfaces that already exist instead of adding broad new domains too early.
