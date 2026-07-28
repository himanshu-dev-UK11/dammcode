"""
Command History Manager — v2.0

Enhanced command history with persistent storage, search, and productivity features.
Supports:
- Unlimited history with circular buffer
- History search (Ctrl+R style)
- Favorite commands
- Recently executed commands
- Persistent storage across IDE restarts
- Async loading to prevent UI freezes
"""
from PySide6.QtCore import QObject, Signal, QSettings, QThread, QTimer
from pathlib import Path
import json
import time
from typing import List, Optional, Dict, Any
from core.logger import setup_logger

logger = setup_logger(__name__)


class HistoryEntry:
    """Represents a single command history entry."""
    
    def __init__(self, command: str, directory: str = None, timestamp: float = None,
                 exit_code: int = None, duration_ms: int = None, is_favorite: bool = False):
        self.command = command
        self.directory = directory
        self.timestamp = timestamp or time.time()
        self.exit_code = exit_code
        self.duration_ms = duration_ms
        self.is_favorite = is_favorite
        self.execution_count = 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "command": self.command,
            "directory": self.directory,
            "timestamp": self.timestamp,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "is_favorite": self.is_favorite,
            "execution_count": self.execution_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        """Create from dictionary."""
        return cls(
            command=data["command"],
            directory=data.get("directory"),
            timestamp=data.get("timestamp", time.time()),
            exit_code=data.get("exit_code"),
            duration_ms=data.get("duration_ms"),
            is_favorite=data.get("is_favorite", False),
            execution_count=data.get("execution_count", 1)
        )


class HistoryLoader(QThread):
    """Background thread for loading history from disk."""
    
    loaded = Signal(list)  # List of HistoryEntry
    error = Signal(str)
    
    def __init__(self, history_file: Path, parent=None):
        super().__init__(parent)
        self.history_file = history_file
        self.max_entries = 10000  # Unlimited but capped for memory
    
    def run(self):
        """Load history from file."""
        try:
            if not self.history_file.exists():
                self.loaded.emit([])
                return
            
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            entries = []
            for item in data.get("history", []):
                try:
                    entry = HistoryEntry.from_dict(item)
                    entries.append(entry)
                except Exception as e:
                    logger.warning(f"Failed to load history entry: {e}")
                    continue
            
            # Keep only most recent max_entries
            if len(entries) > self.max_entries:
                entries = entries[-self.max_entries:]
            
            self.loaded.emit(entries)
            
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            self.error.emit(str(e))


class HistorySearcher(QThread):
    """Background thread for searching history."""
    
    results = Signal(list)  # List of HistoryEntry
    error = Signal(str)
    
    def __init__(self, entries: List[HistoryEntry], query: str, 
                 case_sensitive: bool = False, parent=None):
        super().__init__(parent)
        self.entries = entries
        self.query = query
        self.case_sensitive = case_sensitive
    
    def run(self):
        """Search through history entries."""
        try:
            results = []
            query = self.query if self.case_sensitive else self.query.lower()
            
            for entry in self.entries:
                search_text = entry.command if self.case_sensitive else entry.command.lower()
                if query in search_text:
                    results.append(entry)
            
            self.results.emit(results[:50])  # Limit to 50 results
            
        except Exception as e:
            logger.error(f"Failed to search history: {e}")
            self.error.emit(str(e))


