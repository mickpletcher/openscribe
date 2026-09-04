# Project Standard

**Standard version:** 2.2
**Project tier:** 1
**Lifecycle mode:** Adoption
**Tier rationale:** `openscribe` is an installable tool with multiple application modules, a CLI, a TUI, export libraries, and optional AI integrations. It is not a deployed service and no client agreement or operational support obligation exists in this repository.
**Promotion trigger:** Promote to Tier 2 if the project becomes a deployed or shared service, gains multiple active maintainers, or a runtime failure can affect external users or workflows.

This repository follows Software Project Living Documentation Standard 2.2.

## Authority Mapping

| Responsibility | Authority | Class | Notes |
|---|---|---|---|
| Project overview | `README.md` | Living | Existing authority adapted on 2026-09-04 |
| Current assessment | `assessment.md` | Living | Existing authority adapted on 2026-09-04 |
| Architecture | Not required at this tier | Living | Promote with the repository tier |
| Change history | `changelog.md` | Living | Existing date-based history preserved |
| Defect tracking | Not required at this tier | Living | Use a repository issue only if a defect must be tracked before Tier 2 |
| Technical debt | `TECH-DEBT.md` | Living | Created during adoption |
| Deferred improvements | `future-upgrades.md` | Living | Existing local plan adopted as a tracked authority |
| Validation | `VALIDATION.md` | Living | Created during adoption |
| Operations | Not required at this tier | Living | There is no deployed runtime |
| Requirement traceability | Not required at this tier | Living | Tier 2C only |
| Agreed scope | Not required at this tier | Contractual | No client agreement is stored in this repository |
| Agreed design | Not required at this tier | Contractual | No client agreement is stored in this repository |
| Scope amendments | Not required at this tier | Contractual | No client agreement is stored in this repository |
| Decision history | Not required at this tier | Derived | Optional at Tier 1 |
| Resolved history | `completed-upgrades.md` | Derived | Existing history adopted without reconstruction |
| Development rules | `PROJECT-STANDARD.md` | Governance | This file |
| Agent rules | `AGENTS.md` | Governance | Single repository agent authority |

The machine-readable map is `.docs-authority.json`. It must match this table.

## Document Classes

- Living documents describe current repository truth. Correct them when evidence changes.
- Contractual documents preserve an agreement. Never rewrite one to match implementation.
- Derived documents preserve decisions or resolved history. Existing entries are immutable.
- Governance documents define repository process. Change them only when the process changes and record the change.

## Source of Truth

For what the software does, executable repository state governs, followed by configuration and schemas, tests, validation documentation, the assessment, and README summaries.

For what the software should do, an explicit agreement governs. This Tier 1 repository has no contractual authority. Feature plans in `specs/` and `future-upgrades.md` are not client requirements.

A conflict between behavior and an explicit agreement is a scope finding. Do not rewrite either side to conceal it.

## Change Classes

| Class | Name | Typical work |
|---|---|---|
| 0 | Trivial | Formatting, typo, generated output refresh with no input change |
| 1 | Documentation | Human-facing documentation only |
| 2 | Internal implementation | Refactor or test-only change with no interface change |
| 3 | Functional | Feature, bug fix, dependency, configuration, interface, or API change |
| 4 | Architecture or security | Data model, trust boundary, deployment, authentication, authorization, or major architecture change |

Class 0 changes need no documentation lifecycle. Every Class 1 or higher change is meaningful.

## Routed Reads

Resolve each responsibility through the Authority Mapping before reading or writing.

| Change | Read before work | Review after work |
|---|---|---|
| Documentation only | Target authority | Target authority |
| Internal refactor or tests | Current assessment, technical debt, validation | Change history, technical debt, current assessment |
| Bug fix | Current assessment, validation | Change history, technical debt, current assessment |
| Feature or interface change | Project overview, current assessment, validation, deferred improvements | Project overview, change history, validation, deferred improvements, current assessment |
| Dependency or configuration change | Current assessment, technical debt, validation | Change history, technical debt, validation, current assessment |
| Architecture or security change | Current assessment, technical debt, validation | Change history, technical debt, validation, current assessment, decision history if the tier has one |

Read the Agent Handoff in `assessment.md` for every Class 2 or higher task.

## Development Lifecycle

For every Class 1 or higher change:

1. Classify the change.
2. Resolve and read only the routed authorities.
3. Inspect the relevant repository behavior.
4. For Class 4, presume an ADR is required. If this tier does not maintain decision history, state in the completion report why no ADR was created.
5. For Class 4, obtain a second reviewer where practical. If review is unavailable, state that limitation in the completion report.
6. Implement the smallest coherent change.
7. Run the validation required by `VALIDATION.md`.
8. Record a waiver for required validation that cannot run.
9. Correct living authorities made stale by the result.
10. Perform a final repository and documentation consistency check.

## Branch and History Policy

- On feature branches, add a dated file under `changelog.d/` instead of editing `changelog.md`.
- Consolidate fragments into `changelog.md` on the main branch or during release work.
- Update `assessment.md` on the main branch only.
- Keep validation evidence in the completion report, commit, or pull request. `VALIDATION.md` contains procedures, not run history.
- Do not edit existing entries in `completed-upgrades.md`. Add new resolved history entries without rewriting earlier ones.

## Evidence and Waivers

Every material living-document claim must cite repository evidence, state that it is unverified, or be omitted.

Report executed validation with command, result, exit code, passed, failed, and skipped counts. If a required check cannot run, record the requirement, reason, risk, and follow-up. Time pressure and inconvenience are not waiver grounds.

Standing validation limitations belong in `VALIDATION.md`. Accepted reductions in assurance belong in `TECH-DEBT.md`. Both must be visible in `assessment.md`.

## Security Rules

- Never commit secrets, tokens, credentials, private certificates, or manuscript data from a user's project.
- Use placeholders in configuration examples.
- Do not weaken a security or privacy control to simplify implementation.
- Hosted AI features must disclose what content will leave the machine and require explicit approval before transfer.

## Documentation Review

Run `pwsh -File scripts/docs-check.ps1 -FailOnGap` after every meaningful documentation change and during quarterly review. Review `REVIEW` rows rather than treating age alone as proof of staleness.

Quarterly review is limited to compliance gaps, standing waivers, open debt, resolved-history archival, and removal of living documents that no longer earn their maintenance cost.
