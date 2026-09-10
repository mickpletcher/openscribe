# Repository Assessment

**Last full assessment:** 2026-09-05
**Last targeted safety review:** 2026-09-10
**Assessed implementation:** Current `main` worktree based on commit `27ff24d`
**Basis:** Repository inspection; local Python 3.11 through 3.13 pytest runs; hosted Windows, Ubuntu, and macOS CI for the committed baseline; coverage; Ruff; Node task-pane tests; source, wheel, portable Windows, and Windows installer builds; installed-wheel, packaged-application, install, upgrade, and uninstall smoke tests; sample-index integrity; dependency audit; Bandit; secret scan; living-document compliance; three independent Claude review passes with local reproduction and correction of every confirmed defect
**Assessed by:** Codex. The earlier identity and conflict review used an independent Claude reviewer; no independent reviewer was available for the 2026-09-10 AI provider expansion.

## Executive Summary

`openscribe` is an active Tier 1 pre-release alpha with a local-first Markdown and YAML data model. The original six reported data-integrity defects are fixed. Authoring now uses recoverable drafts, external-edit conflict checks, explicit identity migration and repair, terminal restore states, cross-process locking, and destination-based AI consent. The project also has a packaged Windows desktop application, actionable LanguageTool review, and an experimental identity-preserving Word round trip.

The desktop now offers optional first launch setup for OpenAI, Anthropic Claude, Google Gemini, Mistral, xAI Grok, DeepSeek, Azure OpenAI, LM Studio, OpenAI-compatible hosted APIs, and other local servers. LM Studio has a named keyless preset for its standard loopback endpoint. **Write with AI** turns a writer description into a previewed approximate-page or complete-chapter draft. Accepted output remains an unsaved editor draft until the writer invokes the existing conflict-checked, checkpointed save path. Connection testing sends only a synthetic message and no manuscript text. Provider keys use separate operating system credential-store entries. Existing projects are not changed automatically. Hosted and non-loopback manuscript requests require approval for every transfer.

The four data-integrity defects found by the independent Class 4 review are fixed and independently re-reviewed. Commit `71a57b7` rejects malformed duplicate identities without changing live project files, and the reviewer found no remaining confirmed defect in the reviewed identity or conflict scope. OpenScribe can be used as a primary working copy with independent backups. It should not be the only copy of a manuscript because physical power-loss behavior, native accessibility, real Word save and reopen behavior, and licensed hosted LanguageTool compatibility remain unverified.

## Agent Handoff

- Ordinary reads must not rewrite project data. Persisted-format changes go through explicit, checkpointed migrations or repair commands. Evidence: `src/openscribe/migrations.py`, `src/openscribe/project.py`.
- Persisted chapter and scene relationships use immutable IDs. Titles and slugs resolve only when unique; ambiguous aliases fail and report the matching immutable IDs. Explicit repair replaces one malformed ID but rejects duplicate source IDs before staged changes are installed. Evidence: `src/openscribe/project.py`, `src/openscribe/migrations.py`, `src/openscribe/word.py`.
- Legacy board chapter-link migration rejects ambiguous duplicate titles, slugs, and replaced IDs without installing partial changes. Evidence: `src/openscribe/board.py`, `src/openscribe/editing.py`.
- TUI, desktop, and Word import saves share baseline conflict detection, backups, and journaled replacement behavior. Recoverable drafts protect unsaved navigation and quit paths. Evidence: `src/openscribe/editing.py`, `src/openscribe/tui.py`, `src/openscribe/desktop.py`.
- Scene-operation apply compares the exact previewed UTF-8 bytes. A line-ending-only external edit makes the plan stale and blocks apply. Evidence: `src/openscribe/project.py`.
- Restore journals have validated terminal states and project-scoped locks. Process-interruption tests cover both replacement boundaries. Do not claim physical power-loss atomicity. Evidence: `src/openscribe/snapshots.py`, `src/openscribe/locking.py`, `VALIDATION.md#vl-005-physical-power-loss-durability-is-not-proven`.
- Hosted AI and LanguageTool requests require disclosure and explicit transfer approval based on the actual endpoint. Local loopback use remains the default. Evidence: `src/openscribe/ai.py`, `src/openscribe/network.py`, `src/openscribe/proofreading.py`.
- First launch AI setup verifies hosted or local model access without manuscript text, stores pasted keys separately by provider through the operating system credential store, and does not automatically alter existing projects. Endpoint URLs are non-secret project configuration. Evidence: `src/openscribe/desktop.py`, `src/openscribe/ai.py`, `docs/decisions/ADR-009-first-launch-ai-connection.md`.
- Desktop AI writing uses writer descriptions and selected manuscript context to propose page or chapter prose. Hosted transfers require per-request approval. Generated output is previewed, rejected when stale, and placed only in the unsaved recovery draft before the normal safe save path. Evidence: `src/openscribe/desktop.py`, `src/openscribe/ai.py`, `docs/decisions/ADR-010-previewed-ai-manuscript-drafting.md`.
- Word import, the loopback bridge, and the task pane are experimental. The independent review found no confirmed bridge or Word merge defect, but real Word host validation remains a release gate. Evidence: `docs/decisions/ADR-006-experimental-word-round-trip-availability.md`, `VALIDATION.md#vl-004-native-desktop-and-real-word-interoperability-are-unverified`.
- Windows packaging produces a per-user installer, portable ZIP, checksums, desktop and CLI executables, and automated install, upgrade, and uninstall checks. Release artifacts remain unsigned and need a clean-machine gate before a stable public release. Evidence: `scripts/build-windows.ps1`, `scripts/test-windows-package.ps1`, `scripts/test-windows-installer.ps1`, `.github/workflows/windows-package.yml`, `VALIDATION.md#vl-007-windows-release-trust-and-clean-machine-compatibility-are-unverified`.
- Resolve documentation responsibilities through `PROJECT-STANDARD.md`. Update `assessment.md` only on `main`; use and consolidate `changelog.d/` fragments on feature branches.

