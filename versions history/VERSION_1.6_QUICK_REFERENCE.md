# Version 1.6 — Quick Reference Guide

**Fast lookup for all features**

---

## 🎯 WHAT'S NEW

Version 1.6 transforms MyCodingMaster into a professional IDE with:
- **30+ languages** with syntax highlighting
- **15+ frameworks** with intelligent execution
- **7 file operations** via context menu
- **Integrated terminal** with command history
- **Session persistence** for auto-restore

---

## 🚀 QUICK START

### 1. Open Workspace
```
File → Open Folder → Select directory
```

### 2. Create Files
```
Right-click folder in Explorer → New File
```

### 3. Edit Code
```
Double-click file → Edit with syntax highlighting
```

### 4. Run Project
```
Click Run button (or press F5)
```

### 5. Use Terminal
```
Ctrl+` → Type command → Enter
```

---

## ⌨️ KEYBOARD SHORTCUTS

| Shortcut | Action |
|----------|--------|
| **Ctrl+B** | Toggle Explorer |
| **Ctrl+`** | Toggle Terminal |
| **Ctrl+\\** | Toggle AI Panel |
| **Ctrl+S** | Save File |
| **Ctrl+N** | New File |
| **Ctrl+F** | Find |
| **Ctrl+H** | Replace |
| **F5** | Run Project |
| **Shift+F5** | Stop Process |
| **Ctrl+Shift+P** | Command Palette |
| **Ctrl+Shift+E** | Focus Explorer |
| **Ctrl+Shift+F** | Focus Search |

---

## 📁 FILE OPERATIONS

### Context Menu (Right-click)
- **New File...** — Create new file
- **New Folder...** — Create new folder
- **Rename...** — Rename file/folder
- **Duplicate** — Copy with auto-name
- **Delete...** — Delete (with confirmation)
- **Reveal in Explorer** — Open system explorer
- **Refresh** — Reload tree

### Usage
1. Right-click file/folder
2. Select operation
3. Follow prompts
4. Tree auto-refreshes

---

## 💻 TERMINAL

### Commands
- Type any shell command
- Press **Enter** to execute
- **Up/Down** arrows for history
- View output in real-time

### Features
- Command history (20 commands)
- Color-coded stderr (red)
- Working directory display
- Process control (stop/terminate)
- Clear output button

### Example
```bash
# Navigate
cd src

# Run Python
python main.py

# Install packages
pip install requests

# Git commands
git status
```

---

## ▶️ RUN PROJECTS

### Supported Languages/Frameworks

**Python**
- `python script.py`
- Django: `python manage.py runserver`
- FastAPI: Auto-detected

**JavaScript/Node**
- `node script.js`
- React: `npm start`
- Vite: `npm run dev`

**Other**
- TypeScript: `ts-node` or `npm run dev`
- Flutter: `flutter run`
- Rust: `cargo run`
- Go: `go run`
- C/C++: Compile + execute
- Java: `javac` + `java`

### Auto-Detection
Run Manager automatically detects:
- Entry points (main.py, index.js, etc.)
- Framework files (manage.py, package.json)
- Build configuration (Cargo.toml, pom.xml)

---

## 💾 SESSION MANAGEMENT

### Auto-Save
Session automatically saves:
- Open files list
- Cursor positions
- Active file
- Panel visibility
- Layout state

### Auto-Restore
On startup, restores:
- Last workspace
- All open files
- Cursor positions
- Window layout

### Workspace History
- Tracks last 20 workspaces
- Accessible via File menu
- Pin favorites for quick access

---

## 🎨 SYNTAX HIGHLIGHTING

### Supported Languages (30+)

**Systems**
- C, C++, C#
- Rust, Go
- Java, Kotlin
- Swift

**Web**
- JavaScript, TypeScript
- HTML, CSS, SCSS
- PHP, Ruby

**Scripting**
- Python
- Shell, PowerShell, Batch
- Lua, R

