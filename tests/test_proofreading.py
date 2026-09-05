from __future__ import annotations

import json
from urllib.parse import parse_qs

import pytest

import openscribe.proofreading as proofreading
from openscribe.proofreading import (
    LanguageToolError,
    LanguageToolSettings,
    check_text,
    line_and_column,
    load_languagetool_settings,
    requires_data_transfer_consent,
)


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_load_languagetool_settings_uses_safe_defaults() -> None:
    settings = load_languagetool_settings({})

    assert settings.enabled is False
    assert settings.endpoint == "http://127.0.0.1:8081/v2/check"
    assert settings.language == "en-US"
    assert settings.timeout_seconds == 30
    assert requires_data_transfer_consent(settings) is False


def test_check_text_posts_to_local_server_and_parses_findings(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "software": {"version": "6.6"},
                "language": {"code": "en-US"},
                "warnings": {"incompleteResults": False},
                "matches": [
                    {
                        "message": "Possible spelling mistake found.",
                        "shortMessage": "Spelling mistake",
                        "offset": 5,
                        "length": 3,
                        "replacements": [{"value": "their"}, {"value": "there"}],
                        "context": {"text": "They is here."},
                        "rule": {
                            "id": "MORFOLOGIK_RULE_EN_US",
                            "issueType": "misspelling",
                            "category": {"name": "Possible Typo"},
                        },
                    }
                ],
            }
        )

    monkeypatch.setattr(proofreading, "urlopen", fake_urlopen)
    settings = LanguageToolSettings(True, "http://localhost:8081/v2/check", "en-US", 12)

    result = check_text("They is here.", settings)

    request = captured["request"]
    assert request.full_url == "http://localhost:8081/v2/check"
    assert request.get_method() == "POST"
    assert captured["timeout"] == 12
    assert parse_qs(request.data.decode("utf-8")) == {
        "language": ["en-US"],
        "text": ["They is here."],
    }
    assert result.language == "en-US"
    assert result.software_version == "6.6"
    assert result.incomplete_results is False
    assert len(result.issues) == 1
    assert result.issues[0].rule_id == "MORFOLOGIK_RULE_EN_US"
    assert result.issues[0].replacements == ("their", "there")


def test_hosted_endpoint_requires_explicit_data_transfer_approval() -> None:
    settings = LanguageToolSettings(True, "https://proofreading.example.test/v2/check", "en-US", 30)

    assert requires_data_transfer_consent(settings) is True
    with pytest.raises(LanguageToolError, match="complete chapter text"):
        check_text("Private manuscript text.", settings)


@pytest.mark.parametrize(
    ("endpoint", "message"),
    [
        ("http://proofreading.example.test/v2/check", "must use HTTPS"),
        ("https://api.languagetool.org/v2/check", "does not permit automated requests"),
        ("https://proofreading.example.test/v2/status", "must end with /v2/check"),
        ("https://user:secret@proofreading.example.test/v2/check", "cannot be embedded"),
    ],
)
def test_unsafe_or_unsupported_endpoints_are_rejected(endpoint: str, message: str) -> None:
    settings = LanguageToolSettings(True, endpoint, "en-US", 30)

    with pytest.raises(LanguageToolError, match=message):
        requires_data_transfer_consent(settings)


def test_line_and_column_handles_multiline_text_and_bounds() -> None:
    text = "First line\nSecond line"

    assert line_and_column(text, 0) == (1, 1)
    assert line_and_column(text, 14) == (2, 4)
    assert line_and_column(text, 999) == (2, 12)
