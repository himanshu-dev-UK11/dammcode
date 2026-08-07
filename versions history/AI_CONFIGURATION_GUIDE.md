# AI Configuration Guide

**MyCodingMaster Version 1.7**  
**Date**: June 29, 2026

---

## 🎯 HOW TO CONFIGURE AI PROVIDERS

### Option 1: Ollama (Local AI - Recommended for Beginners)

#### Step 1: Install Ollama
1. Download from https://ollama.com/download
2. Install and run Ollama

#### Step 2: Download a Model
```bash
ollama pull qwen2.5-coder
```

#### Step 3: Verify Installation
```bash
curl http://localhost:11434/api/tags
```
Expected output: List of installed models including `qwen2.5-coder:7b`

#### Step 4: Use in MyCodingMaster
- Open AI Workspace (Ctrl+\)
- Provider will be automatically detected
- Model dropdown shows available models
- Start chatting!

---

### Option 2: Gemini (Cloud AI)

#### Step 1: Get API Key
1. Go to https://aistudio.google.com/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key

#### Step 2: Configure in MyCodingMaster
1. Open AI Workspace (Ctrl+\)
2. Click provider dropdown → Select **GEMINI**
3. Enter your API key in the Advanced Settings section
4. Click **Test** to validate
5. Select a model (e.g., gemini-1.5-flash)
6. Start chatting!

---

### Option 3: Other Cloud Providers

Available providers (API key required):
- OpenAI
- Anthropic
- Groq
- Cerebras
- Fireworks
- DeepInfra
- Together AI

**Configuration**:
1. Get API key from provider
2. Create `config/providers/name.json` with:
```json
{
  "provider_name": "provider-name",
  "endpoint": "https://api.provider.com/v1",
  "auth_type": "api_key",
  "enabled": true,
  "priority": 5,
  "default_model": "model-name",
  "timeout_seconds": 30,
  "retry_count": 3,
  "supports_streaming": true,
  "supports_tool_calling": true,
  "supports_vision": false,
  "supports_function_calling": true
}
```

---

## 📂 CURRENT CONFIGURATION

### Ollama (Local)
- **Endpoint**: `http://localhost:11434`
- **Default Model**: `qwen2.5-coder:7b`
- **Timeout**: 120 seconds
- **Streaming**: ✅ Enabled
- **Tool Calling**: ✅ Enabled

### Gemini (Cloud)
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta`
- **Default Model**: `gemini-1.5-flash`
- **API Key**: Requires user input
- **Streaming**: ✅ Enabled
- **Vision**: ✅ Enabled
- **Tool Calling**: ✅ Enabled

---

## 🛠️ TROUBLESHOOTING

### Ollama Not Connected
1. Check Ollama is running: `ollama list`
2. Check endpoint: `curl http://localhost:11434/api/tags`
3. Verify provider is enabled in config
4. Restart MyCodingMaster

### Gemini Not Connected
1. Verify API key is correct
2. Check API key has required permissions
3. Test connection in Settings
4. Check internet connection

### No Models Showing
1. Run `ollama pull model-name` for local models
2. For Gemini, verify API key works
3. Click **Refresh Models** button
4. Check provider is connected

### Connection Timeouts
1. Increase timeout in config file
2. Check network connection
3. Try local models for faster responses

---

## 🎨 UI ELEMENTS

### Status Bar
- `● OLLAMA` — Provider connected (green)
- `● GEMINI: gemini-1.5-flash` — Model selected (blue)
- `● AI: Thinking` — Generating response
- `● AI: Idle` — Ready for input

### Provider Selection
- Provider dropdown — Select Ollama, Gemini, etc.
- Model dropdown — Select from available models
- Refresh button — Reload model list
- API key input — Enter cloud provider keys

### Diagnostics Page
- Provider status — Connection indicators
- Model list — All available models
- Health check — Provider health metrics
- Test connections — Validate all providers

---

## 💡 TIPS

1. **Start with Ollama** — Local models work offline, no API key needed
2. **Use Gemini for complex tasks** — Better reasoning and coding
3. **Monitor status bar** — See provider and model status
4. **Use Diagnostics** — Check provider health regularly
5. **Refresh models** — After installing new models

---

## 📚 NEXT STEPS

After configuration:
1. Open AI Workspace (Ctrl+\)
2. Select provider (Ollama or Gemini)
3. Send your first message
4. Watch streaming response
5. Try switching between providers

---

**Happy AI Chatting! 🎉**
