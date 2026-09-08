# ADR-007: Graceful rejection of bounded Word bridge requests

**Status:** Accepted
**Date:** 2026-09-08
**Driving requirement:** Deterministic authentication and authorization responses from the local loopback Word bridge on supported Windows
**Supersedes:** None
**Superseded by:** None

## Decision

The bridge must reject an invalid token, origin, host, route, or request size without parsing or applying the submitted document. It must also return the intended HTTP response instead of intermittently resetting the connection when unread request bytes remain on Windows.

For rejected requests with a valid fixed `Content-Length` no larger than `MAX_DOCX_BYTES`, the bridge sends and flushes the rejection response, marks the connection for closure, and then drains the bounded request body without parsing it. Transfer-encoded, missing, malformed, empty, and oversized bodies are not drained.

The listener remains bound to `127.0.0.1`. Rejected requests do not create preview plans, touch project files, or reach the Word importer. The existing 15-second socket timeout and maximum document size remain the resource bounds.

## Consequences

- Windows clients reliably receive the intended `401`, `403`, `404`, or `413` response.
- Authentication and authorization checks still occur before document parsing or project access.
- A local process can keep one bridge request open until the existing socket timeout, but cannot make the bridge parse, persist, or apply an unauthorized document.
- The Word workflow remains experimental until real desktop Word and independent Class 4 review gates are complete.

## Validation

- Repeat invalid token, origin, and host requests in one bridge session.
- Run the bridge tests on every supported Python version.
- Retain real Word and independent review limitations in `VALIDATION.md` and `assessment.md` until verified.
