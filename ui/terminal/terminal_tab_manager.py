"""
Terminal Tab Manager — v2.0 Production

Manages multiple terminal tabs with full production features:
- Multiple terminal tabs
- Tab reordering and renaming
- Duplicate terminal
- Close/kill/restart operations
- Split terminal support (horizontal/vertical)
- Active terminal tracking
- Search functionality
- Keyboard shortcuts
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                               QTabBar, QPushButton, QMenu, QInputDialog,
                               QSplitter, QLabel)
from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtGui import QKeySequence, QShortcut, QAction
from pathlib import Path
from typing import Dict, Optional, List
import uuid

from ui.terminal.terminal_widget import TerminalWidget
from ui.terminal.terminal_search_widget import TerminalSearchWidget
from core.logger import setup_logger

logger = setup_logger(__name__)


class TerminalTabBar(QTabBar):
    """Custom tab bar with right-click menu support."""
    
    tab_rename_requested = Signal(int)
    tab_duplicate_requested = Signal(int)
    tab_close_all_requested = Signal()
    tab_close_others_requested = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _show_context_menu(self, pos):
        """Show context menu for tab."""
        index = self.tabAt(pos)
        if index < 0:
            return
        
        menu = QMenu(self)
        
        # Rename action
        rename_action = QAction("Rename Terminal", self)
        rename_action.triggered.connect(lambda: self.tab_rename_requested.emit(index))
        menu.addAction(rename_action)
        
        # Duplicate action
        duplicate_action = QAction("Duplicate Terminal", self)
        duplicate_action.triggered.connect(lambda: self.tab_duplicate_requested.emit(index))
        menu.addAction(duplicate_action)
        
        menu.addSeparator()
        
        # Close actions
        close_action = QAction("Close Terminal", self)
        close_action.triggered.connect(lambda: self.parent().removeTab(index))
        menu.addAction(close_action)
        
        close_others_action = QAction("Close Other Terminals", self)
        close_others_action.triggered.connect(lambda: self.tab_close_others_requested.emit(index))
        menu.addAction(close_others_action)
        
        close_all_action = QAction("Close All Terminals", self)
        close_all_action.triggered.connect(self.tab_close_all_requested.emit)
        menu.addAction(close_all_action)
        
        menu.exec(self.mapToGlobal(pos))


class TerminalSplitWidget(QWidget):
    """Widget that holds a split terminal layout."""
    
    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.terminals: List[TerminalWidget] = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.splitter = QSplitter(orientation)
        layout.addWidget(self.splitter)
    
    def add_terminal(self, terminal: TerminalWidget):
        """Add a terminal to the split."""
        self.terminals.append(terminal)
        self.splitter.addWidget(terminal)
        
        # Set equal sizes
        if len(self.terminals) > 1:
            sizes = [100 // len(self.terminals)] * len(self.terminals)
            self.splitter.setSizes(sizes)
    
    def remove_terminal(self, terminal: TerminalWidget):
        """Remove a terminal from the split."""
        if terminal in self.terminals:
            self.terminals.remove(terminal)
            terminal.setParent(None)
            terminal.deleteLater()
    
    def get_active_terminal(self) -> Optional[TerminalWidget]:
        """Get the currently active terminal in the split."""
        if self.terminals:
            return self.terminals[0]
        return None
    
    def set_orientation(self, orientation: Qt.Orientation):
        """Change split orientation."""
        self.orientation = orientation
        self.splitter.setOrientation(orientation)


class TerminalTabManager(QWidget):
    """
    Manages multiple terminal tabs with full production features.
    
    Features:
    - Multiple terminal tabs
    - Tab operations (new, close, rename, duplicate)
    - Split terminals (horizontal/vertical)
    - Keyboard shortcuts
    - Context menus
    - Session persistence
    """
    
    # Signals
    terminal_created = Signal(str)  # session_id
    terminal_closed = Signal(str)   # session_id
    terminal_activated = Signal(str)  # session_id
    all_terminals_closed = Signal()
    
    def __init__(self, event_bus, working_dir: Path, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        self.working_dir = working_dir
        self.settings = QSettings("MyCodingMaster", "TerminalTabs")
        
        # State
        self.terminals: Dict[str, TerminalWidget] = {}
        self.tab_to_session: Dict[int, str] = {}  # tab_index -> session_id
        self.session_to_tab: Dict[str, int] = {}  # session_id -> tab_index
        self.active_session_id: Optional[str] = None
        self.terminal_counter = 0
        
        # Default shell
        self.default_shell = self._detect_default_shell()
        
        self.setup_ui()
        self.setup_shortcuts()
        
        # Create initial terminal
        self.create_terminal()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabBar().setElideMode(Qt.TextElideMode.ElideRight)
        self.tabs.tabBar().setUsesScrollButtons(True)
        
        # Use custom tab bar
        custom_tab_bar = TerminalTabBar()
        custom_tab_bar.tab_rename_requested.connect(self._rename_tab)
        custom_tab_bar.tab_duplicate_requested.connect(self._duplicate_tab)
        custom_tab_bar.tab_close_all_requested.connect(self.close_all_terminals)
        custom_tab_bar.tab_close_others_requested.connect(self._close_other_tabs)
        self.tabs.setTabBar(custom_tab_bar)
        
        # Apply styling
        self._apply_tab_styling()
        
        # Connect signals
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.tabs.tabCloseRequested.connect(self._on_tab_close_requested)
        
        layout.addWidget(self.tabs)
        
        # Search widget (hidden by default)
        self.search_widget = TerminalSearchWidget(self)
        self.search_widget.hide()
        self.search_widget.search_requested.connect(self._on_search_requested)
        self.search_widget.find_next_requested.connect(self._on_find_next)
        self.search_widget.find_previous_requested.connect(self._on_find_previous)
        self.search_widget.search_closed.connect(self._on_search_closed)
        layout.addWidget(self.search_widget)
    
    def _apply_tab_styling(self):
        """Apply styling to tabs."""
        from ui.design_system import get_design_system, FontSize
        p = get_design_system().palette
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {p.bg};
            }}
            QTabBar {{
                background-color: {p.bg_secondary};
                border-bottom: 1px solid {p.border_subtle};
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {p.text_tertiary};
                padding: 8px 12px;
                border: none;
                border-right: 1px solid {p.border_subtle};
                font-size: {FontSize.SM}px;
                font-weight: 500;
                min-width: 92px;
                min-height: 28px;
            }}
            QTabBar::tab:selected {{
                color: {p.text};
                border-bottom: 2px solid {p.accent};
                background-color: {p.bg};
            }}
            QTabBar::tab:hover:!selected {{
                color: {p.text_secondary};
                background-color: {p.surface_hover};
            }}
            QTabBar::close-button {{
                image: none;
                background-color: transparent;
                border: none;
                width: 14px;
                height: 14px;
                margin-left: 6px;
                border-radius: 3px;
            }}
            QTabBar::close-button:hover {{
                background-color: rgba(239, 68, 68, 0.5);
                border-radius: 3px;
            }}
        """)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Ctrl+Shift+` - New Terminal
        QShortcut(QKeySequence("Ctrl+Shift+`"), self, self.create_terminal)
        
        # Ctrl+Shift+W - Close Current Terminal
        QShortcut(QKeySequence("Ctrl+Shift+W"), self, self.close_current_terminal)
        
        # Ctrl+Shift+T - Reopen Closed Terminal
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, self.reopen_closed_terminal)
        
        # Ctrl+Tab - Next Terminal
        QShortcut(QKeySequence("Ctrl+Tab"), self, self.focus_next_terminal)
        
        # Ctrl+Shift+Tab - Previous Terminal
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self, self.focus_previous_terminal)
        
        # Ctrl+Shift+5 - Split Terminal Horizontally
        QShortcut(QKeySequence("Ctrl+Shift+5"), self, 
                 lambda: self.split_terminal(Qt.Orientation.Horizontal))
        
        # Ctrl+Shift+\ - Split Terminal Vertically
        QShortcut(QKeySequence("Ctrl+Shift+\\"), self, 
                 lambda: self.split_terminal(Qt.Orientation.Vertical))
        
        # Ctrl+Shift+K - Kill Terminal
        QShortcut(QKeySequence("Ctrl+Shift+K"), self, self.kill_current_terminal)
        
        # Ctrl+F - Find in Terminal
        QShortcut(QKeySequence("Ctrl+F"), self, self.show_search)
    
    def _detect_default_shell(self) -> str:
        """Detect the default shell for the system."""
        import sys
        import shutil
        
        if sys.platform == "win32":
            if shutil.which("powershell.exe"):
                return "powershell"
            return "cmd"
        else:
            # Check for common shells in order of preference
            for shell in ["bash", "zsh", "fish", "sh"]:
                if shutil.which(shell):
                    return shell
            return "bash"
    
    def create_terminal(self, shell: Optional[str] = None, 
                       working_dir: Optional[Path] = None,
                       title: Optional[str] = None) -> str:
        """Create a new terminal tab."""
        self.terminal_counter += 1
        session_id = str(uuid.uuid4())
        
        # Create terminal widget
        terminal = TerminalWidget(
            session_id=session_id,
            working_dir=working_dir or self.working_dir,
            shell=shell or self.default_shell,
            parent=self
        )
        
        # Connect signals
        terminal.process_finished.connect(
            lambda ec, dur: self._on_process_finished(session_id, ec, dur)
        )
        
        # Store terminal
        self.terminals[session_id] = terminal
        
        # Add tab
        tab_title = title or f"Terminal {self.terminal_counter}"
        tab_index = self.tabs.addTab(terminal, tab_title)
        
        # Update mappings
        self.tab_to_session[tab_index] = session_id
        self.session_to_tab[session_id] = tab_index
        self.active_session_id = session_id
        
        # Switch to new tab
        self.tabs.setCurrentIndex(tab_index)
        
        # Emit signal
        self.terminal_created.emit(session_id)
        self.event_bus.publish("terminal_created", {
            "session_id": session_id,
            "shell": shell or self.default_shell,
            "working_directory": str(working_dir or self.working_dir)
        })
        
        logger.info(f"Created terminal: {session_id} ({tab_title})")
        return session_id
    
    def close_terminal(self, session_id: str):
        """Close a terminal by session ID."""
        if session_id not in self.terminals:
            return
        
        terminal = self.terminals[session_id]
        tab_index = self.session_to_tab.get(session_id)
        
        if tab_index is not None:
            # Terminate shell
            terminal.terminate()
            
            # Remove tab
            self.tabs.removeTab(tab_index)
            
            # Update mappings
            del self.tab_to_session[tab_index]
            del self.session_to_tab[session_id]
            
            # Remove terminal
            del self.terminals[session_id]
            terminal.deleteLater()
            
            # Emit signal
            self.terminal_closed.emit(session_id)
            self.event_bus.publish("terminal_closed", {
                "session_id": session_id
            })
            
            logger.info(f"Closed terminal: {session_id}")
            
            # Check if all terminals closed
            if not self.terminals:
                self.all_terminals_closed.emit()
    
    def close_current_terminal(self):
        """Close the currently active terminal."""
        if self.active_session_id:
            self.close_terminal(self.active_session_id)
    
    def close_all_terminals(self):
        """Close all terminal tabs."""
        session_ids = list(self.terminals.keys())
        for session_id in session_ids:
            self.close_terminal(session_id)
    
    def kill_current_terminal(self):
        """Force kill the current terminal."""
        if self.active_session_id and self.active_session_id in self.terminals:
            terminal = self.terminals[self.active_session_id]
            terminal.kill()
    
    def restart_current_terminal(self):
        """Restart the current terminal."""
        if self.active_session_id and self.active_session_id in self.terminals:
            terminal = self.terminals[self.active_session_id]
            terminal.restart()
    
    def duplicate_terminal(self, session_id: Optional[str] = None) -> str:
        """Duplicate a terminal (same shell and working directory)."""
        source_id = session_id or self.active_session_id
        if not source_id or source_id not in self.terminals:
            return self.create_terminal()
        
        source_terminal = self.terminals[source_id]
        return self.create_terminal(
            shell=source_terminal.shell_name,
            working_dir=source_terminal.working_dir
        )
    
    def split_terminal(self, orientation: Qt.Orientation):
        """Split the current terminal."""
        if not self.active_session_id or self.active_session_id not in self.terminals:
            return
        
        current_tab_index = self.tabs.currentIndex()
        current_widget = self.tabs.widget(current_tab_index)
        
        # Check if already a split
        if isinstance(current_widget, TerminalSplitWidget):
            # Add to existing split
            new_terminal = TerminalWidget(
                session_id=str(uuid.uuid4()),
                working_dir=self.working_dir,
                shell=self.default_shell
            )
            current_widget.add_terminal(new_terminal)
        else:
            # Create new split
            split_widget = TerminalSplitWidget(orientation)
            
            # Remove current terminal from tab
            self.tabs.removeTab(current_tab_index)
            
            # Add both terminals to split
            split_widget.add_terminal(current_widget)
            
            new_session_id = str(uuid.uuid4())
            new_terminal = TerminalWidget(
                session_id=new_session_id,
                working_dir=self.working_dir,
                shell=self.default_shell
            )
            split_widget.add_terminal(new_terminal)
            
            # Add split widget back to tab
            self.tabs.insertTab(current_tab_index, split_widget, 
                              self.tabs.tabText(current_tab_index) or "Terminal")
            self.tabs.setCurrentIndex(current_tab_index)
    
    def focus_next_terminal(self):
        """Focus the next terminal tab."""
        current = self.tabs.currentIndex()
        next_index = (current + 1) % self.tabs.count()
        self.tabs.setCurrentIndex(next_index)
    
    def focus_previous_terminal(self):
        """Focus the previous terminal tab."""
        current = self.tabs.currentIndex()
        prev_index = (current - 1) % self.tabs.count()
        self.tabs.setCurrentIndex(prev_index)
    
    def rename_terminal(self, session_id: str, new_title: str):
        """Rename a terminal tab."""
        if session_id in self.session_to_tab:
            tab_index = self.session_to_tab[session_id]
            self.tabs.setTabText(tab_index, new_title)
    
    def get_terminal(self, session_id: str) -> Optional[TerminalWidget]:
        """Get terminal by session ID."""
        return self.terminals.get(session_id)
    
    def get_active_terminal(self) -> Optional[TerminalWidget]:
        """Get the currently active terminal."""
        if self.active_session_id:
            return self.terminals.get(self.active_session_id)
        return None
    
    def get_all_terminals(self) -> List[TerminalWidget]:
        """Get all terminal widgets."""
        return list(self.terminals.values())
    
    def reopen_closed_terminal(self):
        """Reopen the last closed terminal (placeholder for future enhancement)."""
        # TODO: Store closed terminal history and reopen
        self.create_terminal()
    
    def _rename_tab(self, tab_index: int):
        """Show rename dialog for a tab."""
        current_title = self.tabs.tabText(tab_index)
        new_title, ok = QInputDialog.getText(
            self,
            "Rename Terminal",
            "Enter new terminal name:",
            text=current_title
        )
        
        if ok and new_title:
            self.tabs.setTabText(tab_index, new_title)
            session_id = self.tab_to_session.get(tab_index)
            if session_id:
                self.event_bus.publish("terminal_renamed", {
                    "session_id": session_id,
                    "title": new_title
                })
    
    def _duplicate_tab(self, tab_index: int):
        """Duplicate a terminal tab."""
        session_id = self.tab_to_session.get(tab_index)
        if session_id:
            self.duplicate_terminal(session_id)
    
    def _close_other_tabs(self, keep_index: int):
        """Close all tabs except the specified one."""
        session_id_to_keep = self.tab_to_session.get(keep_index)
        session_ids = [sid for sid in self.terminals.keys() if sid != session_id_to_keep]
        
        for session_id in session_ids:
            self.close_terminal(session_id)
    
    def _on_tab_changed(self, index: int):
        """Handle tab change."""
        if index >= 0:
            session_id = self.tab_to_session.get(index)
            if session_id:
                self.active_session_id = session_id
                self.terminal_activated.emit(session_id)
    
    def _on_tab_close_requested(self, index: int):
        """Handle tab close request."""
        session_id = self.tab_to_session.get(index)
        if session_id:
            self.close_terminal(session_id)
    
    def _on_process_finished(self, session_id: str, exit_code: int, duration_ms: int):
        """Handle process finish."""
        self.event_bus.publish("process_finished", {
            "session_id": session_id,
            "exit_code": exit_code,
            "duration_ms": duration_ms
        })
    
    def set_working_directory(self, directory: Path):
        """Set working directory for all terminals."""
        self.working_dir = directory
        for terminal in self.terminals.values():
            terminal.set_working_directory(directory)
    
    def clear_current_terminal(self):
        """Clear the current terminal output."""
        if self.active_session_id and self.active_session_id in self.terminals:
            terminal = self.terminals[self.active_session_id]
            terminal.clear()
    
    def execute_command(self, command: str):
        """Execute a command in the active terminal."""
        if self.active_session_id and self.active_session_id in self.terminals:
            terminal = self.terminals[self.active_session_id]
            terminal.execute_command(command)
    
    # Search functionality
    
    def show_search(self):
        """Show the search widget."""
        self.search_widget.show_search()
    
    def hide_search(self):
        """Hide the search widget."""
        self.search_widget.hide_search()
    
    def _on_search_requested(self, query: str, case_sensitive: bool, 
                            whole_word: bool, regex: bool):
        """Handle search request."""
        terminal = self.get_active_terminal()
        if terminal:
            # Perform search in terminal
            found = terminal.search_text(query, case_sensitive)
            # Update match count (simplified - would need full implementation)
            self.search_widget.update_match_count(1 if found else 0, 1 if found else 0)
    
    def _on_find_next(self):
        """Find next match."""
        terminal = self.get_active_terminal()
        if terminal:
            query = self.search_widget.get_search_query()
            case_sensitive = self.search_widget.is_case_sensitive()
            terminal.find_next(query, case_sensitive)
    
    def _on_find_previous(self):
        """Find previous match."""
        terminal = self.get_active_terminal()
        if terminal:
            query = self.search_widget.get_search_query()
            case_sensitive = self.search_widget.is_case_sensitive()
            terminal.find_previous(query, case_sensitive)
    
    def _on_search_closed(self):
        """Handle search widget closed."""
        # Return focus to terminal
        terminal = self.get_active_terminal()
        if terminal:
            terminal.setFocus()
