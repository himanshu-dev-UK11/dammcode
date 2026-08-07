"""Update PROJECT_BLUEPRINT.md with v0.9 info"""

blueprint_path = "PROJECT_BLUEPRINT.md"

v09_section = """
### v0.9 - AI Engineering Workspace ✅ IN PROGRESS

**AI Workspace Components** (`ui/ai_workspace/`):
- `ai_workspace_panel.py` — Section primitives (SectionHeader, Section)
- `current_task_section.py` — Current objective, phase, progress, elapsed time
- `execution_progress_section.py` — Step tracking with progress bar
- `conversation_section.py` — Markdown-ready conversation with copy buttons
- `execution_plan_section.py` — Phase-based plan with status icons
- `context_section.py` — Token budget, files, dependencies, reasons
- `runtime_tools_section.py` — Live tool execution display
- `models_section.py` — Model selection, fallback, context window
- `ai_engineering_workspace.py` — Main workspace, EventBus integration

**Architecture**:
- EventBus-driven updates (no direct UI modifications)
- All sections collapsible
- Smooth professional animations
- Live progress indicators

**Integration**:
- `main_window.py` — Replaced AIWorkspacePanel with AIEngineeringWorkspace

**Key features**:
- Current Task: objective, status, elapsed time
- Execution Progress: step tracking, progress bar
- Conversation: message bubbles, copy buttons
- Execution Plan: phase-based with icons
- Context: token budget, selected files, dependencies
- Running Tools: live tool execution
- Models: current/fallback, context window, provider info

**Git vs GitHub**:
- Git: Always available locally, used for snapshots, rollback, and history
- GitHub: Optional integration, disabled by default, manual enable required

---

"""

with open(blueprint_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the position of v0.7 section and insert v0.9 before it
insert_pos = content.find('### v0.7 - Verification Engine')
if insert_pos != -1:
    new_content = content[:insert_pos] + v09_section + content[insert_pos:]
    with open(blueprint_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated {blueprint_path} with v0.9 section")
else:
    print("Could not find insertion point")
