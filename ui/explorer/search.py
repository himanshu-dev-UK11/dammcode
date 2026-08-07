"""
Search Manager — v2.3

Manages file search functionality in the Explorer.
Supports: File Name, Folder Name, Fuzzy Search, Case Sensitive, Whole Word, Live Filtering
"""
from pathlib import Path
from typing import List, Optional, Set
from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Qt, Signal, QThread, QObject
from core.logger import setup_logger
import re
import fnmatch

logger = setup_logger(__name__)


class SearchWorker(QObject):
    """Worker thread for search operations."""
    finished = Signal(list, str)  # results, query
    
    def __init__(self, root_path: Path, query: str, options: dict):
        super().__init__()
        self.root_path = root_path
        self.query = query
        self.options = options
    
    def run(self):
        """Run the search operation."""
        try:
            results = self._search_files()
            self.finished.emit(results, self.query)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.finished.emit([], self.query)
    
    def _search_files(self) -> List[dict]:
        """Perform file search."""
        results = []
        query = self.query
        
        # Handle empty query
        if not query:
            return results
        
        # Get search options
        case_sensitive = self.options.get("case_sensitive", False)
        whole_word = self.options.get("whole_word", False)
        search_folders = self.options.get("search_folders", True)
        search_files = self.options.get("search_files", True)
        fuzzy = self.options.get("fuzzy", False)
        
        # Build pattern
        if not case_sensitive:
            pattern_query = query.lower()
        else:
            pattern_query = query
        
        try:
            for item in self.root_path.rglob("*"):
                if not item.exists():
                    continue
                
                is_dir = item.is_dir()
                name = item.name
                
                if not case_sensitive:
                    name_lower = name.lower()
                else:
                    name_lower = name
                
                match = False
                
                if is_dir and search_folders:
                    if fuzzy:
                        match = self._fuzzy_match(name_lower, pattern_query)
                    else:
                        if whole_word:
                            match = name_lower == pattern_query
                        else:
                            match = pattern_query in name_lower
                
                if not match and search_files:
                    if fuzzy:
                        match = self._fuzzy_match(name_lower, pattern_query)
                    else:
                        if whole_word:
                            match = name_lower == pattern_query
                        else:
                            match = pattern_query in name_lower
                
                if match:
                    results.append({
                        "path": str(item),
                        "name": item.name,
                        "is_dir": is_dir,
                        "score": 100  # Simple matching - could use fuzzy score
                    })
                    
        except Exception as e:
            logger.error(f"Error during search: {e}")
        
        return results
    
    def _fuzzy_match(self, text: str, pattern: str) -> bool:
        """Perform fuzzy match - pattern characters must appear in order."""
        if not pattern:
            return True
        
        pattern_idx = 0
        for char in text:
            if pattern_idx < len(pattern) and char == pattern[pattern_idx]:
                pattern_idx += 1
        
        return pattern_idx == len(pattern)


class SearchManager:
    """
    Manages search functionality in the Explorer.
    Supports file name, folder name, fuzzy search, case sensitivity, whole word, and live filtering.
    """
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.root_path: Path = None
        self._search_thread: Optional[QThread] = None
        self._current_search_query = ""
        self._current_results: List[dict] = []
        self._search_options = {
            "case_sensitive": False,
            "whole_word": False,
            "search_folders": True,
            "search_files": True,
            "fuzzy": False,
        }
    
    def set_root_path(self, root: Path):
        """Set the root path for search."""
        self.root_path = root
    
    def search(self, query: str, options: dict = None) -> List[dict]:
        """Perform search and return results."""
        if options:
            self._search_options.update(options)
        
        self._current_search_query = query
        self._current_results = []
        
        # Return cached results for empty query
        if not query:
            return []
        
        # Run search in worker thread for large projects
        if self.root_path and self.root_path.exists():
            self._run_search_async(query)
        else:
            self._current_results = []
        
        return self._current_results
    
    def _run_search_async(self, query: str):
        """Run search in background thread."""
        # Cancel existing search
        if self._search_thread:
            self._search_thread.quit()
            self._search_thread.wait()
        
        # Create new worker and thread
        self._search_thread = QThread()
        worker = SearchWorker(self.root_path, query, self._search_options)
        worker.moveToThread(self._search_thread)
        
        worker.finished.connect(self._on_search_finished)
        worker.finished.connect(self._search_thread.quit)
        self._search_thread.started.connect(worker.run)
        
        self._search_thread.start()
    
    def _on_search_finished(self, results: list, query: str):
        """Handle search completion."""
        self._current_results = results
        self.event_bus.publish("explorer_search_results", {
            "query": query,
            "results": results
        })
    
    def highlight_match(self, text: str, query: str) -> str:
        """Add HTML highlighting to matching text."""
        if not query:
            return text
        
        case_sensitive = self._search_options.get("case_sensitive", False)
        
        if not case_sensitive:
            text_lower = text.lower()
            query_lower = query.lower()
            index = text_lower.find(query_lower)
        else:
            index = text.find(query)
        
        if index >= 0:
            before = text[:index]
            match = text[index:index + len(query)]
            after = text[index + len(query):]
            return f"{before}<b style='color: #4CAF50; background-color: #2E7D32;'>{match}</b>{after}"
        
        return text
    
    def update_options(self, **kwargs):
        """Update search options."""
        self._search_options.update(kwargs)
    
    def get_current_results(self) -> List[dict]:
        """Get current search results."""
        return self._current_results
    
    def clear_results(self):
        """Clear search results."""
        self._current_results = []
        self._current_search_query = ""


class SearchBox(QLineEdit):
    """Search box widget with live filtering."""
    
    search_changed = Signal(str, dict)  # query, options
    search_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Search files and folders...")
        self.setMinimumHeight(32)
        
        # Search options
        self._options = {
            "case_sensitive": False,
            "whole_word": False,
            "search_folders": True,
            "search_files": True,
            "fuzzy": False,
        }
        
        self.textChanged.connect(self._on_text_changed)
        self.textEdited.connect(self._on_text_edited)
    
    def _on_text_changed(self, text: str):
        """Handle text changed (live filtering)."""
        self.search_changed.emit(text, self._options)
    
    def _on_text_edited(self, text: str):
        """Handle text edited (user input)."""
        self.search_requested.emit(text)
    
    def set_options(self, **kwargs):
        """Set search options."""
        self._options.update(kwargs)
    
    def get_options(self) -> dict:
        """Get current search options."""
        return self._options.copy()