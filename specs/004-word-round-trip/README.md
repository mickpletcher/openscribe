# Word Round Trip Design

This development plan defines a local first Word editing path while keeping Markdown as the canonical manuscript.

The design is separate from ordinary one-way DOCX compile. An experimental implementation now exists in `src/openscribe/word.py`, `word_bridge.py`, and `word_addin/`. Package and local bridge tests exist; real Word host validation remains open under VL-004 in `VALIDATION.md`. See ADR-006 for the staged availability decision. This does not claim production Word compatibility.

See:

1. [spec.md](spec.md)
2. [requirements.md](requirements.md)
3. [plan.md](plan.md)
4. [tasks.md](tasks.md)
