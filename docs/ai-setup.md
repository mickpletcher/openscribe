# AI setup

This guide covers how to enable AI in `openscribe`.

Use this to connect the model that powers desktop page and chapter drafting or the `openscribe ai ...` review commands.

## What AI can do now

The desktop **Write with AI** action turns a writer description into either an approximately 250 to 350 word page or a complete chapter draft. It uses the selected chapter or scene as context, previews the result, and adds approved prose only to the unsaved editor draft. See the [desktop guide](desktop-guide.md#write-a-page-or-chapter-with-ai).

The current CLI supports read-only summary, rewrite, outline, pacing, continuity, point-of-view, prose, metadata, brainstorming, and project-query tasks.

```powershell
openscribe ai summarize "Chapter Title"
openscribe ai rewrite "Chapter Title"
openscribe ai outline "Chapter Title"
openscribe ai analyze "Chapter Title" --focus pacing
openscribe ai analyze "Chapter Title" --focus continuity
openscribe ai analyze "Chapter Title" --focus pov
openscribe ai analyze "Chapter Title" --focus prose
openscribe ai metadata "Chapter Title"
openscribe ai brainstorm "Chapter Title" --question "What could fail next?"
openscribe ai query "Which clues remain unresolved?"
```

The commands print model output. They do not change manuscript or metadata files.

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

The Windows desktop installer and portable package include every supported provider client plus the operating system credential storage support used by first launch setup. You do not need to install Python or a provider SDK when using either Windows package.

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
5. set `endpoint` when using Azure OpenAI or an OpenAI-compatible server

## Cloud providers

These options use hosted APIs and usually require an account plus an API key.
The complete selected chapter or scene body, or the complete assembled manuscript for `ai query`, is sent to the configured provider. Review
that provider's current data handling and retention terms before use.

Hosted requests require explicit approval on every command:

```powershell
openscribe ai summarize "The Beginning" --allow-data-transfer
openscribe ai analyze "The Beginning" --focus continuity --allow-data-transfer
openscribe ai query "Which clues remain unresolved?" --allow-data-transfer
```

Without `--allow-data-transfer`, the command stops before loading a provider
SDK or making a network request. The CLI reports the hosted provider, model,
and character count before an approved request.

### Desktop setup

The desktop application asks for AI setup on first launch. Choose a provider, enter an editable model ID, supply an endpoint when required, and select **Connect**. Its connection test sends a short synthetic message to check the API key, endpoint, billing, and model without sending manuscript text.

OpenScribe stores pasted keys separately by provider in the operating system credential store. It does not put them in project YAML or application settings. The provider-specific environment variable takes priority over a saved key. Local servers may omit the API key.

Supported desktop choices are OpenAI, Anthropic Claude, Google Gemini, Mistral AI, xAI Grok, DeepSeek, Azure OpenAI, Hugging Face, OpenRouter, FreeLLMAPI, LM Studio, Meta Llama through Ollama, other local OpenAI-compatible servers, and other OpenAI-compatible providers. Model IDs remain editable because access and model catalogs change.

For **Write with AI**, every hosted or non-loopback request displays the provider, model, and number of manuscript characters that will be sent. Approval applies only to that request. The writing description is sent with the selected manuscript context. Loopback requests do not show the transfer confirmation unless FreeLLMAPI is selected. A loopback proxy, tunnel, or LM Link can still forward a request to another computer, and OpenScribe cannot detect that forwarding.

### OpenAI

Project config:

```yaml
ai:
  enabled: true
  provider: openai
  model: gpt-5.6-terra
```

Environment:

```powershell
$env:OPENAI_API_KEY="your_key_here"
```

Do not put the API key in `.openscribe/project.yaml`, a manuscript file, or source control.

OpenScribe sets `store: false` on OpenAI Responses API calls so response application state is not retained for the default Responses storage period. OpenAI may still retain prompts and responses in abuse-monitoring logs under the account's applicable data controls. Review OpenAI's current data-control documentation before sending private writing.

### Azure OpenAI

Project config:

```yaml
ai:
  enabled: true
  provider: azure-openai
  model: your-deployment-name
  endpoint: https://YOUR-RESOURCE-NAME.openai.azure.com/openai/v1/
```

Environment:

```powershell
$env:AZURE_OPENAI_API_KEY="your_key_here"
$env:AZURE_OPENAI_BASE_URL="https://YOUR-RESOURCE-NAME.openai.azure.com/openai/v1/" # optional override
```

Use the deployment name in `model` if your Azure setup expects that.

### Anthropic

Project config:

```yaml
ai:
  enabled: true
  provider: anthropic
  model: claude-sonnet-4-6
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
  model: gemini-3.5-flash
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

### xAI Grok

Choose **xAI Grok** in the desktop setup or use `provider: xai`. The default endpoint is `https://api.x.ai/v1/`. Set `XAI_API_KEY`; `XAI_BASE_URL` can override the endpoint.

### DeepSeek

Choose **DeepSeek** in the desktop setup or use `provider: deepseek`. The default endpoint is `https://api.deepseek.com/`. Set `DEEPSEEK_API_KEY`; `DEEPSEEK_BASE_URL` can override the endpoint.

### Hugging Face

[Hugging Face Inference Providers](https://huggingface.co/docs/inference-providers/) exposes an OpenAI-compatible router backed by multiple inference providers. Create a token with permission to call Inference Providers, select **Hugging Face**, and keep the preset `https://router.huggingface.co/v1/` endpoint. Model IDs and provider availability change, so copy a current chat-completion model ID from the [Inference Models catalog](https://huggingface.co/models?inference_provider=all&pipeline_tag=text-generation). A provider or routing policy can be appended to the model ID when supported.

Project config:

```yaml
ai:
  enabled: true
  provider: huggingface
  model: openai/gpt-oss-120b:fastest
  endpoint: https://router.huggingface.co/v1/
```

Environment:

```powershell
$env:HF_TOKEN="your_fine_grained_token_here"
$env:HF_INFERENCE_BASE_URL="https://router.huggingface.co/v1/" # optional override
```

Every manuscript request requires explicit transfer approval. Hugging Face may route the request to another inference provider. Review the selected model, routing provider, price, quota, and both services' data policies before sending private writing. Free credits and model availability are not guaranteed.

### OpenRouter

[OpenRouter](https://openrouter.ai/) exposes many model providers through one OpenAI-compatible API. Create an [OpenRouter API key](https://openrouter.ai/settings/keys), select **OpenRouter** in AI setup, and keep the preset `https://openrouter.ai/api/v1/` endpoint.

The default `openrouter/auto` model lets OpenRouter select a model for each prompt. Enter any current model slug from the [OpenRouter model catalog](https://openrouter.ai/models) when you need a specific model. The `openrouter/free` router is also offered as a preset, but free model availability and rate limits can change. Do not assume a model is free. Review the model price and your account settings before sending a request.

Project config:

```yaml
ai:
  enabled: true
  provider: openrouter
  model: openrouter/auto
  endpoint: https://openrouter.ai/api/v1/
```

Environment:

```powershell
$env:OPENROUTER_API_KEY="your_key_here"
$env:OPENROUTER_BASE_URL="https://openrouter.ai/api/v1/" # optional override
```

OpenScribe uses the bundled OpenAI client with OpenRouter's Chat Completions API. OpenRouter's attribution headers are optional and OpenScribe does not send them. Every manuscript request requires explicit transfer approval. OpenRouter then routes the prompt and manuscript context to the selected upstream model provider, so review both OpenRouter's policy and the selected provider's policy before sending private writing.

### FreeLLMAPI

[FreeLLMAPI](https://github.com/tashfeenahmed/freellmapi) is a separate local gateway that combines supported free-tier model providers behind one OpenAI-compatible endpoint. OpenScribe links to its project from the setup dialog. FreeLLMAPI must be installed, running, and configured before OpenScribe can connect.

1. Install the current FreeLLMAPI desktop release or follow its self-hosting instructions.
2. Open its local dashboard at `http://localhost:3001/`.
3. Add the provider keys required for the free-tier models you intend to use.
4. Copy the unified FreeLLMAPI API key from its Keys page.
5. In OpenScribe, select **AI setup**, then choose **FreeLLMAPI**.
6. Keep model `auto` to let the gateway select a model, or enter a model or profile ID exposed by your gateway.
7. Keep endpoint `http://127.0.0.1:3001/v1/` for the default local install.
8. Paste the unified key and select **Connect**.

The resulting project configuration is similar to:

```yaml
ai:
  enabled: true
  provider: freellmapi
  model: auto
  endpoint: http://127.0.0.1:3001/v1/
```

`FREELLMAPI_API_KEY` and `FREELLMAPI_BASE_URL` can override the saved key and endpoint. OpenScribe stores a pasted unified key in the operating system credential store.

The local gateway forwards prompts and manuscript context to hosted model providers. OpenScribe therefore displays the transfer confirmation for every FreeLLMAPI manuscript request even though the preset endpoint is loopback. FreeLLMAPI does not guarantee access without provider accounts or keys. Available models, quotas, retention, and acceptable use depend on the gateway configuration and the upstream providers. Its project describes the service as intended for personal experimentation.

## On prem or local model servers

Use this path when your model runs locally or inside your own network and exposes an OpenAI compatible API.

Examples:

* LM Studio
* Ollama in OpenAI compatibility mode
* vLLM
* LocalAI
* another internal OpenAI compatible gateway

### Meta Llama through Ollama

Choose **Meta Llama (Ollama)** to run a Llama model through Ollama's OpenAI-compatible local API. OpenScribe defaults to the `llama3.2` model and `http://127.0.0.1:11434/v1/` endpoint, but the model ID stays editable.

1. Install and start Ollama.
2. Download the default model with `ollama pull llama3.2`, or pull another Llama model that fits your computer.
3. In OpenScribe, select **AI setup**, then choose **Meta Llama (Ollama)**.
4. Enter the installed model ID.
5. Keep `http://127.0.0.1:11434/v1/` for a same-computer Ollama server.
6. Leave the API key empty unless your gateway requires one.
7. Select **Connect**.

Project config:

```yaml
ai:
  enabled: true
  provider: ollama
  model: llama3.2
  endpoint: http://127.0.0.1:11434/v1/
```

`OLLAMA_BASE_URL` and the optional `OLLAMA_API_KEY` can override the saved endpoint and key. The default loopback endpoint keeps requests on this computer. A remote endpoint must use HTTPS and requires approval before each manuscript transfer.

### LM Studio

Choose **LM Studio** in the desktop setup. First decide where LM Studio will run.

#### LM Studio on the same computer

Use this option if OpenScribe and LM Studio run on the same Windows computer.

1. Open LM Studio.
2. Download or select a model.
3. Open LM Studio's **Developer** page.
4. Start the API server.
5. In OpenScribe, select **AI setup** and choose **LM Studio**.
6. Enter the model identifier shown by LM Studio.
7. Leave the endpoint set to `http://127.0.0.1:1234/v1/`.
8. Leave the API key empty unless you enabled authentication in LM Studio.
9. Select **Connect**.

The resulting project configuration is similar to:

```yaml
ai:
  enabled: true
  provider: lm-studio
  model: openai/gpt-oss-20b
  endpoint: http://127.0.0.1:1234/v1/
```

`LM_STUDIO_BASE_URL` and `LM_STUDIO_API_KEY` can override the saved endpoint and key.

#### LM Studio on another computer with LM Link

This is the simplest option when another computer has the faster GPU or more memory.

1. Install a current LM Studio release on both computers.
2. Follow LM Studio's [LM Link setup](https://lmstudio.ai/docs/developer/core/lmlink) to link them.
3. Download or load the model on the remote computer.
4. On the OpenScribe computer, start LM Studio's API server.
5. In OpenScribe, choose **LM Studio** and keep `http://127.0.0.1:1234/v1/` as the endpoint.
6. Enter the remote model's identifier and select **Connect**.

LM Link makes the remote model available through the local LM Studio server. OpenScribe sees only the loopback address, so it does not display the non-loopback transfer confirmation. Your description and manuscript context are still sent to the linked computer. LM Studio states that linked traffic uses an encrypted connection, but you should link only computers and accounts you trust.

#### Direct connection to LM Studio on another computer

LM Studio can [serve its API on a local network](https://lmstudio.ai/docs/developer/core/server/serve-on-network), but its normal LAN address uses plain HTTP. OpenScribe deliberately rejects nonlocal plain HTTP because manuscript text and API tokens would cross the network without transport encryption.

For a direct connection, all of these must be true:

1. LM Studio has **Serve on Local Network** enabled.
2. LM Studio has **Require Authentication** enabled and you created an API token.
3. The server computer's firewall allows the selected LM Studio port from the OpenScribe computer.
4. A trusted HTTPS reverse proxy or internal AI gateway protects LM Studio.
5. The HTTPS certificate is trusted by Windows on the OpenScribe computer.

Enter an endpoint similar to this in OpenScribe:

```text
https://lmstudio.example.test/v1/
```

Paste the LM Studio API token into the API key field. Do not put the token in the URL. OpenScribe treats this as a non-loopback destination and asks for approval before every manuscript request.

Do not enter an address such as `http://192.168.1.50:1234/v1/`. OpenScribe will reject it with `Nonlocal provider endpoints must use HTTPS.` Do not expose LM Studio to the public internet or configure router port forwarding for it.

### Other OpenAI compatible local servers

Project config:

```yaml
ai:
  enabled: true
  provider: openai-compatible-local
  model: qwen3:8b
  endpoint: http://127.0.0.1:11434/v1/
```

Environment:

```powershell
$env:OPENAI_COMPATIBLE_LOCAL_BASE_URL="http://localhost:1234/v1" # optional override
$env:OPENAI_COMPATIBLE_LOCAL_API_KEY="local"
```

`OPENAI_COMPATIBLE_LOCAL_API_KEY` is optional.
If your local server does not require a token, `openscribe` uses `local` by default.

The default local endpoint matches Ollama's OpenAI compatibility API. Replace it with the endpoint shown by LocalAI, vLLM, or your own compatible server. The server must already be installed, running, and have the selected model available.

### Other OpenAI-compatible providers

For another hosted or self-managed compatible API, choose **Other OpenAI-compatible provider** or configure:

```yaml
ai:
  enabled: true
  provider: openai-compatible
  model: model-id
  endpoint: https://models.example.test/v1/
```

Set `OPENAI_COMPATIBLE_API_KEY` or paste the key in the desktop setup. `OPENAI_COMPATIBLE_BASE_URL` can override the saved endpoint. Loopback destinations stay local. Any non-loopback destination requires HTTPS and per-command transfer approval.

### Example endpoints

LM Studio often exposes an endpoint like:

```powershell
$env:OPENAI_COMPATIBLE_LOCAL_BASE_URL="http://localhost:1234/v1"
```

An internal server protected by HTTPS might look like:

```powershell
$env:OPENAI_COMPATIBLE_LOCAL_BASE_URL="https://ai-gateway.example.test/v1"
$env:OPENAI_COMPATIBLE_LOCAL_API_KEY="your_internal_token"
```

## First run

For a source installation or an existing project that was not configured through the desktop prompt, set the project config and provider environment variable, then run:

```powershell
openscribe ai summarize "The Beginning" --allow-data-transfer
```

Omit `--allow-data-transfer` only when the configured endpoint is loopback, such as `http://127.0.0.1:1234/v1`. A private-network or hosted destination still leaves this machine and requires HTTPS plus explicit transfer consent, even with the `openai-compatible-local` provider label.

Remember that a loopback proxy or LM Link can forward a request elsewhere. OpenScribe cannot detect that routing, so a loopback address does not by itself prove the model runs on the same computer.

## Troubleshooting

If AI is disabled:

* set `ai.enabled: true` in `.openscribe/project.yaml`

If the provider key is missing:

* set the matching environment variable for the provider you chose

If local AI cannot connect:

* confirm the server is running, the endpoint is correct, and the selected model is installed
* open the endpoint's `/models` route from PowerShell as described in [Troubleshooting](troubleshooting.md#lm-studio-on-another-computer-does-not-connect)

If the AI SDKs are missing:

```powershell
python -m pip install -e ".[ai]"
```

## Current provider list

The current code supports:

* `openai`
* `azure-openai`
* `lm-studio`
* `openai-compatible-local`
* `openai-compatible`
* `anthropic`
* `gemini`
* `mistral`
* `xai`
* `deepseek`
