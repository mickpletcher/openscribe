# Specification

## Problem

`openscribe` is aimed at long form writing, but it currently assumes the writer already knows where an idea belongs.

That is not how book planning usually works.

Writers often need a loose space where they can:

1. drop an idea quickly
2. connect it to characters, scenes, or themes
3. cluster related thoughts
4. rearrange their thinking before committing to outline order

Without this, `openscribe` handles manuscript structure but not early stage exploration.

## Proposed MVP Definition

The board MVP is considered complete when this path works:

1. create a board note
2. create more notes anywhere in the same board
3. connect notes together
4. group notes into a cluster
5. review the board without changing binder order
6. promote one or more notes into manuscript structure

## Product Position

This feature is inspired by Scapple style freeform note mapping, but the goal is narrower.

`openscribe` should not try to clone a full visual brainstorming tool in the first pass.

The first version should focus on:

1. freeform note capture
2. note to note links
3. basic grouping
4. rearranging notes
5. promotion into manuscript structure

This board should absorb only the LivingWriter style ideas that help planning directly:

1. planning board behavior
2. research note visibility
3. manuscript structure support through explicit promotion

It should not absorb unrelated platform features such as cloud sync, AI assistance, or heavy collaboration tooling.

The first version should avoid:

1. heavy styling
2. polished diagram behavior
3. print focused board export
4. replacing the main writing workflow

## Interfaces

### CLI Interface

Possible first command shapes:

1. `openscribe board`
2. `openscribe board note add "Idea text"`
3. `openscribe board note list`
4. `openscribe board link add <from> <to>`
5. `openscribe board promote <note-id> --chapter "New Chapter"`

The exact surface can change, but the first version should stay compact.

### TUI Interface

The board can live as a separate TUI mode rather than being mixed into the binder view.

The first version only needs enough interaction to:

1. create notes
2. move focus between notes
3. view linked notes
4. assign groups
5. promote notes

Later board improvements can add board aware previews of related manuscript notes or research notes, but not in the first pass.

### Storage Interface

Board state should be stored in project local files under `.openscribe/`.

Suggested area:

1. `.openscribe/boards/`
2. `.openscribe/boards/default.yaml`

Storage should be plain and inspectable.

## Data Model

The first board data model should support:

1. note id
2. note title
3. note body
4. optional x and y position
5. group id or group name
6. links to other note ids
7. created and updated timestamps

## Constraints

1. This feature comes after compile and other core writing workflow gaps.
2. The first version must work in terminal friendly ways.
3. Board content must stay separate from manuscript content until the user promotes it.
4. Promotion should create or fill normal manuscript files rather than inventing a second manuscript system.
5. The board must stay focused on planning and must not become the place where all note, task, or collaboration features accumulate.

## Risks

1. Board scope could expand too fast into a full diagram tool.
2. Terminal rendering may not feel natural for spatial layouts.
3. Promotion rules may become confusing if they try to do too much.
4. Poor separation between board and binder could make the project model messy.

## Acceptance Criteria

1. A user can create and store freeform planning notes in the project.
2. A user can link related notes.
3. A user can assign notes to simple groups.
4. Board notes do not affect manuscript order unless promoted.
5. A user can promote a board note into a chapter or scene stub.
6. The feature remains clearly separate from the compile and binder workflows.
7. The feature does not require cloud sync, AI features, or collaboration features to be useful.
