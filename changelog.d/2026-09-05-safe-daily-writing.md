# Safe daily writing and experimental Word round trips

- Preserve unsaved drafts across navigation and require a quit decision in both authoring interfaces.
- Share baseline conflict checks, backups, and journaled save behavior between TUI, desktop, and Word import.
- Finish rollback with a terminal state, validate journals before recovery, preserve nested empty directories, and lock concurrent application access.
- Move identity repair and migrations out of reads; refuse ambiguous chapter-editor restructuring and ignore fenced example headings.
- Validate actual AI endpoint locality before bypassing hosted-transfer consent.
- Add the optional PySide6 desktop binder, editor, search, reference views, export, checkpoint, and restore workflow.
- Add background LanguageTool checks with explicit replacement previews, stale-text refusal, ignore, and undo.
- Implement experimental Word export baselines, content controls, conflict preview, safe apply, authenticated local bridge, and packaged task-pane assets.
- Extend CI with cross-platform smoke coverage, dependency/security/secret checks, and documentation checks.
- Make link detection tolerate platform path aliases while still refusing actual symlinks and junctions; make CLI path tests and editor launching portable.
- Record real Word UI, physical power-loss, and independent-review limitations. Do not describe these as passed release gates.

## Main-branch assessment correction required at integration

`assessment.md` is intentionally unchanged on this feature branch under the repository's main-only rule. Its old automatic-migration description, debt counts, design-only Word description, and testing figures do not describe this working tree. On integration, replace those claims using current validation evidence and retain the alpha status and VL-001 through VL-006 gates. Consolidate this fragment into `changelog.md` on main. No merge or publication is included in this task.
