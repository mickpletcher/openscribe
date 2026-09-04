# Requirements

## Functional Requirements

1. Markdown project files remain canonical.
2. A round trip export assigns each Word chapter and scene region its existing immutable OpenScribe ID.
3. Word content controls carry machine readable ID tags without exposing those IDs in visible manuscript text.
4. The DOCX package carries an OpenScribe manifest with an export ID, format version, unit IDs, and baseline hashes.
5. The project stores the exact export baseline locally under `.openscribe/word-roundtrip/`.
6. Import compares the baseline, current Markdown, and current Word text for each unit.
7. Import produces a preview plan and changes no project files by default.
8. Applying an import creates an automatic checkpoint and writes all affected files atomically.
9. Any failed apply restores the checkpoint.
10. Missing, duplicated, or malformed identity controls block import for the affected document.
11. Unresolved tracked changes block import until the writer accepts or rejects them in Word.
12. Formatting only changes do not alter Markdown unless an explicitly supported Markdown mapping exists.
13. The task pane can inspect the active document and request a preview from a local bridge.
14. The bridge binds only to loopback and requires a per-session token.
15. No manuscript text is sent to OpenScribe or another hosted service by the Word integration.

## Conflict Rules

For each chapter or scene, let `B` be the exported baseline, `M` the current Markdown text, and `W` the current Word text.

1. If `M = B` and `W = B`, the unit is unchanged.
2. If `M = B` and `W != B`, the unit is safe to import from Word.
3. If `M != B` and `W = B`, keep the current Markdown.
4. If `M = W`, the unit is already converged.
5. If both `M` and `W` changed from `B` and differ from each other, the unit is a conflict.
6. A conflict is never auto merged in the first implementation.

## Nonfunctional Requirements

1. Import must preserve unknown YAML fields and unrelated project files.
2. The bridge must reject non-loopback connections, unapproved origins, missing tokens, oversized bodies, and unknown project roots.
3. Logs must contain counts, IDs, and status only. They must not contain manuscript text.
4. The add-in must state that it communicates with a local OpenScribe process.
5. Compatibility checks must use stable Word API requirement sets. Preview APIs cannot be required for the first release.
6. Windows desktop Word is the first supported host. Word on the web and macOS remain unverified until tested.

## Out of Scope for the First Implementation

1. Real time two way synchronization
2. Cloud storage or collaboration
3. Automatic semantic conflict merging
4. Importing arbitrary DOCX files without OpenScribe identity data
5. Preserving every Word formatting feature in Markdown
6. Accepting or rejecting tracked changes on the writer's behalf
