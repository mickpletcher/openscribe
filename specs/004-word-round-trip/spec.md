# Specification

## Problem

OpenScribe can compile a manuscript to Word, but the exported DOCX is currently a terminal artifact. Edits made in Word cannot be mapped safely back to the canonical Markdown project.

File names, headings, and paragraph positions are not durable identity. They change during normal revision. A safe round trip needs stable chapter and scene IDs, an export baseline, explicit conflict handling, preview, backup, and rollback.

## Product Position

Word is an optional editing client. OpenScribe project files remain the source of truth.

The integration must feel local and deliberate:

1. export a round trip enabled DOCX
2. edit it in Word
3. inspect changes in a Word task pane or the CLI
4. resolve tracked changes and conflicts
5. preview the exact Markdown changes
6. apply with an automatic checkpoint

The existing ordinary DOCX compile remains a one way publication path.

## Identity Model

Each exported unit is wrapped in a rich text content control.

Content control tags use these forms:

```text
openscribe:chapter:<chapter-id>
openscribe:scene:<scene-id>
```

Titles remain editable presentation text. The tag, not the title or Word control ID, is the OpenScribe identity.

The DOCX package also contains a custom XML part in the namespace `urn:openscribe:roundtrip:v1`. It records:

1. manifest version
2. export ID
3. project fingerprint
4. export timestamp
5. OpenScribe project format version
6. ordered chapter and scene IDs
7. normalized baseline SHA-256 for each unit

The exact baseline text is stored in the originating project under `.openscribe/word-roundtrip/<export-id>/`. That local baseline is required for import. The document manifest is an identity and tamper detection aid, not a substitute for the project baseline.

Microsoft documents stable Word support for rich text content controls, unique named controls and bindings, and custom XML parts. The implementation must stay on stable requirement sets and verify the selected desktop Word version before enabling import.

## Export Contract

Round trip export is a distinct command from ordinary compile:

```powershell
openscribe word export --output build\north-county-roundtrip.docx
```

Export must:

1. validate the full project
2. require unique chapter and scene IDs
3. create a local export baseline atomically
4. produce the DOCX in a temporary path
5. verify content controls, manifest IDs, hashes, and relationships by reopening the package
6. atomically replace the requested output only after verification

The export baseline contains normalized unit text and hashes. It contains manuscript text and must be treated as private project data. It is included in snapshots and excluded from normal diagnostic logs.

## Import Contract

Import has two phases:

```powershell
openscribe word import build\north-county-roundtrip.docx
openscribe word import build\north-county-roundtrip.docx --apply
```

Preview parses the DOCX, verifies its manifest, finds the local baseline, checks content control identity, and creates a per-unit plan. The plan classifies units as:

1. unchanged
2. Word changed, safe to import
3. Markdown changed, keep Markdown
4. already converged
5. conflict
6. invalid identity

The preview includes a unified diff for every proposed Markdown change. It does not write manuscript files or refresh the index.

Apply is refused while any conflict, invalid identity, or unresolved tracked change exists. A valid apply creates a checkpoint, writes affected chapters atomically, validates the resulting project, and rebuilds the derived index. Any failure restores the checkpoint.

## Three Way Comparison

Text is normalized only for transport details that Markdown cannot represent consistently, such as line ending form. Whitespace, punctuation, headings, and paragraph breaks remain meaningful.

Comparison happens at the smallest stable unit:

1. scene when a chapter has scene controls
2. chapter preamble for text outside scenes
3. entire chapter only when the chapter has no scenes

No fuzzy title or position matching is allowed during import. Missing or duplicate IDs are structural errors.

## Tracked Changes

Microsoft exposes tracked change inspection plus accept and reject operations in WordApi 1.6. OpenScribe uses inspection only in the first implementation.

If a document contains unresolved tracked changes, preview reports the count and affected controls, then blocks apply. The task pane directs the writer to review and accept or reject those changes in Word. OpenScribe does not silently choose a revision view and does not mutate Word's review history.

Comments are not imported. Their presence is reported as a warning.

## Local Bridge

The Office task pane cannot write directly to arbitrary project files. It communicates with a local OpenScribe bridge.

```powershell
openscribe word bridge start
```

Bridge rules:

1. bind to `127.0.0.1` only
2. choose an available high port
3. generate a random session token held in memory
4. allow only the installed add-in origin
5. require the token on every request
6. accept only a selected, registered project root
7. enforce request size and timeout limits
8. log unit IDs and counts, never manuscript text
9. expose preview and apply as separate endpoints
10. stop when the owning CLI process exits

The task pane shows project title, export ID, unit counts, tracked change state, conflicts, and the proposed diff. Apply requires a separate user action after preview.

## Failure Behavior

The integration refuses to apply when:

1. the manifest or baseline is missing
2. the manifest version is unsupported
3. the project fingerprint does not match
4. an ID is malformed, missing, or duplicated
5. Word adds, removes, splits, or nests controls ambiguously
6. tracked changes remain unresolved
7. any unit has a three way conflict
8. project validation fails
9. a backup cannot be created

Failures are visible in the task pane and CLI. They include the affected IDs and recovery path without printing manuscript text.

## Validation Strategy

The first implementation requires:

1. OOXML package tests for controls, custom XML, relationships, and hashes
2. round trip tests for unchanged, Word only, Markdown only, converged, and conflicting edits
3. malformed and duplicated ID tests
4. tracked change fixture tests
5. apply failure rollback tests with byte for byte managed state comparison
6. local bridge origin, token, loopback, size, and logging tests
7. real Windows desktop Word interaction tests for export, edit, preview, and apply
8. manual Word restart and document copy tests

## References

1. [Microsoft Word content control API](https://learn.microsoft.com/en-us/javascript/api/word/word.contentcontrol)
2. [Microsoft custom XML part API](https://learn.microsoft.com/en-us/javascript/api/office/office.customxmlpart)
3. [Microsoft tracked change collection API](https://learn.microsoft.com/en-us/javascript/api/word/word.trackedchangecollection)
4. [Microsoft Office Open XML guidance for Word add-ins](https://learn.microsoft.com/en-us/office/dev/add-ins/word/create-better-add-ins-for-word-with-office-open-xml)
