"""
Command Bookmarks Manager — v2.1

Allows users to bookmark, rename, delete, and execute commands.
Supports organizing bookmarks into folders.
"""
from PySide6.QtCore import QObject, Signal, QSettings
from pathlib import Path
import json
import time
from typing import Dict, List, Optional, Any
from core.logger import setup_logger

logger = setup_logger(__name__)


class Bookmark:
    """Represents a bookmarked command."""
    
    def __init__(self, command: str, name: str = None, folder: str = "Default",
                 timestamp: float = None, execution_count: int = 0,
                 description: str = ""):
        self.command = command
        self.name = name or command
        self.folder = folder
        self.timestamp = timestamp or time.time()
        self.execution_count = execution_count
        self.description = description
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "command": self.command,
            "name": self.name,
            "folder": self.folder,
            "timestamp": self.timestamp,
            "execution_count": self.execution_count,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Bookmark":
        """Create from dictionary."""
        return cls(
            command=data["command"],
            name=data.get("name", data["command"]),
            folder=data.get("folder", "Default"),
            timestamp=data.get("timestamp", time.time()),
            execution_count=data.get("execution_count", 0),
            description=data.get("description", "")
        )


class BookmarksManager(QObject):
    """
    Manages command bookmarks with folder organization.
    Supports:
    - Bookmark commands
    - Rename bookmarks
    - Delete bookmarks
    - Execute bookmarked commands
    - Organize into folders
    """
    
    # Signals
    bookmark_created = Signal(str)  # bookmark_id
    bookmark_deleted = Signal(str)  # bookmark_id
    bookmark_renamed = Signal(str, str)  # bookmark_id, new_name
    bookmark_executed = Signal(str)  # command
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._settings = QSettings("MyCodingMaster", "Terminal_Bookmarks")
        self._bookmarks_file = Path("config/terminal_bookmarks.json")
        self._bookmarks: Dict[str, Bookmark] = {}
        self._bookmark_counter = 0
    
    def bookmark_command(self, command: str, name: str = None, folder: str = "Default",
                        description: str = "") -> str:
        """Bookmark a command."""
        self._bookmark_counter += 1
        bookmark_id = f"bookmark-{self._bookmark_counter}"
        
        bookmark = Bookmark(
            command=command,
            name=name or command,
            folder=folder,
            description=description
        )
        self._bookmarks[bookmark_id] = bookmark
        
        self._save_to_disk()
        self.bookmark_created.emit(bookmark_id)
        self.event_bus.publish("terminal_bookmark_created", {
            "bookmark_id": bookmark_id,
            "command": command,
            "name": bookmark.name,
            "folder": folder
        })
        
        return bookmark_id
    
    def delete_bookmark(self, bookmark_id: str) -> bool:
        """Delete a bookmark."""
        if bookmark_id not in self._bookmarks:
            return False
        
        bookmark = self._bookmarks.pop(bookmark_id)
        self._save_to_disk()
        self.bookmark_deleted.emit(bookmark_id)
        self.event_bus.publish("terminal_bookmark_deleted", {
            "bookmark_id": bookmark_id,
            "command": bookmark.command
        })
        
        return True
    
    def rename_bookmark(self, bookmark_id: str, new_name: str) -> bool:
        """Rename a bookmark."""
        if bookmark_id not in self._bookmarks:
            return False
        
        bookmark = self._bookmarks[bookmark_id]
        old_name = bookmark.name
        bookmark.name = new_name
        
        self._save_to_disk()
        self.bookmark_renamed.emit(bookmark_id, new_name)
        self.event_bus.publish("terminal_bookmark_renamed", {
            "bookmark_id": bookmark_id,
            "old_name": old_name,
            "new_name": new_name
        })
        
        return True
    
    def execute_bookmark(self, bookmark_id: str) -> Optional[str]:
        """Execute a bookmarked command."""
        if bookmark_id not in self._bookmarks:
            return None
        
        bookmark = self._bookmarks[bookmark_id]
        bookmark.execution_count += 1
        bookmark.timestamp = time.time()
        
        self._save_to_disk()
        self.bookmark_executed.emit(bookmark.command)
        self.event_bus.publish("terminal_bookmark_executed", {
            "bookmark_id": bookmark_id,
            "command": bookmark.command,
            "execution_count": bookmark.execution_count
        })
        
        return bookmark.command
    
    def get_bookmark(self, bookmark_id: str) -> Optional[Bookmark]:
        """Get a bookmark by ID."""
        return self._bookmarks.get(bookmark_id)
    
    def get_all_bookmarks(self) -> List[Bookmark]:
        """Get all bookmarks."""
        return list(self._bookmarks.values())
    
    def get_bookmarks_by_folder(self, folder: str) -> List[Bookmark]:
        """Get bookmarks in a folder."""
        return [b for b in self._bookmarks.values() if b.folder == folder]
    
    def get_all_folders(self) -> List[str]:
        """Get all folder names."""
        folders = set()
        for bookmark in self._bookmarks.values():
            folders.add(bookmark.folder)
        return sorted(list(folders))
    
    def move_to_folder(self, bookmark_id: str, new_folder: str) -> bool:
        """Move a bookmark to a different folder."""
        if bookmark_id not in self._bookmarks:
            return False
        
        bookmark = self._bookmarks[bookmark_id]
        old_folder = bookmark.folder
        bookmark.folder = new_folder
        
        self._save_to_disk()
        self.event_bus.publish("terminal_bookmark_moved", {
            "bookmark_id": bookmark_id,
            "old_folder": old_folder,
            "new_folder": new_folder
        })
        
        return True
    
    def clear_folder(self, folder: str) -> int:
        """Clear all bookmarks in a folder. Returns count deleted."""
        to_delete = [bid for bid, b in self._bookmarks.items() if b.folder == folder]
        for bid in to_delete:
            del self._bookmarks[bid]
        
        self._save_to_disk()
        self.event_bus.publish("terminal_folder_cleared", {
            "folder": folder,
            "count": len(to_delete)
        })
        
        return len(to_delete)
    
    def load_bookmarks(self) -> List[Bookmark]:
        """Load bookmarks from disk."""
        if not self._bookmarks_file.exists():
            return []
        
        try:
            with open(self._bookmarks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            bookmarks = []
            for item in data.get("bookmarks", []):
                try:
                    bookmark = Bookmark.from_dict(item)
                    bookmarks.append(bookmark)
                except Exception as e:
                    logger.warning(f"Failed to load bookmark: {e}")
            
            # Rebuild counter
            if bookmarks:
                self._bookmark_counter = len(bookmarks)
            
            logger.info(f"Loaded {len(bookmarks)} bookmarks")
            return bookmarks
            
        except Exception as e:
            logger.error(f"Failed to load bookmarks: {e}")
            return []
    
    def save_bookmarks(self):
        """Save bookmarks to disk."""
        self._save_to_disk()
    
    def _save_to_disk(self):
        """Save bookmarks to disk."""
        try:
            data = {
                "version": "2.1",
                "generated_at": time.time(),
                "bookmarks": [b.to_dict() for b in self._bookmarks.values()]
            }
            
            self._bookmarks_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._bookmarks_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save bookmarks: {e}")
    
    def import_bookmarks(self, filepath: Path) -> int:
        """Import bookmarks from a JSON file."""
        if not filepath.exists():
            return 0
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            count = 0
            for item in data.get("bookmarks", []):
                try:
                    bookmark = Bookmark.from_dict(item)
                    self._bookmark_counter += 1
                    bookmark_id = f"bookmark-{self._bookmark_counter}"
                    bookmark._id = bookmark_id
                    self._bookmarks[bookmark_id] = bookmark
                    count += 1
                except Exception:
                    continue
            
            self._save_to_disk()
            logger.info(f"Imported {count} bookmarks")
            return count
            
        except Exception as e:
            logger.error(f"Failed to import bookmarks: {e}")
            return 0
    
    def export_bookmarks(self, filepath: Path) -> bool:
        """Export bookmarks to a JSON file."""
        try:
            data = {
                "version": "2.1",
                "generated_at": time.time(),
                "bookmarks": [b.to_dict() for b in self._bookmarks.values()]
            }
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to export bookmarks: {e}")
            return False
    
    def get_bookmark_count(self) -> int:
        """Get total bookmark count."""
        return len(self._bookmarks)
    
    def get_popular_bookmarks(self, count: int = 10) -> List[Bookmark]:
        """Get most frequently executed bookmarks."""
        sorted_bookmarks = sorted(
            self._bookmarks.values(),
            key=lambda b: b.execution_count,
            reverse=True
        )
        return sorted_bookmarks[:count]
