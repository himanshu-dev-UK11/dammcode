"""
Quick Access Manager — v2.3

Manages quick access section in the Explorer.
Displays: Recent Files, Recent Folders, Pinned Items, Favorite Projects
"""
from pathlib import Path
from typing import List, Dict, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem, QLabel
from PySide6.QtCore import Qt, Signal, QTimer
from core.logger import setup_logger
import json
from datetime import datetime, timedelta

logger = setup_logger(__name__)


class QuickAccessManager:
    """
    Manages quick access data in the Explorer.
    Tracks recent files, recent folders, and maintains quick access items.
    """
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.recent_files_file = Path("config/recent_files.json")
        self.recent_folders_file = Path("config/recent_folders.json")
        
        self._recent_files: List[Dict] = []
        self._recent_folders: List[Dict] = []
        
        self._load_recent_files()
        self._load_recent_folders()
    
    def _load_recent_files(self):
        """Load recent files from config."""
        try:
            if self.recent_files_file.exists():
                with open(self.recent_files_file, "r", encoding="utf-8") as f:
                    self._recent_files = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load recent files: {e}")
            self._recent_files = []
    
    def _load_recent_folders(self):
        """Load recent folders from config."""
        try:
            if self.recent_folders_file.exists():
                with open(self.recent_folders_file, "r", encoding="utf-8") as f:
                    self._recent_folders = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load recent folders: {e}")
            self._recent_folders = []
    
    def _save_recent_files(self):
        """Save recent files to config."""
        try:
            self.recent_files_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.recent_files_file, "w", encoding="utf-8") as f:
                json.dump(self._recent_files, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save recent files: {e}")
    
    def _save_recent_folders(self):
        """Save recent folders to config."""
        try:
            self.recent_folders_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.recent_folders_file, "w", encoding="utf-8") as f:
                json.dump(self._recent_folders, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save recent folders: {e}")
    
    def add_recent_file(self, path: str, name: str = None):
        """Add a file to recent files."""
        path_obj = Path(path).resolve()
        
        # Remove if already exists
        self._recent_files = [f for f in self._recent_files if Path(f["path"]).resolve() != path_obj]
        
        if not name:
            name = path_obj.name
        
        recent_file = {
            "path": str(path_obj),
            "name": name,
            "accessed": datetime.utcnow().isoformat()
        }
        
        self._recent_files.insert(0, recent_file)
        self._recent_files = self._recent_files[:20]  # Keep last 20
        self._save_recent_files()
    
    def add_recent_folder(self, path: str, name: str = None):
        """Add a folder to recent folders."""
        path_obj = Path(path).resolve()
        
        # Remove if already exists
        self._recent_folders = [f for f in self._recent_folders if Path(f["path"]).resolve() != path_obj]
        
        if not name:
            name = path_obj.name
        
        recent_folder = {
            "path": str(path_obj),
            "name": name,
            "accessed": datetime.utcnow().isoformat()
        }
        
        self._recent_folders.insert(0, recent_folder)
        self._recent_folders = self._recent_folders[:10]  # Keep last 10
        self._save_recent_folders()
    
    def get_recent_files(self, limit: int = 10) -> List[Dict]:
        """Get recent files."""
        return self._recent_files[:limit]
    
    def get_recent_folders(self, limit: int = 10) -> List[Dict]:
        """Get recent folders."""
        return self._recent_folders[:limit]
    
    def get_quick_access_items(self) -> List[Dict]:
        """Get all quick access items."""
        return {
            "recent_files": self.get_recent_files(),
            "recent_folders": self.get_recent_folders()
        }


class QuickAccessWidget(QWidget):
    """Widget for displaying quick access items."""
    
    item_double_clicked = Signal(str)  # path
    
    def __init__(self, quick_access_manager: QuickAccessManager, parent=None):
        super().__init__(parent)
        self.quick_access_manager = quick_access_manager
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Recent Files section
        recent_files_label = QLabel("Recent Files")
        recent_files_label.setStyleSheet("""
            font-size: 10px;
            font-weight: 600;
            color: #8E8E98;
            letter-spacing: 0.8px;
            margin: 4px 0;
        """)
        layout.addWidget(recent_files_label)
        
        self.files_tree = QTreeWidget()
        self.files_tree.setHeaderHidden(True)
        self.files_tree.setRootIsDecorated(False)
        self.files_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.files_tree)
        
        # Recent Folders section
        recent_folders_label = QLabel("Recent Folders")
        recent_folders_label.setStyleSheet("""
            font-size: 10px;
            font-weight: 600;
            color: #8E8E98;
            letter-spacing: 0.8px;
            margin: 4px 0 0 0;
        """)
        layout.addWidget(recent_folders_label)
        
        self.folders_tree = QTreeWidget()
        self.folders_tree.setHeaderHidden(True)
        self.folders_tree.setRootIsDecorated(False)
        self.folders_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.folders_tree)
        
        layout.addStretch()
        
        self._refresh_items()
    
    def _refresh_items(self):
        """Refresh the quick access items."""
        self.files_tree.clear()
        self.folders_tree.clear()
        
        # Recent Files
        recent_files = self.quick_access_manager.get_recent_files()
        for item in recent_files:
            path = Path(item["path"])
            name = item.get("name", path.name)
            
            tree_item = QTreeWidgetItem([name])
            tree_item.setData(0, Qt.UserRole, item["path"])
            tree_item.setText(0, f"📄 {name}")
            self.files_tree.addTopLevelItem(tree_item)
        
        # Recent Folders
        recent_folders = self.quick_access_manager.get_recent_folders()
        for item in recent_folders:
            path = Path(item["path"])
            name = item.get("name", path.name)
            
            tree_item = QTreeWidgetItem([name])
            tree_item.setData(0, Qt.UserRole, item["path"])
            tree_item.setText(0, f"📂 {name}")
            self.folders_tree.addTopLevelItem(tree_item)
    
    def _on_item_double_clicked(self, item, column):
        """Handle double-click on item."""
        path = item.data(0, Qt.UserRole)
        if path:
            self.item_double_clicked.emit(path)