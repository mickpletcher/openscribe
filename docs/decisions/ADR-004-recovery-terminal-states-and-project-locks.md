# ADR-004: Recovery terminal states and project locks

**Status:** Accepted
**Date:** 2026-09-05
**Driving requirement:** Assessment recovery and concurrent-write findings
**Supersedes:** ADR-002 recovery completion behavior
**Superseded by:** None

## Decision

All restore transactions acquire a reentrant, process-shared project lock. Recovery validates the entire journal before modifying any path. A completed rollback writes a durable `rolled_back` state before cleanup. Both `committed` and `rolled_back` journals are cleanup-only on later startup. Failed cleanup must never trigger another rollback.

Ordinary editor saves and scene changes use the same journaled replacement layer as restores. Migrations, identity repair, and part/chapter reordering prepare changes in an isolated project copy before installing the result. Backups precede apply. Missing identities are repaired only by an explicit command; normal listing does not rewrite source files.

## Evidence and limits

`tests/test_recovery_process.py` terminates child processes after moving the old manuscript and after installing the replacement. `tests/test_safety.py` covers rollback residue, a failed commit, invalid journals, and repeated recovery.

This is process-interruption recovery, not proof of physical power-loss durability on every filesystem. External editors and sync clients do not honor the application lock. Content comparison detects stale edits but cannot make arbitrary external filesystem writers transactional. Symlinks and junctions in managed paths are refused.

## Review

No independent reviewer was available in this task. Failure injection and regression tests provide executable evidence, but are not a substitute for an independent review before public release.
