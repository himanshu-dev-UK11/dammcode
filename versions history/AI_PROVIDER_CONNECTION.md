# AI Provider Connection - Quick Guide

## What's New

I've built a complete system for connecting different AI providers using API tokens in your program. Here's what you get:

### Key Features
- ✅ Connect multiple AI providers (OpenAI, Anthropic, Google Gemini, Groq, DeepSeek, etc.)
- ✅ Store API keys securely with encryption
- ✅ Select AI provider and model from the UI
- ✅ Test connections before saving
- ✅ Auto-connect on app startup (no re-entry needed)
- ✅ Easy provider management (add, remove, edit)

## How to Use

### 1. First Time Setup
When you first launch the app:
- A setup dialog appears
- Enter your API key and provider name
- Click "Connect Provider"
- Done! The provider is saved securely

### 2. Connecting Additional Providers
1. Open **AI Engineering Workspace** (Ctrl+\)
2. Expand **Models & Providers** section
3. Click **"+ Connect New Provider"**
4. Enter provider info and test connection
5. Save - provider is now available

### 3. Switching Between Providers
In the AI Chat panel:
- Use **Provider** dropdown to select provider
- Use **Model** dropdown to select model from that provider
- Chat normally - system uses selected provider

## Files Created/Modified

### New Files
1. `ai/providers/api_token_manager.py` - Secure API key storage
2. `ui/ai_workspace/connect_provider_dialog.py` - Dialog to add new providers
3. `ui/ai_workspace/connected_providers_panel.py` - Manage connected providers
4. `ui/ai_workspace/provider_setup_dialog.py` - Initial setup dialog
5. `AI_PROVIDERS_GUIDE.md` - Complete documentation

### Modified Files
1. `ui/ai_workspace/models_section.py` - Added "Connect New Provider" button
2. `ui/ai_workspace/provider_selection_section.py` - Added remove provider option
3. `ai/providers/provider_registry.py` - Added `get_loaded_providers` method
4. `main.py` - Initialize token manager and show setup dialog

## Supported Providers

### Cloud Providers
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google Gemini
- Groq (Llama, Mistral)
- DeepSeek
- DeepInfra
- Fireworks AI
- Together AI

### Local Providers
- Ollama
- LM Studio

### Compatible APIs
Any OpenAI-compatible API server works automatically!

## API Token Storage

**Location:** `config/api_tokens/`

**Security:**
- Tokens encrypted with Fernet (AES-128)
- Hashed for verification
- No plain-text storage

## Testing

To test the system:

1. Launch the app - setup dialog should appear if no providers connected
2. Enter your API key and provider name
3. Click "Connect Provider"
4. Open AI Engineering Workspace
5. Check that provider appears in the list
6. Try switching providers in the AI Chat panel

## Troubleshooting

**Connection fails:**
- Check API key is correct
- Verify endpoint URL
- Check internet connection
- Ensure provider API is online

**Provider not showing:**
- Click "Refresh" in the provider list
- Check provider is enabled
- Verify connection status

**API key not saved:**
- Check file permissions on `config/api_tokens/`
- Ensure encryption key exists at `config/api_tokens/.key`