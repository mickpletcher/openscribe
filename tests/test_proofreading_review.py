import pytest

from openscribe.proofreading import LanguageToolError, ProofreadingIssue, _normalize_issue, preview_replacement


def test_unicode_offsets_and_stale_suggestion():
    text = "\U0001f600 This are wrong."
    issue = ProofreadingIssue("Use is", "", 8, 3, ("is",), "GRAMMAR", "Grammar", "grammar", text)
    normalized = _normalize_issue(text, issue)
    assert text[normalized.offset:normalized.offset + normalized.length] == "are"
    preview = preview_replacement(text, normalized, "is")
    assert preview.apply(text) == "\U0001f600 This is wrong."
    assert "This is wrong" in preview.diff
    with pytest.raises(LanguageToolError, match="Text changed"):
        preview.apply(text + "Later edit")
    with pytest.raises(LanguageToolError, match="Choose one"):
        preview_replacement(text, normalized, "unlisted")
