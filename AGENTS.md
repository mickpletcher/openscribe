# AI Agent Repository Rules

**Standard version:** 2.2
**Project tier:** 1

## Authority Resolution

This file is the only repository agent-rules authority.

Resolve documentation responsibilities through the Authority Mapping in `PROJECT-STANDARD.md`. Never create a second document for an already mapped responsibility.

## Document Classes

- Living: current truth. Update when repository evidence changes.
- Contractual: frozen agreement. Never rewrite to match implementation.
- Derived: append-only history. Never rewrite an existing entry.
- Governance: repository process. Version and record material changes.

## Source of Truth

For current behavior, repository state governs documentation. For intended behavior, an explicit agreement governs implementation. A conflict is a finding, not permission to rewrite one side.

This Tier 1 repository has no contractual authorities. Files under `specs/` are development plans, not reconstructed client requirements.

## Startup

1. Read this file.
2. Classify the change from Class 0 through Class 4.
3. For Class 0, make the trivial change and stop.
4. For Class 1 or higher, resolve the routed authorities in `PROJECT-STANDARD.md`.
5. For Class 2 or higher, read the Agent Handoff in `assessment.md`.
6. Inspect the relevant implementation before editing.

Do not read the full documentation set for every task.

For Class 4 changes, presume an ADR is required. If decision history is not maintained at the current tier, explicitly state why no ADR was created. Obtain a second reviewer where practical, or state in the completion report why review was unavailable.

## Evidence Rules

- Never claim a test, lint, build, scan, or compliance check passed unless it ran in the current task.
- Report the exact command, exit code, passed count, failed count, and skipped count.
- State why any skipped test was skipped.
- Never weaken a valid test to make a change pass.
- Use `Not assessed` when evidence is unavailable.
- Do not carry an old health conclusion forward under a new date.

## Waiver Rules

If required validation cannot run, record a waiver with the unmet requirement, reason, risk, and follow-up. Missing tooling, unsafe execution, permissions, unavailable dependencies, and unavailable external systems are valid grounds. Time pressure is not.

Put recurring procedural limitations in `VALIDATION.md`. Put accepted reductions in assurance in `TECH-DEBT.md`.

## Documentation Rules

- Do not modify documentation merely to create a diff.
- Do not invent capabilities, requirements, integrations, dependencies, tests, or status.
- Link to another authority instead of duplicating its content.
- Update `assessment.md` only on the main branch.
- Use `changelog.d/` on feature branches. Consolidate fragments on main.
- Do not edit existing derived-history entries.
- Review every routed living authority after a meaningful change and update only stale content.

## Security Rules

- Never commit secrets, credentials, tokens, private certificates, or private manuscript content.
- Use placeholders in examples.
- Never document real service credentials or private infrastructure identifiers.
- Do not weaken data-integrity, backup, or AI disclosure controls.

## Completion Rule

A meaningful task is complete only when implementation, validation, waivers, and routed documentation agree with the resulting repository state.

Run the applicable commands from `VALIDATION.md` and `pwsh -File scripts/docs-check.ps1 -FailOnGap` before reporting completion.
