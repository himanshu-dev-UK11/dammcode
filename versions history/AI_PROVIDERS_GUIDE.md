# AI Provider Connection Guide

## Overview

This document explains how to connect different AI providers using API tokens in MyCodingMaster.

## Features

- ✅ Multiple AI provider support (OpenAI, Anthropic, Google Gemini, Groq, DeepSeek, etc.)
- ✅ Secure API token storage with encryption
- ✅ Easy provider management (add, edit, remove)
- ✅ Model discovery and selection
- ✅ Connection testing before saving
- ✅ Auto-connection on app startup
- ✅ No API key re-entry required for connected providers

## Architecture

### Core Components

1. **API Token Manager** (`ai/providers/api_token_manager.py`)
   - Secure storage of API tokens
   - Token hashing for verification
   - Provider metadata management
   - Encryption using Fernet (AES-128)

2. **Provider Registry** (`ai/providers/provider_registry.py`)
   - Manages all registered providers
   - Loads providers from config directory
   - Tracks provider health and status

3. **Provider Manager** (`ai/providers/provider_manager.py`)
   - Validates API keys
   - Tests connections
   - Manages provider lifecycle

4. **Model Center** (`ai/models/model_center.py`)
   - Model discovery and registration
   - Model recommendations
   - Provider grouping and filtering

### UI Components

1. **Models & Providers Section** (`ui/ai_workspace/models_section.py`)
   - Display connected providers
   - Show available models
   - "Connect New Provider" button

2. **Connect Provider Dialog** (`ui/ai_workspace/connect_provider_dialog.py`)
   - Add new providers with API key
   - Test connection before saving
   - Auto-fetch models from provider

3. **Connected Providers Panel** (`ui/ai_workspace/connected_providers_panel.py`)
   - List all connected providers
   - Edit/remove providers
   - View provider details

4. **Provider Setup Dialog** (`ui/ai_workspace/provider_setup_dialog.py`)
   - Initial setup on first launch
   - Quick connect for first provider
   - Skip option for later setup

## Adding a New AI Provider

### Method 1: Through UI (Recommended)

1. Open the **AI Engineering Workspace** (Ctrl+\)
2. Expand the **Models & Providers** section
3. Click **"+ Connect New Provider"** button
4. Enter:
   - Provider Name: Your name for the provider (e.g., "OpenAI", "Custom")
   - API Key: Your actual API key
   - Endpoint: Provider's API endpoint (default: standard provider endpoint)
5. Click **"Test Connection"** to verify
6. If successful, click **"Connect Provider"** to save

### Method 2: Automatic on First Launch

When you first launch the app with no providers configured:
- The Provider Setup Dialog appears
- Enter your API key and provider name
- Click "Connect Provider" to save

## Connecting Different AI Providers

### OpenAI
```
Provider Name: openai
API Key: sk-... (your OpenAI API key)
Endpoint: https://api.openai.com/v1
```

### Anthropic (Claude)
```
Provider Name: anthropic
API Key: sk-ant-... (your Anthropic API key)
Endpoint: https://api.anthropic.com/v1
```

### Google Gemini
```
Provider Name: gemini
API Key: AIza... (your Google API key)
Endpoint: https://generativelanguage.googleapis.com/v1beta
```

### Groq
```
Provider Name: groq
API Key: gsk_... (your Groq API key)
Endpoint: https://api.groq.com/openai/v1
```

### DeepSeek
```
Provider Name: deepseek
API Key: sk-... (your DeepSeek API key)
Endpoint: https://api.deepseek.com/v1
```

### Local (Ollama)
```
Provider Name: ollama
API Key: (leave empty for local)
Endpoint: http://localhost:11434
```

## Managing Connected Providers

### View Connected Providers

1. Open **AI Engineering Workspace**
2. Expand **Models & Providers** section
3. Scroll to see connected providers
4. Each provider shows:
   - Provider name
   - Number of available models
   - Connection status

### Remove a Provider

1. Expand **Connected Providers** panel
2. Select the provider you want to remove
3. Click **"Remove"** button
4. Confirm removal

### Switch Between Providers

1. In the AI Chat panel, use the **Provider** dropdown
2. Select your desired provider
3. Use the **Model** dropdown to select a model from that provider
4. Chat as usual - the system will use the selected provider

## API Token Storage

### Location

API tokens are stored in:
```
config/api_tokens/tokens.json
```

### Security

- Tokens are encrypted using Fernet (AES-128)
- Encryption key stored in: `config/api_tokens/.key`
- Token hashes used for verification
- Actual tokens are not stored in plain text

### Backup

To backup your connected providers:
```bash
# Copy the api_tokens directory
cp -r config/api_tokens backup/api_tokens
```

To restore:
```bash
# Copy backup back
cp -r backup/api_tokens config/api_tokens
```

## Troubleshooting

### Connection Test Fails

1. **Check API Key**: Verify your API key is correct
2. **Check Endpoint**: Ensure the endpoint URL is correct
3. **Network**: Check your internet connection
4. **API Status**: Verify the provider's API is operational

### "No Models Available"

1. The provider connection is successful, but no models were detected
2. Try clicking **"Refresh"** in the provider selection
3. Check if the provider has model restrictions on your account

### "Provider Already Connected"

If you see this error:
1. The provider is already in your connected list
2. Check the **Connected Providers** panel
3. Remove the existing connection first if you want to reconfigure

### API Key Not Being Saved

1. Check file permissions on `config/api_tokens/` directory
2. Ensure the encryption key file exists: `config/api_tokens/.key`
3. If missing, the app will generate a new one (this will invalidate old tokens)

## Programmatic Provider Connection

You can also connect providers programmatically:

```python
from ai.providers.api_token_manager import APITokenManager
from ai.providers.base_provider import ProviderConfig, AuthenticationType

# Initialize token manager
token_manager = APITokenManager()

# Store provider configuration
success = token_manager.store_token(
    provider_name="openai",
    api_key="sk-...",
    display_name="OpenAI",
    endpoint="https://api.openai.com/v1",
    models=["gpt-4", "gpt-3.5-turbo"]
)

# Create provider config
config = ProviderConfig(
    provider_name="openai",
    endpoint="https://api.openai.com/v1",
    auth_type=AuthenticationType.API_KEY,
    api_key="sk-...",
    enabled=True
)
```

## Supported Provider Types

### Cloud Providers
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 2, 3, Opus, Sonnet)
- Google Gemini (Pro, Ultra, Flash)
- Groq (Llama 3, Mistral, Mixtral)
- DeepSeek (Chat, Code)
- DeepInfra
- Fireworks AI
- Together AI
- Perplexity

### Local Providers
- Ollama
- LM Studio
- Local LLM servers

### Compatible APIs
Any OpenAI-compatible API server:
- vLLM
- Text Generation WebUI
- LM Studio API
- Local AI servers

## API Key Safety

⚠️ **Security Best Practices:**

1. Never commit API keys to version control
2. Use `.env` files for development (not committed)
3. Rotate your API keys regularly
4. Use provider-specific API keys when possible
5. Monitor API usage to prevent unexpected charges

## Support

For issues or questions:
1. Check the documentation
2. Review error messages in the AI panel
3. Check the logs in the **Logs** section
4. Contact support with provider name and error details

## Changelog

### v1.0
- Initial provider connection system
- Secure token storage
- Multiple provider support
- Model discovery
- Connection testing