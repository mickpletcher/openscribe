from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest

from openscribe.ai import (
    AIConfigurationError,
    AISettings,
    generate_draft,
    load_api_key,
    provider_definition,
    requires_data_transfer_consent,
    run_ai_task,
    save_api_key,
    summarize_text,
)
from openscribe.ai import (
    test_ai_connection as check_ai_connection,
)


class _FakeOpenAIClient:
    last_kwargs = None
    last_response_kwargs = None

    def __init__(self, *args, **kwargs) -> None:
        type(self).last_kwargs = kwargs

        def create(**call_kwargs):
            type(self).last_response_kwargs = call_kwargs
            return SimpleNamespace(output_text="openai summary")

        self.responses = SimpleNamespace(create=create)
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **call_kwargs: SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="compatible summary"))]
                )
            )
        )


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
            "mistralai.client",
            SimpleNamespace(Mistral=_FakeMistralClient),
            "mistral summary",
        ),
        (
            "lm-studio",
            "LM_STUDIO_BASE_URL",
            "openai",
            SimpleNamespace(OpenAI=_FakeOpenAIClient),
            "compatible summary",
        ),
        (
            "openai-compatible-local",
            "OPENAI_COMPATIBLE_LOCAL_BASE_URL",
            "openai",
            SimpleNamespace(OpenAI=_FakeOpenAIClient),
            "compatible summary",
        ),
        (
            "xai",
            "XAI_API_KEY",
            "openai",
            SimpleNamespace(OpenAI=_FakeOpenAIClient),
            "compatible summary",
        ),
        (
            "deepseek",
            "DEEPSEEK_API_KEY",
            "openai",
            SimpleNamespace(OpenAI=_FakeOpenAIClient),
            "compatible summary",
        ),
        (
            "openrouter",
            "OPENROUTER_API_KEY",
            "openai",
            SimpleNamespace(OpenAI=_FakeOpenAIClient),
            "compatible summary",
        ),
        (
            "huggingface",
            "HF_TOKEN",
            "openai",
            SimpleNamespace(OpenAI=_FakeOpenAIClient),
            "compatible summary",
        ),
        (
            "ollama",
            "OLLAMA_BASE_URL",
            "openai",
            SimpleNamespace(OpenAI=_FakeOpenAIClient),
            "compatible summary",
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
    endpoint_environment = {
        "xai": "XAI_BASE_URL",
        "deepseek": "DEEPSEEK_BASE_URL",
        "openrouter": "OPENROUTER_BASE_URL",
        "huggingface": "HF_INFERENCE_BASE_URL",
    }.get(provider)
    if endpoint_environment:
        monkeypatch.delenv(endpoint_environment, raising=False)
    if provider == "azure-openai":
        monkeypatch.setenv("AZURE_OPENAI_BASE_URL", "https://example.openai.azure.com/openai/v1/")
    if provider in {"lm-studio", "ollama", "openai-compatible-local"}:
        endpoint_env = {
            "lm-studio": "LM_STUDIO_BASE_URL",
            "ollama": "OLLAMA_BASE_URL",
            "openai-compatible-local": "OPENAI_COMPATIBLE_LOCAL_BASE_URL",
        }[provider]
        key_env = {
            "lm-studio": "LM_STUDIO_API_KEY",
            "ollama": "OLLAMA_API_KEY",
            "openai-compatible-local": "OPENAI_COMPATIBLE_LOCAL_API_KEY",
        }[provider]
        monkeypatch.setenv(endpoint_env, "http://localhost:1234/v1")
        monkeypatch.delenv(key_env, raising=False)
        _FakeOpenAIClient.last_kwargs = None

    monkeypatch.setitem(sys.modules, module_name, module_value)
    if module_name == "google.genai":
        google_module = ModuleType("google")
        google_module.genai = module_value
        monkeypatch.setitem(sys.modules, "google", google_module)

    endpoint = "http://localhost:1234/v1" if provider in {"lm-studio", "ollama", "openai-compatible-local"} else ""
    if provider == "xai":
        endpoint = "https://api.x.ai/v1/"
    if provider == "deepseek":
        endpoint = "https://api.deepseek.com/"
    if provider == "openrouter":
        endpoint = "https://openrouter.ai/api/v1/"
    if provider == "huggingface":
        endpoint = "https://router.huggingface.co/v1/"
    if provider == "azure-openai":
        endpoint = "https://example.openai.azure.com/openai/v1/"
    settings = AISettings(enabled=True, provider=provider, model="test-model", endpoint=endpoint)
    result = summarize_text(
        "Sample text",
        settings,
        "chapter",
        allow_data_transfer=provider not in {"lm-studio", "ollama", "openai-compatible-local"},
    )

    assert result == expected
    if provider == "openai":
        assert _FakeOpenAIClient.last_response_kwargs["store"] is False
    if provider in {
        "lm-studio",
        "ollama",
        "openai-compatible-local",
        "xai",
        "deepseek",
        "openrouter",
        "huggingface",
    }:
        assert result == "compatible summary"
    if provider in {"lm-studio", "ollama", "openai-compatible-local"}:
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


def test_local_provider_does_not_require_data_transfer_consent(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_COMPATIBLE_LOCAL_BASE_URL", "http://127.0.0.1:1234/v1")
    settings = AISettings(
        enabled=True,
        provider="openai-compatible-local",
        model="test-model",
    )

    assert not requires_data_transfer_consent(settings)


@pytest.mark.parametrize(
    ("task", "question", "expected_fragment"),
    [
        ("pacing", "", "Review pacing"),
        ("continuity", "", "Review continuity"),
        ("point-of-view", "", "Review point of view"),
        ("prose", "", "Review prose"),
        ("rewrite", "", "Propose a revised version"),
        ("outline", "", "Create a structural outline"),
        ("metadata", "", "Suggest a concise title"),
        ("brainstorm", "What could go wrong?", "Direction: What could go wrong?"),
        ("query", "Who found the ledger?", "Who found the ledger?"),
        ("draft-page", "Reveal the hidden map.", "approximately 250 to 350 words"),
        ("draft-chapter", "Resolve the station conflict.", "complete chapter draft"),
    ],
)
def test_run_ai_task_builds_scoped_read_only_prompts(monkeypatch, task, question, expected_fragment) -> None:
    captured: dict[str, str] = {}

    def fake_provider(prompt: str, settings: AISettings) -> str:
        captured["prompt"] = prompt
        return "review output"

    monkeypatch.setattr("openscribe.ai._summarize_with_openai", fake_provider)
    settings = AISettings(enabled=True, provider="openai", model="test-model")

    output = run_ai_task(
        "Private manuscript",
        settings,
        "chapter",
        task,
        question=question,
        allow_data_transfer=True,
    )

    assert output == "review output"
    assert expected_fragment in captured["prompt"]
    assert "Do not claim to edit or save files" in captured["prompt"]
    assert captured["prompt"].endswith("Private manuscript")


def test_project_query_requires_a_question(monkeypatch) -> None:
    monkeypatch.setattr("openscribe.ai._summarize_with_openai", lambda prompt, settings: "unused")
    settings = AISettings(enabled=True, provider="openai", model="test-model")

    with pytest.raises(AIConfigurationError, match="nonempty question"):
        run_ai_task("Private manuscript", settings, "project manuscript", "query", allow_data_transfer=True)


def test_generate_draft_requires_supported_scope_and_description(monkeypatch) -> None:
    monkeypatch.setattr("openscribe.ai._summarize_with_openai", lambda prompt, settings: prompt)
    settings = AISettings(enabled=True, provider="openai", model="test-model")

    result = generate_draft(
        "Existing chapter",
        settings,
        "chapter",
        "page",
        "Continue with the storm arriving.",
        allow_data_transfer=True,
    )

    assert "Writing direction: Continue with the storm arriving." in result
    assert result.endswith("Existing chapter")
    with pytest.raises(AIConfigurationError, match="Describe"):
        generate_draft("", settings, "chapter", "page", "", allow_data_transfer=True)
    with pytest.raises(AIConfigurationError, match="scope"):
        generate_draft("", settings, "chapter", "book", "description", allow_data_transfer=True)


def test_provider_key_uses_environment_before_credential_store(monkeypatch) -> None:
    credential = "environment" + "-value"
    monkeypatch.setenv("OPENAI_API_KEY", credential)
    monkeypatch.setattr("openscribe.ai._load_dependency", lambda *args: pytest.fail("keyring should not load"))
    assert load_api_key("openai") == credential


def test_provider_key_round_trip_uses_separate_credential_store_accounts(monkeypatch) -> None:
    credential = "synthetic" + "-value"
    stored = {}
    keyring = SimpleNamespace(
        get_password=lambda service, account: stored.get((service, account)),
        set_password=lambda service, account, value: stored.__setitem__((service, account), value),
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("openscribe.ai._load_dependency", lambda *args: keyring)
    save_api_key("anthropic", credential)
    assert load_api_key("anthropic") == credential
    assert ("OpenScribe", "anthropic-api-key") in stored


def test_openai_connection_checks_model_without_manuscript(monkeypatch) -> None:
    credential = "synthetic" + "-value"
    checked = {}

    class FakeClient:
        def __init__(self, **kwargs):
            checked["client"] = kwargs
            self.responses = SimpleNamespace(create=lambda **call_kwargs: checked.update(request=call_kwargs))

    monkeypatch.setattr("openscribe.ai._load_dependency", lambda *args: SimpleNamespace(OpenAI=FakeClient))
    check_ai_connection(AISettings(True, "openai", "gpt-test"), credential)
    assert checked == {
        "client": {"api_key": credential, "timeout": 15.0, "max_retries": 0},
        "request": {
            "model": "gpt-test",
            "input": "This is an OpenScribe connection test. Reply with OK.",
            "max_output_tokens": 16,
            "store": False,
        },
    }


def test_local_connection_uses_configured_endpoint_without_requiring_a_key(monkeypatch) -> None:
    checked = {}

    class FakeClient:
        def __init__(self, **kwargs):
            checked["client"] = kwargs
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=lambda **call_kwargs: checked.update(request=call_kwargs))
            )

    monkeypatch.delenv("OPENAI_COMPATIBLE_LOCAL_API_KEY", raising=False)
    monkeypatch.setattr("openscribe.ai._load_dependency", lambda *args: SimpleNamespace(OpenAI=FakeClient))
    settings = AISettings(True, "openai-compatible-local", "local-model", "http://127.0.0.1:11434/v1/")
    check_ai_connection(settings)
    assert checked["client"] == {
        "api_key": "local",
        "base_url": "http://127.0.0.1:11434/v1/",
        "timeout": 15.0,
        "max_retries": 0,
    }
    assert checked["request"]["messages"][0]["content"].startswith("This is an OpenScribe connection test")


@pytest.mark.parametrize(
    ("provider", "module"),
    [
        ("anthropic", SimpleNamespace(Anthropic=_FakeAnthropicClient)),
        ("gemini", SimpleNamespace(Client=_FakeGeminiClient)),
        ("mistral", SimpleNamespace(Mistral=_FakeMistralClient)),
    ],
)
def test_hosted_connection_routes_supported_provider(monkeypatch, provider, module) -> None:
    monkeypatch.setattr("openscribe.ai._load_dependency", lambda *args: module)
    check_ai_connection(AISettings(True, provider, "test-model"), "synthetic-value")


def test_remote_compatible_endpoint_requires_transfer_consent() -> None:
    settings = AISettings(True, "openai-compatible", "remote-model", "https://models.example.test/v1/")
    assert requires_data_transfer_consent(settings)


def test_freellmapi_preset_routes_through_local_gateway_but_requires_transfer_consent(monkeypatch) -> None:
    checked = {}
    credential = "synthetic" + "-value"

    class FakeClient:
        def __init__(self, **kwargs):
            checked["client"] = kwargs
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=lambda **call_kwargs: checked.update(request=call_kwargs))
            )

    monkeypatch.setattr("openscribe.ai._load_dependency", lambda *args: SimpleNamespace(OpenAI=FakeClient))
    settings = AISettings(True, "freellmapi", "auto")

    assert provider_definition("freellmapi").account_url == "https://github.com/tashfeenahmed/freellmapi"
    assert requires_data_transfer_consent(settings)
    check_ai_connection(settings, credential)
    assert checked["client"] == {
        "api_key": credential,
        "base_url": "http://127.0.0.1:3001/v1/",
        "timeout": 15.0,
        "max_retries": 0,
    }
    assert checked["request"]["model"] == "auto"


