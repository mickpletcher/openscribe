# Technical Debt

### TD-001: Persisted format migrations are ad hoc

**Status:** Open
**Severity:** High
**Area:** Project data model
**Introduced/Discovered:** 2026-09-04
**Standing waiver:** No

**Related files**

- `src/openscribe/schema.py`
- `src/openscribe/project.py`
- `src/openscribe/board.py`

**Description**

Persisted YAML now receives structural and field type validation, and chapter and board identities migrate automatically. There is no general migration registry that ties the project format version to ordered, repeatable migrations.

**Why it exists**

The current format grew incrementally before a versioned migration system was needed.

**Impact**

Future schema changes can require one-off migration logic. That increases the risk of partial upgrades and makes downgrade behavior undefined.

**Recommended resolution**

Define a persisted schema version, an ordered migration runner, backup requirements, and fixtures for every supported version transition.

**Fix trigger**

Before adding scene IDs or another incompatible persisted field group.

**Estimated effort:** Medium

### TD-002: Snapshot restore is not power-loss atomic

**Status:** Open
**Severity:** Medium
**Area:** Recovery
**Introduced/Discovered:** 2026-09-04
**Standing waiver:** No

**Related files**

- `src/openscribe/snapshots.py`
- `tests/test_project.py`

**Description**

Restore stages saved data, creates an automatic backup, replaces managed paths on the same volume, and rolls back ordinary process failures. Replacing several top-level paths cannot be one filesystem operation.

**Why it exists**

The project uses multiple human-readable directories instead of a transactional database or one replaceable container.

**Impact**

Power loss or external interference during the replacement window can require recovery from the automatic backup.

**Recommended resolution**

Add an on-disk restore journal with startup recovery and test interruption after every replacement boundary.

**Fix trigger**

Before claiming production-grade recovery or using snapshots as the only backup for irreplaceable work.

**Estimated effort:** Medium

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

Mounted tests now cover search, keyboard metadata actions, board movement, promotion, and visible compile failures. Many selection, rendering, filtering, and error paths remain uncovered.

**Why it exists**

The TUI grew faster than its interaction suite.

**Impact**

Widget lifecycle and terminal-specific regressions can survive unit and headless interaction tests.

**Recommended resolution**

Add mounted tests for every mutation, selection type, empty state, malformed-data state, and supported terminal-size boundary.

**Fix trigger**

Before expanding freeform editing or adding scene mutation controls to the TUI.

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