## Living Documentation Compliance

Generated by `scripts/docs-check.ps1` on 2026-09-08.

| Responsibility | Authority | Last updated | Status |
|---|---|---|---|
| Project overview | README.md | 2026-09-08 | Current |
| Current assessment | assessment.md | 2026-09-08 | Current |
| Architecture | Not required at this tier |  | Not required |
| Change history | changelog.md | 2026-09-08 | Current |
| Defect tracking | Not required at this tier |  | Not required |
| Technical debt | TECH-DEBT.md | 2026-09-08 | Current |
| Deferred improvements | future-upgrades.md | 2026-09-08 | Current |
| Validation | VALIDATION.md | 2026-09-08 | Current |
| Operations | Not required at this tier |  | Not required |
| Requirement traceability | Not required at this tier |  | Not required |
| Agreed scope | Not required at this tier |  | Not required |
| Agreed design | Not required at this tier |  | Not required |
| Scope amendments | Not required at this tier |  | Not required |
| Decision history | docs/decisions/README.md | 2026-09-08 | Current |
| Resolved history | completed-upgrades.md | 2026-09-05 | Current |
| Development rules | PROJECT-STANDARD.md | 2026-09-05 | Current |
| Agent rules | AGENTS.md | 2026-09-05 | Current |

## Current Health

