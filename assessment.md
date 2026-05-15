# openscribe assessment

## current state

`openscribe` has a real first slice.
The repo is not empty scaffolding anymore.
You can initialize a project, create parts, create chapters, view an outline, view status, and open a basic read only TUI.

The project also has a clean milestone structure under `specs/`.
That part is ahead of the code, but it is useful because the next phases are already broken into requirements, spec, plan, and task files.

## what is working now

The core manuscript path is functional.
I verified the CLI help entrypoint and a smoke flow for:

1. `openscribe init`
2. `openscribe new part`
3. `openscribe new chapter`
4. `openscribe outline`
5. `openscribe status`

The file based model is the right foundation for this kind of tool.
Plain Markdown plus YAML frontmatter is a good fit for git friendly long form writing.
The repo also keeps the app shape small enough to change without a rewrite.

## strengths

### clear product direction

The repo already has a coherent opinion.
Markdown files are the source of truth.
The app is a thin layer over readable project files.
That is the right differentiator.

### simple codebase

The current package is small.
`project.py` owns most of the file and metadata behavior.
`cli.py` is easy to follow.
That keeps the next milestone cheap to change.

### decent spec discipline

The numbered spec packages are useful.
They make the roadmap concrete instead of hand waving future ideas.

## current issues

### 1. the docs are broader than the shipped product

The README is strong on direction, but a lot of it is still future facing.
The project currently ships one AI command and two provider paths, yet the README spends a large amount of space on provider expansion and future patterns.
That pulls attention away from the actual writing workflow.

### 2. the part model is too thin

Parts only exist as numbered folder names.
There is no part metadata file and no separate display title.
That means the user sees storage ids like `part-01-opening` in the outline, status output, and TUI.

That is acceptable for a first pass.
It will become a real constraint once compile, board promotion, and element linking need stable human readable part identity.

### 3. one visible output bug already exists

The outline command tries to print chapter status as `Title [status]`, but Rich treats square brackets as markup.
In a real run the status text does not render as intended.

### 4. optional AI is not really optional at install time

The product story says AI is optional.
That is true at runtime for feature use.
It is not true in packaging.

`openai` is a required dependency in `pyproject.toml`, and `cli.py` imports the AI module at startup.
So the base install still carries AI client dependency even for users who only want the manuscript tool.

### 5. there is no test safety yet

I did not find an automated test suite or CI validation path in the repo.
That is normal for this stage, but it matters now because the next milestones touch parsing, ordered assembly, promotion, and compile behavior.
Those areas will regress easily without even a small smoke test layer.

## delivery assessment

The repo feels like a solid prototype, not a v1.

That is not a criticism.
It means the foundation is good enough to keep building on, but the next work should tighten the core before chasing more feature surface.

Right now the value is:

1. file based manuscript setup
2. basic structure management
3. a simple review interface
4. a real roadmap

Right now the gaps are:

1. no compile path
2. no editing inside the TUI
3. no tests
4. no stronger domain model for parts and future entities
5. no proof yet that the spec milestones can land without refactoring the current data model

## what to do next

### priority 1

Build the compile milestone before board mode or elements.

Reason:
compile is the first feature that proves the manuscript structure is worth using in real work.
It also forces the codebase to define ordered assembly, title handling, and project metadata more cleanly.

### priority 2

Add a real part model before the compile work goes too far.

Minimum version:

1. keep numbered folders on disk
2. add a part metadata file or frontmatter source for display title
3. separate storage slug from user facing title

### priority 3

Add a tiny test layer.

At minimum:

1. project init test
2. part creation numbering test
3. chapter creation and frontmatter parse test
4. outline or status smoke test
5. compile assembly ordering test once compile exists

### priority 4

Trim the README so shipped behavior is always obvious.

Keep the AI section shorter until more of it is real.
The strongest pitch today is the Markdown first writing workflow, not multi provider AI.

## bottom line

The project is pointed in the right direction.
The core idea is good.
The repo is already useful as a prototype.

The next success condition is not more breadth.
It is proving one full manuscript lifecycle path:

1. create structure
2. write in Markdown
3. inspect in CLI or TUI
4. compile to output

If that path gets solid, the rest of the roadmap has something real to build on.
