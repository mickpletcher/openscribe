# ADR-010: Previewed AI manuscript drafting

**Status:** Accepted
**Date:** 2026-09-10
**Driving requirement:** Use the connected AI ecosystem to draft a book from writer descriptions at page or chapter scope
**Supersedes:** None
**Superseded by:** None

## Decision

The desktop application provides a **Write with AI** workflow for the selected chapter or scene. The writer supplies a description containing the intended events, characters, setting, tone, point of view, and constraints.

Page scope requests approximately 250 to 350 words and inserts accepted prose at the current editor cursor. A temporary marker in the request context identifies that insertion point and is never saved. Chapter scope requests a complete chapter and is available only when a chapter, rather than an individual scene, is selected. It replaces the current chapter text in the editor only after preview approval.

AI output is never written directly to the manuscript file. The generated prose is previewed first. Accepted prose becomes an unsaved recovery draft in the existing editor, where the writer can revise or undo it. The existing explicit save path performs disk-conflict detection and creates the normal checkpoint before changing canonical Markdown.

The selected chapter or scene text is supplied as manuscript context so the model can continue established voice and facts. For a hosted or non-loopback provider, the desktop displays the provider, model, and manuscript character count and requires approval for every generation request. Local loopback providers do not require transfer approval.

If the selected document or editor text changes while generation is running, the returned text is not previewed or applied. This prevents delayed output from being placed into a different or newer draft.

## Limits

Page scope is a prose-length target, not a rendered print page. Actual pagination depends on later export formatting.

Generated text can be incorrect, derivative, inconsistent, or unsuitable. The writer remains responsible for review, factual accuracy, rights, disclosure obligations, and final authorship decisions.

This first drafting workflow uses only the selected chapter or scene as context. Automatic retrieval across character sheets, research, notes, and the entire manuscript remains future work.

No independent reviewer was available for this change.
