# Technical Debt

### TD-003: TUI interaction coverage is incomplete

**Status:** Open
**Severity:** Medium
**Area:** Textual interface
**Introduced/Discovered:** 2026-09-04
**Standing waiver:** No

**Related files**

- `src/openscribe/tui.py`
- `tests/test_tui.py`
- `tests/test_safety.py`
- `tests/test_desktop.py`

**Description**

Mounted tests cover search, keyboard metadata actions, board movement, promotion, chapter and scene editing, recovery drafts, local proofreading, hosted proofreading refusal, and visible failures. The desktop has Qt interaction tests. Native rendering, accessibility, and the full range of terminal sizes remain unverified. See VL-002 and VL-004 in `VALIDATION.md`.

**Why it exists**

The TUI grew faster than its interaction suite.

**Impact**

Widget lifecycle and terminal-specific regressions can survive unit and headless interaction tests.

**Recommended resolution**

Add mounted tests for every mutation, selection type, empty state, malformed-data state, and supported terminal-size boundary.

**Fix trigger**

Before the first public release or claiming broad terminal and accessibility support.

**Estimated effort:** Medium

TD-004's missing scan configuration is resolved by the security job in `.github/workflows/ci.yml`. This is a configuration claim, not evidence of a hosted run. See the appended resolution in `completed-upgrades.md` and the hosted-validation gate in `VALIDATION.md`.
