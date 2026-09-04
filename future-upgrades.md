# Future Upgrades

### FU-001: Add scene identity and metadata

**Status:** Planned
**Priority:** High
**Area:** Manuscript data model
**Origin:** Internal

**Opportunity**

Add immutable scene IDs plus status, synopsis, point of view, target, notes, and related-element metadata without abandoning Markdown headings.

**Potential benefit**

Scenes can be linked and reorganized without depending on changeable headings or positions.

**Why deferred**

The versioned migration framework in `TD-001` must be resolved first.

**Trigger**

After the current integrity changes pass hosted CI and a restore drill.

**Estimated effort:** Large
**Dependencies:** TD-001

### FU-002: Add previewable scene restructuring

**Status:** Planned
**Priority:** High
**Area:** Manuscript workflow
**Origin:** Internal

**Opportunity**

Add scene reorder, split, and merge commands within and across chapters.

**Potential benefit**

Large drafts can be restructured without manual copy and paste.

**Why deferred**

Safe restructuring depends on stable scene identity and recovery behavior.

**Trigger**

After FU-001 and a destructive-operation preview design are complete.

**Estimated effort:** Large
**Dependencies:** FU-001

### FU-003: Add scoped AI review and suggestion commands

**Status:** Planned
**Priority:** High
**Area:** AI workflow
**Origin:** Internal

**Opportunity**

Add pacing, continuity, point of view, prose, rewrite-suggestion, outline, metadata-suggestion, and project-query commands.

**Potential benefit**

Writers can request focused analysis instead of generic chat.

**Why deferred**

Scene workflow and data-selection boundaries should stabilize first.

**Trigger**

After FU-001 and FU-002 establish stable scene scope.

**Estimated effort:** Large
**Dependencies:** FU-001, FU-002, existing hosted data-transfer approval

### FU-004: Design Word round-trip integration

**Status:** Proposed
**Priority:** Medium
**Area:** Microsoft Word integration
**Origin:** Internal

**Opportunity**

Define paragraph-to-chapter and scene identity, conflict detection, preview, backup, tracked-change handling, and a desktop local bridge before building an Office add-in.

**Potential benefit**

Writers can use Word without making DOCX the canonical store.

**Why deferred**

Round-trip identity and conflict behavior are not defined, and Word export is currently one-way.

**Trigger**

After scene identity and recovery behavior are proven.

**Estimated effort:** Large
**Dependencies:** FU-001, FU-002

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
**Dependencies:** TD-001

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

### FU-012: Surface LanguageTool findings in the TUI editor

**Status:** Proposed
**Priority:** Medium
**Area:** Proofreading and TUI
**Origin:** User

**Opportunity**

Display LanguageTool findings beside chapter text with navigation, ignore controls, and previewable replacement actions.

**Potential benefit**

Writers can review prose without leaving the authoring interface while Markdown remains the source of truth.

**Why deferred**

The chapter CLI integration proves the API and privacy boundary first. Safe replacement workflows also need broader TUI interaction coverage.

**Trigger**

After TD-003 is reduced and the local LanguageTool contract is verified against a real server.

**Estimated effort:** Medium
**Dependencies:** TD-003, current chapter proofreading command