- Hosted CI: PASS for commit `27ff24d` on 2026-09-08. [Run 34305049709](https://github.com/mickpletcher/openscribe/actions/runs/34305049709) completed all nine documentation, lint, security, package, Windows, Ubuntu, and macOS jobs successfully, including Python 3.11 through 3.13.
- Tests: PASS on 2026-09-10. Final isolated local Python 3.11, 3.12, and 3.13 runs each reported 189 passed, 0 failed, and 0 skipped. The final Python 3.13 coverage run reported 189 passed and 87.02 percent coverage.
- Word task pane: PASS on 2026-09-08. `node --test tests/word_addin.test.cjs` exited `0` with 8 passed, 0 failed, and 0 skipped. Rejected Word bridge requests passed 10 consecutive Windows response-delivery runs.
- Lint: PASS on 2026-09-10. `python -m ruff check src tests scripts/check-secrets.py scripts/check_markdown_links.py` exited `0` with no findings.
- Build and CLI smoke: PASS on 2026-09-08. `uv build --python 3.13 --no-create-gitignore` produced one source distribution and one wheel. The installed wheel and source checkout displayed the expected CLI, desktop, and Word help.
- Security and dependencies: PASS on 2026-09-10. The dependency audit found no known third-party vulnerabilities; the unpublished local package was skipped because it is not on PyPI. Bandit found no medium-or-higher issues. The reviewed-baseline secret scan found 0 unreviewed findings.
- Documentation: PASS on 2026-09-10. The living-document check reported no missing, invalid, or review rows. The link checker resolved 60 local links and heading anchors across 52 Markdown files, and all 6 executable beginner-workflow tests passed.
- Windows distribution: The final expanded 2026-09-10 portable build passed and produced a 128,989,705-byte ZIP with SHA-256 `2cd67ee010c710f625499aa916d84c2045a5ecc609770ffadcfed054c5dbcd20`. The frozen application imported every bundled AI provider client, included the updated novice AI instructions, then passed CLI help, synthetic project creation, exact snapshot recovery, and DOCX, PDF, and EPUB export. Installer lifecycle testing was not rerun because Inno Setup is unavailable on this machine. The prior baseline passed locally and in hosted CI on 2026-09-08, including install, upgrade, shortcut, uninstall, and user-project preservation. [Run 34305049663](https://github.com/mickpletcher/openscribe/actions/runs/34305049663) contains that baseline evidence.
- Independent safety review: PASS on 2026-09-08 for commit `71a57b7`. Claude verified all four original findings as resolved, reproduced duplicate malformed-ID refusal through both repair and v1-to-v2 migration, and found no new release blocker in the reviewed identity or conflict scope. The reviewer also found no confirmed defect in snapshot rollback, cross-process locking, the Word bridge trust boundary, Word three-way conflict handling, or hosted-transfer consent gates.
- Native application validation: The frozen GUI startup path passed locally, but interactive accessibility and real Word behavior remain unassessed. See VL-004 through VL-007 in `VALIDATION.md`.

## Standing Limitations and Gates

- Hosted AI provider compatibility is covered by mocked contracts only. See `VALIDATION.md#vl-001-hosted-ai-providers-use-mocked-contracts`.
- TUI interaction validation is headless and does not prove visual rendering or accessibility. See `VALIDATION.md#vl-002-tui-validation-is-headless`.
- Licensed hosted LanguageTool compatibility is covered by mocked contracts only. See `VALIDATION.md#vl-003-licensed-hosted-languagetool-compatibility-is-unverified`.
- Native desktop accessibility and real Word interoperability are unverified. See `VALIDATION.md#vl-004-native-desktop-and-real-word-interoperability-are-unverified`.
- Physical power-loss durability is not proven. See `VALIDATION.md#vl-005-physical-power-loss-durability-is-not-proven`.
- The independent Class 4 identity and conflict review passed after remediation. See `VALIDATION.md#vl-006-independent-class-4-review-passed-after-remediation`.
- Windows release packages are unsigned and clean-machine compatibility is unverified. See `VALIDATION.md#vl-007-windows-release-trust-and-clean-machine-compatibility-are-unverified`.

## Current Capabilities

The package provides a PySide6 desktop authoring application, a Textual TUI, and a CLI over the same Markdown and YAML project store. Windows users can install a self-contained per-user setup package or extract a portable ZIP without installing Python. It supports project and manuscript structure, stable chapter and scene identity, planning boards, research and notes, search and reporting, exact snapshot restore, DOCX, PDF, and EPUB export, local-first LanguageTool review, optional first launch hosted or local AI connection, previewed AI page and chapter drafting, disclosed AI review, and experimental tagged Word export and import through a project-bound local bridge. The product overview is in `README.md`; the authoritative command and usage inventory is in `docs/cli-reference.md`.

## Known Issues and Risks

Native desktop and TUI accessibility are not manually verified. Windows packages are unsigned and have not completed a separate clean-machine test. Real Word can rewrite OOXML in ways synthetic fixtures do not reproduce, and task-pane sideloading and certificate handling have not completed a live round trip. Process termination recovery does not prove behavior during physical power loss, storage-cache loss, OneDrive conflicts, or edits from tools that ignore the project lock. Hosted provider contracts remain mocked. OpenScribe cannot detect when a loopback AI service or tunnel forwards manuscript text to another computer. The identity helper is safe through its shipped checkpointed staging paths but is not internally atomic if a future caller bypasses those paths. Keep independent backups and do not remove the experimental Word label.

## Technical Debt Summary

Two Medium technical-debt entries remain open: TD-003 for incomplete native TUI interaction and accessibility coverage, and TD-005 for unsigned Windows release packages. Validation limitations and release gates are recorded as VL-001 through VL-005 and VL-007 in `VALIDATION.md`; VL-006 records the completed independent review and remediation evidence.

## Recently Changed

See `changelog.md`.

## Current Priorities

1. Add protected Windows code signing and test the signed installer on a clean Windows VM.
2. Run the documented synthetic real desktop Word round trip, task-pane sideload, certificate, and wrong-origin checks.
3. Perform native desktop and TUI accessibility and terminal-size checks.
4. Run disposable VM power-cut recovery drills before making any physical power-loss durability claim.
5. Run the synthetic LanguageTool contract smoke against a self-hosted server and retain mocked-only status for licensed hosted endpoints.
6. Keep identity repair behind the checkpointed staging wrapper if new repair entry points are added.

## Repository Limitations

This repository is a local installable tool, not a deployed service. There is no client agreement, acceptance authority, runtime operations responsibility, or contractual traceability requirement at Tier 1. Architecture, defect tracking, operations, and contractual authorities are intentionally not required. Decision history is maintained under `docs/decisions/`. Evidence: `PROJECT-STANDARD.md`, `.docs-authority.json`.
