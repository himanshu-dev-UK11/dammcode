"""
Settings Manager — v0.8

Handles application settings persistence and management.
Supports:
- General settings
- Appearance settings
- Editor settings
- Workspace settings
- Models settings
- AI settings
- Git settings
- Keyboard shortcuts

All settings are persisted to a JSON file.
"""

import json
from pathlib import Path
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt, QLocale


class SettingsManager:
    """
    Manages application settings with persistence.
    
    Settings are stored in config/settings.json
    """
    
    def __init__(self):
        self._config_dir = Path("config")
        self._config_file = self._config_dir / "settings.json"
        self._settings = {}
        self._default_settings = self._get_default_settings()
        self._load()
        
    def _get_default_settings(self) -> dict:
        """Get default settings."""
        return {
            "general": {
                "auto_save": False,
                "auto_save_delay": 3000,
                "restore_session": True,
                "show_welcome": True,
                "language": "en",
                "theme": "system"
            },
            "appearance": {
                "font_family": "Inter, Segoe UI, SF Pro Display, system-ui, sans-serif",
                "font_size": 12,
                "font_ligatures": True,
                "line_height": 1.5,
                "letter_spacing": 0,
                "word_wrap": True,
                "minimap": True,
                "scrollbar_size": 8
            },
            "editor": {
                "tab_size": 4,
                "insert_spaces": True,
                "render_whitespace": "none",
                "cursor_blinking": True,
                "cursor_style": "line",
                "word_based_suggestions": True,
                "automatic_completions": True,
                "format_on_type": True,
                "format_on_save": False
            },
            "workspace": {
                "auto_scan": True,
                "scan_delay": 1000,
                "follow_symlinks": False,
                "exclude_patterns": [
                    ".git",
                    "__pycache__",
                    "node_modules",
                    ".vscode",
                    ".idea"
                ]
            },
            "models": {
                "default_model": "auto",
                "banned_models": ["deepseek"],
                "models": {
                    "qwen3:8b": {
                        "name": "Qwen 3 8B",
                        "provider": "ollama",
                        "context_window": 32768,
                        "enabled": True
                    }
                }
            },
            "ai": {
                "auto_context": True,
                "max_context_files": 10,
                "max_tokens": 4096,
                "temperature": 0.7,
                "streaming": True,
                "smart_suggestions": True,
                "auto_verify": True
            },
            "git": {
                "enabled": True,
                "auto_refresh": True,
                "refresh_interval": 5000,
                "commit_on_save": False,
                "push_on_close": False
            },
            "github": {
                "enabled": False,
                "token": "",
                "username": "",
                "default_branch": "main"
            },
            "keyboard": {
                "shortcuts": {
                    "command_palette": ["Ctrl+Shift+P"],
                    "new_file": ["Ctrl+N"],
                    "open_folder": ["Ctrl+K", "Ctrl+O"],
                    "save": ["Ctrl+S"],
                    "save_all": ["Ctrl+Shift+S"],
                    "close": ["Ctrl+W"],
                    "next_tab": ["Ctrl+Tab"],
                    "prev_tab": ["Ctrl+Shift+Tab"],
                    "run": ["F5"],
                    "stop": ["Shift+F5"],
                    "toggle_terminal": ["Ctrl+`"],
                    "toggle_explorer": ["Ctrl+B"],
                    "toggle_ai_panel": ["Ctrl+\\"] 
                }
            },
            "window": {
                "restore_layout": True,
                "remember_position": True,
                "remember_size": True,
                "remember_maximized": True
            },
            "terminal": {
                "font_family": "JetBrains Mono, Cascadia Code, Consolas",
                "font_size": 11,
                "cursor_shape": "block",
                "cursor_blink": True,
                "line_height": 1.5,
                "scrollback_size": 10000,
                "default_shell": "cmd",
                "default_working_dir": "",
                "copy_on_select": False,
                "confirm_before_close": True,
                "bell": False,
                "smooth_scrolling": True,
                "padding": 8
            }
        }
        
    def _load(self):
        """Load settings from file."""
        try:
            if self._config_file.exists():
                with open(self._config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure new settings exist
                    self._settings = self._deep_merge(self._default_settings, loaded)
            else:
                self._settings = self._default_settings
                self._save()
        except Exception as e:
            print(f"Error loading settings: {e}")
            self._settings = self._default_settings
            
    def _save(self):
        """Save settings to file."""
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def _deep_merge(self, default: dict, loaded: dict) -> dict:
        """Deep merge loaded into default."""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
        
    def get(self, category: str, key: str, default=None):
        """Get a setting value."""
        category_data = self._settings.get(category, {})
        return category_data.get(key, default)
        
    def set(self, category: str, key: str, value):
        """Set a setting value."""
        if category not in self._settings:
            self._settings[category] = {}
        self._settings[category][key] = value
        self._save()
        
    def get_all(self, category: str) -> dict:
        """Get all settings for a category."""
        return self._settings.get(category, {})
        
    def set_all(self, category: str, settings: dict):
        """Set all settings for a category."""
        self._settings[category] = settings
        self._save()
        
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self._settings = self._default_settings.copy()
        self._save()
        
    def reset_category(self, category: str):
        """Reset a category to defaults."""
        if category in self._settings:
            self._settings[category] = self._default_settings.get(category, {}).copy()
            self._save()
            
    def get_theme(self) -> str:
        """Get current theme setting."""
        theme = self.get("general", "theme", "system")
        if theme == "system":
            # Detect system theme
            return self._detect_system_theme()
        return theme
        
    def _detect_system_theme(self) -> str:
        """Detect system theme (dark/light)."""
        # Try Qt's policy first
        if hasattr(QGuiApplication, 'styleHints'):
            color_scheme = QGuiApplication.styleHints().colorScheme()
            if color_scheme == Qt.ColorScheme.Dark:
                return "dark"
            elif color_scheme == Qt.ColorScheme.Light:
                return "light"
        
        # Fallback: check if any widget has dark background
        return "dark"  # Default to dark for now
        
    def get_font_family(self) -> str:
        """Get font family for UI."""
        return self.get("appearance", "font_family", "Inter, Segoe UI, sans-serif")
        
    def get_font_size(self) -> int:
        """Get font size for UI."""
        return self.get("appearance", "font_size", 12)
        
    def is_auto_save_enabled(self) -> bool:
        """Check if auto-save is enabled."""
        return self.get("general", "auto_save", False)
        
    def get_auto_save_delay(self) -> int:
        """Get auto-save delay in milliseconds."""
        return self.get("general", "auto_save_delay", 3000)
        
    def is_restore_session_enabled(self) -> bool:
        """Check if session restore is enabled."""
        return self.get("general", "restore_session", True)
        
    def is_show_welcome_enabled(self) -> bool:
        """Check if welcome screen should be shown."""
        return self.get("general", "show_welcome", True)
        
    def get_keyboard_shortcut(self, action: str) -> list:
        """Get keyboard shortcut for an action."""
        shortcuts = self.get("keyboard", "shortcuts", {})
        return shortcuts.get(action, [])
        
    def set_keyboard_shortcut(self, action: str, keys: list):
        """Set keyboard shortcut for an action."""
        shortcuts = self.get("keyboard", "shortcuts", {})
        shortcuts[action] = keys
        self.set("keyboard", "shortcuts", shortcuts)
        
    def is_git_enabled(self) -> bool:
        """Check if Git is enabled."""
        return self.get("git", "enabled", True)
        
    def is_github_enabled(self) -> bool:
        """Check if GitHub integration is enabled."""
        return self.get("github", "enabled", False)
        
    def get_exclude_patterns(self) -> list:
        """Get workspace exclude patterns."""
        return self.get("workspace", "exclude_patterns", [])
        
    def get_default_model(self) -> str:
        """Get default AI model."""
        return self.get("models", "default_model", "auto")


# Global instance
_settings_manager = None


def get_settings_manager() -> SettingsManager:
    """Get the global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def reset_settings_manager():
    """Reset the global settings manager (for testing)."""
    global _settings_manager
    _settings_manager = None
