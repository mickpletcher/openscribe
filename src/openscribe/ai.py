from __future__ import annotations

import importlib
import os
from dataclasses import dataclass


class AIConfigurationError(RuntimeError):
    pass


@dataclass(slots=True)
class AISettings:
    enabled: bool
    provider: str
    model: str


def load_ai_settings(config: dict) -> AISettings:
    ai_config = config.get("ai", {})
    return AISettings(
        enabled=bool(ai_config.get("enabled", False)),
        provider=str(ai_config.get("provider", "openai")),
        model=str(ai_config.get("model", "gpt-4.1")),
    )


def summarize_text(text: str, settings: AISettings, context_label: str) -> str:
    if not settings.enabled:
        raise AIConfigurationError(
            "AI is disabled in .openscribe/project.yaml. Set ai.enabled to true first."
        )

    provider = settings.provider.strip().lower()
    prompt = _summary_prompt(text, context_label)
    if provider == "openai":
        return _summarize_with_openai(prompt, settings.model)
    if provider == "azure-openai":
        return _summarize_with_azure_openai(prompt, settings.model)
    if provider == "openai-compatible-local":
        return _summarize_with_openai_compatible_local(prompt, settings.model)
    if provider == "anthropic":
        return _summarize_with_anthropic(prompt, settings.model)
    if provider == "gemini":
        return _summarize_with_gemini(prompt, settings.model)
    if provider == "mistral":
        return _summarize_with_mistral(prompt, settings.model)

    raise AIConfigurationError(
        f"Provider '{settings.provider}' is not implemented in the CLI yet."
    )


def _summary_prompt(text: str, context_label: str) -> str:
    return (
        "You are helping a writer review a manuscript section.\n\n"
        f"Summarize this {context_label} with:\n"
        "1. A short overview paragraph.\n"
        "2. Five concise bullet points.\n"
        "3. One revision risk to review next.\n\n"
        f"Text:\n{text}"
    )


def _summarize_with_openai(prompt: str, model: str) -> str:
    if not os.environ.get("OPENAI_API_KEY"):
        raise AIConfigurationError("OPENAI_API_KEY is not set.")

    OpenAI = getattr(_load_dependency("openai", "OpenAI Python SDK"), "OpenAI")
    client = OpenAI()
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    return response.output_text.strip()


def _summarize_with_azure_openai(prompt: str, model: str) -> str:
    base_url = os.environ.get("AZURE_OPENAI_BASE_URL")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    if not base_url:
        raise AIConfigurationError("AZURE_OPENAI_BASE_URL is not set.")
    if not api_key:
        raise AIConfigurationError("AZURE_OPENAI_API_KEY is not set.")

    OpenAI = getattr(_load_dependency("openai", "OpenAI Python SDK"), "OpenAI")
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    return response.output_text.strip()


def _summarize_with_openai_compatible_local(prompt: str, model: str) -> str:
    base_url = os.environ.get("OPENAI_COMPATIBLE_LOCAL_BASE_URL")
    if not base_url:
        raise AIConfigurationError("OPENAI_COMPATIBLE_LOCAL_BASE_URL is not set.")

    api_key = os.environ.get("OPENAI_COMPATIBLE_LOCAL_API_KEY", "local")
    OpenAI = getattr(_load_dependency("openai", "OpenAI Python SDK"), "OpenAI")
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    return response.output_text.strip()


def _summarize_with_anthropic(prompt: str, model: str) -> str:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise AIConfigurationError("ANTHROPIC_API_KEY is not set.")

    anthropic = _load_dependency("anthropic", "Anthropic Python SDK")
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_anthropic_text(message).strip()


def _summarize_with_gemini(prompt: str, model: str) -> str:
    if not os.environ.get("GEMINI_API_KEY"):
        raise AIConfigurationError("GEMINI_API_KEY is not set.")

    genai = _load_dependency("google.genai", "Google Gen AI Python SDK")
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        text = getattr(response, "text", "")
        if not text:
            raise AIConfigurationError("Gemini returned an empty response.")
        return str(text).strip()
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


def _summarize_with_mistral(prompt: str, model: str) -> str:
    if not os.environ.get("MISTRAL_API_KEY"):
        raise AIConfigurationError("MISTRAL_API_KEY is not set.")

    mistralai = _load_dependency("mistralai", "Mistral Python SDK")
    client = mistralai.Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    response = client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_mistral_text(response).strip()


def _load_dependency(module_name: str, package_label: str):
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise AIConfigurationError(
            f"{package_label} is not installed. Run `python -m pip install -e \".[ai]\"`."
        ) from exc


def _extract_anthropic_text(message) -> str:
    content = getattr(message, "content", [])
    parts: list[str] = []
    for item in content:
        text = getattr(item, "text", None)
        if text:
            parts.append(str(text))
    if parts:
        return "\n".join(parts)
    return str(content)


def _extract_mistral_text(response) -> str:
    choices = getattr(response, "choices", [])
    if not choices:
        raise AIConfigurationError("Mistral returned no choices.")

    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content

    parts: list[str] = []
    for item in content or []:
        text = getattr(item, "text", None)
        if text:
            parts.append(str(text))
    if parts:
        return "\n".join(parts)
    return str(content)
