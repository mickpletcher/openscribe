# ADR-008: Strict identity references and byte-exact scene plans

**Status:** Accepted
**Date:** 2026-09-08
**Driving requirement:** Prevent ambiguous identity selection and stale scene operations from changing the wrong manuscript data
**Supersedes:** None
**Superseded by:** None

## Decision

Immutable chapter and scene IDs are authoritative. A title or slug remains a convenience reference only when it identifies exactly one chapter or scene. An ambiguous convenience reference must fail and report the matching immutable IDs. It must never select the first match.

Legacy board-link migration follows the same rule. Existing immutable IDs resolve before titles and slugs. A missing or malformed chapter ID is replaced only by the explicit checkpointed migration or repair workflow, and a board link to the replaced value follows the new ID. If a legacy title or slug matches multiple chapters, the staged operation fails without installing any changes.

Scene move, split, and merge plans retain the exact UTF-8 file content read during preview. Apply compares that content byte for byte with the current file. A line-ending-only external change therefore makes the plan stale and requires a new preview.

## Consequences

- Duplicate chapter and scene titles remain allowed, but automation must use immutable IDs when their aliases are ambiguous.
- Migration can require manual board-link disambiguation instead of guessing at historical intent.
- Explicit identity repair handles both missing and malformed chapter IDs while preserving unambiguous board relationships.
- External changes cannot bypass scene-operation conflict detection through line-ending normalization.
- A structural scene operation can still normalize formatting as part of its reviewed output after the exact baseline check succeeds.

## Validation

- Repair a malformed chapter ID and verify a board link to the old value follows the replacement ID.
- Create duplicate chapter and scene aliases, verify aliases fail, and verify immutable IDs still resolve.
- Attempt identity repair with duplicate legacy board titles and slugs, then verify no project file changed.
- Change only LF line endings to CRLF after preview and verify apply refuses without changing the file.
- Preview again from the CRLF version and verify the requested operation can apply.
