"""
Terminal Settings — v2.0

Configuration for terminal appearance and behavior:
- Font family and size
- Color theme
- Cursor style and blink
- Line spacing
- Scrollback buffer size
- Shell preferences
- Keyboard shortcuts
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QComboBox, QSpinBox, QCheckBox, QPushButton,
                               QGroupBox, QColorDialog, QFontDialog)
from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtGui import QFont, QColor
from typing import Dict, Any


class TerminalSettings(QWidget):
    """Terminal settings configuration widget."""
    
    # Signals
    settings_changed = Signal(dict)  # settings dict
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("MyCodingMaster", "TerminalSettings")
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Font settings
        font_group = QGroupBox("Font")
        font_layout = QVBoxLayout()
        
        font_select_layout = QHBoxLayout()
        font_select_layout.addWidget(QLabel("Font:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems([
            "JetBrains Mono",
            "Cascadia Code",
            "Fira Code",
            "Source Code Pro",
            "Consolas",
            "Monaco",
            "Menlo",
            "Ubuntu Mono"
        ])
        self.font_combo.currentTextChanged.connect(self._on_settings_changed)
        font_select_layout.addWidget(self.font_combo)
        font_select_layout.addStretch()
        font_layout.addLayout(font_select_layout)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(10)
        self.font_size_spin.valueChanged.connect(self._on_settings_changed)
        size_layout.addWidget(self.font_size_spin)
        size_layout.addStretch()
        font_layout.addLayout(size_layout)
        
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # Cursor settings
        cursor_group = QGroupBox("Cursor")
        cursor_layout = QVBoxLayout()
        
        cursor_style_layout = QHBoxLayout()
        cursor_style_layout.addWidget(QLabel("Style:"))
        self.cursor_style_combo = QComboBox()
        self.cursor_style_combo.addItems(["Block", "Line", "Underline"])
        self.cursor_style_combo.currentTextChanged.connect(self._on_settings_changed)
        cursor_style_layout.addWidget(self.cursor_style_combo)
        cursor_style_layout.addStretch()
        cursor_layout.addLayout(cursor_style_layout)
        
        self.cursor_blink_check = QCheckBox("Cursor blink")
        self.cursor_blink_check.setChecked(True)
        self.cursor_blink_check.stateChanged.connect(self._on_settings_changed)
        cursor_layout.addWidget(self.cursor_blink_check)
        
        cursor_group.setLayout(cursor_layout)
        layout.addWidget(cursor_group)
        
        # Display settings
        display_group = QGroupBox("Display")
        display_layout = QVBoxLayout()
        
        line_spacing_layout = QHBoxLayout()
        line_spacing_layout.addWidget(QLabel("Line spacing:"))
        self.line_spacing_spin = QSpinBox()
        self.line_spacing_spin.setRange(0, 10)
        self.line_spacing_spin.setValue(2)
        self.line_spacing_spin.valueChanged.connect(self._on_settings_changed)
        line_spacing_layout.addWidget(self.line_spacing_spin)
        line_spacing_layout.addStretch()
        display_layout.addLayout(line_spacing_layout)
        
        self.show_timestamps_check = QCheckBox("Show timestamps")
        self.show_timestamps_check.stateChanged.connect(self._on_settings_changed)
        display_layout.addWidget(self.show_timestamps_check)
        
        self.word_wrap_check = QCheckBox("Word wrap")
        self.word_wrap_check.stateChanged.connect(self._on_settings_changed)
        display_layout.addWidget(self.word_wrap_check)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # Scrollback settings
        scrollback_group = QGroupBox("Scrollback")
        scrollback_layout = QVBoxLayout()
        
        buffer_layout = QHBoxLayout()
        buffer_layout.addWidget(QLabel("Buffer size (lines):"))
        self.scrollback_spin = QSpinBox()
        self.scrollback_spin.setRange(100, 100000)
        self.scrollback_spin.setValue(10000)
        self.scrollback_spin.setSingleStep(1000)
        self.scrollback_spin.valueChanged.connect(self._on_settings_changed)
        buffer_layout.addWidget(self.scrollback_spin)
        buffer_layout.addStretch()
        scrollback_layout.addLayout(buffer_layout)
        
        scrollback_group.setLayout(scrollback_layout)
        layout.addWidget(scrollback_group)
        
        # Shell settings
        shell_group = QGroupBox("Shell")
        shell_layout = QVBoxLayout()
        
        default_shell_layout = QHBoxLayout()
        default_shell_layout.addWidget(QLabel("Default shell:"))
        self.default_shell_combo = QComboBox()
        import sys
        if sys.platform == "win32":
            self.default_shell_combo.addItems(["cmd", "powershell", "bash", "wsl"])
        else:
            self.default_shell_combo.addItems(["bash", "zsh", "fish", "sh"])
        self.default_shell_combo.currentTextChanged.connect(self._on_settings_changed)
        default_shell_layout.addWidget(self.default_shell_combo)
        default_shell_layout.addStretch()
        shell_layout.addLayout(default_shell_layout)
        
        self.auto_cd_check = QCheckBox("Auto change directory with workspace")
        self.auto_cd_check.setChecked(True)
        self.auto_cd_check.stateChanged.connect(self._on_settings_changed)
        shell_layout.addWidget(self.auto_cd_check)
        
        shell_group.setLayout(shell_layout)
        layout.addWidget(shell_group)
        
        # Behavior settings
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout()
        
        self.confirm_close_check = QCheckBox("Confirm before closing running terminals")
        self.confirm_close_check.setChecked(True)
        self.confirm_close_check.stateChanged.connect(self._on_settings_changed)
        behavior_layout.addWidget(self.confirm_close_check)
        
        self.restore_sessions_check = QCheckBox("Restore terminal sessions on startup")
        self.restore_sessions_check.setChecked(False)
        self.restore_sessions_check.stateChanged.connect(self._on_settings_changed)
        behavior_layout.addWidget(self.restore_sessions_check)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_button)
        
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_button)
        
        layout.addLayout(button_layout)
    
    def _on_settings_changed(self):
        """Handle settings change."""
        pass  # Settings are saved on apply
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current settings as dictionary."""
        return {
            "font_family": self.font_combo.currentText(),
            "font_size": self.font_size_spin.value(),
            "cursor_style": self.cursor_style_combo.currentText(),
            "cursor_blink": self.cursor_blink_check.isChecked(),
            "line_spacing": self.line_spacing_spin.value(),
            "show_timestamps": self.show_timestamps_check.isChecked(),
            "word_wrap": self.word_wrap_check.isChecked(),
            "scrollback_size": self.scrollback_spin.value(),
            "default_shell": self.default_shell_combo.currentText(),
            "auto_cd": self.auto_cd_check.isChecked(),
            "confirm_close": self.confirm_close_check.isChecked(),
            "restore_sessions": self.restore_sessions_check.isChecked(),
        }
    
    def set_settings(self, settings: Dict[str, Any]):
        """Set settings from dictionary."""
        if "font_family" in settings:
            index = self.font_combo.findText(settings["font_family"])
            if index >= 0:
                self.font_combo.setCurrentIndex(index)
        
        if "font_size" in settings:
            self.font_size_spin.setValue(settings["font_size"])
        
        if "cursor_style" in settings:
            index = self.cursor_style_combo.findText(settings["cursor_style"])
            if index >= 0:
                self.cursor_style_combo.setCurrentIndex(index)
        
        if "cursor_blink" in settings:
            self.cursor_blink_check.setChecked(settings["cursor_blink"])
        
        if "line_spacing" in settings:
            self.line_spacing_spin.setValue(settings["line_spacing"])
        
        if "show_timestamps" in settings:
            self.show_timestamps_check.setChecked(settings["show_timestamps"])
        
        if "word_wrap" in settings:
            self.word_wrap_check.setChecked(settings["word_wrap"])
        
        if "scrollback_size" in settings:
            self.scrollback_spin.setValue(settings["scrollback_size"])
        
        if "default_shell" in settings:
            index = self.default_shell_combo.findText(settings["default_shell"])
            if index >= 0:
                self.default_shell_combo.setCurrentIndex(index)
        
        if "auto_cd" in settings:
            self.auto_cd_check.setChecked(settings["auto_cd"])
        
        if "confirm_close" in settings:
            self.confirm_close_check.setChecked(settings["confirm_close"])
        
        if "restore_sessions" in settings:
            self.restore_sessions_check.setChecked(settings["restore_sessions"])
    
    def save_settings(self):
        """Save settings to QSettings."""
        settings_dict = self.get_settings()
        for key, value in settings_dict.items():
            self.settings.setValue(f"terminal/{key}", value)
        self.settings.sync()
    
    def load_settings(self):
        """Load settings from QSettings."""
        settings_dict = {
            "font_family": self.settings.value("terminal/font_family", "JetBrains Mono"),
            "font_size": self.settings.value("terminal/font_size", 10, int),
            "cursor_style": self.settings.value("terminal/cursor_style", "Block"),
            "cursor_blink": self.settings.value("terminal/cursor_blink", True, bool),
            "line_spacing": self.settings.value("terminal/line_spacing", 2, int),
            "show_timestamps": self.settings.value("terminal/show_timestamps", False, bool),
            "word_wrap": self.settings.value("terminal/word_wrap", False, bool),
            "scrollback_size": self.settings.value("terminal/scrollback_size", 10000, int),
            "default_shell": self.settings.value("terminal/default_shell", "bash"),
            "auto_cd": self.settings.value("terminal/auto_cd", True, bool),
            "confirm_close": self.settings.value("terminal/confirm_close", True, bool),
            "restore_sessions": self.settings.value("terminal/restore_sessions", False, bool),
        }
        self.set_settings(settings_dict)
    
    def apply_settings(self):
        """Apply current settings."""
        self.save_settings()
        settings_dict = self.get_settings()
        self.settings_changed.emit(settings_dict)
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        defaults = {
            "font_family": "JetBrains Mono",
            "font_size": 10,
            "cursor_style": "Block",
            "cursor_blink": True,
            "line_spacing": 2,
            "show_timestamps": False,
            "word_wrap": False,
            "scrollback_size": 10000,
            "default_shell": "bash",
            "auto_cd": True,
            "confirm_close": True,
            "restore_sessions": False,
        }
        self.set_settings(defaults)
        self.apply_settings()
