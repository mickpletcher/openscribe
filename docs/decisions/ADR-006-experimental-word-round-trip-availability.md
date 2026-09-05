# ADR-006: Experimental Word round-trip availability

**Status:** Accepted
**Date:** 2026-09-05
**Driving requirement:** User authorization to implement the assessed roadmap
**Supersedes:** ADR-003 all-or-nothing availability gate only
**Superseded by:** None

## Decision

Expose the implemented OOXML exporter, preview/import commands, and local bridge as experimental alpha functionality while keeping real Word host validation an explicit release gate. ADR-003's identity, privacy, baseline, conflict, and backup rules remain in force.

Tagged chapter controls contain chapter titles and preambles plus tagged scene controls. The project stores a versioned local baseline with a project ID, export ID, unit IDs, and hashes. Import verifies the manifest against that baseline, classifies three-way changes, refuses ambiguous structure and tracked changes, and installs a validated staged project with an automatic backup. Ordinary DOCX compile is still separate.

The bridge is bound to one selected project and `127.0.0.1`. It validates Host, Origin, a per-session bearer token, request limits, and short-lived preview IDs. The task pane obtains the full active document through the stable `CompressedFile` API and talks only to its own local origin. HTTPS with a separately trusted local certificate is required for Word task-pane hosting. The application never silently installs a trust certificate or sideloads an add-in.

## Validation gate

Package, conflict, malformed-identity, tracked-change, failure, and local HTTP security tests are automated. Real Word opening, editing, saving, copying, restarting, and task-pane interaction are not verified: Windows application input timed out and focus recovery failed during this task. No claim of production Word compatibility is made. See VL-004 in `VALIDATION.md`.

No independent reviewer was available. Public release remains blocked on host validation and independent data-integrity/security review.

## References

- [Microsoft full-document access](https://learn.microsoft.com/en-us/office/dev/add-ins/develop/get-the-whole-document-from-an-add-in-for-powerpoint-or-word)
- [Word round-trip development plan](../../specs/004-word-round-trip/README.md)
