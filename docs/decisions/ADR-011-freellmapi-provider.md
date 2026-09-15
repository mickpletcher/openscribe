# ADR-011: FreeLLMAPI provider

**Status:** Accepted
**Date:** 2026-09-15
**Driving requirement:** Link OpenScribe to FreeLLMAPI as an optional route to free-tier hosted models
**Supersedes:** None
**Superseded by:** None

## Decision

OpenScribe provides a named **FreeLLMAPI** choice in first launch and later AI setup. The choice links to the FreeLLMAPI GitHub project and presets its OpenAI-compatible endpoint to `http://127.0.0.1:3001/v1/`. The initial model is `auto`, with editable `auto:fast`, `auto:smart`, `fusion`, profile, and model identifiers.

The writer installs and configures FreeLLMAPI separately. OpenScribe accepts FreeLLMAPI's unified API key through `FREELLMAPI_API_KEY` or its existing operating system credential-store workflow. The key is not written to project YAML. `FREELLMAPI_BASE_URL` can override the project endpoint.

FreeLLMAPI is treated as a hosted-transfer provider even when OpenScribe connects to its loopback gateway. Desktop writing requires approval for every request. CLI requests require `--allow-data-transfer`. This exception to destination-based loopback handling is necessary because the gateway normally forwards prompts to external model providers.

OpenScribe uses the existing OpenAI-compatible Chat Completions client and does not install, start, configure, update, or administer the gateway. The connection test sends only the existing synthetic message.

## Limits

FreeLLMAPI is a router, not a model included with OpenScribe. Users may need accounts and API keys for its supported free-tier providers. Model availability, quotas, acceptable use, privacy, and retention depend on the gateway configuration and the selected upstream provider.

The FreeLLMAPI project describes its intended use as personal experimentation. OpenScribe does not claim unrestricted, anonymous, production, or commercially suitable free inference.

Compatibility is covered by mocked OpenAI-compatible contracts. A live FreeLLMAPI installation and its upstream providers remain unverified until credential-isolated testing uses synthetic text.

## References

- [FreeLLMAPI](https://github.com/tashfeenahmed/freellmapi)
- [FreeLLMAPI REST API](https://github.com/tashfeenahmed/freellmapi/blob/main/docs/en/api/01-rest-api.md)
- [FreeLLMAPI installation](https://github.com/tashfeenahmed/freellmapi/blob/main/docs/en/install/01-install.md)
