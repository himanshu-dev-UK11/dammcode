"""
Command Palette — v0.8

Ctrl+Shift+P style command palette with:
- Open File
- Open Folder
- Recent Projects
- Settings
- Run Command
- Search Files
- Search Symbols (placeholder)
- Search AI Commands
- Recent Commands

Keyboard navigation with arrow keys and enter.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QFrame, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QFocusEvent


class CommandItem(QListWidgetItem):
    """Single command item in the palette."""
    def __init__(self, text: str, subtitle: str = "", icon: str = "", command_type: str = "command"):
        super().__init__(text)
        self.subtitle = subtitle
        self.icon = icon
        self.command_type = command_type
        self.shortcut = ""
        
    def set_shortcut(self, shortcut: str):
        """Set keyboard shortcut for this command."""
        self.shortcut = shortcut


class CommandPalette(QWidget):
    """Command palette widget."""
    command_executed = Signal(str)  # command_id
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._recent_commands = []
        self._current_index = 0
        self._commands = []
        self._is_open = False
        self._parent_window = None
        
        from ui.design_system import get_design_system, Radius, FontSize, Spacing
        p = get_design_system().palette
        
        self.setObjectName("CommandPalette")
        self.setStyleSheet(f"""
            #CommandPalette {{
                background-color: {p.surface};
                border: 1px solid {p.border};
                border-radius: {Radius.XL}px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        
        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a command or search...")
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {p.bg};
                color: {p.text};
                border: 1px solid {p.border};
                border-radius: {Radius.SM}px;
                padding: 8px 12px;
                font-size: {FontSize.MD}px;
            }}
            QLineEdit:focus {{
                border-color: {p.accent};
            }}
        """)
        self._input.textChanged.connect(self._filter_commands)
        self._input.returnPressed.connect(self._execute_selected)
        self._input.setFocusPolicy(Qt.StrongFocus)
        layout.addWidget(self._input)
        
        self._list = QListWidget()
        self._list.setStyleSheet(f"""
            QListWidget {{
                background-color: {p.bg};
                border: 1px solid {p.border};
                border-radius: {Radius.SM}px;
                padding: {Spacing.XS}px;
                font-size: {FontSize.SM}px;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                min-height: 26px;
                border-radius: {Radius.SM}px;
                margin: 1px 2px;
            }}
            QListWidget::item:hover {{
                background-color: {p.surface_hover};
            }}
            QListWidget::item:selected {{
                background-color: {p.accent};
                color: {p.primary_text};
            }}
            QListWidget::item:selected:active {{
                background-color: {p.accent_active};
            }}
        """)
        self._list.itemSelectionChanged.connect(self._on_item_selected)
        self._list.itemDoubleClicked.connect(self._execute_selected)
        layout.addWidget(self._list)
        
        self._recent_section = QWidget()
        self._recent_section.setStyleSheet("background-color: transparent;")
        recent_layout = QVBoxLayout(self._recent_section)
        recent_layout.setContentsMargins(0, 0, 0, 0)
        recent_layout.setSpacing(4)
        
        recent_title = QLabel("RECENT COMMANDS")
        recent_title.setStyleSheet(f"""
            color: {p.text_tertiary};
            font-size: 9px;
            font-weight: 600;
            letter-spacing: 0.06em;
            background-color: transparent;
            padding: 4px 10px;
        """)
        recent_layout.addWidget(recent_title)
        
        self._recent_list = QListWidget()
        self._recent_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 4px 10px;
                min-height: 22px;
                border-radius: 2px;
            }
            QListWidget::item:hover {
                background-color: #1E3A5F;
                color: #E2E2E6;
            }
            QListWidget::item:selected {
                background-color: #3B82F6;
                color: white;
            }
        """)
        self._recent_list.itemClicked.connect(self._execute_recent)
        recent_layout.addWidget(self._recent_list)
        self._recent_section.setVisible(False)
        layout.addWidget(self._recent_section)
        
        footer = QWidget()
        footer.setStyleSheet("background-color: transparent;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(12)
        
        up_down = QLabel("↑↓ to navigate  ENTER to execute")
        up_down.setStyleSheet("""
            color: #52525C;
            font-size: 10px;
            background-color: transparent;
        """)
        footer_layout.addWidget(up_down)
        
        footer_layout.addStretch()
        
        esc = QLabel("ESC to close")
        esc.setStyleSheet("""
            color: #52525C;
            font-size: 10px;
            background-color: transparent;
        """)
        footer_layout.addWidget(esc)
        
        layout.addWidget(footer)
        
        self._setup_shortcuts()
        self._load_recent_commands()
        self._build_command_list()
        
        self.event_bus.subscribe("command_executed", self._on_command_executed)
        self.hide()
        
    def set_parent_window(self, parent):
        """Store reference to parent window for focus return."""
        self._parent_window = parent
        
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Esc to close
        QShortcut(QKeySequence("Esc"), self).activated.connect(self.close_palette)
        QShortcut(QKeySequence("Esc"), self._list).activated.connect(self.close_palette)
        QShortcut(QKeySequence("Esc"), self._input).activated.connect(self.close_palette)
        
    def _build_command_list(self):
        """Build the initial command list."""
        self._commands = []
        
        # File operations
        self._add_command("File: Open File", "Open a file from workspace", "📁", "file.open")
        self._add_command("File: Open Folder", "Open a project folder", "📂", "file.open_folder")
        self._add_command("File: New File", "Create a new file", "📄", "file.new")
        self._add_command("File: Save", "Save current file", "💾", "file.save")
        self._add_command("File: Save All", "Save all open files", "📚", "file.save_all")
        self._add_command("File: Close", "Close current file", "✕", "file.close")
        
        # Navigation
        self._add_command("Navigation: Go to Symbol", "Search symbols in workspace", "⭐", "nav.symbol")
        self._add_command("Navigation: Go to Line", "Jump to a specific line", "🔢", "nav.line")
        self._add_command("Navigation: Back", "Navigate back", "↩", "nav.back")
        self._add_command("Navigation: Forward", "Navigate forward", "↪", "nav.forward")
        
        # Workspace
        self._add_command("Workspace: Scan", "Scan workspace for files", "🔍", "workspace.scan")
        self._add_command("Workspace: Refresh", "Refresh workspace", "↻", "workspace.refresh")
        
        # AI
        self._add_command("AI: New Task", "Start a new AI task", "🤖", "ai.new_task")
        self._add_command("AI: Cancel", "Cancel current AI task", "🛑", "ai.cancel")
        self._add_command("AI: Conversation", "Start a conversation", "💬", "ai.conversation")
        
        # Run/Debug
        self._add_command("Run: Run File", "Run current file", "▶", "run.run")
        self._add_command("Run: Stop", "Stop running process", "⏹", "run.stop")
        self._add_command("Run: Debug", "Start debugging", "🐛", "run.debug")
        
        # Settings
        self._add_command("Settings: Open", "Open settings", "⚙", "settings.open")
        self._add_command("Settings: Keyboard", "Keyboard shortcuts", "⌨", "settings.keys")
        self._add_command("Settings: Themes", "Theme preferences", "🎨", "settings.theme")
        
        # View
        self._add_command("View: Toggle Explorer", "Show/hide explorer", "-sidebar", "view.explorer")
        self._add_command("View: Toggle Terminal", "Show/hide terminal", "console", "view.terminal")
        self._add_command("View: Toggle AI Workspace", "Show/hide AI panel", "pane", "view.ai")
        self._add_command("View: Toggle Fullscreen", "Fullscreen mode", "⛶", "view.fullscreen")
        
        # Search
        self._add_command("Search: Find", "Find in current file", "find", "search.find")
        self._add_command("Search: Replace", "Replace in current file", "replace", "search.replace")
        self._add_command("Search: Find in Files", "Find in workspace", "find_files", "search.files")
        
        # More commands (placeholder)
        for i in range(10):
            self._add_command(f"Command {i+1}: Placeholder", "This is a placeholder command", "📦", f"command.placeholder_{i+1}")
        
        # Update list
        self._filter_commands("")
        
    def _add_command(self, text: str, subtitle: str, icon: str, cmd_id: str):
        """Add a command to the list."""
        item = CommandItem(text, subtitle, icon, "command")
        item.setData(Qt.UserRole, cmd_id)
        self._commands.append(item)
        
    def _filter_commands(self, text: str):
        """Filter commands based on input text."""
        self._list.clear()
        
        text = text.lower().strip()
        
        if not text:
            # Show all commands
            for cmd in self._commands[:10]:
                self._list.addItem(cmd)
        else:
            # Filter commands
            filtered = []
            for cmd in self._commands:
                if text in cmd.text().lower() or text in cmd.subtitle.lower():
                    filtered.append(cmd)
            
            # Add recent commands if few results
            if len(filtered) < 5 and self._recent_commands:
                for recent_cmd in self._recent_commands[:5]:
                    if recent_cmd not in filtered:
                        item = CommandItem(f"Recent: {recent_cmd}", "Previously executed", "clock", "recent")
                        filtered.append(item)
            
            for cmd in filtered[:10]:
                self._list.addItem(cmd)
        
        # Select first item
        if self._list.count() > 0:
            self._list.setCurrentRow(0)
            self._current_index = 0
            
    def _on_item_selected(self):
        """Handle item selection change."""
        self._current_index = self._list.currentRow()
        
    def _execute_selected(self):
        """Execute the selected command."""
        item = self._list.currentItem()
        if item:
            cmd_id = item.data(Qt.UserRole)
            if cmd_id:
                self._record_command(item.text())
                # Close first, then emit
                self.close_palette()
                self.command_executed.emit(cmd_id)
                
    def _execute_recent(self, item):
        """Execute a recent command."""
        text = item.text()
        cmd_id = f"recent.{text}"
        self._record_command(text)
        self.command_executed.emit(cmd_id)
        self.close_palette()
        
    def _record_command(self, text: str):
        """Record a command as recent."""
        if text not in self._recent_commands:
            self._recent_commands.insert(0, text)
            self._recent_commands = self._recent_commands[:20]  # Keep last 20
            self._save_recent_commands()
        self._update_recent_list()
        
    def _update_recent_list(self):
        """Update the recent commands list."""
        self._recent_list.clear()
        for cmd in self._recent_commands[:5]:
            self._recent_list.addItem(cmd)
        self._recent_section.setVisible(len(self._recent_commands) > 0)
        
    def _load_recent_commands(self):
        """Load recent commands from config."""
        from pathlib import Path
        import json
        
        try:
            config_file = Path("config/recent_commands.json")
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    self._recent_commands = json.load(f)
                    self._update_recent_list()
        except Exception:
            pass
        
    def _save_recent_commands(self):
        """Save recent commands to config."""
        from pathlib import Path
        import json
        
        try:
            config_file = Path("config/recent_commands.json")
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(self._recent_commands, f, indent=2)
        except Exception:
            pass
    
    def _on_command_executed(self, data):
        """Handle command execution event."""
        cmd = data.get("command", "")
        if cmd:
            self._record_command(cmd)
            
    def show_palette(self):
        """Show the command palette."""
        if not self._is_open:
            self._is_open = True
            self.show()
            self.raise_()
            self.activateWindow()
            self._input.clear()
            self._input.setFocus()
            self._filter_commands("")
        
    def close_palette(self):
        """Close the command palette and return focus to editor."""
        if self._is_open:
            self._is_open = False
            self.hide()
            # Return focus to parent window's active widget
            if self._parent_window and hasattr(self._parent_window, 'center'):
                # Try to focus editor tabs first
                if hasattr(self._parent_window.center, 'editor_tabs'):
                    editor = self._parent_window.center.editor_tabs
                    if editor and editor.currentWidget():
                        editor.currentWidget().setFocus()
                        return
                # Fallback to center panel
                self._parent_window.center.setFocus()
            elif self._parent_window:
                self._parent_window.setFocus()
            
    def focusOutEvent(self, event):
        """Handle focus out - close palette when clicking outside."""
        # Only close if not clicking on any child widget
        if self._is_open:
            QTimer.singleShot(100, lambda: self._check_focus_lost())
        super().focusOutEvent(event)
        
    def _check_focus_lost(self):
        """Check if focus was lost and close palette."""
        if not self._is_open:
            return
        focus_widget = QApplication.focusWidget()
        # Close if focus is completely lost or moved to another window
        if focus_widget is None or (not self.isAncestorOf(focus_widget) and focus_widget != self):
            self.close_palette()
            
    def keyPressEvent(self, event):
        """Handle keyboard navigation."""
        key = event.key()
        
        # ESC always closes palette
        if key == Qt.Key_Escape:
            self.close_palette()
            return
            
        if key == Qt.Key_Down:
            if self._list.currentRow() < self._list.count() - 1:
                self._list.setCurrentRow(self._list.currentRow() + 1)
            elif self._list.count() > 0:
                self._list.setCurrentRow(0)  # Wrap to top
            return
            
        if key == Qt.Key_Up:
            if self._list.currentRow() > 0:
                self._list.setCurrentRow(self._list.currentRow() - 1)
            elif self._list.count() > 0:
                self._list.setCurrentRow(self._list.count() - 1)  # Wrap to bottom
            return
            
        if key == Qt.Key_PageDown and self._list.count() > 0:
            new_row = min(self._list.currentRow() + 5, self._list.count() - 1)
            self._list.setCurrentRow(new_row)
            return
            
        if key == Qt.Key_PageUp and self._list.count() > 0:
            new_row = max(self._list.currentRow() - 5, 0)
            self._list.setCurrentRow(new_row)
            return
        
        # Let parent handle other keys (input)
        super().keyPressEvent(event)
