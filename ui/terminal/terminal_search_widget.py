"""
Terminal Search Widget — v2.0

Advanced search functionality for terminal output with:
- Find text with next/previous navigation
- Case-sensitive search
- Whole word matching
- Regular expression support
- Search result highlighting
- Match count display
"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton,
                               QLabel, QCheckBox, QToolButton)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut, QIcon
from typing import Optional


class TerminalSearchWidget(QWidget):
    """Search widget for terminal output."""
    
    # Signals
    search_requested = Signal(str, bool, bool, bool)  # query, case_sensitive, whole_word, regex
    find_next_requested = Signal()
    find_previous_requested = Signal()
    search_closed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_match = 0
        self.total_matches = 0
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the search UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Apply styling
        from ui.design_system import get_design_system, FontSize
        p = get_design_system().palette
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {p.bg_secondary};
                border-top: 1px solid {p.border_subtle};
            }}
        """)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in terminal...")
        self.search_input.setMinimumWidth(200)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {p.bg};
                color: {p.text};
                border: 1px solid {p.border};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: {FontSize.SM}px;
            }}
            QLineEdit:focus {{
                border-color: {p.accent};
            }}
        """)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.returnPressed.connect(self.find_next_requested.emit)
        layout.addWidget(self.search_input)
        
        # Match counter
        self.match_label = QLabel("No matches")
        self.match_label.setStyleSheet(f"""
            QLabel {{
                color: {p.text_tertiary};
                font-size: {FontSize.XS}px;
                padding: 0 8px;
            }}
        """)
        layout.addWidget(self.match_label)
        
        # Previous button
        self.prev_button = QToolButton()
        self.prev_button.setText("↑")
        self.prev_button.setToolTip("Previous match (Shift+Enter)")
        self.prev_button.setFixedSize(24, 24)
        self.prev_button.setStyleSheet(f"""
            QToolButton {{
                background-color: {p.bg};
                color: {p.text_secondary};
                border: 1px solid {p.border};
                border-radius: 4px;
            }}
            QToolButton:hover {{
                background-color: {p.surface_hover};
                color: {p.text};
            }}
            QToolButton:pressed {{
                background-color: {p.surface_active};
            }}
        """)
        self.prev_button.clicked.connect(self.find_previous_requested.emit)
        layout.addWidget(self.prev_button)
        
        # Next button
        self.next_button = QToolButton()
        self.next_button.setText("↓")
        self.next_button.setToolTip("Next match (Enter)")
        self.next_button.setFixedSize(24, 24)
        self.next_button.setStyleSheet(f"""
            QToolButton {{
                background-color: {p.bg};
                color: {p.text_secondary};
                border: 1px solid {p.border};
                border-radius: 4px;
            }}
            QToolButton:hover {{
                background-color: {p.surface_hover};
                color: {p.text};
            }}
            QToolButton:pressed {{
                background-color: {p.surface_active};
            }}
        """)
        self.next_button.clicked.connect(self.find_next_requested.emit)
        layout.addWidget(self.next_button)
        
        # Case sensitive checkbox
        self.case_checkbox = QCheckBox("Aa")
        self.case_checkbox.setToolTip("Match case")
        self.case_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {p.text_secondary};
                font-size: {FontSize.XS}px;
                spacing: 4px;
            }}
            QCheckBox:hover {{
                color: {p.text};
            }}
        """)
        self.case_checkbox.stateChanged.connect(self._on_options_changed)
        layout.addWidget(self.case_checkbox)
        
        # Whole word checkbox
        self.whole_word_checkbox = QCheckBox("W")
        self.whole_word_checkbox.setToolTip("Match whole word")
        self.whole_word_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {p.text_secondary};
                font-size: {FontSize.XS}px;
                spacing: 4px;
            }}
            QCheckBox:hover {{
                color: {p.text};
            }}
        """)
        self.whole_word_checkbox.stateChanged.connect(self._on_options_changed)
        layout.addWidget(self.whole_word_checkbox)
        
        # Regex checkbox
        self.regex_checkbox = QCheckBox(".*")
        self.regex_checkbox.setToolTip("Use regular expression")
        self.regex_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {p.text_secondary};
                font-size: {FontSize.XS}px;
                spacing: 4px;
            }}
            QCheckBox:hover {{
                color: {p.text};
            }}
        """)
        self.regex_checkbox.stateChanged.connect(self._on_options_changed)
        layout.addWidget(self.regex_checkbox)
        
        layout.addStretch()
        
        # Close button
        self.close_button = QToolButton()
        self.close_button.setText("✕")
        self.close_button.setToolTip("Close search (Esc)")
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                color: {p.text_tertiary};
                border: none;
                border-radius: 3px;
            }}
            QToolButton:hover {{
                background-color: {p.surface_hover};
                color: {p.text};
            }}
        """)
        self.close_button.clicked.connect(self._on_close)
        layout.addWidget(self.close_button)
        
        # Keyboard shortcuts
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self._on_close)
        QShortcut(QKeySequence("Shift+Return"), self, self.find_previous_requested.emit)
    
    def _on_search_text_changed(self, text: str):
        """Handle search text change."""
        if text:
            self.search_requested.emit(
                text,
                self.case_checkbox.isChecked(),
                self.whole_word_checkbox.isChecked(),
                self.regex_checkbox.isChecked()
            )
        else:
            self.update_match_count(0, 0)
    
    def _on_options_changed(self):
        """Handle search options change."""
        text = self.search_input.text()
        if text:
            self.search_requested.emit(
                text,
                self.case_checkbox.isChecked(),
                self.whole_word_checkbox.isChecked(),
                self.regex_checkbox.isChecked()
            )
    
    def _on_close(self):
        """Handle close request."""
        self.search_closed.emit()
        self.hide()
    
    def show_search(self):
        """Show the search widget and focus input."""
        self.show()
        self.search_input.setFocus()
        self.search_input.selectAll()
    
    def hide_search(self):
        """Hide the search widget."""
        self.hide()
        self.search_input.clear()
    
    def update_match_count(self, current: int, total: int):
        """Update match counter display."""
        self.current_match = current
        self.total_matches = total
        
        if total == 0:
            self.match_label.setText("No matches")
        else:
            self.match_label.setText(f"{current}/{total}")
    
    def get_search_query(self) -> str:
        """Get current search query."""
        return self.search_input.text()
    
    def is_case_sensitive(self) -> bool:
        """Check if case-sensitive search is enabled."""
        return self.case_checkbox.isChecked()
    
    def is_whole_word(self) -> bool:
        """Check if whole word search is enabled."""
        return self.whole_word_checkbox.isChecked()
    
    def is_regex(self) -> bool:
        """Check if regex search is enabled."""
        return self.regex_checkbox.isChecked()
