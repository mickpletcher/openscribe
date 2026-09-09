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

TD-004's missing scan configuration is resolved by the security job in `.github/workflows/ci.yml`. The job passed in hosted CI run 33974973049 on 2026-09-05. See the appended resolution in `completed-upgrades.md`.

### TD-005: Windows release packages are not digitally signed

**Status:** Open
**Severity:** Medium
**Area:** Windows distribution
**Introduced/Discovered:** 2026-09-08
**Standing waiver:** No

**Related files**

- `.github/workflows/windows-package.yml`
- `scripts/build-windows.ps1`
- `packaging/openscribe.iss`

**Description**

The Windows setup executable and portable application are reproducible and checksummed, but their executable files do not carry an Authenticode signature.

**Why it exists**

The repository does not yet have a protected code-signing certificate or signing service.

**Impact**

Windows can show an unknown-publisher or SmartScreen warning. A checksum proves file integrity only after the user obtains a trusted checksum from the same release.

**Recommended resolution**

Use a protected CI signing identity. Sign the desktop executable, CLI executable, and installer. Verify signatures before release publication and test the signed installer on a clean Windows VM.

**Fix trigger**

Before the first public stable release.

**Estimated effort:** Medium
