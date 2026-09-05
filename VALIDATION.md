# Validation

This file defines how to prove changes to `openscribe`. It is a procedure, not a history of prior runs.

## Validation Levels

### Basic

Use for Class 2 internal changes and as the minimum for Class 3 work:

1. Ruff against source and tests.
2. The full pytest suite in the active supported Python environment.
3. CLI help smoke test.

### Integration

Use for CLI, TUI, persistence, import, export, snapshot, or provider-adapter changes:

1. Basic validation.
2. The pytest suite on Python 3.11, 3.12, and 3.13.
3. The relevant mounted TUI tests for TUI changes.
4. A derived-index check against the sample project for index or persistence changes.

### Full

Use for dependency, packaging, architecture, security, release, or broad data-model changes:

1. Integration validation.
2. Coverage with the enforced 80 percent floor.
3. Source distribution and wheel build.
4. Installed-wheel CLI smoke test.
5. Dependency vulnerability audit.
6. Medium-and-higher Python security scan.
7. Living-document compliance check.
8. Repository secret scan and Word task-pane contract tests.
9. Mounted desktop interaction tests for desktop changes; real Word validation before claiming Word interoperability.

## Environment Requirements

- Windows 11 or a compatible platform for the Python suite.
- PowerShell 7 for `scripts/docs-check.ps1`.
- Python 3.11, 3.12, and 3.13 for the supported-version matrix.
- `uv` for isolated multi-version and wheel checks.
- Project development dependencies from `.[dev]`.
- Node.js 22 or later for task-pane contract tests.
- Set `UV_LINK_MODE=copy` if the Windows filesystem cannot create uv cache hardlinks.
- Set `QT_QPA_PLATFORM=offscreen` for headless Qt tests. Native desktop review is a separate gate.

## Setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Commands

### Ruff

```powershell
python -m ruff check src tests
```

Expected exit code: `0`.
Expected output: `All checks passed!` or no findings.
Typical runtime: under 10 seconds.

### Tests and coverage

```powershell
python -m pytest --cov=openscribe --cov-report=term-missing --cov-fail-under=80
```

Expected exit code: `0`.
Expected output: all collected tests pass, skipped tests are explained, and total coverage is at least 80 percent.
Typical runtime: under 90 seconds on the supported Windows development environment.

### Supported Python matrix

```powershell
uv run --isolated --python 3.11 --extra dev python -m pytest -q
uv run --isolated --python 3.12 --extra dev python -m pytest -q
uv run --isolated --python 3.13 --extra dev python -m pytest -q
```

Expected exit code: `0` for each command.
Expected output: identical collection count and no failures on every supported version.
Typical runtime: under 90 seconds per version after dependency caching.

### Source and wheel build

```powershell
uv run --isolated --python 3.13 --with build python -m build
```

Expected exit code: `0`.
Expected output: one source archive and one wheel under `dist/`.
Typical runtime: under two minutes after dependency caching.

### Installed-wheel CLI smoke test

```powershell
$wheel = Get-ChildItem -LiteralPath dist -Filter *.whl | Select-Object -First 1
uv run --isolated --python 3.13 --no-project --with $wheel.FullName openscribe --help
```

Expected exit code: `0`.
Expected output: top-level `openscribe` usage and command list.
Typical runtime: under one minute after dependency caching.

### Sample index integrity

```powershell
python -c "from pathlib import Path; from openscribe.index import index_is_current; assert index_is_current(Path('examples/north-county'))"
```

Expected exit code: `0`.
Expected output: none.
Typical runtime: under 10 seconds.

### CLI source smoke test

```powershell
python -m openscribe --help
```

Expected exit code: `0`.
Expected output: top-level usage and command list.
Typical runtime: under 10 seconds.

### Local LanguageTool contract smoke test

Run this only when a local LanguageTool server is available. The request uses synthetic text, not manuscript content.

```powershell
$response = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8081/v2/check" -Body @{
    text = "This are a synthetic test."
    language = "en-US"
}
if ($response.PSObject.Properties.Name -notcontains "matches") {
    throw "LanguageTool response did not contain a matches field."
}
```

Expected exit code: `0`.
Expected output: a response object with a `matches` field.
Typical runtime: under 10 seconds after the server starts.

### Living-document compliance

```powershell
pwsh -File scripts/docs-check.ps1 -FailOnGap -Markdown
```

Expected exit code: `0`.
Expected output: one row for every mapped responsibility and no `MISSING`, `INVALID`, or `REVIEW` status.
Typical runtime: under 10 seconds.

### Dependency audit

```powershell
uv run --isolated --python 3.13 --extra dev --extra ai --with pip-audit pip-audit
```

Expected exit code: `0`.
Expected output: no known vulnerabilities in third-party dependencies. The unpublished local package may be reported as skipped.
Typical runtime: under two minutes after dependency caching.

