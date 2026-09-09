# OpenScribe desktop guide

The desktop application is the recommended interface for most writers.

Complete [Getting started](../getting-started.md) first if OpenScribe is not installed.

## Start the application

After using the Windows installer, open the Start menu, type `OpenScribe`, and select **OpenScribe**.

To open a known project immediately, start **OpenScribe command line** and run:

```powershell
openscribe desktop --project "C:\Users\YourName\Documents\OpenScribe\my-novel"
```

Use your own project path. Do not copy the example username literally.

Source installations use the activated Python environment:

```powershell
.\.venv\Scripts\Activate.ps1
openscribe desktop
```

## Understand the window

The window has four main areas:

| Area | Purpose |
|---|---|
| Toolbar | Project, save, structure, proofreading, export, checkpoint, restore, and Word actions |
| Project binder | Chapters, scenes, characters, research, and notes |
| Manuscript editor | Draft text for the selected chapter or scene |
| Reference panel | Proofreading findings and supporting information |

On a narrow window, some toolbar actions appear in the toolbar overflow menu.

## Create a project

1. Select **New project**.
2. Choose an empty folder.
3. Enter the project title.
4. Wait for the binder to appear.

OpenScribe creates the project directly in the folder you chose. It will refuse a folder that already contains an OpenScribe project.

To open an existing project, select **Open** and choose the folder containing `.openscribe\project.yaml`.

## Create a chapter and scene

1. Select **New chapter**.
2. Enter a chapter title.
3. Select the chapter in the binder.
4. Select **New scene**.
5. Enter a scene title.
6. Select the chapter or scene you want to edit.

If the manuscript has no part yet, the desktop application creates a default `Manuscript` part when you add the first chapter.

## Write and save

Type in the center editor and press `Ctrl+S` to save.

A save does three things:

1. checks that the manuscript file has not changed since it was loaded
2. creates a checkpoint
3. writes the edited text through the shared recovery transaction

OpenScribe does not silently replace a newer external edit.

The chapter editor is for prose. Keep scene headings and hidden identity markers intact. Use **New scene**, **Move up**, and **Move down** for structure changes.

## Navigate with unsaved text

OpenScribe keeps a separate draft for each chapter or scene you edit. Moving to another binder item does not throw away the first draft.

Local recovery drafts are written about once per second and during navigation. They are stored under `.openscribe\drafts`.

When closing with unsaved text, choose:

- **Save** to write the manuscript after conflict checks
- **Discard** to remove the draft and keep the last saved manuscript
- **Cancel** to stay in the application

Choose **Cancel** if you are uncertain.

Recovery drafts reduce risk but do not guarantee the final second of typing after an abrupt failure.

## Reload a document

Use **Reload** when you intentionally want the current disk version.

If the current editor contains an unsaved draft, OpenScribe asks before discarding it. Reload does not merge the draft with external changes.

Copy important draft text to a separate file before discarding it during a conflict.

## Handle an external-edit conflict

If VSCode, Word, synchronization software, or another OpenScribe window changes the chapter after it was loaded, save is blocked.

When that happens:

1. leave the OpenScribe window open
2. copy the visible draft to a separate temporary text file
3. inspect the current Markdown file in the external editor
4. decide which changes to keep
5. reload the OpenScribe document
6. reapply the wanted draft text
7. save again

Do not delete the external version merely to make the warning disappear.

## Search and reference material

Use the search field above the binder to filter chapters, scenes, characters, research, and notes.

Character, research, and note documents are currently reference views. Edit those Markdown files in an external editor when changes are needed.

## Proofread with LanguageTool

Desktop proofreading works only with a configured local LanguageTool-compatible endpoint.

1. Start the local LanguageTool server.
2. Enable proofreading in `.openscribe\project.yaml`.
3. Select a chapter or scene.
4. Select **Proofread** or press `Ctrl+G`.
5. Select a finding and replacement.
6. Preview the replacement.
7. Apply it to the current draft.
8. Press `Ctrl+S` when you are ready to save.

Undo reverses the last proofreading replacement. A text change after preview invalidates that preview.

The desktop application refuses hosted proofreading. Use the CLI disclosure flow for an approved licensed hosted endpoint.

## Move a scene

Select a scene and use **Move up** or **Move down**.

OpenScribe saves the current draft first, then displays the planned change. Review the preview before applying it. Applied scene movement creates a checkpoint.

Use the CLI for moving scenes across chapters, splitting scenes, and merging scenes. See [Scene structure](cli-reference.md#scene-structure).

## Export a manuscript

1. Select **Export**.
2. Choose DOCX, PDF, or EPUB.
3. Choose the output filename.
4. Save it under `build` or another review folder.

Export saves the active draft first. Exported files are outputs. Markdown remains the manuscript source.

## Create a checkpoint

Select **Checkpoint** before a large rewrite, scene movement, import, or restore experiment.

The checkpoint is stored under `.openscribe\snapshots`. It is not an off-device backup.

## Restore a checkpoint

1. Save or discard the active draft.
2. Select **Restore**.
3. Choose a checkpoint.
4. Review the files that will be added, modified, or deleted.
5. Apply only when the preview matches your intent.

Restore creates another automatic backup before changing managed project files.

Do not interrupt a restore intentionally. If the application stops during restore, reopening the project runs transaction recovery before loading project data.

## Export to Word for normal review

Use **Export** and select DOCX when someone only needs to read, comment on, or submit the manuscript. Changes in that normal DOCX do not import back into OpenScribe.

## Experimental Word import

**Word export** creates a tagged round-trip document and a private baseline. **Word import** previews changes from that tagged file and can apply them after validation.

The import is blocked when OpenScribe detects:

- conflicting Markdown and Word edits
- missing or duplicate identity controls
- unsupported structural changes
- unresolved tracked changes
- a changed project after preview

Use this only with synthetic or copied writing until real desktop Word testing is complete. See [Experimental Word round trips](safety-and-recovery.md#experimental-word-round-trips).

## Exit safely

1. Save the active draft with `Ctrl+S`.
2. Confirm the status bar reports success.
3. Close the application.
4. Resolve any Save, Discard, or Cancel prompt deliberately.
5. Make an independent backup after important sessions.

## Current desktop limitations

- Rich-text formatting is not provided in the manuscript editor.
- Drag-based binder reordering is not implemented.
- Reference documents are read only in the desktop application.
- Hosted proofreading is CLI only.
- Native accessibility and real Word interoperability remain release gates.

For errors, use [Troubleshooting](troubleshooting.md). For backup and recovery rules, use [Safety and recovery](safety-and-recovery.md).
