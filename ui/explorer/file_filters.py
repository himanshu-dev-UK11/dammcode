"""
File Filters Manager — v2.3

Manages file filtering in the Explorer.
Supports: Language, Extension, Folder, Git Status, Hidden Files, Ignored Files
"""
from pathlib import Path
from typing import List, Dict, Set, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QComboBox, QPushButton
from PySide6.QtCore import Qt, Signal
from core.logger import setup_logger
import fnmatch

logger = setup_logger(__name__)


class FileFilters:
    """Represents current file filter settings."""
    
    def __init__(self):
        self.visible_extensions: Set[str] = set()  # Empty = show all
        self.hidden_extensions: Set[str] = set()
        self.visible_languages: Set[str] = set()
        self.hidden_languages: Set[str] = set()
        self.show_hidden_files = False
        self.show_ignored_files = False
        self.git_statuses: Set[str] = set()
        self.folders_only = False
        self.files_only = False
    
    def copy(self) -> "FileFilters":
        """Create a copy of the filters."""
        f = FileFilters()
        f.visible_extensions = self.visible_extensions.copy()
        f.hidden_extensions = self.hidden_extensions.copy()
        f.visible_languages = self.visible_languages.copy()
        f.hidden_languages = self.hidden_languages.copy()
        f.show_hidden_files = self.show_hidden_files
        f.show_ignored_files = self.show_ignored_files
        f.git_statuses = self.git_statuses.copy()
        f.folders_only = self.folders_only
        f.files_only = self.files_only
        return f


class FileFiltersManager:
    """
    Manages file filtering in the Explorer.
    Supports filtering by language, extension, folder, git status, hidden files, ignored files.
    """
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self._filters = FileFilters()
        self._language_map: Dict[str, List[str]] = {}
        self._gitignore_patterns: List[str] = []
        self._load_gitignore()
    
    def _load_gitignore(self):
        """Load .gitignore patterns."""
        try:
            gitignore = Path(".gitignore")
            if gitignore.exists():
                with open(gitignore, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            self._gitignore_patterns.append(line)
        except Exception as e:
            logger.error(f"Failed to load .gitignore: {e}")
    
    def filter_path(self, path: Path, git_status: str = "clean") -> bool:
        """Check if a path passes the current filters."""
        name = path.name
        suffix = path.suffix.lower()
        is_dir = path.is_dir()
        
        # Language filter (from extension)
        language = self._get_language_from_extension(suffix)
        if self._filters.visible_languages and language not in self._filters.visible_languages:
            return False
        
        # Extension filter
        if self._filters.visible_extensions and suffix not in self._filters.visible_extensions:
            return False
        
        # Hidden files
        if name.startswith(".") and not self._filters.show_hidden_files:
            return False
        
        # Git ignored files
        if self._git_ignored(path) and not self._filters.show_ignored_files:
            return False
        
        # Git status filter
        if self._filters.git_statuses and git_status not in self._filters.git_statuses:
            return False
        
        # Files/folders only
        if self._filters.folders_only and not is_dir:
            return False
        
        if self._filters.files_only and is_dir:
            return False
        
        return True
    
    def _get_language_from_extension(self, extension: str) -> str:
        """Get language name from file extension."""
        languages = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "JavaScript",
            ".tsx": "TypeScript",
            ".java": "Java",
            ".c": "C",
            ".h": "C",
            ".cpp": "C++",
            ".hpp": "C++",
            ".cs": "C#",
            ".rb": "Ruby",
            ".go": "Go",
            ".rs": "Rust",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".sass": "Sass",
            ".less": "Less",
            ".json": "JSON",
            ".xml": "XML",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".md": "Markdown",
            ".txt": "Text",
            ".sql": "SQL",
            ".sh": "Shell",
            ".bash": "Bash",
            ".zsh": "Zsh",
            ".toml": "TOML",
            ".ini": "INI",
            ".cfg": "INI",
            ".conf": "INI",
        }
        return languages.get(extension, "Unknown")
    
    def _git_ignored(self, path: Path) -> bool:
        """Check if a path matches .gitignore patterns."""
        rel_path = str(path)
        
        for pattern in self._gitignore_patterns:
            # Handle negation patterns
            if pattern.startswith("!"):
                if fnmatch.fnmatch(rel_path, pattern[1:]):
                    return False
                continue
            
            # Regular pattern
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            
            # Handle directory patterns
            if pattern.endswith("/"):
                if fnmatch.fnmatch(rel_path, pattern + "*") or fnmatch.fnmatch(rel_path, pattern[:-1]):
                    return True
        
        return False
    
    def set_filters(self, filters: FileFilters):
        """Set the filter settings."""
        self._filters = filters.copy()
        self.event_bus.publish("file_filters_changed", {"filters": self._filters.to_dict() if hasattr(self._filters, 'to_dict') else {}})
    
    def get_filters(self) -> FileFilters:
        """Get current filter settings."""
        return self._filters.copy()
    
    def toggle_hidden_files(self, show: bool):
        """Toggle hidden files visibility."""
        self._filters.show_hidden_files = show
        self.event_bus.publish("file_filters_changed", {"filters": self._filters.to_dict() if hasattr(self._filters, 'to_dict') else {}})
    
    def toggle_ignored_files(self, show: bool):
        """Toggle ignored files visibility."""
        self._filters.show_ignored_files = show
        self.event_bus.publish("file_filters_changed", {"filters": self._filters.to_dict() if hasattr(self._filters, 'to_dict') else {}})
    
    def toggle_folders_only(self, show: bool):
        """Toggle folders-only mode."""
        self._filters.folders_only = show
        self._filters.files_only = not show
        self.event_bus.publish("file_filters_changed", {"filters": self._filters.to_dict() if hasattr(self._filters, 'to_dict') else {}})
    
    def toggle_files_only(self, show: bool):
        """Toggle files-only mode."""
        self._filters.files_only = show
        self._filters.folders_only = not show
        self.event_bus.publish("file_filters_changed", {"filters": self._filters.to_dict() if hasattr(self._filters, 'to_dict') else {}})
    
    def set_visible_extensions(self, extensions: List[str]):
        """Set visible file extensions."""
        self._filters.visible_extensions = set(extensions)
        self.event_bus.publish("file_filters_changed", {"filters": self._filters.to_dict() if hasattr(self._filters, 'to_dict') else {}})
    
    def set_visible_languages(self, languages: List[str]):
        """Set visible languages."""
        self._filters.visible_languages = set(languages)
        self.event_bus.publish("file_filters_changed", {"filters": self._filters.to_dict() if hasattr(self._filters, 'to_dict') else {}})


