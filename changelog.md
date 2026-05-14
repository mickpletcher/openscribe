# changelog

## 2026-05-14

### Initial scaffold

* created the Python package structure for `openscribe`
* added `pyproject.toml` with CLI entrypoint and core dependencies
* added the `openscribe` CLI with `init`, `new part`, `new chapter`, `outline`, `status`, and `tui`
* added project initialization and manuscript file management
* added a lightweight Textual TUI for binder style manuscript browsing

### Documentation

* rewrote `README.md` into a detailed usage guide
* documented installation, project setup, command usage, frontmatter fields, workflow, and current limitations
* added a root link to this changelog from `README.md`

### Repo planning

* added a root `future-upgrades.md` planning file for local roadmap tracking
* updated `.gitignore` so `future-upgrades.md` stays local only

### Specification

* added `specs/001-compile-pipeline/` for the first GitHub Spec package
* defined requirements, scope, plan, and tasks for the first compile milestone
* linked the spec package from `README.md`

### Feature planning refresh

* updated `future-upgrades.md` to reflect the current MVP feature order based on Scrivener style gaps
* updated the compile spec so it stays focused on compile while preserving room for a later Scrivenings style feature
* added a second spec package for a lightweight planning board mode inspired by Scapple style freeform note mapping
* updated board planning to absorb the useful LivingWriter board ideas without taking on cloud, AI, or collaboration scope
* added a third spec package for elements, aliases, relations, and appears in tracking
