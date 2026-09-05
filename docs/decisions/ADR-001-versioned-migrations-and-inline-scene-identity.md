# ADR-001: Versioned migrations and inline scene identity

**Status:** Accepted
**Date:** 2026-09-04
**Driving requirement:** TD-001, FU-001, FU-002
**Supersedes:** None
**Superseded by:** None

## Context

OpenScribe stores projects as Markdown and YAML. Earlier format changes added fields through ad hoc load-time repair. Chapter identity now survives renames and reordering, but project version `1` does not describe those changes. Scenes are inferred from mutable level-two headings and cannot be moved or linked safely.

Evidence: `src/openscribe/project.py`, `src/openscribe/board.py`, `TECH-DEBT.md#td-001-persisted-format-migrations-are-ad-hoc`, `future-upgrades.md#fu-001-add-scene-identity-and-metadata`.

## Decision

OpenScribe will maintain one integer project format version and an ordered migration registry. Every migration has one source version and one target version. A migration run creates a checkpoint before changing managed files, advances the version only after each step succeeds, and restores the checkpoint if any step fails.

Scene identity will use immutable `scene-<uuid>` values stored in an HTML comment immediately after each scene heading:

```markdown
## Bus Stop
<!-- openscribe-scene-id: scene-0123456789abcdef -->
```

The comment keeps Markdown readable, remains hidden in rendered output, and travels with the scene when it moves. Reordering retains all scene IDs. Splitting retains the original ID for the first half and creates a new ID for the second half. Merging retains the destination ID and removes the consumed ID.

Scene restructuring will preview by default. Applying a change requires an explicit flag and creates a checkpoint first. Markdown remains canonical.

## Rationale

The registry makes format evolution ordered, testable, and recoverable. Inline identity keeps a scene and its identifier in one human-readable file without introducing a database or a sidecar synchronization problem.

## Alternatives Considered

- Heading text or position: rejected because both change during normal editing.
- Pandoc heading attributes: rejected because native exporters and some editors can expose the attribute as visible title text.
- A YAML sidecar per chapter: rejected because copying or manually editing a chapter could separate text from identity.
- A database: rejected because it would weaken the file-first portability model.

## Consequences

- Existing projects receive new comments and a higher project format version.
- Migration and scene mutation code must preserve unknown chapter frontmatter.
- Exporters and searches must ignore the identity comments as prose.
- Power-loss atomicity remains limited by TD-002, but every migration and applied restructure has a recoverable checkpoint.

## Related

- `TECH-DEBT.md#td-001-persisted-format-migrations-are-ad-hoc`
- `TECH-DEBT.md#td-002-snapshot-restore-is-not-power-loss-atomic`
- `future-upgrades.md#fu-001-add-scene-identity-and-metadata`
- `future-upgrades.md#fu-002-add-previewable-scene-restructuring`
