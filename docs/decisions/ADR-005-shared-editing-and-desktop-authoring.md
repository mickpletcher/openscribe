# ADR-005: Shared editing and desktop authoring

**Status:** Accepted
**Date:** 2026-09-05
**Driving requirement:** Safe daily writing milestone
**Supersedes:** None
**Superseded by:** None

## Decision

The optional PySide6 desktop application is the author-facing surface. The CLI remains available for automation and the Textual TUI remains supported. Markdown and YAML remain canonical. No second persistence system is introduced.

Both editors use `EditSession`: an exact byte baseline, an unsaved text buffer, conflict-checked save, and a local recovery draft. Drafts are retained across selection changes and written to local recovery files once per second and on navigation. These recovery files are separate from save checkpoints. Quit requires saving or explicitly discarding dirty drafts. Draft files contain private manuscript text and are excluded from Git. Their concurrent modification is checked before replacement or deletion.

The chapter editor permits prose changes with an unchanged scene-heading sequence. Ambiguous structural changes are refused. Explicit scene operations carry the existing IDs; titles and positions are not used to guess identity after restructuring.

LanguageTool checks run in background workers. Findings are bound to the checked text. Replacements require an explicit preview and application, remain undoable draft edits, and are refused after intervening text changes. Desktop review offers every returned replacement; TUI shortcuts preview the first suggestion.

AI consent is determined by the configured destination, not the `openai-compatible-local` label. Only loopback endpoints bypass transfer consent; nonlocal endpoints require HTTPS and explicit consent.

## Limits

The first desktop build is an alpha editor, not a full rich-text publishing environment. Research views are read only. The draft timer is not a guarantee against losing keystrokes immediately before an abrupt process failure. A separate independent review was unavailable.

## References

- [Qt plain-text editor](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QPlainTextEdit.html)
- [Qt worker threads](https://doc.qt.io/qtforpython-6.10/PySide6/QtCore/QThread.html)
- [LanguageTool local HTTP server](https://dev.languagetool.org/http-server)