### Python security scan

```powershell
uvx bandit -r src -q -ll
```

Expected exit code: `0`.
Expected output: no medium-or-higher findings.
Typical runtime: under one minute.

### Desktop and Word checks

```powershell
python -m pytest tests/test_desktop.py tests/test_safety.py tests/test_recovery_process.py tests/test_word.py tests/test_word_bridge.py -q
node --test tests/word_addin.test.cjs
python -m openscribe desktop --help
python -m openscribe word --help
uv run --isolated --python 3.13 --with detect-secrets python scripts/check-secrets.py
```

Expected exit code: `0` for each command. The secret scan compares exact path, detector, and value hash against reviewed false positives in `.secrets.baseline`. It does not verify credentials over the network. New findings fail the check; no file or detector is excluded wholesale.

Use synthetic manuscripts for real Word validation. Export, open in Word, edit, save, close, reopen, preview, and apply. Verify byte-preserved unrelated Markdown, identity retention, conflict refusal, tracked-change refusal, rollback, and index freshness. Sideload the task-pane manifest using an approved Office process and a locally trusted certificate; test wrong origin/token, stale preview, document changes between preview and apply, and slice cleanup. Do not use an only copy of real writing.

## Known Validation Limitations

### VL-004: Native desktop and real Word interoperability are unverified

Requirement: native authoring, accessibility, real Word save/reopen, and task-pane sideload validation.

Reason: automated Qt tests are headless. The live Word inspection could launch and read the start page, but keyboard input timed out and window activation failed during recovery. Computer-use safety rules stopped further native interaction. No document round trip or live task-pane session was completed.

Risk: Word can rewrite package structures and the native host can expose rendering, focus, or certificate defects that synthetic fixtures do not cover. Word features remain experimental.

Follow-up: complete the synthetic native validation procedure above on supported desktop Word before claiming interoperability or release readiness.

### VL-005: Physical power-loss durability is not proven

Requirement: recovery after abrupt physical power loss across supported filesystems.

Reason: child-process termination tests exercise both replacement boundaries, not storage-controller caches, power loss, OneDrive synchronization, or external editors that ignore the project lock.

Risk: filesystem behavior or an uncooperative external writer can exceed the recovery guarantees demonstrated by process tests.

Follow-up: perform disposable VM power-cut and filesystem recovery drills before making a power-loss atomicity claim. Keep independent manuscript backups.

### VL-006: Independent Class 4 review and new hosted CI runs remain release gates

Requirement: independent review of identity, transaction, and local-bridge trust boundaries; hosted validation of the changed CI matrix.

Reason: no independent reviewer is available in this task. The workflow is configured locally; these changes have not been published or run on hosted Windows, Linux, or macOS runners.

Risk: local tests and the implementing agent's own review can miss platform and architecture defects.

Follow-up: obtain a separate reviewer and run the changed workflow on all configured runners before release. This waiver does not imply approval to publish changes.

### VL-001: Hosted AI providers use mocked contracts

Live provider calls require external accounts, credentials, network access, and approval to send test text. Automated tests use fakes and do not prove current remote API compatibility.

Risk: a provider SDK or API change can break an adapter while local tests remain green.

Follow-up: run credential-isolated contract tests with synthetic text before releasing an AI-enabled build.

### VL-002: TUI validation is headless

Textual tests mount the application and send keyboard input, but do not prove visual rendering, accessibility, or behavior in every terminal host.

Risk: visual or terminal-specific defects can remain undetected.

Follow-up: perform a manual TUI smoke and accessibility review before a public release or major TUI expansion.

### VL-003: Licensed hosted LanguageTool compatibility is unverified

Automated tests mock the LanguageTool `/v2/check` response. A local synthetic smoke proves compatibility with a running self-hosted server when the procedure above is executed. No licensed hosted endpoint is available to the repository suite.

Risk: authentication or service-specific behavior at a licensed hosted endpoint can differ from the self-hosted server.

Follow-up: test a licensed hosted endpoint only with explicit approval, isolated credentials, and nonprivate synthetic text before claiming hosted compatibility.

## Validation Matrix

| Change type | Class | Unit | Integration | Security | Smoke |
|---|---:|---|---|---|---|
| Documentation only | 1 | No | No | No | Documentation check |
| Internal refactor | 2 | Yes | As needed | No | CLI |
| Test-only change | 2 | Changed tests | As needed | No | As needed |
| Bug fix | 3 | Yes | Affected workflows | As needed | CLI and affected surface |
| Feature or interface change | 3 | Yes | Yes | As needed | CLI and affected surface |
| Dependency change | 3 | Yes | Yes | Required | Package and CLI |
| Configuration change | 3 | Yes | Yes | As needed | CLI and affected surface |
| Architecture or security change | 4 | Yes | Yes | Required | Full |
