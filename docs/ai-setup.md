# AI setup

This guide covers how to enable AI in `openscribe`.

Use this only if you want `openscribe ai ...` features.
The base writing workflow does not need AI.

## What AI can do now

The current CLI supports:

* `openscribe ai summarize "Chapter Title"`

This reads the chapter body and returns:

* a short overview paragraph
* five concise bullet points
* one revision risk to review next

## Base install vs AI install

Base install:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

AI install:

```powershell
python -m pip install -e ".[ai]"
```

## Project config

Each project includes an AI section in `.openscribe/project.yaml`:

```yaml
ai:
  enabled: false
  provider: openai
  model: gpt-4.1
```

To enable AI:

1. open `.openscribe/project.yaml`
2. set `enabled: true`
3. set `provider`
4. set `model`

## Cloud providers

These options use hosted APIs and usually require an account plus an API key.
The complete selected chapter body is sent to the configured provider. Review
that provider's current data handling and retention terms before use.

Hosted requests require explicit approval on every command:

```powershell
openscribe ai summarize "The Beginning" --allow-data-transfer
```

Without `--allow-data-transfer`, the command stops before loading a provider
SDK or making a network request. The CLI reports the hosted provider, model,
and character count before an approved request.

### OpenAI

Project config:

```yaml
ai:
  enabled: true
  provider: openai
  model: gpt-5.5
```

Environment:

```powershell
$env:OPENAI_API_KEY="your_key_here"
```

### Azure OpenAI

Project config:

```yaml
ai:
  enabled: true
  provider: azure-openai
  model: gpt-4.1
```

Environment:

```powershell
$env:AZURE_OPENAI_API_KEY="your_key_here"
$env:AZURE_OPENAI_BASE_URL="https://YOUR-RESOURCE-NAME.openai.azure.com/openai/v1/"
```

Use the deployment name in `model` if your Azure setup expects that.

### Anthropic

Project config:

```yaml
ai:
  enabled: true
  provider: anthropic
  model: claude-sonnet-4-5
```

Environment:

```powershell
$env:ANTHROPIC_API_KEY="your_key_here"
```

### Gemini

Project config:

```yaml
ai:
  enabled: true
  provider: gemini
  model: gemini-2.5-flash
```

Environment:

```powershell
$env:GEMINI_API_KEY="your_key_here"
```

### Mistral

Project config:

```yaml
ai:
  enabled: true
  provider: mistral
  model: mistral-large-latest
```

Environment:

```powershell
$env:MISTRAL_API_KEY="your_key_here"
```

## On prem or local model servers

Use this path when your model runs locally or inside your own network and exposes an OpenAI compatible API.

Examples:

* LM Studio
* Ollama in OpenAI compatibility mode
* vLLM
* LocalAI
* another internal OpenAI compatible gateway

### OpenAI compatible local

Project config:

```yaml
ai:
  enabled: true
  provider: openai-compatible-local
  model: qwen3-8b
```

Environment:

```powershell
$env:OPENAI_COMPATIBLE_LOCAL_BASE_URL="http://localhost:1234/v1"
$env:OPENAI_COMPATIBLE_LOCAL_API_KEY="local"
```

`OPENAI_COMPATIBLE_LOCAL_API_KEY` is optional.
If your local server does not require a token, `openscribe` uses `local` by default.

### Example local setups

LM Studio often exposes an endpoint like:

```powershell
$env:OPENAI_COMPATIBLE_LOCAL_BASE_URL="http://localhost:1234/v1"
```

An internal server on your network might look like:

```powershell
$env:OPENAI_COMPATIBLE_LOCAL_BASE_URL="http://ai-gateway.contoso.local:8000/v1"
$env:OPENAI_COMPATIBLE_LOCAL_API_KEY="your_internal_token"
```

## First run

Once the project config and environment variables are set:

```powershell
openscribe ai summarize "The Beginning" --allow-data-transfer
```

Omit `--allow-data-transfer` when using `openai-compatible-local`.

## Troubleshooting

If AI is disabled:

* set `ai.enabled: true` in `.openscribe/project.yaml`

If the provider key is missing:

* set the matching environment variable for the provider you chose

If local AI is selected and the base URL is missing:

* set `OPENAI_COMPATIBLE_LOCAL_BASE_URL`

If the AI SDKs are missing:

```powershell
python -m pip install -e ".[ai]"
```

## Current provider list

The current code supports:

* `openai`
* `azure-openai`
* `openai-compatible-local`
* `anthropic`
* `gemini`
* `mistral`