def test_openrouter_preset_uses_openai_compatible_api_and_requires_transfer_consent(monkeypatch) -> None:
    checked = {}
    credential = "synthetic" + "-value"

    class FakeClient:
        def __init__(self, **kwargs):
            checked["client"] = kwargs
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=lambda **call_kwargs: checked.update(request=call_kwargs))
            )

    monkeypatch.setattr("openscribe.ai._load_dependency", lambda *args: SimpleNamespace(OpenAI=FakeClient))
    settings = AISettings(True, "openrouter", "openrouter/auto")

    definition = provider_definition("openrouter")
    assert definition.account_url == "https://openrouter.ai/settings/keys"
    assert requires_data_transfer_consent(settings)
    check_ai_connection(settings, credential)
    assert checked["client"] == {
        "api_key": credential,
        "base_url": "https://openrouter.ai/api/v1/",
        "timeout": 15.0,
        "max_retries": 0,
    }
    assert checked["request"]["model"] == "openrouter/auto"


@pytest.mark.parametrize(
    ("provider", "model", "account_url", "base_url", "requires_consent", "credential"),
    [
        (
            "huggingface",
            "openai/gpt-oss-120b:fastest",
            "https://huggingface.co/settings/tokens",
            "https://router.huggingface.co/v1/",
            True,
            "synthetic-value",
        ),
        (
            "ollama",
            "llama3.2",
            "https://docs.ollama.com/api/openai-compatibility",
            "http://127.0.0.1:11434/v1/",
            False,
            None,
        ),
        (
            "xai",
            "grok-4.6",
            "https://console.x.ai/",
            "https://api.x.ai/v1/",
            True,
            "synthetic-value",
        ),
    ],
)
def test_named_provider_presets_use_openai_compatible_api(
    monkeypatch,
    provider,
    model,
    account_url,
    base_url,
    requires_consent,
    credential,
) -> None:
    checked = {}

    class FakeClient:
        def __init__(self, **kwargs):
            checked["client"] = kwargs
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=lambda **call_kwargs: checked.update(request=call_kwargs))
            )

    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    monkeypatch.setattr("openscribe.ai._load_dependency", lambda *args: SimpleNamespace(OpenAI=FakeClient))
    definition = provider_definition(provider)
    monkeypatch.delenv(definition.endpoint_environment, raising=False)
    settings = AISettings(True, provider, model)

    assert definition.account_url == account_url
    assert requires_data_transfer_consent(settings) is requires_consent
    check_ai_connection(settings, credential)
    assert checked["client"] == {
        "api_key": credential or "local",
        "base_url": base_url,
        "timeout": 15.0,
        "max_retries": 0,
    }
    assert checked["request"]["model"] == model


def test_connection_rejects_nonlocal_plain_http_before_loading_provider_client(monkeypatch) -> None:
    monkeypatch.setattr("openscribe.ai._load_dependency", lambda *args: pytest.fail("client must not load"))
    settings = AISettings(True, "openai-compatible", "remote-model", "http://192.0.2.1/v1/")
    with pytest.raises(AIConfigurationError, match="must use HTTPS"):
        check_ai_connection(settings, "synthetic-value")
