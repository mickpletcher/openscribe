# ADR-003: Local-first Word round trip

**Status:** Accepted
**Date:** 2026-09-04
**Driving requirement:** FU-004
**Supersedes:** None
**Superseded by:** None

## Context

OpenScribe exports DOCX files but cannot safely map Word edits back to canonical Markdown. Headings and paragraph positions are mutable. Word edits can also race with later Markdown edits or contain unresolved tracked changes.

## Decision

The future round-trip implementation will keep Markdown canonical and use tagged Word content controls for immutable chapter and scene identity. A custom XML manifest will identify the export and unit hashes. The project will keep the exact export baseline locally.

Import will use a three-way comparison of baseline, current Markdown, and Word text. It will preview by default, refuse conflicts and unresolved tracked changes, and create a checkpoint before atomic apply. The Word task pane will communicate only with an authenticated loopback bridge. The integration will not send manuscript text to a hosted OpenScribe service.

The detailed behavior and implementation gates are defined in `specs/004-word-round-trip/`.

## Rationale

Stable content-control tags survive title changes and normal editing. A local baseline makes conflict classification deterministic. A loopback bridge lets the Office task pane request file operations without granting the add-in direct arbitrary filesystem access.

## Alternatives Considered

- Make DOCX canonical: rejected because it breaks the plain-file project model.
- Match headings or paragraph positions: rejected because both change during editing.
- Last writer wins: rejected because it can silently destroy concurrent manuscript edits.
- Hosted synchronization service: rejected because it adds an unnecessary manuscript data-transfer boundary.

## Consequences

- Ordinary DOCX compile remains one way.
- Round-trip export and import require a separate package format and local baseline lifecycle.
- Windows desktop Word is the first validation target.
- The design is accepted, but no Office add-in or Word import capability is claimed until the tasks in the development spec pass.
