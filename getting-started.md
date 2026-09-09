# OpenScribe getting started on Windows

This guide takes you from an empty Windows computer to a saved and exported writing project.

You do not need Python, Git, command-line, or AI experience.

## What you will do

You will:

1. download and install OpenScribe
2. start the desktop application
3. create a project, chapter, and scene
4. save and reopen your writing
5. create a checkpoint
6. export a Word document

Allow about 10 minutes for the first setup.

## Before you start

OpenScribe is pre-release alpha software. Keep an independent copy of important writing outside the project folder.

You need Windows 11 and a web browser. The packaged installer includes the application and its Python runtime.

You do not need Microsoft Word, Pandoc, LanguageTool, or an AI account for the basic workflow.

## Step 1: Download OpenScribe

1. Open the [OpenScribe releases page](https://github.com/mickpletcher/openscribe/releases).
2. Open the newest release.
3. Download `OpenScribe-Setup-VERSION-x64.exe`.
4. Download `SHA256SUMS.txt` from the same release.

If the release has no Windows setup file, use [Install from source instead](#install-from-source-instead).

## Step 2: Check the download

This check confirms that the installer is the same file published with the release.

Open PowerShell and run:

```powershell
Set-Location $env:USERPROFILE\Downloads
$installer = Get-ChildItem -LiteralPath . -Filter "OpenScribe-Setup-*-x64.exe" | Select-Object -First 1
Get-FileHash -LiteralPath $installer.FullName -Algorithm SHA256
Get-Content -LiteralPath .\SHA256SUMS.txt
```

Compare the long SHA-256 value printed by both commands. The letters can differ in capitalization. The numbers and letters must otherwise match exactly. Stop if they do not match.

## Step 3: Install OpenScribe

1. Double-click the downloaded setup file.
2. If Windows shows **Windows protected your PC**, select **More info** and confirm the publisher says **Unknown publisher**. Continue only after the checksum matched in Step 2 and you downloaded the file from this repository. Select **Run anyway**.
3. Keep the default installation folder.
4. Leave **Create a desktop shortcut** selected if you want one.
5. Select **Install**, then **Finish**.

OpenScribe installs only for your Windows account. It does not require administrator access.

## Step 4: Start the desktop application

1. Open the Start menu.
2. Type `OpenScribe`.
3. Select **OpenScribe**.

The application opens with a toolbar, a project binder on the left, a writing editor in the center, and reference information on the right.

If no window appears, use [The installed desktop application does not open](docs/troubleshooting.md#the-installed-desktop-application-does-not-open).

## Step 5: Create your first project

In the desktop application:

1. Select **New project**.
2. Create or choose an empty folder such as `Documents\OpenScribe\my-novel`.
3. Enter `My Novel` as the project title.
4. Select **New chapter**.
5. Enter `Arrival`.
6. Select the new chapter in the binder.
7. Select **New scene**.
8. Enter `Bus Stop`.
9. Select the scene and type a few sentences in the editor.
10. Press `Ctrl+S`.

The status bar should confirm the save. The project folder now contains `.openscribe`, `manuscript`, `characters`, `research`, `notes`, and `build` folders.

For a detailed explanation of every screen area and button, use the [desktop guide](docs/desktop-guide.md).

## Step 6: Close and reopen the project

1. Close OpenScribe.
2. Start it again from the Start menu.
3. Select **Open**.
4. Choose the `my-novel` project folder, not its `manuscript` subfolder.
5. Select `Arrival` and `Bus Stop`.

Your saved text should appear.

If you close while text is unsaved, OpenScribe asks you to Save, Discard, or Cancel. Choose **Cancel** when you are unsure.

## Step 7: Create a checkpoint

Before a large rewrite or structural change:

1. Select **Checkpoint** in the toolbar.
2. Confirm that the status bar reports a checkpoint.

You can also create one from the **OpenScribe command line** Start menu shortcut:

```powershell
openscribe snapshot save "first-writing-session"
openscribe snapshot list
```

Snapshots are stored under `.openscribe\snapshots` inside the project.

## Step 8: Export a Word document

In the desktop application:

1. Select **Export**.
2. Choose `docx`.
3. Save the file in the project's `build` folder.

Or run this from the project folder:

```powershell
openscribe compile --format docx
```

This creates a normal Word document for reading, review, or submission. It is separate from the experimental Word round-trip workflow.

PDF and EPUB are also available:

```powershell
openscribe compile --format pdf
openscribe compile --format epub
```

## Install from source instead

Use the source route for development or when a packaged release is not available.

1. Install [Git for Windows](https://git-scm.com/download/win).
2. Install [Python 3.11 or newer](https://www.python.org/downloads/windows/).
3. Open PowerShell.
4. Run one block at a time:

```powershell
Set-Location $env:USERPROFILE\Documents
git clone https://github.com/mickpletcher/openscribe.git
Set-Location .\openscribe
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[desktop]"
openscribe desktop
```

Python 3.12 and 3.13 are also supported. If activation fails, use [Troubleshooting](docs/troubleshooting.md).

## Command-line alternative

You can create the same first project without using the **New project** window.

Open **OpenScribe command line** from the Start menu. It defines the `openscribe` command for that PowerShell window. Source users can run the same commands from their activated environment.

```powershell
$projectPath = Join-Path $env:USERPROFILE "Documents\OpenScribe\my-novel-cli"
openscribe init "My Novel" --path $projectPath --template fiction
Set-Location $projectPath
openscribe migrate status
openscribe new part "Opening"
openscribe new chapter "Arrival" --part "Opening"
openscribe new scene "Bus Stop" --chapter "Arrival" --body "The bus doors closed behind her."
openscribe outline
openscribe outliner
openscribe status
openscribe read
openscribe snapshot save "first-pass"
openscribe snapshot list
openscribe snapshot restore "first-pass"
openscribe compile --format docx
```

Important points:

- `--path` creates the project in the folder you selected.
- Most later commands must run from that project folder or one of its subfolders.
- `migrate status` should say no migration is required for a new project.
- `snapshot restore` without `--apply` is only a preview.
- Use `snapshot restore "first-pass" --apply` only after reviewing that preview.

## Using the terminal interface

From a project folder, run:

```powershell
openscribe tui
```

Essential keys:

| Key | Action |
|---|---|
| `Ctrl+S` | Save the selected chapter or scene |
| `Ctrl+F` | Focus search |
| `Ctrl+G` | Run configured local LanguageTool proofreading |
| `Ctrl+J` and `Ctrl+K` | Move through proofreading findings |
| `Ctrl+Shift+R` | Preview a suggested replacement |
| `Ctrl+Shift+A` | Apply the previewed replacement to the draft |
| `Ctrl+Shift+I` | Ignore a finding |
| `Ctrl+Z` | Undo a proofreading replacement |
| `q` | Quit and handle any unsaved draft |

The [desktop guide](docs/desktop-guide.md) explains the equivalent visual workflow.

## Research project example

Use a different unused folder for this example:

```powershell
$researchPath = Join-Path $env:USERPROFILE "Documents\OpenScribe\grid-study"
openscribe init "Grid Study" --path $researchPath --template research
Set-Location $researchPath
openscribe workflow research-paper --part "Paper"
Add-Content -LiteralPath .\manuscript\part-01-paper\ch-01-abstract.md -Value "`nThis paper examines resilient rural energy systems."
openscribe workflow source-note "River Ledger Study" --type article --author "J. Harper" --year 2024
openscribe workflow citation-pack --style Chicago
openscribe compile --profile research-paper
```

Do not run a second `init` command inside an existing project.

## Your project files

| Folder or file | Purpose |
|---|---|
| `.openscribe\project.yaml` | Project settings and format version |
| `.openscribe\drafts` | Recoverable unsaved desktop and TUI drafts |
| `.openscribe\snapshots` | Checkpoints and automatic backups |
| `manuscript` | Parts, chapters, and scenes |
| `characters` | Character profiles and notes |
| `research` | Sources, citations, and research notes |
| `notes` | Planning, revision notes, and story ideas |
| `build` | Exported DOCX, PDF, and EPUB files |

Markdown remains the source of truth. Do not delete `chapter_id` fields or `openscribe-scene-id` comments when editing files manually.

## Safe daily habits

- Press `Ctrl+S` regularly.
- Create a checkpoint before moving, splitting, or merging scenes.
- Preview restores and structural commands before applying them.
- Close other editors before resolving a save conflict.
- Keep an independent backup outside the project folder.
- Do not use experimental Word import on your only manuscript copy.
- Read the disclosure before allowing manuscript text to reach a hosted AI or proofreading service.

Read [Safety and recovery](docs/safety-and-recovery.md) for the full rules.

## Where to go next

- [Desktop guide](docs/desktop-guide.md)
- [Complete CLI reference](docs/cli-reference.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Safety and recovery](docs/safety-and-recovery.md)
- [North County sample project](examples/north-county/README.md)
- [Optional AI setup](docs/ai-setup.md)
