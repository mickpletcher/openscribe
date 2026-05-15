# openscribe assessment

## current state

`openscribe` is now a real manuscript workflow tool.
It is past the early scaffold stage.
The repo supports project setup, manuscript structure, metadata editing, search, reporting, planning notes, element tracking, continuous reading, and export.

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
7. read the manuscript as one continuous document
8. export to `docx`, `pdf`, and `epub`

The planning and tracking layer is also real:

1. board notes can be added, grouped, linked, and promoted into chapters
2. elements can be tracked as characters, settings, and items
3. aliases and relations are stored explicitly
4. chapter appearance lookup works across chapter text and metadata
5. story ideas can be stored separately from the active manuscript

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

### 2. compile formatting is still fairly shallow

Pandoc support improves the backend story, but the formatting model is still small.
The current templates are useful, not rich.
There is no deeper profile system yet for print, ebook, and submission output.

### 3. board mode is functional but still early

The board model is right sized for now, but still simple.
It stores notes, groups, links, and promotion paths.
It does not yet provide a stronger visual layout or a dedicated TUI mode.

### 4. element appearance tracking is still heuristic

The current appears in model is derived from name and alias matches in chapter text and metadata.
That is acceptable for now.
It will eventually need scene awareness or explicit tagging if the repo grows into denser manuscripts.

### 5. roadmap discipline depends on keeping the docs current

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

Bring the TUI closer to the CLI.

The biggest usability gap now is not raw capability.
It is surface consistency.
Reports, board activity, element inspection, and metadata editing should become easier to use without dropping back to commands for every action.

### priority 2

Add richer compile profiles.

The next compile step should separate output intent more clearly:

1. print
2. ebook
3. submission

That will make the export story feel finished instead of merely present.

### priority 3

Add reordering and stronger outliner behavior.

The current numbered file model is stable, but still rigid.
Explicit part and chapter reorder commands would improve everyday manuscript work.

### priority 4

Deepen the board and element integration.

The board and element features exist now.
The next value is tighter connection between them and the manuscript:

1. chapter links to related elements
2. chapter links to board notes
3. more direct TUI visibility

## bottom line

The repo has crossed the important threshold.
It is no longer proving that the app can exist.
It is now proving that the workflow can hold together.

The next stage should focus on tightening the surfaces that already exist instead of adding broad new domains too early.
