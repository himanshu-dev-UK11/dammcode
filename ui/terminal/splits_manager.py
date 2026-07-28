"""
Terminal Splits Manager — v2.1

Manages terminal split layouts with resize, collapse, expand, and focus capabilities.
"""
from PySide6.QtWidgets import QSplitter, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QSettings, QObject
from typing import Dict, List, Optional, Tuple
from core.logger import setup_logger

logger = setup_logger(__name__)


class SplitGroup:
    """Represents a group of terminals in a split layout."""
    
    def __init__(self, group_id: str, direction: str = "horizontal"):
        self.group_id = group_id
        self.direction = direction  # "horizontal" or "vertical"
        self.terminals: List[str] = []  # List of session_ids
        self.sizes: List[int] = []
        self.collapsed: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "group_id": self.group_id,
            "direction": self.direction,
            "terminals": self.terminals,
            "sizes": self.sizes,
            "collapsed": self.collapsed
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SplitGroup":
        """Create from dictionary."""
        group = cls(data["group_id"], data.get("direction", "horizontal"))
        group.terminals = data.get("terminals", [])
        group.sizes = data.get("sizes", [])
        group.collapsed = data.get("collapsed", False)
        return group


class SplitsManager(QObject):
    """
    Manages terminal split layouts with full control.
    Supports:
    - Resize, collapse, expand, close individual split
    - Focus next/previous split
    - Horizontal and vertical splitting
    """
    
    # Signals
    split_created = Signal(str, str)  # session_id, direction
    split_resized = Signal(str, list)  # session_id, sizes
    split_collapsed = Signal(str)  # session_id
    split_expanded = Signal(str)  # session_id
    split_closed = Signal(str)  # session_id
    focus_next_split = Signal()
    focus_previous_split = Signal()
    directory_changed = Signal(str, str)  # session_id, new_directory
    
    def __init__(self, event_bus, parent_splitter: QSplitter = None):
        super().__init__()
        self.event_bus = event_bus
        self._parent_splitter = parent_splitter
        self._settings = QSettings("MyCodingMaster", "Terminal_Splits")
        self._split_groups: Dict[str, SplitGroup] = {}
        self._current_group_id: str = None
        self._group_counter = 0
    
    def create_split(self, session_id: str, direction: str = "horizontal") -> str:
        """Create a new split for a session."""
        self._group_counter += 1
        group_id = f"split-{self._group_counter}"
        
        group = SplitGroup(group_id, direction)
        group.terminals.append(session_id)
        group.sizes = [100]  # Initial size
        
        self._split_groups[group_id] = group
        
        if not self._current_group_id:
            self._current_group_id = group_id
        
        self.split_created.emit(session_id, direction)
        self.event_bus.publish("terminal_split_created", {
            "session_id": session_id,
            "direction": direction,
            "group_id": group_id
        })
        
        return group_id
    
    def add_terminal_to_split(self, session_id: str, group_id: str):
        """Add a terminal to an existing split group."""
        if group_id not in self._split_groups:
            return
        
        group = self._split_groups[group_id]
        group.terminals.append(session_id)
        
        # Update sizes - give new terminal 50% of group
        total = len(group.terminals)
        group.sizes = [int(100 / total)] * total
        
        self.event_bus.publish("terminal_terminal_added_to_split", {
            "session_id": session_id,
            "group_id": group_id,
            "sizes": group.sizes
        })
    
    def remove_terminal_from_split(self, session_id: str, group_id: str):
        """Remove a terminal from a split group."""
        if group_id not in self._split_groups:
            return
        
        group = self._split_groups[group_id]
        if session_id not in group.terminals:
            return
        
        group.terminals.remove(session_id)
        
        if group.terminals:
            # Rebalance sizes
            count = len(group.terminals)
            group.sizes = [int(100 / count)] * count
        else:
            # Remove empty group
            del self._split_groups[group_id]
        
        self.split_closed.emit(session_id)
        self.event_bus.publish("terminal_terminal_removed_from_split", {
            "session_id": session_id,
            "group_id": group_id
        })
    
    def resize_split(self, group_id: str, sizes: List[int]):
        """Resize terminals in a split."""
        if group_id not in self._split_groups:
            return
        
        group = self._split_groups[group_id]
        group.sizes = sizes
        
        self.split_resized.emit(group_id, sizes)
        self.event_bus.publish("terminal_split_resized", {
            "group_id": group_id,
            "sizes": sizes
        })
    
    def collapse_split(self, session_id: str, group_id: str):
        """Collapse a terminal in a split."""
        if group_id not in self._split_groups:
            return
        
        group = self._split_groups[group_id]
        
        if session_id in group.terminals:
            # Mark as collapsed
            idx = group.terminals.index(session_id)
            group.sizes[idx] = 0
            group.collapsed = True
        
        self.split_collapsed.emit(session_id)
        self.event_bus.publish("terminal_split_collapsed", {
            "session_id": session_id,
            "group_id": group_id
        })
    
    def expand_split(self, session_id: str, group_id: str):
        """Expand a collapsed terminal."""
        if group_id not in self._split_groups:
            return
        
        group = self._split_groups[group_id]
        
        if session_id in group.terminals:
            idx = group.terminals.index(session_id)
            group.sizes[idx] = 50  # Restore to 50%
            group.collapsed = False
        
        self.split_expanded.emit(session_id)
        self.event_bus.publish("terminal_split_expanded", {
            "session_id": session_id,
            "group_id": group_id
        })
    
    def focus_next_split(self, group_id: str, current_idx: int) -> Optional[str]:
        """Focus next terminal in split group."""
        if group_id not in self._split_groups:
            return None
        
        group = self._split_groups[group_id]
        next_idx = (current_idx + 1) % len(group.terminals)
        return group.terminals[next_idx]
    
    def focus_previous_split(self, group_id: str, current_idx: int) -> Optional[str]:
        """Focus previous terminal in split group."""
        if group_id not in self._split_groups:
            return None
        
        group = self._split_groups[group_id]
        prev_idx = (current_idx - 1) % len(group.terminals)
        return group.terminals[prev_idx]
    
    def set_active_split(self, group_id: str):
        """Set the currently active split group."""
        if group_id in self._split_groups:
            self._current_group_id = group_id
            self.event_bus.publish("terminal_split_activated", {
                "group_id": group_id
            })
    
    def get_active_split(self) -> Optional[SplitGroup]:
        """Get the currently active split group."""
        if self._current_group_id:
            return self._split_groups.get(self._current_group_id)
        return None
    
    def get_all_splits(self) -> List[SplitGroup]:
        """Get all split groups."""
        return list(self._split_groups.values())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "current_group_id": self._current_group_id,
            "groups": {gid: g.to_dict() for gid, g in self._split_groups.items()}
        }
    
    def from_dict(self, data: dict):
        """Load from dictionary."""
        self._current_group_id = data.get("current_group_id")
        self._split_groups = {}
        
        for gid, gdata in data.get("groups", {}).items():
            self._split_groups[gid] = SplitGroup.from_dict(gdata)
    
    def clear(self):
        """Clear all splits."""
        self._split_groups = {}
        self._current_group_id = None
        self.event_bus.publish("terminal_splits_cleared", {})
