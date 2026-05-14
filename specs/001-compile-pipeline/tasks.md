# Tasks

## Project Model Tasks

- [ ] Extend `.openscribe/project.yaml` defaults for compile settings
- [ ] Decide output folder naming and filename slug rules
- [ ] Define the first template folder layout under `.openscribe/templates/`

## CLI Tasks

- [ ] Add `openscribe compile`
- [ ] Add `--format` option for `docx`, `pdf`, and `epub`
- [ ] Add `--template` option
- [ ] Add `--output` option
- [ ] Add clear errors for missing Pandoc
- [ ] Add clear errors for empty manuscripts

## Manuscript Assembly Tasks

- [ ] Collect part folders in numeric order
- [ ] Collect chapter files in numeric order within each part
- [ ] Parse frontmatter and body content for each chapter
- [ ] Build the temporary compile input document
- [ ] Decide how part titles and chapter titles appear in output

## Template Tasks

- [ ] Add one default template that works out of the box
- [ ] Define how title page content is included
- [ ] Define how author metadata is included
- [ ] Validate format specific behavior for `docx`, `pdf`, and `epub`

## Validation Tasks

- [ ] Compile a sample project to `docx`
- [ ] Compile a sample project to `epub`
- [ ] Compile a sample project to `pdf` on a machine with a working PDF engine
- [ ] Confirm output order matches binder order
- [ ] Confirm missing dependency errors are readable
- [ ] Update README with compile instructions after implementation
