# Requirements

## Goal

Add first class project elements and relations to `openscribe` so writers can track characters, settings, items, aliases, and chapter usage across a manuscript.

The elements milestone is complete when a writer can:

1. create elements in structured project files
2. classify them by type
3. record aliases or alternate names
4. define relations between elements
5. see where elements appear in the manuscript
6. inspect element information without leaving the project

## Functional Requirements

1. `openscribe` must support structured elements at the project level.
2. The first element types must include character, setting, and item.
3. Each element must support a name.
4. Each element must support notes or description text.
5. Each element must support tags or labels.
6. Each element must support alternate names or aliases.
7. The project must support relations between elements.
8. The project must support appears in tracking across chapters and later scenes.
9. The feature must expose element inspection from the CLI or TUI.
10. The feature must not require board mode to exist first.

## Non Functional Requirements

1. Storage must stay plain and project readable.
2. The first version must stay lightweight and avoid a complex database.
3. Element tracking must help long form writing directly.
4. The first version must work for fiction first while staying extensible for nonfiction later.

## Out Of Scope

1. Full collaboration features
2. AI character generation
3. Rich graphical family trees
4. Cloud sync
5. Full screenplay specific element models
