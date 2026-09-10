# ADR-009: First launch AI connection

**Status:** Accepted
**Date:** 2026-09-10
**Driving requirement:** Prompt desktop users to connect a hosted or local AI model on first launch
**Supersedes:** None
**Superseded by:** None

## Decision

The desktop application displays optional provider-neutral AI setup on first launch. The writer can connect or select **Not now**. The choice is recorded in per-user application settings so the automatic prompt appears only once. **AI setup** remains available on the toolbar.

The setup supports OpenAI, Anthropic Claude, Google Gemini, Mistral, xAI Grok, DeepSeek, Azure OpenAI, OpenAI-compatible hosted APIs, and OpenAI-compatible local servers such as Ollama, LM Studio, LocalAI, and vLLM. Model IDs are editable. Providers that need an endpoint expose it directly. Connection testing sends a short synthetic message without manuscript text.

Pasted keys are saved separately by provider through the operating system credential store. They are never stored in project YAML, application settings, logs, or manuscript files. Provider-specific environment variables remain supported and take priority over saved keys. Local servers may omit the key.

Connecting while a project is open explicitly enables the selected provider for that project. Connecting without an open project sets the default for projects later created through the desktop application. Existing projects are not modified automatically. Non-secret endpoint URLs can be stored in project YAML.

Connection does not grant standing approval to transfer writing. Every hosted CLI request retains the existing disclosure and `--allow-data-transfer` requirement. Destination controls remain authoritative: only loopback endpoints bypass transfer consent, and non-loopback compatible endpoints require HTTPS. OpenAI and Azure OpenAI Responses requests set `store: false`.

The packaged desktop and CLI include every supported provider client and credential-store runtime.

## Limits

This is a bring-your-own-key desktop design. Any process running as the same operating system user may be able to request access to that user's credential store. It is not equivalent to a remote backend that keeps API credentials off the endpoint.

OpenAI-compatible servers vary. OpenScribe uses the broadly supported Chat Completions interface for local and custom compatible endpoints. The server must already be installed, running, and have the selected model available.

Model availability, billing, retention, and API behavior depend on the selected provider and account. Hosted compatibility remains covered by mocked tests until credential-isolated synthetic live tests are authorized and completed. A separate independent reviewer was unavailable for this change.

## References

- [OpenAI Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create)
- [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)
- [Google Gemini API](https://ai.google.dev/api)
- [Mistral chat completions](https://docs.mistral.ai/api/endpoint/chat)
- [Azure OpenAI Responses API](https://learn.microsoft.com/azure/ai-foundry/openai/quickstart)
- [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility)
- [xAI API compatibility](https://docs.x.ai/developers/rest-api-reference/inference)
- [DeepSeek API compatibility](https://api-docs.deepseek.com/)
