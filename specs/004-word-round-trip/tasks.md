# Tasks

## Format Tasks

- [ ] Define manifest schema
- [ ] Define local baseline schema
- [ ] Add project identity if required
- [ ] Add content controls to round trip exports
- [ ] Add and verify the custom XML manifest
- [ ] Keep ordinary DOCX compile unchanged

## Import Tasks

- [ ] Parse and validate round trip DOCX packages
- [ ] Implement three way unit comparison
- [ ] Render a no-write preview and unified diffs
- [ ] Detect missing and duplicate identities
- [ ] Detect unresolved tracked changes
- [ ] Add checkpoint, atomic apply, validation, and rollback

## Bridge and Add-in Tasks

- [ ] Implement loopback-only binding
- [ ] Implement per-session authentication
- [ ] Restrict origins and project roots
- [ ] Add request limits and manuscript-safe logging
- [ ] Build the Word task pane
- [ ] Show preview, conflicts, warnings, and tracked change state

## Validation Tasks

- [ ] Add OOXML fixture and package tests
- [ ] Add all three way comparison cases
- [ ] Add malformed identity tests
- [ ] Add rollback failure injection tests
- [ ] Add bridge security tests
- [ ] Complete a real Windows desktop Word round trip
- [ ] Document supported Word versions and remaining platform gaps
