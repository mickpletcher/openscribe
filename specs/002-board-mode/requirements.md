# Requirements

## Goal

Add a lightweight board mode to `openscribe` so writers can capture loose ideas, group them, connect them, and later promote them into manuscript structure.

The board milestone is complete when a writer can:

1. create freeform notes inside a project
2. connect related notes
3. group notes by topic or purpose
4. rearrange notes without affecting binder order
5. turn selected notes into manuscript parts, chapters, or scene stubs

## Functional Requirements

1. `openscribe` must expose a board focused command or mode.
2. Board data must live inside the project in plain text or another project readable format.
3. A board note must support free text content.
4. A board note must support a title or short label.
5. Board notes must be creatable without assigning them to the manuscript binder.
6. The board must support links between notes.
7. The board must support simple group membership for related notes.
8. Moving notes on the board must not change manuscript order.
9. The board must support promoting a note or group into manuscript content.
10. Promotion must be explicit and user directed.
11. The board must remain usable without requiring mouse heavy interaction.

## Non Functional Requirements

1. The first version must stay simple and text first.
2. The first version must not depend on complex canvas rendering.
3. The design must support book planning better than generic mind mapping.
4. The board must not become a blocker for the writing workflow if a user chooses to ignore it.
5. Storage must remain project local and inspectable.

## Out Of Scope

1. Fancy visual diagram behavior
2. Curved connectors or rich styling tools
3. Print ready board layouts
4. Real time collaboration
5. Full graphical desktop canvas
