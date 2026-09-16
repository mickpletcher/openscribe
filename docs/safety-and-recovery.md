# Safety and recovery

OpenScribe is designed to keep Markdown and YAML files under the writer's control. It still requires independent backups.

## The main rule

Do not keep the only copy of important writing inside one OpenScribe project, one computer, or one synchronization folder.

Maintain at least one independent copy that a mistaken edit, restore, device failure, or synchronization conflict cannot immediately replace.

## What is canonical

The project folder is the source of truth.

- chapter prose is stored in Markdown files under `manuscript`
- chapter metadata is stored in YAML frontmatter
- project settings are stored in `.openscribe\project.yaml`
- planning and reference data is stored in ordinary Markdown or YAML files
- exported DOCX, PDF, and EPUB files are outputs

You can read the manuscript without OpenScribe.

## What not to remove

Chapter frontmatter contains an immutable `chapter_id`. Scene headings are followed by hidden comments such as `openscribe-scene-id`.

Do not manually change, copy, or delete those identities. OpenScribe uses them to preserve relationships across renames and reordering.

If identities are missing or malformed, run:

```powershell
openscribe migrate repair
```

The repair command creates a checkpoint first. It replaces malformed IDs and preserves board links to those replaced values. Duplicate identities and ambiguous legacy title or slug links require manual review because OpenScribe cannot safely guess which record is correct.

Titles and slugs are convenience references. They work only when one chapter or scene matches. If titles or slugs are duplicated, use the immutable IDs reported by the command.

## Unsaved drafts

The desktop application and TUI maintain recovery drafts under `.openscribe\drafts`.

- navigation does not silently discard dirty text
- drafts are refreshed about once per second
- reopening the same project and document loads a valid recovery draft
- Save writes the manuscript and removes the corresponding draft
- Discard removes the draft and returns to the last saved text

Drafts are local recovery data. They are not a replacement for saving or backup. An abrupt failure can still lose the most recent typing interval.

## Save conflict protection

Each editing session remembers the exact chapter bytes that were loaded. Before saving, OpenScribe compares that baseline with the current file.

If another editor or synchronization process changed the file, OpenScribe refuses the save. It does not automatically merge two versions.

When a conflict occurs:

1. preserve the visible draft in a separate temporary file
2. inspect the external file
3. decide how to combine the changes
4. reload the document in OpenScribe
5. reapply the wanted text
6. save again

Do not disable the conflict check.

## Checkpoints

Create a checkpoint before:

- moving, splitting, or merging scenes
- applying a migration or identity repair
- importing Word changes
- creating manuscript parts and chapters from a brainstorming outline
- applying a snapshot restore
- making a large manual rewrite

Create one with:

```powershell
openscribe snapshot save "before-major-edit"
openscribe snapshot list
```

Checkpoints are stored inside the project. Copying the whole project to another device or backup location protects against device loss.

Scene move, split, and merge previews remember the exact source bytes. If another tool changes the file after preview, even by changing only line endings, OpenScribe refuses apply. Preview again from the current file before continuing.

Brainstorming outline creation makes its own checkpoint. The preview is tied to the exact board file. If an idea, connection, or position changes after preview, OpenScribe refuses apply and requires a new preview.

## Restore preview and apply

Always preview first:

```powershell
openscribe snapshot restore "before-major-edit"
```

The preview lists files that will be added, modified, or deleted. Nothing changes without `--apply`.

Apply only after review:

```powershell
openscribe snapshot restore "before-major-edit" --apply
```

Apply creates an automatic backup, stages the replacement, updates managed paths, and records a recovery journal.

An exact restore can delete managed files created after the selected checkpoint. That deletion is intentional and appears in the preview.

## Interrupted restore recovery

Restore transactions live temporarily under `.openscribe\.restore-transaction-*`.

When a project opens, OpenScribe validates unfinished journals before loading project configuration. It rolls back an interrupted applying transaction and removes a completed or rolled-back transaction.

Do not edit or delete a transaction folder while recovery is in progress. If the journal is reported as invalid, preserve the entire project and transaction folder before troubleshooting.

Process-interruption recovery is tested. Physical power loss, storage-controller cache loss, OneDrive conflicts, and external programs that ignore project locks are not fully proven.

## Project locking

OpenScribe uses a project-scoped lock for mutations. Close other OpenScribe windows when a lock error appears.

External editors do not honor that lock. Save conflict detection is the second protection against overwriting their changes.

## Migrations

Ordinary reading does not add identities or rewrite formatting.

Check an older project with:

```powershell
openscribe migrate status
```

Apply the reported migration with:

