from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest

from openscribe.ai import (
    AIConfigurationError,
    AISettings,
    requires_data_transfer_consent,
    summarize_text,
)


class _FakeOpenAIClient:
    last_kwargs = None

    def __init__(self, *args, **kwargs) -> None:
        type(self).last_kwargs = kwargs
        self.responses = SimpleNamespace(create=lambda **call_kwargs: SimpleNamespace(output_text="openai summary"))


class _FakeAnthropicClient:
    def __init__(self, *args, **kwargs) -> None:
        self.messages = SimpleNamespace(
            create=lambda **call_kwargs: SimpleNamespace(content=[SimpleNamespace(text="anthropic summary")])
        )


class _FakeGeminiClient:
    def __init__(self, *args, **kwargs) -> None:
        self.models = SimpleNamespace(generate_content=lambda **call_kwargs: SimpleNamespace(text="gemini summary"))

    def close(self) -> None:
        return None


class _FakeMistralClient:
    def __init__(self, *args, **kwargs) -> None:
        self.chat = SimpleNamespace(
            complete=lambda **call_kwargs: SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="mistral summary"))]
            )
        )


@pytest.mark.parametrize(
    ("provider", "env_name", "module_name", "module_value", "expected"),
    [
        (
            "openai",
            "OPENAI_API_KEY",
            "openai",
            SimpleNamespace(OpenAI=_FakeOpenAIClient),
            "openai summary",
        ),
        (
            "azure-openai",
            "AZURE_OPENAI_API_KEY",
            "openai",
            SimpleNamespace(OpenAI=_FakeOpenAIClient),
            "openai summary",
        ),
        (
            "anthropic",
            "ANTHROPIC_API_KEY",
            "anthropic",
            SimpleNamespace(Anthropic=_FakeAnthropicClient),
            "anthropic summary",
        ),
        (
            "gemini",
            "GEMINI_API_KEY",
            "google.genai",
            SimpleNamespace(Client=_FakeGeminiClient),
            "gemini summary",
        ),
        (
            "mistral",
            "MISTRAL_API_KEY",
            "mistralai",
            SimpleNamespace(Mistral=_FakeMistralClient),
            "mistral summary",
        ),
        (
            "openai-compatible-local",
            "OPENAI_COMPATIBLE_LOCAL_BASE_URL",
            "openai",
            SimpleNamespace(OpenAI=_FakeOpenAIClient),
            "openai summary",
        ),
    ],
)
def test_summarize_text_routes_supported_providers(
    monkeypatch,
    provider: str,
    env_name: str,
    module_name: str,
    module_value,
    expected: str,
) -> None:
    monkeypatch.setenv(env_name, "test-key")
    if provider == "azure-openai":
        monkeypatch.setenv("AZURE_OPENAI_BASE_URL", "https://example.openai.azure.com/openai/v1/")
    if provider == "openai-compatible-local":
        monkeypatch.setenv("OPENAI_COMPATIBLE_LOCAL_BASE_URL", "http://localhost:1234/v1")
        monkeypatch.delenv("OPENAI_COMPATIBLE_LOCAL_API_KEY", raising=False)
        _FakeOpenAIClient.last_kwargs = None

    monkeypatch.setitem(sys.modules, module_name, module_value)
    if module_name == "google.genai":
        google_module = ModuleType("google")
        google_module.genai = module_value
        monkeypatch.setitem(sys.modules, "google", google_module)

    settings = AISettings(enabled=True, provider=provider, model="test-model")
    result = summarize_text(
        "Sample text",
        settings,
        "chapter",
        allow_data_transfer=provider != "openai-compatible-local",
    )

    assert result == expected
    if provider == "openai-compatible-local":
        assert _FakeOpenAIClient.last_kwargs == {
            "api_key": "local",
            "base_url": "http://localhost:1234/v1",
        }


def test_summarize_text_requires_sdk_when_missing(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delitem(sys.modules, "anthropic", raising=False)

    real_import_module = __import__("importlib").import_module

    def _fail_import(name: str, package=None):
        if name == "anthropic":
            raise ImportError("missing anthropic")
        return real_import_module(name, package)

    monkeypatch.setattr("importlib.import_module", _fail_import)

    settings = AISettings(enabled=True, provider="anthropic", model="test-model")
    with pytest.raises(AIConfigurationError, match="not installed"):
        summarize_text(
            "Sample text",
            settings,
            "chapter",
            allow_data_transfer=True,
        )


def test_hosted_provider_requires_explicit_data_transfer_consent() -> None:
    settings = AISettings(enabled=True, provider="openai", model="test-model")

    assert requires_data_transfer_consent(settings)
    with pytest.raises(AIConfigurationError, match="complete chapter text"):
        summarize_text("Private manuscript", settings, "chapter")


def test_local_provider_does_not_require_data_transfer_consent() -> None:
    settings = AISettings(
        enabled=True,
        provider="openai-compatible-local",
        model="test-model",
    )

    assert not requires_data_transfer_consent(settings)
