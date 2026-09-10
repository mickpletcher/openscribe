OpenScribe portable edition

Run OpenScribe.exe to open the desktop writing application.
Run openscribe-cli.exe from PowerShell for advanced commands.
The first desktop launch can connect OpenAI, Anthropic Claude, Google Gemini, Mistral, xAI Grok, DeepSeek, Azure OpenAI, LM Studio, another local model server, or another OpenAI-compatible provider. API keys are stored separately by provider in the operating system credential store, not in this portable folder.

To write with AI, open a project, select a chapter or scene, and select Write with AI. Choose an approximate page or a complete chapter, describe what should happen, and review the result. Applied text remains an unsaved draft until you save it.

LM Studio on this computer normally uses http://127.0.0.1:1234/v1/. LM Studio on another computer can be reached through LM Link while OpenScribe keeps that loopback address. Direct network endpoints must use HTTPS. OpenScribe cannot detect when LM Link or another loopback proxy forwards text to a different computer.

This package requires no separate Python installation. Keep the entire folder together.
Projects are stored wherever you choose and are not removed with the application.
The supported hosted and local AI provider clients are bundled. LanguageTool is an optional separate service.
Microsoft Word round trips remain experimental.
OpenScribe's license is included as LICENSE.txt. Bundled dependency licenses are in THIRD-PARTY-LICENSES.txt.

OpenScribe is pre-release alpha software. Keep an independent backup of important writing.