class FileFiltersWidget(QWidget):
    """Widget for file filter controls."""
    
    filters_changed = Signal()
    
    def __init__(self, filters_manager: FileFiltersManager, parent=None):
        super().__init__(parent)
        self.filters_manager = filters_manager
        self._setup_ui()
        self._apply_filters()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Hidden files
        self.hidden_check = QCheckBox("Show hidden files (.*)")
        self.hidden_check.setChecked(False)
        self.hidden_check.stateChanged.connect(self._on_hidden_changed)
        layout.addWidget(self.hidden_check)
        
        # Ignored files
        self.ignored_check = QCheckBox("Show ignored files")
        self.ignored_check.setChecked(False)
        self.ignored_check.stateChanged.connect(self._on_ignored_changed)
        layout.addWidget(self.ignored_check)
        
        # Files/Folders only
        self.files_check = QCheckBox("Files only")
        self.files_check.setChecked(False)
        self.files_check.stateChanged.connect(self._on_files_only_changed)
        layout.addWidget(self.files_check)
        
        self.folders_check = QCheckBox("Folders only")
        self.folders_check.setChecked(False)
        self.folders_check.stateChanged.connect(self._on_folders_only_changed)
        layout.addWidget(self.folders_check)
        
        layout.addStretch()
    
    def _apply_filters(self):
        """Apply current filter settings."""
        self._on_hidden_changed(self.hidden_check.checkState())
        self._on_ignored_changed(self.ignored_check.checkState())
        self._on_files_only_changed(self.files_check.checkState())
        self._on_folders_only_changed(self.folders_check.checkState())
    
    def _on_hidden_changed(self, state):
        """Handle hidden files checkbox change."""
        self.filters_manager.toggle_hidden_files(state == Qt.Checked)
        self.filters_changed.emit()
    
    def _on_ignored_changed(self, state):
        """Handle ignored files checkbox change."""
        self.filters_manager.toggle_ignored_files(state == Qt.Checked)
        self.filters_changed.emit()
    
    def _on_files_only_changed(self, state):
        """Handle files only checkbox change."""
        if state == Qt.Checked:
            self.folders_check.setChecked(False)
        self.filters_manager.toggle_files_only(state == Qt.Checked)
        self.filters_changed.emit()
    
    def _on_folders_only_changed(self, state):
        """Handle folders only checkbox change."""
        if state == Qt.Checked:
            self.files_check.setChecked(False)
        self.filters_manager.toggle_folders_only(state == Qt.Checked)
        self.filters_changed.emit()