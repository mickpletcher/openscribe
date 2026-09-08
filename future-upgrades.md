# Future Upgrades

### FU-001: Add richer scene metadata

**Status:** Planned
**Priority:** High
**Area:** Manuscript data model
**Origin:** Internal

**Opportunity**

Add status, synopsis, point of view, target, notes, and related-element metadata keyed to the immutable scene IDs without abandoning Markdown headings.

**Potential benefit**

Writers can manage scene progress and continuity with the same depth already available at chapter level.

**Why deferred**

Immutable scene IDs and the versioned migration framework are complete. The remaining metadata format needs a separate persisted-data decision before implementation.

**Trigger**

When scene-level planning becomes a higher priority than the remaining TUI and release hardening work.

**Estimated effort:** Large
**Dependencies:** Immutable scene IDs

### FU-004: Validate and harden Word round-trip integration

**Status:** In progress
**Priority:** Medium
**Area:** Microsoft Word integration
**Origin:** Internal

**Opportunity**

Validate the experimental OOXML importer, local bridge, and task pane against real supported desktop Word hosts before claiming production interoperability. The implemented safety design is described in `specs/004-word-round-trip/` and ADR-006.

**Potential benefit**

Writers can use Word without making DOCX the canonical store.

**Why deferred**

The package layer, importer, bridge, and task pane are implemented. The 2026-09-08 independent Class 4 review found no confirmed defect in the Word bridge or three-way merge logic, but it found separate identity and conflict release blockers that require remediation and re-review. Real Word save/reopen, task-pane sideload, certificate, and accessibility gates also remain open. See VL-004 and VL-006 in `VALIDATION.md`.

**Trigger**

Before removing the experimental label or using the workflow on an only copy of a manuscript.

**Estimated effort:** Large
**Dependencies:** `specs/004-word-round-trip/`, stable chapter and scene IDs, snapshot recovery

### FU-005: Customize compile profiles per project

**Status:** Proposed
**Priority:** Medium
**Area:** Compile pipeline
**Origin:** Internal

**Opportunity**

Add project-level profile names, filenames, heading rules, and richer formatting controls.

**Potential benefit**

Projects can encode repeatable publication and submission formats.

**Why deferred**

Current profiles cover the basic export workflow.

**Trigger**

When a real project requires formatting the existing profiles cannot express.

**Estimated effort:** Medium
**Dependencies:** None

### FU-006: Deepen board and manuscript links

**Status:** Proposed
**Priority:** Medium
**Area:** Planning and TUI
**Origin:** Internal

**Opportunity**

Add board backlink summaries, chapter links to elements and research, and freeform synopsis and notes editing in the TUI.

**Potential benefit**

Planning data becomes easier to navigate from manuscript structure.

**Why deferred**

The current CLI covers these authoring operations and TUI interaction debt remains open.

**Trigger**

After TD-003 is reduced.

**Estimated effort:** Medium
**Dependencies:** TD-003

### FU-007: Add library comparison views

**Status:** Proposed
**Priority:** Low
**Area:** TUI
**Origin:** Internal

**Opportunity**

Add side-by-side comparison for research, characters, chapters, and revisions.

**Potential benefit**

Related material can be reviewed without switching tools.

**Why deferred**

Core mutation and accessibility coverage has higher value.

**Trigger**

After TD-003 is reduced.

**Estimated effort:** Medium
**Dependencies:** TD-003

### FU-008: Promote story ideas into projects

**Status:** Proposed
**Priority:** Low
**Area:** Project workflow
**Origin:** Internal

**Opportunity**

Create a new project scaffold from a structured story idea.

**Potential benefit**

Planning notes can enter the writing workflow without manual recreation.

**Why deferred**

It does not improve current manuscript integrity or recovery.

**Trigger**

When story-idea capture is used across multiple real projects.

**Estimated effort:** Small
**Dependencies:** None

### FU-009: Import and share template packages

**Status:** Proposed
**Priority:** Low
**Area:** Templates
**Origin:** Internal

**Opportunity**

Import versioned template packages from files or repositories with validation and provenance.

**Potential benefit**

Template reuse can extend beyond one local project.

**Why deferred**

External package trust and update rules are not defined.

**Trigger**

After the template schema is versioned and trust rules are documented.

**Estimated effort:** Medium
**Dependencies:** Versioned template schema and documented external-package trust rules

### FU-010: Add milestones and revision phases

**Status:** Proposed
**Priority:** Low
**Area:** Project tracking
**Origin:** Internal

**Opportunity**

Track project milestones and revision phases alongside existing goals and deadlines.

**Potential benefit**

Long projects gain clearer progress reporting.

**Why deferred**

Current goal tracking is enough to validate the workflow.

**Trigger**

When multiple revision cycles are managed in one real project.

**Estimated effort:** Medium
**Dependencies:** None

### FU-011: Deepen citation and conference workflows

**Status:** Proposed
**Priority:** Low
**Area:** Research and conference output
**Origin:** Internal

**Opportunity**

Add venue-specific bibliography styles, bulk source relinking, deeper schedule transforms, and reminder integration.

**Potential benefit**

Research and conference output needs less manual cleanup.

**Why deferred**

The current research workflow is usable and integrity work has higher priority.

**Trigger**

When a specific venue or journal exposes a reproducible gap.

**Estimated effort:** Medium
**Dependencies:** None
