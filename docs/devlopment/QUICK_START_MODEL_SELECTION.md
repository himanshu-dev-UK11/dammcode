# Quick Start: AI Model Selection

## ✅ What Changed

Your AI model selection is now **fully automatic** and **smart**:

1. **No more deepseek** - It will NEVER be selected
2. **Only active models** - Models must be running and able to respond
3. **Local models first** - Your downloaded local LLMs are prioritized
4. **Auto-selection** - Best model chosen automatically on startup

## 🚀 How To Use

### When You Start the Application:

1. **Application opens** → Best local model is auto-selected
2. **Chat panel opens** → Only working models appear in dropdown
3. **Start chatting** → No manual model selection needed!

### What You'll See:

```
Provider: Automatic
Model: 🟢 Qwen 3 8B (or your first available local model)
Status: ● Ready: 3 models available
```

### Models That Appear:

✅ **Local models** (Ollama, LM Studio, etc.) - if running  
✅ **Cloud models** (Gemini, OpenAI, etc.) - if connected  
❌ **Deepseek** - NEVER shown  
❌ **Offline models** - Hidden until connected  

## 🔍 How It Works

### The Selection Logic:

1. **Check all providers** (Ollama, Gemini, etc.)
2. **Find connected providers** only
3. **Get models from connected providers**
4. **Filter out**:
   - ❌ Deepseek (per your request)
   - ❌ Disconnected providers
   - ❌ Offline models
   - ❌ Models that can't respond
5. **Prioritize**:
   - 🥇 Local models (highest priority)
   - 🥈 Fast models
   - 🥉 Low-cost models
6. **Auto-select** the best one

### Example Selection:

```
Available models:
- Ollama: qwen3:8b ✅ (Local, Fast, Score: 10,650)
- Ollama: llama3:8b ✅ (Local, Score: 10,500)
- Gemini: gemini-2.0-flash ✅ (Cloud, Score: 450)
- Deepseek: deepseek-coder ❌ (Excluded)

Selected: qwen3:8b (highest score, local, can reply)
```

## 🎯 What You Control

You still have full control:

1. **Manual selection** - Click dropdown to choose different model
2. **Provider selection** - Choose "Automatic" or specific provider
3. **Model switching** - Switch models anytime during chat

## 📊 Status Indicators

### In the Chat Panel:

| Indicator | Meaning |
|-----------|---------|
| 🟢 **Green dot** | Model is connected and ready |
| 🟡 **Yellow dot** | Model is available but slow |
| 🔴 **Red dot** | Model is offline/unavailable |

### Status Messages:

| Message | Meaning |
|---------|---------|
| "Ready: 3 models available" | ✅ Good to go! |
| "No active models available" | ❌ Connect a provider first |
| "Loading models..." | ⏳ Checking providers... |

## ⚙️ Settings

Default model is now set to **"auto"** in:
- `config/settings.json`
- `models.default_model: "auto"`

This means:
- ✅ Automatic best-model selection
- ✅ No hardcoded defaults
- ✅ Always picks the best available model

## 🐛 Troubleshooting

### "No active models available"

**Cause:** No providers are connected

**Solution:**
1. Start Ollama: `ollama serve`
2. Or connect to Gemini/OpenAI in Settings
3. Refresh providers in Settings > AI Providers

### "Provider not connected"

**Cause:** Provider service not running

**Solution:**
- **Ollama:** Start with `ollama serve`
- **LM Studio:** Open LM Studio and start server
- **Cloud:** Check API key in Settings

### Model not appearing in dropdown

**Cause:** Model is offline or provider disconnected

**Solution:**
1. Check provider is running
2. Verify model is downloaded (for local)
3. Check Settings > AI Providers > Provider Status

## 📝 Logs

Check logs for detailed selection info:

```
Location: Console output or log files
Look for: "Auto-selected initial model: ..."
```

Example log:
```
[INFO] Auto-selecting best available model on startup...
[INFO] Skipping deepseek model per user request
[INFO] ✓ Auto-selected: qwen3:8b (can reply and is active)
```

## 💡 Tips

1. **Keep local models running** for fastest responses
2. **Use "Automatic" provider** for best selection
3. **Check logs** if model selection seems wrong
4. **Switch models anytime** if needed for specific tasks

## ❓ FAQ

**Q: Can deepseek ever be selected?**  
A: No. It's completely excluded from all automatic selections.

**Q: What if no local models are available?**  
A: System will select the best available cloud model (if connected).

**Q: Can I force a specific model?**  
A: Yes! Just select it manually from the dropdown.

**Q: What makes a model "active"?**  
A: Provider is connected, model is online, and can respond to requests.

**Q: Will this slow down startup?**  
A: No. Provider checks happen in background threads.

## 🎉 Enjoy!

Your AI chat now automatically selects the best available model that can actually respond. No more deepseek, no more offline models, just working AI!
