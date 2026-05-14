# Specification

## Problem

`openscribe` can create and organize a manuscript, but it cannot yet turn that manuscript into a usable book output.

That leaves the current workflow incomplete for the main use case.

A writer can draft chapters and inspect structure, but there is no built in path to produce:

1. a Word file for editing or sharing
2. a PDF for review
3. an EPUB for digital reading

Without compile support, the project is a manuscript organizer, not a full writing workflow.

The current feature gap is clearer when compared to the core long form writing workflow:

1. binder structure exists in early form
2. compile does not exist yet
3. a Scrivenings style continuous manuscript view does not exist yet
4. metadata exists in files but is still thin in the interface
5. outliner style structure plus metadata review is not built yet

This spec covers the first of those missing pieces because compile is the shortest path from manuscript organizer to usable writing tool.

## Proposed MVP Definition

The compile MVP is considered complete when this path works:

1. initialize a project
2. create at least one part and one chapter
3. write body text into the chapter files
4. run `openscribe compile`
5. receive a compiled output file in the expected location
6. rerun compile with another output format or template
7. confirm the output follows manuscript order and basic project metadata

## Interfaces

### CLI Interface

The first command shape should be:

1. `openscribe compile`
2. `openscribe compile --format docx`
3. `openscribe compile --format pdf`
4. `openscribe compile --format epub`
5. `openscribe compile --template novel`
6. `openscribe compile --output .\build\my-book.docx`

Optional later flags can be added, but the first pass should stay small.

### Project Config Interface

`.openscribe/project.yaml` should become the source of compile defaults.

Expected areas:

1. default output format
2. default template name
3. optional output directory
4. optional author metadata
5. optional title page settings

### Template Interface

Templates should live under `.openscribe/templates/`.

The first template model should be plain and inspectable.

Expected template inputs:

1. output format target
2. optional reference files
3. chapter heading style
4. front matter include or skip settings
5. scene break style if later supported

## Feature Priority Context

The current product priority for `openscribe` is:

1. compile
2. Scrivenings style continuous reading
3. richer metadata commands and views
4. outliner
5. research viewing
6. corkboard
7. templates beyond compile defaults

This spec only defines item one.
It should not grow to absorb the later milestones.

## Data Flow

1. load project config
2. enumerate part folders in numeric order
3. enumerate chapter files in numeric order inside each part
4. parse frontmatter and body text
5. concatenate body content into a temporary compile document
6. pass the document and selected options to Pandoc
7. write the compiled file to the final output path

## Output Location

Default output should go under a project local build folder.

Suggested path:

1. `build/`
2. `build/<project-title>.<format>`

The exact filename can be slugged for safety.

## Constraints

1. Pandoc is an external dependency and may not be installed.
2. PDF generation may need a local PDF engine, depending on the Pandoc setup.
3. The first version should avoid a heavy abstraction layer over Pandoc.
4. The first version should not hide the template files from the user.
5. Binder order must stay aligned with numbered folder and file names until a richer ordering model exists.

## Risks

1. Pandoc setup may differ across machines.
2. PDF support may fail even when Pandoc itself is installed.
3. Template configuration could become too complex too early.
4. Manuscript metadata may drift if file frontmatter and project config disagree.
5. Concatenation rules for chapter headings and spacing may need iteration after real usage.

## Acceptance Criteria

1. A sample manuscript can compile to `docx`.
2. The compiled output respects part and chapter order.
3. Missing Pandoc produces a clear error.
4. Missing manuscript content produces a clear error.
5. At least one default template works without manual edits.
6. The README explains how to install the compile prerequisites and run the command.
7. The implementation leaves room for a later Scrivenings command to reuse the same ordered manuscript assembly logic.