**Mobile**
- Dart, Flutter

**Data**
- JSON, YAML, XML, TOML
- SQL, INI

**Markup**
- Markdown
- Dockerfile, Makefile

---

## 🎯 FEATURES BY CATEGORY

### Workspace
- ✅ Open folder
- ✅ Recent projects (20)
- ✅ Pinned projects
- ✅ Workspace refresh
- ✅ Session persistence

### Editor
- ✅ Multi-file tabs
- ✅ Syntax highlighting
- ✅ Line numbers
- ✅ Current line highlight
- ✅ Find/Replace
- ✅ Undo/Redo
- ✅ Zoom

### Execution
- ✅ Auto-detect frameworks
- ✅ Run projects
- ✅ Output capture
- ✅ Error highlighting
- ✅ Stop processes

### UI
- ✅ Professional themes (5)
- ✅ Status bar
- ✅ Context menus
- ✅ Dialogs
- ✅ Notifications

---

## 🔧 COMMON TASKS

### Create New Project
```
1. File → Open Folder
2. Select/create directory
3. Right-click → New File
4. Create project files
5. Start coding
```

### Edit Existing Project
```
1. File → Open Folder
2. Select project directory
3. Explorer shows all files
4. Double-click to open
5. Edit and save
```

### Run and Debug
```
1. Open project
2. Click Run (F5)
3. View output
4. Fix errors
5. Run again
```

### Use Terminal
```
1. Press Ctrl+`
2. Type commands
3. View output
4. Navigate history
5. Stop if needed
```

---

## 🆘 TROUBLESHOOTING

### File Operations Not Working
- Check file permissions
- Ensure file exists
- Try refresh (F5)

### Terminal Not Executing
- Check command syntax
- Verify working directory
- Look for errors in output

### Syntax Highlighting Missing
- Check file extension
- Save file first
- Reopen if needed

### Session Not Restoring
- Check ~/.mycodingmaster/session.json
- Ensure workspace path is valid
- Try manual workspace open

---

## 📊 PERFORMANCE TIPS

1. **Large Projects**: Use workspace refresh sparingly
2. **Many Files**: Close unused tabs
3. **Terminal**: Clear output periodically
4. **Memory**: Restart IDE if sluggish
5. **Theme**: Use Dark theme for performance

---

## 🎓 BEST PRACTICES

### File Organization
```
project/
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
├── config/        # Configuration
└── README.md      # Project info
```

### Workflow
1. Open workspace once
2. Let session restore handle reopening
3. Use context menu for file operations
4. Use terminal for commands
5. Use Run button for execution

### Tips
- Pin frequently used workspaces
- Use keyboard shortcuts
- Keep terminal open
- Clear output regularly
- Save work frequently

---

## 📚 DOCUMENTATION

### Full Documentation
- `VERSION_1.6_FINAL_SUMMARY.md` — Complete overview
- `VERSION_1.6_COMPLETION_CERTIFICATE.md` — Official certification
- `VERSION_1.6_VISUAL_SUMMARY.md` — Visual guide
- `VERSION_1.6_EXECUTIVE_SUMMARY.md` — One-page overview
- `VERSION_1.6_FINAL_CHECKLIST.md` — Complete verification

### Component Documentation
- Each component has inline docstrings
- Check source files for API details
- EventBus events documented in code

---

## 🎯 SUPPORT

### Getting Help
1. Check this quick reference
2. Read full documentation
3. Check inline docstrings
4. Review example usage
5. Consult logs for errors

### Reporting Issues
1. Note exact steps to reproduce
2. Check log output
3. Verify file permissions
4. Test with simple example
5. Document error messages

---

## 🎉 YOU'RE READY!

MyCodingMaster Version 1.6 is a complete professional IDE.

Start coding and enjoy the experience!

---

*Quick Reference — Version 1.6*  
*Date: June 29, 2026*  
*Status: Production Ready*

**Happy Coding! 🚀**
