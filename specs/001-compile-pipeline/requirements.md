# Requirements

## Goal

Add a first class compile workflow to `openscribe` so a manuscript project can be exported into common writing and publishing formats.

The compile milestone is complete when a writer can:

1. define compile settings in the project
2. preserve manuscript order from the binder structure
3. export the manuscript into at least one working output file
4. reuse a named compile template
5. understand the workflow from the repo docs alone

## Functional Requirements

1. `openscribe` must expose a `compile` command.
2. The compile command must read the current project from the `.openscribe` folder.
3. The compile command must gather manuscript content from the `manuscript` folder in binder order.
4. Binder order must come from numbered part folders and numbered chapter files.
5. The compile command must support `docx` output.
6. The compile command must support `pdf` output when the local Pandoc toolchain supports it.
7. The compile command must support `epub` output.
8. The compile command must support selecting a named template.
9. The compile command must write output to a predictable folder inside the project.
10. The compile command must allow the caller to override the output path.
11. The compile command must fail clearly when Pandoc is not installed.
12. The compile command must fail clearly when no manuscript content exists.
13. The compile command must respect project title metadata during export.
14. The compile command must allow inclusion of front matter such as title page content.

## Non Functional Requirements

1. The first compile workflow must stay simple enough for a beginner to understand.
2. Markdown files must remain the source of truth.
3. Compile behavior must be deterministic for the same manuscript tree and settings.
4. Template configuration must be plain text and project readable.
5. Error messages must tell the user what to fix next.
6. The implementation must not block later support for richer templates or per output customization.

## Out Of Scope

1. Full interactive compile wizard
2. Rich GUI editor
3. Live preview rendering
4. Scene level compile filtering
5. Cloud sync
6. Multi user collaboration
