# Specification

## Problem

Long form writing projects often depend on recurring entities such as characters, settings, organizations, and important objects.

Without structured element tracking, writers end up scattering this information across notes, chapter text, and memory.

That makes it harder to:

1. keep names and aliases consistent
2. remember relationships between characters or places
3. check where an element appears
4. review continuity across the manuscript

LivingWriter exposes useful ideas here through elements, relations, aliases, and appears in tracking.

`openscribe` should adopt the useful core of that model without importing the rest of the platform complexity.

## Proposed MVP Definition

The elements MVP is considered complete when this path works:

1. create a character element
2. create a setting or item element
3. add aliases and notes to an element
4. define a relation between two elements
5. inspect where an element appears in the manuscript
6. review element details from the CLI or TUI

## Product Position

This feature should focus on:

1. structured element records
2. aliases
3. relations
4. appears in tracking
5. lightweight review in CLI and TUI

It should avoid:

1. full graphical relationship maps
2. cloud collaboration
3. AI first workflows
4. trying to replace the board or manuscript systems

## Interfaces

### CLI Interface

Possible first command shapes:

1. `openscribe element add character "Marcus Vale"`
2. `openscribe element add setting "North Station"`
3. `openscribe element alias add <element-id> "The Courier"`
4. `openscribe element relate <element-a> <element-b> --type ally`
5. `openscribe element show <element-id>`
6. `openscribe element appears-in <element-id>`

The exact surface can change, but the first version should stay readable and narrow.

### TUI Interface

The first TUI support only needs enough to:

1. list elements
2. filter by type
3. inspect details
4. inspect relations
5. inspect appears in results

### Storage Interface

Element data should live under project local plain files.

Suggested area:

1. `characters/`
2. `.openscribe/elements/`

The first version should choose one clear approach and keep it simple.

## Data Model

The first element model should support:

1. element id
2. type
3. primary name
4. aliases
5. tags or labels
6. notes or description
7. relations to other element ids
8. appears in references
9. created and updated timestamps

## Appears In Tracking

The first version can start with chapter level tracking.

Two acceptable strategies for the MVP:

1. explicit references in chapter frontmatter
2. derived references from a controlled scan pass

The important part is that the behavior is clear and documented.

## Constraints

1. This feature comes after compile and core manuscript workflow improvements.
2. Storage must stay human readable.
3. The first version must not require a derived index, though it may benefit from one later.
4. The model must stay flexible enough for future scene level tracking.

## Risks

1. Element scope could sprawl into worldbuilding software.
2. Automatic appears in detection could become noisy if done too early.
3. Too many commands could make the feature feel heavier than the benefit it provides.
4. Multiple storage locations could confuse users if the model is not chosen clearly.

## Acceptance Criteria

1. A user can create and inspect elements of multiple types.
2. A user can add aliases to an element.
3. A user can create relations between elements.
4. A user can inspect where an element appears in the manuscript.
5. The feature remains separate from board mode and usable without it.
6. The feature remains separate from cloud, collaboration, and AI features.
