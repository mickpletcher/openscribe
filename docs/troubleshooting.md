# Troubleshooting OpenScribe

Start with the section that matches the message or behavior you see.

Do not delete project files, drafts, snapshots, or recovery journals just to clear an error.

## Git or Python is not recognized

Check:

```powershell
git --version
py --version
py -0p
```

If `git` is not recognized, install [Git for Windows](https://git-scm.com/download/win).

If `py` is not recognized, install a supported Python version from [python.org](https://www.python.org/downloads/windows/). OpenScribe supports Python 3.11, 3.12, and 3.13.

Close and reopen PowerShell after installation so the updated `PATH` is loaded.

## PowerShell blocks Activate.ps1

The error commonly says that script execution is disabled.

Allow scripts only in the current PowerShell process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

This setting ends when that PowerShell window closes. It does not change the machine-wide policy.

If organizational policy still blocks activation, call the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[desktop]"
.\.venv\Scripts\python.exe -m openscribe --help
```

## openscribe is not recognized

Activate the environment from the OpenScribe source folder:

```powershell
.\.venv\Scripts\Activate.ps1
openscribe --help
```

Or use:

```powershell
python -m openscribe --help
```

If that fails, reinstall the project into the active environment:

```powershell
python -m pip install -e ".[desktop]"
```

## The desktop application does not open

Confirm the desktop dependency is installed:

```powershell
python -m pip install -e ".[desktop]"
openscribe desktop --help
openscribe desktop
```

Run the final command from PowerShell and keep the window open. Read any error printed there.

Do not set `QT_QPA_PLATFORM=offscreen` for normal desktop use. That setting is for automated headless tests.

## No openscribe project found

Most commands need to run from the project folder or one of its subfolders.

Find the folder that contains:

```text
.openscribe\project.yaml
```

Then change to it:

```powershell
Set-Location "C:\Users\YourName\Documents\OpenScribe\my-novel"
openscribe status
```

Selecting `manuscript` in the desktop **Open** dialog is also wrong. Select the project folder above it.

## Project already exists

`openscribe init` refuses a folder that already contains `.openscribe\project.yaml`.

To use that project, open it instead of initializing again:

```powershell
Set-Location "C:\path\to\existing-project"
openscribe status
openscribe desktop --project .
```

To make a different project, choose a new empty path with `--path`.

## The quick-start project folder was not created

Use an explicit `--path`:

```powershell
$projectPath = Join-Path $env:USERPROFILE "Documents\OpenScribe\my-novel"
openscribe init "My Novel" --path $projectPath --template fiction
Set-Location $projectPath
```

Without `--path`, `openscribe init` initializes the current directory.

## An older project needs migration

Check without changing files:

```powershell
openscribe migrate status
```

Make an independent backup, then apply the reported steps:

```powershell
openscribe migrate apply
```

Migration creates an OpenScribe checkpoint before changing managed files.

## Chapter or scene identity is missing or malformed

Run:

```powershell
openscribe migrate repair
```

This explicitly replaces missing or malformed identities and repairs unambiguous legacy board links after creating a checkpoint.

OpenScribe will not guess how to fix duplicate identities or board links that match multiple titles or slugs. Preserve the project, inspect the reported IDs, replace each ambiguous legacy link with the intended immutable chapter ID, and run the command again.

If a normal command reports an ambiguous chapter or scene reference, rerun it with one of the immutable IDs listed in the error.

## Save says the chapter changed on disk

Another editor, synchronization process, or OpenScribe window changed the file after it was loaded.

Do this:

1. keep the editor open
2. copy the visible draft into a separate temporary text file
3. open the current Markdown chapter in VSCode or another editor
4. compare both versions
5. keep the text you need
6. reload the chapter in OpenScribe
7. reapply the chosen changes and save

OpenScribe blocks the save to prevent overwriting the newer disk version.

## A recovery draft appears

OpenScribe stores unsaved desktop and TUI drafts under `.openscribe\drafts`.

Reopen the same project and select the same chapter or scene. Review the recovered text before choosing Save or Discard.

If OpenScribe says the recovery draft is invalid, preserve the project and the reported draft file. Do not edit the JSON by guessing.

## The project is locked

Close other OpenScribe desktop windows, TUIs, or commands that are changing the same project. Then retry.

External editors do not use the OpenScribe lock. Close them before restore, migration, or Word import operations when possible.

Do not manually remove a lock during an active operation.

## The search index is stale

Rebuild it from the Markdown and YAML sources:

```powershell
openscribe index rebuild
openscribe index search "search words"
```

The index is derived data. Rebuilding it does not replace the manuscript.

## Export does not use Pandoc

Pandoc is optional. The default `auto` backend uses Pandoc when it is available and otherwise uses OpenScribe's native exporters.

Check whether PowerShell can find Pandoc:

```powershell
pandoc --version
Get-Command pandoc
```

Normal DOCX, PDF, and EPUB exports do not require Pandoc when the native dependencies are installed.

## Exported file is missing

Unless `--output` is supplied, exported files go under the project's `build` folder.

Run:

```powershell
openscribe compile --format docx
Get-ChildItem -LiteralPath .\build
```

Read the path printed by the compile command.

## LanguageTool does not connect

LanguageTool is optional and disabled by default.

Confirm the project configuration contains an enabled local endpoint similar to:

```yaml
proofreading:
  enabled: true
  endpoint: http://127.0.0.1:8081/v2/check
  language: en-US
  timeout_seconds: 30
```

Then test the server with synthetic text:

```powershell
$response = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8081/v2/check" -Body @{
    text = "This are a synthetic test."
    language = "en-US"
}
$response.matches.Count
```

If the connection is refused, start the local LanguageTool server and confirm it is listening on port `8081`.

Automated use of `https://api.languagetool.org` is intentionally rejected. Use a self-hosted server or an approved licensed endpoint.

## Hosted proofreading is refused in the desktop or TUI

That is intentional. Those interfaces allow local endpoints only.

Use the CLI for an approved licensed hosted endpoint. It displays the destination and text size and requires `--allow-data-transfer`.

Never place credentials inside the endpoint URL.

## AI provider command is blocked

Hosted AI commands require explicit approval on every invocation:

```powershell
openscribe ai summarize "Arrival" --allow-data-transfer
```

Read the disclosure first. Do not use the flag unless you approve sending the reported manuscript text to the reported endpoint.

If an SDK is missing, install the AI extras:

```powershell
python -m pip install -e ".[ai]"
```

See [AI setup](ai-setup.md) for provider configuration.

## Snapshot restore shows unexpected deletions

Cancel. A restore without `--apply` is only a preview.

An exact restore removes managed files that did not exist in the selected checkpoint. Inspect the snapshot label and preview again:

```powershell
openscribe snapshot list
openscribe snapshot diff "checkpoint-label"
openscribe snapshot restore "checkpoint-label"
```

Do not add `--apply` until every listed deletion is expected.

## Restore was interrupted

Reopen the project normally. OpenScribe runs journal recovery before loading project configuration.

If it reports an invalid journal, preserve the entire project including `.openscribe\.restore-transaction-*`. Do not delete the transaction folder or continue writing until it is inspected.

## Word import is blocked

Run preview from PowerShell for the clearest report:

```powershell
openscribe word import build\roundtrip.docx
```

Common causes are:

- current Markdown and Word both changed the same text
- tracked changes remain unresolved
- a chapter or scene content control is missing or duplicated
- headings or structure changed in Word
- the project changed after preview

Keep Markdown unchanged while investigating. Accept or reject tracked changes in Word, save a new filename, and preview again. Never force an import into the only manuscript copy.

## OneDrive created a conflict copy

Stop editing on every device. Preserve all versions. Compare them before choosing one.

Do not assume the newest timestamp contains every change. Synchronization conflicts are outside OpenScribe's transaction lock.

## Get more diagnostic information

Confirm the current location and versions:

```powershell
Get-Location
python --version
python -m openscribe --help
git status --short --branch
```

When reporting a problem, include:

- the exact command
- the complete error text
- Python version
- operating system
- whether the project is inside OneDrive or another sync folder
- whether another editor had the project open

Do not include API keys, private manuscript text, private paths, or `.openscribe\drafts` content in a public issue.
