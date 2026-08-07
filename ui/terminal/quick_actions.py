"""
Quick Actions Manager — v2.1

Detects common commands and provides one-click actions.
Examples: Open File, Open Folder, Copy Path, Copy Error, Run Again, Open Explorer.
"""
from PySide6.QtCore import QObject, Signal, QSettings
from pathlib import Path
import re
import os
from typing import Dict, List, Optional, Tuple
from core.logger import setup_logger

logger = setup_logger(__name__)


class QuickAction:
    """Represents a quick action for a detected pattern."""
    
    def __init__(self, name: str, icon: str, pattern: str,
                 action_type: str, enabled: bool = True):
        self.name = name
        self.icon = icon
        self.pattern = pattern  # Regex pattern
        self.action_type = action_type  # "open_file", "open_folder", "copy_path", etc.
        self.enabled = enabled
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "icon": self.icon,
            "pattern": self.pattern,
            "action_type": self.action_type,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "QuickAction":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            icon=data["icon"],
            pattern=data["pattern"],
            action_type=data["action_type"],
            enabled=data.get("enabled", True)
        )


class QuickActionsManager(QObject):
    """
    Manages quick actions for terminal output.
    Detects common patterns and provides one-click actions.
    """
    
    # Signals
    action_triggered = Signal(str, str)  # action_type, matched_text
    output_scanned = Signal(int)  # action_count
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._settings = QSettings("MyCodingMaster", "Terminal_QuickActions")
        self._actions: Dict[str, QuickAction] = {}
        self._last_scan_output = ""
        self._last_matches: List[Tuple[str, str, str]] = []  # (action_name, action_type, text)
        
        self._setup_default_actions()
    
    def _setup_default_actions(self):
        """Setup default quick actions."""
        default_actions = [
            QuickAction(
                name="Open File",
                icon="📄",
                pattern=r'(["\']?)([a-zA-Z]:\\[^"\']+?\.(?:py|js|ts|jsx|tsx|css|html|json|md|txt|xml|yml|yaml))(["\']?)',
                action_type="open_file"
            ),
            QuickAction(
                name="Open File (Unix)",
                icon="📄",
                pattern=r'(["\']?)(/[^"\']+?\.(?:py|js|ts|jsx|tsx|css|html|json|md|txt|xml|yml|yaml))(["\']?)',
                action_type="open_file"
            ),
            QuickAction(
                name="Open Folder",
                icon="📂",
                pattern=r'(["\']?)([a-zA-Z]:\\[^"\']+?["\']?)',
                action_type="open_folder"
            ),
            QuickAction(
                name="Copy Path",
                icon="📋",
                pattern=r'(["\']?)([a-zA-Z]:\\[^\s"\']+?["\']?)',
                action_type="copy_path"
            ),
            QuickAction(
                name="Copy Error",
                icon="⚠️",
                pattern=r'(Error|Exception|Traceback|Traceback \(most recent call last\):)',
                action_type="copy_error"
            ),
            QuickAction(
                name="Run Again",
                icon="▶️",
                pattern=r'(["\']?)(python|node|npm|yarn|pip|go|rustc|javac)\s+[^"\']+?["\']?',
                action_type="run_again"
            ),
            QuickAction(
                name="Open Explorer",
                icon="📁",
                pattern=r'(?:cd\s+)?(["\']?)([a-zA-Z]:\\[^\s"\']+?)["\']?',
                action_type="open_explorer"
            ),
            QuickAction(
                name="Open Explorer (Unix)",
                icon="📁",
                pattern=r'(?:cd\s+)?(["\']?)(/[^"\s]+?)["\']?',
                action_type="open_explorer"
            ),
            QuickAction(
                name="Copy File Path",
                icon="📋",
                pattern=r'(?:file://)?([a-zA-Z]:\\[^"\s]+?\.\\w+)',
                action_type="copy_file_path"
            ),
            QuickAction(
                name="Copy Command",
                icon="⌨️",
                pattern=r'^(python|node|npm|yarn|pip|go|rustc|javac|bash|sh)\s+.*$',
                action_type="copy_command"
            ),
        ]
        
        for action in default_actions:
            self._actions[action.name] = action
    
    def scan_output(self, output: str) -> List[Tuple[str, str, str]]:
        """Scan output for quick action patterns."""
        self._last_scan_output = output
        self._last_matches = []
        
        for action_name, action in self._actions.items():
            if not action.enabled:
                continue
            
            matches = re.finditer(action.pattern, output, re.MULTILINE)
            for match in matches:
                matched_text = match.group(0).strip().strip('"\'')
                self._last_matches.append((action_name, action.action_type, matched_text))
        
        self.output_scanned.emit(len(self._last_matches))
        return self._last_matches
    
    def get_matching_actions(self, output: str) -> List[Dict]:
        """Get all matching actions for output."""
        matches = self.scan_output(output)
        return [
            {"action": name, "type": action_type, "text": text}
            for name, action_type, text in matches
        ]
    
    def get_action(self, action_name: str) -> Optional[QuickAction]:
        """Get an action by name."""
        return self._actions.get(action_name)
    
    def trigger_action(self, action_name: str, text: str):
        """Trigger a quick action."""
        action = self.get_action(action_name)
        if action:
            self.action_triggered.emit(action.action_type, text)
            self.event_bus.publish("terminal_quick_action_triggered", {
                "action": action_name,
                "action_type": action.action_type,
                "text": text
            })
    
    def add_custom_action(self, name: str, icon: str, pattern: str,
                         action_type: str) -> bool:
        """Add a custom quick action."""
        if name in self._actions:
            return False
        
        action = QuickAction(name, icon, pattern, action_type)
        self._actions[name] = action
        return True
    
    def remove_action(self, name: str) -> bool:
        """Remove a quick action."""
        if name not in self._actions:
            return False
        
        del self._actions[name]
        return True
    
    def enable_action(self, name: str) -> bool:
        """Enable a quick action."""
        if name not in self._actions:
            return False
        
        self._actions[name].enabled = True
        return True
    
    def disable_action(self, name: str) -> bool:
        """Disable a quick action."""
        if name not in self._actions:
            return False
        
        self._actions[name].enabled = False
        return True
    
    def get_all_actions(self) -> List[QuickAction]:
        """Get all quick actions."""
        return list(self._actions.values())
    
    def get_enabled_actions(self) -> List[QuickAction]:
        """Get all enabled quick actions."""
        return [a for a in self._actions.values() if a.enabled]