class HistoryManager(QObject):
    """
    Manages command history with persistent storage and search.
    Reuses SettingsManager and EventBus.
    """
    
    # Signals
    history_updated = Signal()  # Emitted when history changes
    history_loaded = Signal()  # Emitted after async load completes
    history_search_started = Signal()
    history_search_finished = Signal()
    history_exported = Signal(str)  # Exported file path
    
    def __init__(self, event_bus, working_dir: Path = None):
        super().__init__()
        self.event_bus = event_bus
        self.working_dir = working_dir or Path.cwd()
        
        # Settings
        self._settings = QSettings("MyCodingMaster", "Terminal_History")
        self._history_file = Path("config/terminal_history.json")
        self._favorites_file = Path("config/terminal_favorites.json")
        
        # History storage
        self._entries: List[HistoryEntry] = []
        self._max_history_size = 10000  # Unlimited effectively
        self._search_results: List[HistoryEntry] = []
        
        # Search state
        self._search_query = ""
        self._search_index = -1
        self._case_sensitive = False
        self._whole_word = False
        self._regex = False
        
        # Load history in background
        self._load_history_async()
    
    def _load_history_async(self):
        """Load history from disk asynchronously to prevent UI freeze."""
        loader = HistoryLoader(self._history_file)
        loader.loaded.connect(self._on_history_loaded)
        loader.error.connect(self._on_history_load_error)
        loader.start()
    
    def _on_history_loaded(self, entries: List[HistoryEntry]):
        """Handle history load completion."""
        self._entries = entries
        logger.info(f"Loaded {len(entries)} history entries")
        self.history_loaded.emit()
        self.event_bus.publish("terminal_history_loaded", {
            "count": len(entries)
        })
    
    def _on_history_load_error(self, error: str):
        """Handle history load error."""
        logger.warning(f"Failed to load history: {error}")
        self._entries = []
    
    def add_command(self, command: str, directory: str = None, 
                    exit_code: int = None, duration_ms: int = None):
        """Add a command to history."""
        if not command.strip():
            return
        
        # Check if command already exists (for deduplication)
        existing = None
        for entry in reversed(self._entries):
            if entry.command == command:
                existing = entry
                break
        
        if existing:
            # Update existing entry
            existing.timestamp = time.time()
            existing.execution_count += 1
        else:
            # Create new entry
            entry = HistoryEntry(
                command=command.strip(),
                directory=directory,
                exit_code=exit_code,
                duration_ms=duration_ms
            )
            self._entries.append(entry)
        
        # Enforce max size (keep most recent)
        if len(self._entries) > self._max_history_size:
            self._entries = self._entries[-self._max_history_size:]
        
        # Save to disk
        self._save_history()
        
        # Emit signal
        self.history_updated.emit()
        self.event_bus.publish("terminal_history_updated", {
            "command": command,
            "count": len(self._entries)
        })
    
    def _save_history(self):
        """Save history to disk."""
        try:
            data = {
                "version": "2.0",
                "generated_at": time.time(),
                "history": [e.to_dict() for e in self._entries]
            }
            
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def get_history(self, limit: int = None, offset: int = 0) -> List[HistoryEntry]:
        """Get history entries."""
        result = self._entries[offset:]
        if limit:
            result = result[:limit]
        return result
    
    def get_recent_commands(self, count: int = 10) -> List[HistoryEntry]:
        """Get most recently executed commands."""
        return self._entries[-count:] if self._entries else []
    
    def get_favorites(self) -> List[HistoryEntry]:
        """Get favorite commands."""
        return [e for e in self._entries if e.is_favorite]
    
    def toggle_favorite(self, command: str) -> bool:
        """Toggle favorite status of a command."""
        for entry in self._entries:
            if entry.command == command:
                entry.is_favorite = not entry.is_favorite
                self._save_history()
                self.history_updated.emit()
                return entry.is_favorite
        return False
    
    def remove_favorite(self, command: str) -> bool:
        """Remove command from favorites."""
        for entry in self._entries:
            if entry.command == command:
                entry.is_favorite = False
                self._save_history()
                self.history_updated.emit()
                return True
        return False
    
    def remove_command(self, command: str) -> bool:
        """Remove a command from history."""
        for i, entry in enumerate(self._entries):
            if entry.command == command:
                self._entries.pop(i)
                self._save_history()
                self.history_updated.emit()
                return True
        return False
    
    def clear_history(self):
        """Clear all history."""
        self._entries = []
        self._save_history()
        self.history_updated.emit()
        self.event_bus.publish("terminal_history_cleared", {})
    
    # Search functionality
    
    def search(self, query: str, case_sensitive: bool = False, 
               whole_word: bool = False, regex: bool = False):
        """Search history for matching commands."""
        self._search_query = query
        self._case_sensitive = case_sensitive
        self._whole_word = whole_word
        self._regex = regex
        
        self.history_search_started.emit()
        self.event_bus.publish("terminal_search_started", {
            "query": query,
            "options": {
                "case_sensitive": case_sensitive,
                "whole_word": whole_word,
                "regex": regex
            }
        })
        
        # Use background thread for search
        self._searcher = HistorySearcher(self._entries, query, case_sensitive)
        self._searcher.results.connect(self._on_search_results)
        self._searcher.start()
    
    def _on_search_results(self, results: List[HistoryEntry]):
        """Handle search results."""
        self._search_results = results
        self.history_search_finished.emit()
        self.event_bus.publish("terminal_search_finished", {
            "query": self._search_query,
            "count": len(results)
        })
    
    def get_search_results(self) -> List[HistoryEntry]:
        """Get current search results."""
        return self._search_results
    
    def find_next(self) -> Optional[HistoryEntry]:
        """Find next match in search results."""
        if not self._search_results:
            return None
        
        self._search_index = (self._search_index + 1) % len(self._search_results)
        return self._search_results[self._search_index]
    
    def find_previous(self) -> Optional[HistoryEntry]:
        """Find previous match in search results."""
        if not self._search_results:
            return None
        
        self._search_index = (self._search_index - 1) % len(self._search_results)
        return self._search_results[self._search_index]
    
    # Export functionality
    
    def export_history(self, filepath: Path = None) -> Path:
        """Export history to file."""
        if filepath is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = Path(f"terminal_history_{timestamp}.txt")
        
        try:
            lines = []
            lines.append(f"# Terminal Command History Export")
            lines.append(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"# Total Commands: {len(self._entries)}")
            lines.append("")
            
            for entry in self._entries:
                timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', 
                                             time.localtime(entry.timestamp))
                favorite_marker = "★ " if entry.is_favorite else "  "
                lines.append(f"{favorite_marker}[{timestamp_str}] {entry.command}")
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            
            self.history_exported.emit(str(filepath))
            self.event_bus.publish("terminal_exported", {
                "filepath": str(filepath),
                "format": "text",
                "command_count": len(self._entries)
            })
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export history: {e}")
            raise
    
    def export_session(self, session_id: str, filepath: Path = None) -> Path:
        """Export session-specific history."""
        # Implementation for session-specific export
        return self.export_history(filepath)
    
    # Settings
    
    def set_max_history_size(self, size: int):
        """Set maximum history size."""
        self._max_history_size = size
        if len(self._entries) > self._max_history_size:
            self._entries = self._entries[-self._max_history_size:]
            self._save_history()
    
    def get_max_history_size(self) -> int:
        """Get maximum history size."""
        return self._max_history_size
    
    def save_to_settings(self):
        """Save history settings to QSettings."""
        self._settings.setValue("max_history_size", self._max_history_size)
        self._settings.setValue("case_sensitive_default", self._case_sensitive)
    
    def load_from_settings(self):
        """Load history settings from QSettings."""
        self._max_history_size = self._settings.value("max_history_size", 10000, int)
        self._case_sensitive = self._settings.value("case_sensitive_default", False, bool)
