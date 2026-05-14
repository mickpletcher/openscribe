from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI


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
    if provider == "openai":
        return _summarize_with_openai(text, settings.model, context_label)
    if provider == "azure-openai":
        return _summarize_with_azure_openai(text, settings.model, context_label)

    raise AIConfigurationError(
        f"Provider '{settings.provider}' is not implemented in the CLI yet."
    )


def _summarize_with_openai(text: str, model: str, context_label: str) -> str:
    if not os.environ.get("OPENAI_API_KEY"):
        raise AIConfigurationError("OPENAI_API_KEY is not set.")

    client = OpenAI()
    response = client.responses.create(
        model=model,
        input=(
            "You are helping a writer review a manuscript section.\n\n"
            f"Summarize this {context_label} with:\n"
            "1. A short overview paragraph.\n"
            "2. Five concise bullet points.\n"
            "3. One revision risk to review next.\n\n"
            f"Text:\n{text}"
        ),
    )
    return response.output_text.strip()


def _summarize_with_azure_openai(text: str, model: str, context_label: str) -> str:
    base_url = os.environ.get("AZURE_OPENAI_BASE_URL")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    if not base_url:
        raise AIConfigurationError("AZURE_OPENAI_BASE_URL is not set.")
    if not api_key:
        raise AIConfigurationError("AZURE_OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.responses.create(
        model=model,
        input=(
            "You are helping a writer review a manuscript section.\n\n"
            f"Summarize this {context_label} with:\n"
            "1. A short overview paragraph.\n"
            "2. Five concise bullet points.\n"
            "3. One revision risk to review next.\n\n"
            f"Text:\n{text}"
        ),
    )
    return response.output_text.strip()
