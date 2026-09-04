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

**Description**

Mounted tests cover search, keyboard metadata actions, board movement, promotion, chapter and scene editing, local proofreading, hosted proofreading refusal, and visible compile failures. Many selection, rendering, filtering, accessibility, and terminal-size paths remain uncovered.

**Why it exists**

The TUI grew faster than its interaction suite.

**Impact**

Widget lifecycle and terminal-specific regressions can survive unit and headless interaction tests.

**Recommended resolution**

Add mounted tests for every mutation, selection type, empty state, malformed-data state, and supported terminal-size boundary.

**Fix trigger**

Before the first public release or claiming broad terminal and accessibility support.

**Estimated effort:** Medium

### TD-004: Automated security and dependency scanning is absent

**Status:** Accepted
**Severity:** Medium
**Area:** Supply chain and static analysis
**Introduced/Discovered:** 2026-09-04
**Standing waiver:** Yes

**Related files**

- `.github/workflows/ci.yml`
- `pyproject.toml`

**Description**

CI runs tests, Ruff, package builds, and CLI smoke tests. It does not run a dependency vulnerability audit, secret scanner, or security-focused static analyzer.

**Why it exists**

The first CI baseline focused on compatibility and packaging.

**Impact**

Known vulnerable dependencies or accidentally committed credentials may not be detected automatically.

**Recommended resolution**

Add a dependency audit, repository secret scan, and a Python security analyzer with reviewed suppression rules.

**Fix trigger**

Before the first public release or enabling hosted AI in a published build.

**Estimated effort:** Small
