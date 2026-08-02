"""
Multi-tab editor interface with professional IDE features.
Integrated: Breadcrumb, Minimap, Line Highlighting, Indent Guides, Bracket Matching,
Sticky Tabs, Tab Operations, Split Editor support.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QMenu, QSplitter, QHBoxLayout, QTabBar
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QTextDocument, QTextCursor, QKeySequence, QAction, QShortcut, QRegularExpression
from PySide6.QtGui import QMouseEvent

from ui.editor.code_editor import CodeEditor
from ui.editor.search_replace import SearchReplaceWidget
from ui.editor.language_support import get_language_id_for_file
from ui.editor.breadcrumb_bar import BreadcrumbNavigation
from ui.editor.minimap import MinimapPanel
from ui.editor.highlighter import HighlightManager
from ui.editor.indent_guides import IndentGuideManager
from ui.editor.bracket_matcher import BracketMatcher
from ui.editor.sticky_tabs import StickyTabManager
from ui.editor.tab_operations import TabOperationsManager
from ui.editor.splitted_editor import SplitEditorManager
from core.logger import setup_logger

logger = setup_logger(__name__)


class EditorTabBar(QTabBar):
    """Tab bar with middle-click close support and room for IDE-style actions."""

    middle_clicked = Signal(int)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            index = self.tabAt(event.position().toPoint())
            if index >= 0:
                self.middle_clicked.emit(index)
                event.accept()
                return
        super().mouseReleaseEvent(event)


class EditorTabs(QWidget):
    """Professional multi-tab editor with IDE features."""
    
    # Signals
    tab_pinned = Signal(str)
    tab_unpinned = Signal(str)
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self.editors = {}  # path_str -> CodeEditor
        self.pinned_tabs = set()  # paths of pinned tabs
        self._editor_states = {}
        self._closed_tabs = []
        self._search_state = None
        self._session_state = {
            "open_tabs": [],
            "active_tab": None,
            "tabs": {},
            "splits": [],
        }
        self._session_loaded = False
        self.lsp_manager = None
        
        # Feature managers
        self.breadcrumb = None
        self.minimap = None
        self.highlight_manager = None
        self.indent_manager = None
        self.bracket_matcher = None
        self.sticky_tab_manager = None
        self.tab_operations = None
        self.split_manager = None
        
        self.setup_ui()
        self.setup_connections()

        # Subscribe to save events to clear modified indicator
        self.event_bus.subscribe("editor_saved", self._on_editor_saved_event)

    def setup_ui(self):
        """Setup the main UI layout with all features."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top: Search Widget (Overlay style)
        self.search_widget = SearchReplaceWidget()
        layout.addWidget(self.search_widget)
        self.search_widget.hide()

        # Main content area with splitter for minimap
        content_splitter = QSplitter(self)
        content_splitter.setOrientation(Qt.Horizontal)
        content_splitter.setHandleWidth(2)
        # Splitter handle color driven by global stylesheet (QSplitter::handle)
        layout.addWidget(content_splitter)

        # Left: Editor (default, can add minimap to right)
        self.editor_container = QWidget()
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add breadcrumb navigation
        self.breadcrumb = BreadcrumbNavigation()
        self.breadcrumb.path_navigated.connect(self._on_breadcrumb_navigated)
        self.breadcrumb.symbol_selected.connect(self._on_symbol_selected)
        editor_layout.addWidget(self.breadcrumb)

        # Tabs widget (premium styling via global QSS + minimal inline customization)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs.setTabBar(EditorTabBar())
        self.tabs.tabBar().setElideMode(Qt.TextElideMode.ElideRight)
        self.tabs.tabBar().setUsesScrollButtons(True)
        # Tab styling is now primarily driven by ThemeManager global QSS
        self.tabs.setStyleSheet("")
        editor_layout.addWidget(self.tabs)

        content_splitter.addWidget(self.editor_container)

        # Right: Minimap (optional, hidden by default)
        self.minimap_panel = MinimapPanel()
        self.minimap_panel.setVisible(False)
        content_splitter.addWidget(self.minimap_panel)
        content_splitter.setSizes([400, 120])  # Default: 400px editor, 120px minimap

        # Set proportional resize policy
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 0)

    def setup_connections(self):
        """Setup signal connections."""
        # Tab signals
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.tabs.customContextMenuRequested.connect(self._show_tab_context_menu)
        
        # Search widget signals
        self.search_widget.find_requested.connect(self.find_text)
        self.search_widget.replace_requested.connect(self.replace_text)
        self.search_widget.replace_all_requested.connect(self.replace_all_text)
        
        # Minimap toggle
        QShortcut(QKeySequence("Alt+M"), self, self.toggle_minimap)

        # Ctrl+F — show find bar
        QShortcut(QKeySequence("Ctrl+F"), self, self._show_search)
        # Ctrl+H — show replace bar (same widget, just visible)
        QShortcut(QKeySequence("Ctrl+H"), self, self._show_search)
        # Escape — hide find bar
        QShortcut(QKeySequence("Escape"), self, self._hide_search)
        
        # Connect editor signals for comprehensive event publishing
        self.tabs.tabBar().tabMoved.connect(self._on_tab_reordered)
        self.tabs.tabBar().tabBarClicked.connect(self._on_tab_clicked)
        self.tabs.tabBar().tabBarDoubleClicked.connect(self._on_tab_double_clicked)
        if isinstance(self.tabs.tabBar(), EditorTabBar):
            self.tabs.tabBar().middle_clicked.connect(self.close_tab)

        # Session lifecycle
        self.event_bus.subscribe("editor_session_loaded", self._on_editor_session_loaded)
        self.event_bus.subscribe("editor_session_updated", self._on_editor_session_updated)

    def _show_search(self):
        """Show the find/replace bar and focus it."""
        self.search_widget.show()
        self.search_widget.find_input.setFocus()
        self.search_widget.find_input.selectAll()

    def _hide_search(self):
        """Hide the find/replace bar."""
        self.search_widget.hide()
        editor = self.get_current_editor()
        if editor:
            editor.setFocus()

    # ── Breadcrumb Navigation ──────────────────────────────────────────────
    def update_breadcrumb(self, file_path: str, symbol_name: str = None):
        """Update breadcrumb navigation."""
        if self.breadcrumb:
            self.breadcrumb.update_breadcrumbs(file_path, symbol_name)

    def _on_breadcrumb_navigated(self, path: str, segment_type: str):
        """Handle breadcrumb navigation."""
        self.event_bus.publish("breadcrumb_navigated", {
            "path": path,
            "segment_type": segment_type
        })

    def _on_symbol_selected(self, symbol_name: str):
        """Handle symbol selection from breadcrumb."""
        self.event_bus.publish("symbol_selected", {"symbol_name": symbol_name})

    # ── Minimap ────────────────────────────────────────────────────────────
    def toggle_minimap(self):
        """Toggle minimap visibility."""
        if self.minimap_panel:
            self.minimap_panel.toggle_visibility()
            self.event_bus.publish("minimap_visible_changed", {
                "visible": self.minimap_panel.is_visible()
            })

    def set_editor_for_minimap(self, editor: CodeEditor):
        """Set editor for minimap to mirror."""
        if self.minimap_panel:
            self.minimap_panel.set_editor(editor)

    # ── Line Highlighting ──────────────────────────────────────────────────
    def setup_highlight_manager(self, editor: CodeEditor):
        """Setup highlighting manager for an editor."""
        if not self.highlight_manager:
            self.highlight_manager = HighlightManager(editor)
        return self.highlight_manager

    def toggle_current_line_highlight(self, editor: CodeEditor, enabled: bool):
        """Toggle current line highlight for editor."""
        if self.highlight_manager:
            self.highlight_manager.set_highlight_current_line(enabled)

    def toggle_line_number_highlight(self, editor: CodeEditor, enabled: bool):
        """Toggle line number highlight for editor."""
        if self.highlight_manager:
            self.highlight_manager.set_highlight_line_number(enabled)

    def toggle_matching_brackets(self, editor: CodeEditor, enabled: bool):
        """Toggle matching bracket highlighting."""
        if self.highlight_manager:
            self.highlight_manager.set_highlight_matching_brackets(enabled)

    # ── Bracket Matching ───────────────────────────────────────────────────
    def setup_bracket_matcher(self, editor: CodeEditor):
        """Setup bracket matcher for an editor."""
        if not self.bracket_matcher:
            self.bracket_matcher = BracketMatcher(editor)
        return self.bracket_matcher

    def highlight_brackets(self, editor: CodeEditor):
        """Highlight matching brackets around cursor."""
        if self.bracket_matcher:
            self.bracket_matcher.highlight_matching_brackets()

    # ── Indent Guides ──────────────────────────────────────────────────────
    def setup_indent_manager(self, editor: CodeEditor, overlay_widget: QWidget):
        """Setup indent guide manager."""
        if not self.indent_manager:
            self.indent_manager = IndentGuideManager(editor)
            self.indent_manager.set_parent(overlay_widget)
        return self.indent_manager

    def toggle_indent_guides(self, enabled: bool):
        """Toggle indent guide visibility."""
        if self.indent_manager:
            self.indent_manager.set_enabled(enabled)

    # ── Sticky Tabs ────────────────────────────────────────────────────────
    def setup_sticky_tab_manager(self):
        """Setup sticky tab manager."""
        return None

    def _on_tab_pinned(self, path: str):
        """Handle tab pinned event."""
        self.pinned_tabs.add(path)
        self.tab_pinned.emit(path)
        self.event_bus.publish("editor_tab_pinned", {"path": path})

    def _on_tab_unpinned(self, path: str):
        """Handle tab unpinned event."""
        self.pinned_tabs.discard(path)
        self.tab_unpinned.emit(path)
        self.event_bus.publish("editor_tab_unpinned", {"path": path})

    def _tab_label(self, path_str: str, editor: CodeEditor = None):
        name = Path(path_str).name if path_str else "Untitled"
        if editor and editor.isReadOnly():
            return f"{name} 🔒"
        if path_str in self.pinned_tabs:
            return f"📌 {name}"
        if editor and editor.document().isModified():
            return f"{name} ●"
        return name

    def _update_tab_labels(self):
        for path_str, editor in self.editors.items():
            idx = self.tabs.indexOf(editor)
            if idx >= 0:
                self.tabs.setTabText(idx, self._tab_label(path_str, editor))

    def is_tab_pinned(self, tab_index: int) -> bool:
        """Check if tab is pinned."""
        path = self._get_tab_path(tab_index)
        return bool(path and path in self.pinned_tabs)

    def toggle_pin_tab(self, tab_index: int):
        """Toggle tab pin state."""
        path = self._get_tab_path(tab_index)
        if not path:
            return

        if path in self.pinned_tabs:
            self._on_tab_unpinned(path)
        else:
            self._on_tab_pinned(path)
        self._update_tab_labels()

    # ── Tab Operations ─────────────────────────────────────────────────────
    def setup_tab_operations(self):
        """Setup tab operations manager."""
        return None

    def duplicate_tab(self, tab_index: int = None):
        """Duplicate current tab."""
        if tab_index is None:
            tab_index = self.tabs.currentIndex()
        if tab_index < 0:
            return

        original = self.tabs.widget(tab_index)
        if not original:
            return

        duplicate = CodeEditor(None, self.event_bus)
        duplicate.load_file(original.toPlainText())
        duplicate.document().setModified(original.document().isModified())
        duplicate.cursor_position_changed.connect(self.on_cursor_moved)

        title = self.tabs.tabText(tab_index)
        new_index = self.tabs.insertTab(tab_index + 1, duplicate, f"{title} (Copy)")
        self.tabs.setCurrentIndex(new_index)
        duplicate.setFocus()
        self.event_bus.publish("editor_duplicate_tab", {})

    def close_others(self, keep_index: int = None):
        """Close all tabs except one."""
        if keep_index is None:
            keep_index = self.tabs.currentIndex()
        for i in reversed(range(self.tabs.count())):
            if i != keep_index:
                self.close_tab(i)
        self.event_bus.publish("editor_close_others", {})

    def close_left(self, current_index: int = None):
        """Close tabs to the left."""
        if current_index is None:
            current_index = self.tabs.currentIndex()
        for i in reversed(range(current_index)):
            self.close_tab(i)
        self.event_bus.publish("editor_close_left", {})

    def close_right(self, current_index: int = None):
        """Close tabs to the right."""
        if current_index is None:
            current_index = self.tabs.currentIndex()
        for i in reversed(range(current_index + 1, self.tabs.count())):
            self.close_tab(i)
        self.event_bus.publish("editor_close_right", {})

    def reopen_closed_tab(self):
        """Reopen the most recently closed tab."""
        if not self._closed_tabs:
            return

        index, path_str, title, state, content = self._closed_tabs.pop()
        if path_str and path_str in self.editors:
            self.tabs.setCurrentIndex(self.tabs.indexOf(self.editors[path_str]))
            return

        editor = CodeEditor(path_str, self.event_bus)
        editor.state_changed.connect(lambda state_data, p=path_str: self._on_editor_state_changed(p, state_data))
        if state:
            editor.set_pending_restore_state(state)
        editor.load_file(content)
        if path_str:
            self.editors[path_str] = editor
            self._editor_states[path_str] = state or {}

        new_index = min(index, self.tabs.count())
        self.tabs.insertTab(new_index, editor, title)
        self.tabs.setCurrentIndex(new_index)
        editor.setFocus()
        self.event_bus.publish("editor_reopen_tab", {})
        self._publish_session_update()

    # ── Search Replace ─────────────────────────────────────────────────────
    def find_text(self, text: str, forward: bool, case_sensitive: bool, regex: bool):
        """Find text in current editor and move cursor to match."""
        editor = self.get_current_editor()
        if not editor or not text:
            return

        self._search_state = {
            "find": text,
            "forward": forward,
            "case_sensitive": case_sensitive,
            "regex": regex,
        }

        flags = QTextDocument.FindFlags()
        if not forward:
            flags |= QTextDocument.FindBackward
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively

        found = editor.document().find(text, editor.textCursor(), flags)
        if found.isNull():
            # Wrap around
            wrap_cursor = editor.textCursor()
            wrap_cursor.movePosition(
                QTextCursor.Start if forward else QTextCursor.End
            )
            found = editor.document().find(text, wrap_cursor, flags)

        if not found.isNull():
            editor.setTextCursor(found)
            editor.ensureCursorVisible()
        self._highlight_search_results(editor, text, case_sensitive, regex)
        self._publish_session_update()

    def replace_text(self, find: str, replace: str, forward: bool, case_sensitive: bool, regex: bool):
        """Replace the current selection if it matches, then find next."""
        editor = self.get_current_editor()
        if not editor or not find:
            return

        cursor = editor.textCursor()
        if cursor.hasSelection():
            sel = cursor.selectedText()
            if (sel.lower() == find.lower() and not case_sensitive) or sel == find:
                cursor.insertText(replace)

        self.find_text(find, forward, case_sensitive, regex)
        self._publish_session_update()

    def replace_all_text(self, find: str, replace: str, case_sensitive: bool, regex: bool):
        """Replace all occurrences of find with replace in the current editor."""
        editor = self.get_current_editor()
        if not editor or not find:
            return

        flags = QTextDocument.FindFlags()
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively

        cursor = editor.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.Start)
        editor.setTextCursor(cursor)

        count = 0
        while True:
            found = editor.document().find(find, editor.textCursor(), flags)
            if found.isNull():
                break
            found.insertText(replace)
            editor.setTextCursor(found)
            count += 1

        cursor.endEditBlock()
        if count:
            self.event_bus.publish("log_message", {
                "message": f"Replaced {count} occurrence(s) of '{find}'"
            })
        self._highlight_search_results(editor, find, case_sensitive, regex)
        self._publish_session_update()

    def _build_session_snapshot(self):
        open_tabs = list(self.editors.keys())
        active_editor = self.get_current_editor()
        active_path = getattr(active_editor, "file_path", None) if active_editor else None
        return {
            "open_tabs": open_tabs,
            "active_tab": active_path,
            "tabs": dict(self._editor_states),
            "splits": self._session_state.get("splits", []),
            "search": self._search_state,
        }

    def _publish_session_update(self):
        self.event_bus.publish("editor_session_updated", self._build_session_snapshot())

    def _on_editor_session_loaded(self, data: dict):
        self._session_state = data or self._session_state
        self._editor_states = dict(self._session_state.get("tabs", {}))
        self._session_loaded = True

    def _on_editor_session_updated(self, data: dict):
        if not data:
            return
        self._session_state = data
        tabs = data.get("tabs", {})
        if isinstance(tabs, dict):
            self._editor_states.update(tabs)

    def _on_editor_state_changed(self, path_str: str, state: dict):
        if not path_str:
            return
        self._editor_states[path_str] = state or {}
        self._publish_session_update()

    def _restore_editor_state(self, editor: CodeEditor, path_str: str):
        state = self._editor_states.get(path_str)
        if state:
            editor.restore_state(state)

    def _highlight_search_results(self, editor: CodeEditor, text: str, case_sensitive: bool, regex: bool):
        if not editor or not text:
            editor.set_search_highlights([])
            return

        selections = []
        cursor = QTextCursor(editor.document())
        flags = QTextDocument.FindFlags()
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively

        pattern = QRegularExpression(text) if regex else None
        if pattern and not pattern.isValid():
            editor.set_search_highlights([])
            return

        cursor.movePosition(QTextCursor.Start)
        while True:
            if regex and pattern is not None:
                match = pattern.match(editor.toPlainText(), cursor.position())
                if not match.hasMatch():
                    break
                found = QTextCursor(editor.document())
                found.setPosition(match.capturedStart())
                found.setPosition(match.capturedEnd(), QTextCursor.KeepAnchor)
                cursor.setPosition(match.capturedEnd())
            else:
                found = editor.document().find(text, cursor, flags)
                if found.isNull():
                    break
                cursor = QTextCursor(found)
            selection = QTextEdit.ExtraSelection()
            selection.cursor = QTextCursor(found)
            selection.format.setBackground(QColor("rgba(250, 204, 21, 0.25)"))
            selections.append(selection)
        editor.set_search_highlights(selections)

    def _clear_search_results(self, editor: CodeEditor):
        if editor:
            editor.set_search_highlights([])

    def _on_tab_reordered(self, from_index: int, to_index: int):
        """Handle tab reorder event."""
        self.event_bus.publish("editor_tab_reordered", {
            "from_index": from_index,
            "to_index": to_index
        })

    def _on_tab_clicked(self, index: int):
        """Handle tab click event."""
        path = self._get_tab_path(index)
        self.event_bus.publish("editor_tab_clicked", {
            "path": path,
            "index": index
        })

    def _on_tab_double_clicked(self, index: int):
        """Handle tab double-click event."""
        path = self._get_tab_path(index)
        self.event_bus.publish("editor_tab_double_clicked", {
            "path": path,
            "index": index
        })

    def _get_tab_path(self, index: int):
        """Get file path for tab index."""
        widget = self.tabs.widget(index)
        if hasattr(widget, 'file_path'):
            return widget.file_path
        return None

    # ── Split Editor Support ───────────────────────────────────────────────
    def setup_split_manager(self):
        """Setup split editor manager."""
        if not self.split_manager:
            self.split_manager = SplitEditorManager(self.event_bus)
        return self.split_manager

    def get_split_editor_area(self):
        """Get the split editor area widget."""
        if self.split_manager:
            return self.split_manager.get_area_widget()
        return None

    # ── Tab Context Menu ───────────────────────────────────────────────────
    def _show_tab_context_menu(self, pos):
        """Show context menu on tab."""
        tab_index = self.tabs.tabBar().tabAt(pos)
        if tab_index < 0:
            return
            
        editor = self.tabs.widget(tab_index)
        path_str = getattr(editor, "file_path", None)
        
        menu = QMenu(self)
        
        # Pin/Unpin
        is_pinned = path_str in self.pinned_tabs
        pin_action = QAction("Unpin Tab" if is_pinned else "Pin Tab", self)
        pin_action.triggered.connect(lambda: self.toggle_pin_tab(tab_index))
        menu.addAction(pin_action)
        
        menu.addSeparator()
        
        # Duplicate
        dup_action = QAction("Duplicate Tab", self)
        dup_action.triggered.connect(lambda: self.duplicate_tab(tab_index))
        menu.addAction(dup_action)
        
        menu.addSeparator()
        
        # Close operations
        close_action = QAction("Close", self)
        close_action.triggered.connect(lambda: self.close_tab(tab_index))
        menu.addAction(close_action)
        
        close_others_action = QAction("Close Others", self)
        close_others_action.triggered.connect(lambda: self.close_others(tab_index))
        menu.addAction(close_others_action)
        
        close_left_action = QAction("Close to Left", self)
        close_left_action.triggered.connect(lambda: self.close_left(tab_index))
        menu.addAction(close_left_action)
        
        close_right_action = QAction("Close to Right", self)
        close_right_action.triggered.connect(lambda: self.close_right(tab_index))
        menu.addAction(close_right_action)
        
        # Reopen
        reopen_action = QAction("Reopen Closed Tab", self)
        reopen_action.triggered.connect(self.reopen_closed_tab)
        reopen_action.setEnabled(bool(self._closed_tabs))
        menu.addAction(reopen_action)
        
        menu.exec_(self.tabs.tabBar().mapToGlobal(pos))

    # ── Tab Management ─────────────────────────────────────────────────────
    def open_file(self, path: Path, content: str, read_only: bool = False):
        """Open a file in a new tab or switch to existing tab."""
        logger.info(f"[EditorTabs.open_file] Starting with path: {path}, read_only: {read_only}")
        path_str = str(path)

        # If already open — just switch to it
        if path_str in self.editors:
            logger.info(f"[EditorTabs.open_file] File already open, switching to existing tab")
            idx = self.tabs.indexOf(self.editors[path_str])
            self.tabs.setCurrentIndex(idx)
            editor = self.editors[path_str]
            self._restore_editor_state(editor, path_str)
            editor.setFocus()
            self._highlight_search_results(editor, *(self._search_state or {}).get("find", ""), *(False, False)) if False else None
            return

        logger.info(f"[EditorTabs.open_file] Creating new editor widget")
        # Create editor widget
        editor = CodeEditor(path_str, self.event_bus)
        editor.state_changed.connect(lambda state, p=path_str: self._on_editor_state_changed(p, state))

        if path_str in self._editor_states:
            editor.set_pending_restore_state(self._editor_states[path_str])

        editor.load_file(content)

        if read_only:
            editor.setReadOnly(True)

        # Connect signals
        editor.modified_state_changed.connect(
            lambda m, p=path_str: self.on_editor_modified(p, m)
        )
        editor.cursor_position_changed.connect(self.on_cursor_moved)
        editor.ai_action_requested.connect(
            lambda a, t: self._on_editor_ai_action(a, t, path_str)
        )

        logger.info(f"[EditorTabs.open_file] Adding new tab")
        # Add tab
        self.editors[path_str] = editor
        tab_label = self._tab_label(path_str, editor)
        idx = self.tabs.addTab(editor, tab_label)
        self.tabs.setCurrentIndex(idx)
        editor.setFocus()

        # Wire up managers
        self.update_breadcrumb(path_str)
        self.set_editor_for_minimap(editor)
        self.setup_highlight_manager(editor)
        self.setup_bracket_matcher(editor)

        # LSP
        if self.lsp_manager:
            lang_id = get_language_id_for_file(path)
            editor.set_lsp_manager(self.lsp_manager)
            self.lsp_manager.open_document(path, lang_id, content)

        self._restore_editor_state(editor, path_str)
        if self._search_state:
            self._highlight_search_results(
                editor,
                self._search_state.get("find", ""),
                self._search_state.get("case_sensitive", False),
                self._search_state.get("regex", False),
            )

        logger.info(f"[EditorTabs.open_file] Tab added successfully, index: {idx}")
        # Events
        self.event_bus.publish("editor_opened", {"path": path_str, "index": idx})
        self.event_bus.publish("tab_created",   {"path": path_str, "index": idx})
        logger.info(f"Opened tab: {path.name}")
        self._publish_session_update()

    def close_tab(self, index):
        """Close a tab by index."""
        editor = self.tabs.widget(index)
        if not editor:
            return

        path_str = getattr(editor, "file_path", None)

        # Prompt if unsaved
        if editor.document().isModified():
            from PySide6.QtWidgets import QMessageBox
            name = Path(path_str).name if path_str else "Untitled"
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                f"'{name}' has unsaved changes. Save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if reply == QMessageBox.Save:
                if path_str:
                    self.event_bus.publish("request_save_file", {
                        "editor": editor, "path": path_str
                    })
            elif reply == QMessageBox.Cancel:
                return

        state = editor.capture_state() if hasattr(editor, "capture_state") else {}
        if path_str:
            self._closed_tabs.append((index, path_str, self.tabs.tabText(index), state, editor.toPlainText() if hasattr(editor, "toPlainText") else ""))
            self._editor_states[path_str] = state

        # Remove from editors dict first
        if path_str and path_str in self.editors:
            del self.editors[path_str]

        # Remove tab
        self.tabs.removeTab(index)
        editor.deleteLater()

        # Publish events
        if path_str:
            self.event_bus.publish("request_close_file", {"path": path_str})
            self.event_bus.publish("editor_closed",      {"path": path_str, "index": index})
            self.event_bus.publish("tab_closed",         {"path": path_str, "index": index})
        self._publish_session_update()

    def force_close_tab(self, path_str):
        """Force close a tab by path."""
        if path_str in self.editors:
            editor = self.editors.pop(path_str)
            idx = self.tabs.indexOf(editor)
            if idx >= 0:
                self.tabs.removeTab(idx)
            editor.deleteLater()
            self.event_bus.publish("editor_closed", {"path": path_str, "index": idx})
            self._publish_session_update()

    def on_editor_modified(self, path_str, modified):
        """Handle editor modified state change — update tab label + publish events."""
        if path_str in self.editors:
            editor = self.editors[path_str]
            idx    = self.tabs.indexOf(editor)
            self.tabs.setTabText(idx, self._tab_label(path_str, editor))
            self.event_bus.publish("file_modified_state", {
                "path": path_str, "modified": modified
            })
            self.event_bus.publish("editor_modified", {
                "path": path_str, "modified": modified
            })
            self._editor_states[path_str] = editor.capture_state() if hasattr(editor, "capture_state") else self._editor_states.get(path_str, {})
            self._publish_session_update()
            
    def on_editor_saved(self, path_str):
        """Handle editor save completion — clear modified indicator."""
        if path_str in self.editors:
            editor = self.editors[path_str]
            editor.document().setModified(False)
            idx  = self.tabs.indexOf(editor)
            self.tabs.setTabText(idx, self._tab_label(path_str, editor))
            self.event_bus.publish("editor_saved", {"path": path_str})
            self._editor_states[path_str] = editor.capture_state() if hasattr(editor, "capture_state") else self._editor_states.get(path_str, {})
            self._publish_session_update()

    def on_tab_changed(self, index):
        """Handle tab change — update breadcrumb, status bar, minimap."""
        editor = self.tabs.widget(index)
        if editor:
            path = getattr(editor, "file_path", None)
            self.event_bus.publish("tab_switched",  {"path": path})
            self.event_bus.publish("tab_changed",   {"path": path, "index": index})
            self.update_breadcrumb(path)
            self.set_editor_for_minimap(editor)
            self.on_cursor_moved()
            # Sync modified indicator
            if path and path in self.editors:
                modified = editor.document().isModified()
                self.on_editor_modified(path, modified)
            if self._search_state:
                self._highlight_search_results(
                    editor,
                    self._search_state.get("find", ""),
                    self._search_state.get("case_sensitive", False),
                    self._search_state.get("regex", False),
                )
            else:
                self._clear_search_results(editor)
            self._publish_session_update()

    def on_cursor_moved(self):
        """Handle cursor movement."""
        editor = self.get_current_editor()
        if editor:
            cursor = editor.textCursor()
            line = cursor.blockNumber() + 1
            col = cursor.columnNumber() + 1
            total = editor.blockCount()
            
            self.event_bus.publish("cursor_moved", {
                "path": getattr(editor, "file_path", None),
                "line": line,
                "col": col,
                "total": total
            })
            
            # Highlight matching brackets
            self.highlight_brackets(editor)

    def get_current_editor(self):
        """Get the currently active editor."""
        return self.tabs.currentWidget()

    def set_lsp_manager(self, lsp_manager):
        """Set LSP manager for all editors."""
        self.lsp_manager = lsp_manager
        for editor in self.editors.values():
            editor.set_lsp_manager(lsp_manager)

    def _on_editor_saved_event(self, data: dict):
        """Clear modified indicator when editor_saved event is received."""
        path_str = data.get("path", "")
        if path_str:
            self.on_editor_saved(path_str)

    def _on_editor_ai_action(self, action_name: str, selected_text: str, file_path: str):
        """Handle AI action from editor context menu."""
        self.event_bus.publish("ai_action_requested", {
            "action": action_name,
            "selected_text": selected_text,
            "file_path": file_path
        })