```powershell
openscribe migrate apply
```

Migration creates a checkpoint and rolls back an ordinary process failure. Back up the project independently before migrating valuable work.

## Index recovery

The derived search index uses source hashes. When files change outside OpenScribe, index commands can require a rebuild:

```powershell
openscribe index rebuild
```

The index is derived data. The Markdown and YAML sources remain authoritative.

## Hosted AI and proofreading

Local writing features do not require AI or LanguageTool.

Before a hosted AI or licensed hosted LanguageTool request, OpenScribe displays the actual endpoint and the amount of text being sent. The CLI requires `--allow-data-transfer` for that invocation.

Review the disclosure every time. Do not send private manuscript text unless you understand and accept the provider's terms and data handling.

The first desktop launch can test OpenAI, Anthropic Claude, Google Gemini, Mistral, xAI Grok, DeepSeek, Azure OpenAI, OpenRouter, FreeLLMAPI, LM Studio, another local server, or another OpenAI-compatible endpoint with a short synthetic message. It does not send manuscript text. Pasted keys are stored separately by provider in the operating system credential store, not in project YAML. Provider-specific environment variables take priority. OpenScribe sends OpenAI and Azure OpenAI Responses requests with `store: false`, but hosted-provider abuse-monitoring and account-level retention policies can still apply.

Local AI is treated as local only when the configured endpoint resolves to loopback. A LAN, VPN, or internet endpoint still crosses the machine boundary. Non-loopback AI endpoints require HTTPS and explicit transfer approval even when the provider is labeled local.

FreeLLMAPI is the explicit exception to the normal loopback rule. Its OpenScribe preset connects to a local gateway, but that gateway routes requests to external providers. OpenScribe therefore requires hosted-transfer approval for every FreeLLMAPI manuscript request. Review the data handling and limits of both FreeLLMAPI and the provider that handles the selected model.

OpenRouter is always treated as a hosted provider. OpenScribe asks before every manuscript request and discloses that OpenRouter routes the content to the selected upstream model provider. Review the policies of both services.

LM Link and other proxies can accept a request on loopback and forward it to another computer. OpenScribe cannot inspect that routing and will not show its non-loopback confirmation. When using LM Link, treat the linked computer as a manuscript recipient even though the configured endpoint is `127.0.0.1`.

**Write with AI** sends the complete selected chapter or scene plus the writer's description. The generated page or chapter is previewed before use. Accepted text is placed in an unsaved recovery draft and does not change the manuscript file until the writer saves it. If the selected text changes while generation is running, OpenScribe refuses the returned result.

The desktop and TUI allow local LanguageTool endpoints only. Automated use of LanguageTool's free public endpoint is rejected.

## Experimental Word round trips

Normal DOCX export is one way. The experimental round-trip workflow is different.

It stores an export baseline under `.openscribe\word-roundtrip`, embeds chapter and scene identities in Word content controls, and compares Word, baseline, and current Markdown during import.

Preview before apply:

```powershell
openscribe word import build\roundtrip.docx
openscribe word import build\roundtrip.docx --apply
```

Do not apply when the preview is unclear. Import refuses known conflicts, tracked changes, missing controls, duplicate controls, unsupported structure, and stale previews.

Real desktop Word can rewrite package structures in ways synthetic tests do not reproduce. Certificate setup and Office task-pane sideloading also remain unverified. Use a copied synthetic project until those release gates are complete.

## OneDrive and other synchronization tools

Synchronization is useful, but it can create another writer that OpenScribe does not control.

- wait for synchronization to finish before opening the project on another device
- do not edit the same chapter on two devices at once
- treat conflict-copy files as evidence, not clutter to delete immediately
- keep a backup outside the synchronized project
- close external editors before applying a restore or migration

## Recovery decision table

| Situation | Safest first action |
|---|---|
| Unsaved text is visible | Copy it to a separate text file before troubleshooting |
| Save says the file changed | Preserve both versions and compare them |
| Project reports a lock | Close other OpenScribe instances and retry |
| Restore preview deletes unexpected files | Cancel and inspect the selected checkpoint |
| Restore journal is invalid | Preserve the project and journal; do not force deletion |
| Project needs migration | Make an independent backup, preview status, then apply |
| Word import is blocked | Keep Markdown unchanged and inspect the CLI preview |
| Index is stale | Rebuild the index from the source files |
| Computer failed during editing | Reopen the project and inspect the recovered draft before discarding |

See [Troubleshooting](troubleshooting.md) for command-specific fixes and [VALIDATION.md](../VALIDATION.md) for known assurance limits.
