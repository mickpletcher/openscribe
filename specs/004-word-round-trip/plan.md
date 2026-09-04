# Plan

## Phase 1: Package and Baseline

1. Add project identity if the implementation needs a durable project ID.
2. Define and schema validate the manifest and local baseline formats.
3. Add a round trip DOCX exporter with chapter and scene content controls.
4. Verify every produced package before replacing its output target.

## Phase 2: Read Only Import Preview

1. Parse content controls and the custom XML manifest.
2. Load the matching local baseline.
3. Implement deterministic three way classification.
4. Render per-unit unified diffs.
5. Reject missing, malformed, or duplicate identities.

## Phase 3: Safe Apply

1. Refuse conflicts and unresolved tracked changes.
2. Create an automatic checkpoint.
3. Apply all chapter changes atomically.
4. Validate the project and rebuild the index.
5. Restore the checkpoint on any failure.

## Phase 4: Local Bridge and Task Pane

1. Implement a loopback only authenticated bridge.
2. Build the Word task pane on stable Word API requirement sets.
3. Show identity, tracked change, preview, and conflict state.
4. Keep preview and apply as separate user actions.

## Phase 5: Real Word Validation

1. Test on supported Windows desktop Word versions.
2. Test save, close, reopen, rename, and copy behavior.
3. Test content control deletion and duplication.
4. Test accepted, rejected, and unresolved tracked changes.
5. Record macOS and Word on the web as unverified until exercised.
