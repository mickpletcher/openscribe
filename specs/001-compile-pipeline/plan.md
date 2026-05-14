# Plan

## Phase 1

Define the compile model and project defaults.

1. extend `.openscribe/project.yaml` with compile settings that match the spec
2. decide the default output folder and filename rules
3. define the first template layout under `.openscribe/templates/`

## Phase 2

Build manuscript collection and compile preparation.

1. enumerate parts and chapters in binder order
2. parse chapter metadata and body content
3. generate a temporary compile document for Pandoc input
4. validate empty manuscript and malformed project cases
5. keep manuscript assembly logic reusable for a later Scrivenings command

## Phase 3

Build the CLI compile command.

1. add `openscribe compile`
2. add format, template, and output options
3. add dependency checks for Pandoc
4. add clear error handling and result messages

## Phase 4

Add templates and output validation.

1. create the first default compile template
2. validate `docx` output
3. validate `epub` output
4. validate `pdf` output where the local toolchain supports it

## Phase 5

Document and test the feature.

1. add tests for ordering, config loading, and compile command behavior
2. update README with compile setup and usage
3. add example output paths and expected results
