# Sprint v1.5.1 - UI Stabilization & First Working AI Workspace

## Command Palette (Priority: Critical)
- [x] **ESC to close** - Command palette doesn't close on ESC
- [ ] **Click outside to close** - Click outside palette should dismiss it
- [ ] **Command execution close** - Palette should auto-close after command execution
- [ ] **Maintain recent commands** - Already implemented, verify persistence
- [ ] **Maintain search history** - Already implemented, verify persistence

## Theme System (Priority: High)
- [ ] **Theme manager** - Replace current theme implementation
- [ ] **Support 12 themes** - Dark, Light, Midnight, Dracula, GitHub Dark/Light, One Dark, Nord, Gruvbox Dark/Light, Solarized Dark/Light, Monokai, High Contrast
- [ ] **Theme switching** - Instant switching without restart
- [ ] **Remember selected theme** - Persist theme preference

## Theme Quality Improvements (Priority: Medium)
- [ ] **Spacing** - Remove excessive empty space
- [ ] **Margins** - Improve margins across panels
- [ ] **Contrast** - Improve text/background contrast
- [ ] **Borders** - Professional borders
- [ ] **Hover states** - Better hover feedback
- [ ] **Rounded corners** - Consistent 3px radius
- [ ] **Icons** - Better icon alignment
- [ ] **Fonts** - Professional typography
- [ ] **Animations** - Smooth transitions

## AI Workspace (Priority: High)
- [ ] **Layout** - Replace placeholder panels
- [ ] **Scrollable messages** - Conversation section
- [ ] **Input box** - Working message input
- [ ] **Send button** - Functional send button
- [ ] **Stop button** - Cancel streaming
- [ ] **Clear chat** - Clear conversation
- [ ] **New chat** - Start new session
- [ ] **History** - Chat history sidebar

## Provider & Model Selector (Priority: High)
- [ ] **Provider selector** - Dropdown with providers
- [ ] **Provider list** - Automatic, Ollama, Gemini, Groq, Together, DeepInfra, OpenAI Compatible
- [ ] **Disabled providers** - Appear grayed out
- [ ] **Model selector** - Dynamic from Provider Manager
- [ ] **No hardcoded models** - Populate from Model Center

## AI Chat Features (Priority: High)
- [ ] **Markdown** - Render markdown in messages
- [ ] **Code blocks** - Syntax highlighted code blocks
- [ ] **Copy button** - Copy message content
- [ ] **Regenerate** - Regenerate responses
- [ ] **Stop generation** - Cancel streaming
- [ ] **Auto scroll** - Auto-scroll to bottom
- [ ] **Syntax highlighting** - Code syntax highlight
- [ ] **Streaming placeholder** - Show typing indicator
- [ ] **Message timestamps** - Show time sent

## AI Status Display (Priority: High)
- [ ] **Connected** - Show connected status
- [ ] **Disconnected** - Show disconnected status
- [ ] **Provider** - Current provider name
- [ ] **Model** - Current model name
- [ ] **Streaming** - Streaming indicator
- [ ] **Offline** - Offline status
- [ ] **Error** - Error state display
- [ ] **Empty state** - "No provider configured" with Configure button

## Toolbar (Priority: High)
- [ ] **Every button works** - No dead buttons
- [ ] **Configure AI Providers dialog** - Show when AI button clicked but no provider configured

## Polish (Priority: Medium)
- [ ] **Remove placeholder text** - Replace "placeholder" with actual text
- [ ] **Improve spacing** - Consistent spacing
- [ ] **Improve typography** - Professional fonts
- [ ] **Improve icon alignment** - Align icons properly
- [ ] **Improve resizing** - Better resize behavior
- [ ] **Improve docking** - Better panel docking

## Documentation (Priority: Medium)
- [ ] **Update PROJECT_BLUEPRINT.md** - Reflect v1.5.1 changes
- [ ] **Update PROGRESS_TRACKER.md** - Mark tasks complete
- [ ] **Run save_progress.py** - Update progress tracking