"""
Favorites Manager — v2.3

Manages pinned favorites in the Explorer.
Supports: Add, Remove, Rename, Reorder favorites (files, folders, projects)
"""
from pathlib import Path
from typing import List, Dict, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem, QMenu
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction
from core.logger import setup_logger
import json

logger = setup_logger(__name__)


class FavoritesManager:
    """
    Manages pinned favorites in the Explorer.
    Supports adding, removing, renaming, and reordering favorites.
    """
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.favorites_file = Path("config/favorites.json")
        self._favorites: List[Dict] = []
        self._load_favorites()
    
    def _load_favorites(self):
        """Load favorites from config file."""
        try:
            if self.favorites_file.exists():
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    self._favorites = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load favorites: {e}")
            self._favorites = []
    
    def _save_favorites(self):
        """Save favorites to config file."""
        try:
            self.favorites_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump(self._favorites, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save favorites: {e}")
    
    def get_favorites(self) -> List[Dict]:
        """Get all favorites."""
        return self._favorites.copy()
    
    def add_favorite(self, path: str, name: str = None, type_: str = "file") -> bool:
        """Add a favorite."""
        path_obj = Path(path).resolve()
        
        # Check if already exists
        for fav in self._favorites:
            if Path(fav["path"]).resolve() == path_obj:
                return False
        
        if not name:
            name = path_obj.name
        
        favorite = {
            "path": str(path_obj),
            "name": name,
            "type": type_,
            "created": str(Path(path).stat().st_ctime if path_obj.exists() else "")
        }
        
        self._favorites.insert(0, favorite)  # Add to top
        self._save_favorites()
        self.event_bus.publish("favorites_updated", {"favorites": self._favorites})
        return True
    
    def remove_favorite(self, path: str) -> bool:
        """Remove a favorite."""
        path_obj = Path(path).resolve()
        
        for i, fav in enumerate(self._favorites):
            if Path(fav["path"]).resolve() == path_obj:
                self._favorites.pop(i)
                self._save_favorites()
                self.event_bus.publish("favorites_updated", {"favorites": self._favorites})
                return True
        
        return False
    
    def rename_favorite(self, path: str, new_name: str) -> bool:
        """Rename a favorite."""
        path_obj = Path(path).resolve()
        
        for fav in self._favorites:
            if Path(fav["path"]).resolve() == path_obj:
                fav["name"] = new_name
                self._save_favorites()
                self.event_bus.publish("favorites_updated", {"favorites": self._favorites})
                return True
        
        return False
    
    def move_favorite(self, from_index: int, to_index: int) -> bool:
        """Reorder a favorite."""
        if from_index < 0 or from_index >= len(self._favorites):
            return False
        if to_index < 0 or to_index >= len(self._favorites):
            return False
        
        favorite = self._favorites.pop(from_index)
        self._favorites.insert(to_index, favorite)
        self._save_favorites()
        self.event_bus.publish("favorites_updated", {"favorites": self._favorites})
        return True
    
    def is_favorite(self, path: str) -> bool:
        """Check if a path is a favorite."""
        path_obj = Path(path).resolve()
        for fav in self._favorites:
            if Path(fav["path"]).resolve() == path_obj:
                return True
        return False
    
    def get_favorite_by_path(self, path: str) -> Optional[Dict]:
        """Get favorite data by path."""
        path_obj = Path(path).resolve()
        for fav in self._favorites:
            if Path(fav["path"]).resolve() == path_obj:
                return fav.copy()
        return None


class FavoritesWidget(QWidget):
    """Widget for displaying favorites."""
    
    favorite_double_clicked = Signal(str)  # path
    
    def __init__(self, favorites_manager: FavoritesManager, parent=None):
        super().__init__(parent)
        self.favorites_manager = favorites_manager
        self._setup_ui()
        self._refresh_favorites()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        layout.addWidget(self.tree)
    
    def _refresh_favorites(self):
        """Refresh the favorites list."""
        self.tree.clear()
        
        favorites = self.favorites_manager.get_favorites()
        
        for fav in favorites:
            path = Path(fav["path"])
            name = fav.get("name", path.name)
            type_ = fav.get("type", "file")
            
            item = QTreeWidgetItem([name])
            item.setData(0, Qt.UserRole, fav["path"])
            item.setData(0, Qt.UserRole + 1, type_)
            
            # Add icon based on type
            if type_ == "folder":
                item.setText(0, f"📁 {name}")
            else:
                item.setText(0, f"📄 {name}")
            
            self.tree.addTopLevelItem(item)
    
    def _on_item_double_clicked(self, item, column):
        """Handle double-click on favorite."""
        path = item.data(0, Qt.UserRole)
        if path:
            self.favorite_double_clicked.emit(path)
    
    def _show_context_menu(self, position):
        """Show context menu for favorites."""
        item = self.tree.itemAt(position)
        if not item:
            return
        
        path = item.data(0, Qt.UserRole)
        if not path:
            return
        
        menu = QMenu(self)
        
        # Rename action
        rename_action = QAction("Rename", menu)
        rename_action.triggered.connect(lambda: self._rename_favorite(item))
        menu.addAction(rename_action)
        
        # Remove action
        remove_action = QAction("Remove", menu)
        remove_action.triggered.connect(lambda: self._remove_favorite(item))
        menu.addAction(remove_action)
        
        menu.exec_(self.tree.viewport().mapToGlobal(position))
    
    def _rename_favorite(self, item):
        """Rename a favorite."""
        from PySide6.QtWidgets import QInputDialog
        
        path = item.data(0, Qt.UserRole)
        current_name = item.text(0)
        
        name, ok = QInputDialog.getText(
            self, "Rename Favorite",
            f"Rename '{current_name}' to:",
            text=current_name
        )
        
        if ok and name:
            self.favorites_manager.rename_favorite(path, name)
            self._refresh_favorites()
    
    def _remove_favorite(self, item):
        """Remove a favorite."""
        path = item.data(0, Qt.UserRole)
        self.favorites_manager.remove_favorite(path)
        self._refresh_favorites()