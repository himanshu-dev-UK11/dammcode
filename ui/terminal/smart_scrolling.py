"""
Smart Scrolling Manager — v2.1

Manages automatic scrolling for terminal output with "Jump to Latest" functionality.
When user scrolls up, auto-scroll is disabled with a jump button.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from typing import Optional
from core.logger import setup_logger

logger = setup_logger(__name__)


class SmartScrollingManager:
    """
    Manages smart scrolling behavior for terminal output.
    Features:
    - Auto-follow output when streaming
    - Disable auto-scroll when user scrolls up
    - Show "Jump to Latest" button when not at bottom
    """
    
    def __init__(self, event_bus, scrollbar, output_widget):
        self.event_bus = event_bus
        self.scrollbar = scrollbar
        self.output_widget = output_widget
        
        # State
        self._auto_scroll = True
        self._user_scrolled = False
        self._last_scroll_value = 0
        
        # Timer for scroll threshold check
        self._scroll_threshold = 10  # pixels
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setInterval(100)
        self._debounce_timer.timeout.connect(self._check_scroll_position)
    
    def connect_signals(self):
        """Connect scrollbar signals."""
        self.scrollbar.valueChanged.connect(self._on_scrollbar_changed)
    
    def disconnect_signals(self):
        """Disconnect scrollbar signals."""
        try:
            self.scrollbar.valueChanged.disconnect(self._on_scrollbar_changed)
        except TypeError:
            pass  # Already disconnected
    
    def _on_scrollbar_changed(self, value: int):
        """Handle scrollbar value change."""
        if self._auto_scroll and value >= self.scrollbar.maximum() - self._scroll_threshold:
            # User is at or near bottom - auto-scroll remains on
            self._user_scrolled = False
            self._last_scroll_value = value
            self.event_bus.publish("terminal_autoscroll_changed", {
                "enabled": True,
                "reason": "at_bottom"
            })
        else:
            # User scrolled up - disable auto-scroll
            if self._auto_scroll:
                self._auto_scroll = False
                self._user_scrolled = True
                self.event_bus.publish("terminal_autoscroll_changed", {
                    "enabled": False,
                    "reason": "user_scrolled"
                })
        
        self._last_scroll_value = value
    
    def _check_scroll_position(self):
        """Check if we should show/hide the jump button."""
        max_value = self.scrollbar.maximum()
        current_value = self.scrollbar.value()
        
        if not self._auto_scroll and current_value < max_value - self._scroll_threshold:
            # Show jump button
            self._emit_jump_available()
        else:
            # Hide jump button
            self._emit_jump_hidden()
    
    def _emit_jump_available(self):
        """Emit jump button available."""
        self.event_bus.publish("terminal_jump_available", {
            "scroll_value": self.scrollbar.value(),
            "max_value": self.scrollbar.maximum()
        })
    
    def _emit_jump_hidden(self):
        """Emit jump button hidden."""
        self.event_bus.publish("terminal_jump_hidden", {})
    
    def jump_to_latest(self):
        """Jump to latest output (bottom)."""
        if self.scrollbar:
            self.scrollbar.setValue(self.scrollbar.maximum())
        
        self._auto_scroll = True
        self._user_scrolled = False
        self.event_bus.publish("terminal_autoscroll_changed", {
            "enabled": True,
            "reason": "jump_to_latest"
        })
    
    def set_auto_scroll(self, enabled: bool):
        """Set auto-scroll mode."""
        self._auto_scroll = enabled
        
        if enabled:
            # Scroll to bottom
            if self.scrollbar:
                self.scrollbar.setValue(self.scrollbar.maximum())
        
        self.event_bus.publish("terminal_autoscroll_changed", {
            "enabled": enabled,
            "reason": "user_action"
        })
    
    def is_auto_scroll(self) -> bool:
        """Check if auto-scroll is enabled."""
        return self._auto_scroll
    
    def is_user_scrolled(self) -> bool:
        """Check if user has manually scrolled."""
        return self._user_scrolled
    
    def reset(self):
        """Reset to initial state."""
        self._auto_scroll = True
        self._user_scrolled = False
        if self.scrollbar:
            self.scrollbar.setValue(self.scrollbar.maximum())
        self.event_bus.publish("terminal_autoscroll_changed", {
            "enabled": True,
            "reason": "reset"
        })
