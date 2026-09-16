# Troubleshooting OpenScribe

Start with the section that matches the message or behavior you see.

Do not delete project files, drafts, snapshots, or recovery journals just to clear an error.

## Windows blocks the installer

OpenScribe release packages are not digitally signed yet. Windows can therefore show **Windows protected your PC** or list the publisher as **Unknown publisher**.

Before continuing:

1. download the setup file only from the [OpenScribe releases page](https://github.com/mickpletcher/openscribe/releases)
2. download `SHA256SUMS.txt` from the same release
3. compare the installer hash as described in [Getting started](../getting-started.md#step-2-check-the-download)

If the hash matches, select **More info**, then **Run anyway**. Stop if the hash does not match.

## The installer checksum does not match

Delete the downloaded installer and `SHA256SUMS.txt`. Download both again from the same release.

Do not run the setup file if the second comparison also fails. Report the release version and both calculated hashes without attaching the installer.

## The installed desktop application does not open

Try **OpenScribe** from the Start menu again. If it still does not open, read the startup log in PowerShell:

```powershell
Get-Content -LiteralPath "$env:LOCALAPPDATA\OpenScribe\openscribe-error.log"
```

If the file does not exist, reinstall the same release. Your writing projects are stored outside the application folder and are not removed by normal reinstall or uninstall operations.

When reporting the problem, include the release version and error log, but remove private paths or manuscript text first.

## The portable application does not open

Extract the entire portable ZIP to a normal folder before running `OpenScribe.exe`. The `_internal` folder must remain beside the executable.

Do not run the executable from inside the ZIP and do not copy `OpenScribe.exe` by itself.

## Git or Python is not recognized during source installation

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

For an installer installation, open **OpenScribe command line** from the Start menu. That shortcut defines the `openscribe` command for its PowerShell window.

The remaining steps in this section apply to a source installation.

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

## The source desktop application does not open

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

## First launch AI connection fails

The first launch connection test sends a short synthetic test message, not manuscript text. It verifies the API key, endpoint, billing, and selected model.

Check all of the following:

1. the selected provider matches the API key
2. API billing or credits are available when required
3. the selected model ID or Azure deployment name is available to that account
4. the endpoint is correct for Azure, local, or custom compatible providers
5. the local server is running and the selected model is installed
6. Windows can reach the configured endpoint
7. the operating system credential store is available

The error deliberately does not repeat the API key. Use **AI setup** on the desktop toolbar to retry. You can instead set the provider-specific environment variable before starting OpenScribe; it takes priority over a saved key.

For a Meta Llama model, start Ollama, make sure the model is installed, choose **Meta Llama (Ollama)**, and use `http://127.0.0.1:11434/v1/`. LM Studio commonly uses `http://127.0.0.1:1234/v1/`. No key is normally required for a loopback server.

For Hugging Face, confirm the token has permission to call Inference Providers, the model supports chat completion through an active provider, and the endpoint is `https://router.huggingface.co/v1/`. Model access, provider capacity, credits, and routing policies can all cause a connection test to fail.

## Write with AI is unavailable or fails

Check these items in order:

1. Open a project and select a chapter or scene.
2. Select **AI setup** and confirm that a provider connects successfully.
3. For a complete chapter, select the chapter itself rather than one of its scenes.
4. Enter a specific writing description. A blank description is rejected.
5. Confirm the selected model supports text generation and has enough context capacity for the selected manuscript text.

If OpenScribe says the draft changed while generation was running, nothing was applied. Review your current text and run **Write with AI** again. This protection prevents an older response from replacing newer work.

If the result opens in the preview but does not appear in the manuscript file, select **Apply**, review the editor, and press `Ctrl+S`. Applying AI text changes only the unsaved recovery draft. It does not automatically save the manuscript.

## LM Studio on another computer does not connect

The easiest remote setup is LM Link. Follow the [LM Link instructions](https://lmstudio.ai/docs/developer/core/lmlink), load the model on the remote computer, start the LM Studio server on the OpenScribe computer, and keep OpenScribe's endpoint set to:

```text
http://127.0.0.1:1234/v1/
```

LM Link forwards the request to the linked computer. OpenScribe cannot detect that forwarding and will not display its non-loopback confirmation. Do not link a computer you do not trust with your manuscript.

For a direct network connection, first test whether Windows can reach the remote computer. Replace the example address with the LM Studio computer's actual address:

```powershell
Test-NetConnection -ComputerName 192.168.1.50 -Port 1234
```

`TcpTestSucceeded` must be `True`. If it is `False`, confirm that LM Studio is running, **Serve on Local Network** is enabled, both computers are on the expected network, and the server firewall allows the port.

LM Studio's normal address, such as `http://192.168.1.50:1234/v1/`, is not accepted by OpenScribe. Nonlocal endpoints must use HTTPS. Put LM Studio behind a trusted HTTPS reverse proxy or internal gateway, enable LM Studio authentication, and enter the HTTPS address and API token in **AI setup**.

To check an HTTPS endpoint without sending manuscript text:

```powershell
$headers = @{ Authorization = "Bearer YOUR_TEST_TOKEN" }
Invoke-RestMethod -Uri "https://lmstudio.example.test/v1/models" -Headers $headers
```

Use a temporary or limited test token in command history. Never put an API token in the endpoint URL. Do not expose LM Studio through router port forwarding or directly to the public internet.

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
