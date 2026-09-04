# ADR-002: Journaled restore recovery

**Status:** Accepted
**Date:** 2026-09-04
**Driving requirement:** TD-002
**Supersedes:** None
**Superseded by:** None

## Context

An exact snapshot restore replaces several managed project paths. Each individual replacement is atomic on the same volume, but the complete set cannot be replaced in one filesystem operation. The existing process-level rollback did not cover power loss or process termination between replacements.

## Decision

Every exact restore transaction will stage its target state and preserve the prior state under a transaction directory inside `.openscribe`. Before the first managed-path replacement, it will atomically write a journal containing the original and staged existence state for every managed path.

The journal has two durable states:

1. `applying` means startup must restore the original paths in reverse order.
2. `committed` means startup must retain the restored paths and remove transaction residue.

Project configuration loading will recover any interrupted transactions before reading persisted project state. The normal restore path will still create an independent checkpoint first.

## Rationale

This produces deterministic all-old or all-new recovery after interruption while keeping Markdown and YAML as ordinary files. It closes the power-loss consistency gap without moving the project into a database or archive container.

## Alternatives Considered

- One directory rename: rejected because managed files intentionally span project-visible top-level directories.
- Database transaction: rejected because it conflicts with the file-first source-of-truth model.
- Backup only: rejected because recovery would depend on a manual step after an interruption.

## Consequences

- Interrupted transactions can leave a temporary private copy until the next project load completes cleanup.
- Recovery code is part of normal project startup and must remain small, deterministic, and covered at both replacement boundaries.
- Transaction directories and project snapshots remain excluded from Git.
