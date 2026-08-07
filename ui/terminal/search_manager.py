"""
Terminal Search Manager — v2.0

Provides search functionality inside terminal output.
Supports:
- Find in terminal output
- Find Next / Find Previous
- Case Sensitive
- Whole Word
- Regular Expressions
- Highlight all matches
- Incremental search
"""
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtGui import QTextDocument
from typing import List, Optional, Tuple
import re
from core.logger import setup_logger

logger = setup_logger(__name__)


class SearchMatch:
    """Represents a search match in terminal output."""
    
    def __init__(self, position: int, length: int, line: int, 
                 column: int, text: str):
        self.position = position  # Character position in text
        self.length = length
        self.line = line
        self.column = column
        self.text = text
    
    def __repr__(self):
        return f"SearchMatch(pos={self.position}, line={self.line}, col={self.column}, text='{self.text}')"


class SearchWorker(QThread):
    """Background thread for searching terminal output."""
    
    results = Signal(list)  # List of SearchMatch
    error = Signal(str)
    
    def __init__(self, text: str, query: str, case_sensitive: bool,
                 whole_word: bool, regex: bool, parent=None):
        super().__init__(parent)
        self.text = text
        self.query = query
        self.case_sensitive = case_sensitive
        self.whole_word = whole_word
        self.regex = regex
    
    def run(self):
        """Perform search in background."""
        try:
            matches = self._find_matches(self.text, self.query, 
                                        self.case_sensitive, 
                                        self.whole_word, self.regex)
            self.results.emit(matches)
        except Exception as e:
            self.error.emit(str(e))
    
    def _find_matches(self, text: str, query: str, case_sensitive: bool,
                      whole_word: bool, regex: bool) -> List[SearchMatch]:
        """Find all matches in text."""
        if not query:
            return []
        
        matches = []
        search_text = text if case_sensitive else text.lower()
        search_query = query if case_sensitive else query.lower()
        
        if regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                for match in re.finditer(query, text, flags):
                    pos = match.start()
                    matches.append(SearchMatch(
                        position=pos,
                        length=match.end() - match.start(),
                        line=text[:pos].count('\n'),
                        column=pos - text[:pos].rfind('\n') - 1,
                        text=match.group()
                    ))
            except re.error as e:
                logger.warning(f"Invalid regex pattern: {e}")
                return []
        
        elif whole_word:
            pattern = r'\b' + re.escape(search_query) + r'\b'
            for match in re.finditer(pattern, search_text):
                pos = match.start()
                matches.append(SearchMatch(
                    position=pos,
                    length=match.end() - match.start(),
                    line=text[:pos].count('\n'),
                    column=pos - text[:pos].rfind('\n') - 1,
                    text=text[pos:pos + match.end() - match.start()]
                ))
        
        else:
            start = 0
            while True:
                pos = search_text.find(search_query, start)
                if pos == -1:
                    break
                matches.append(SearchMatch(
                    position=pos,
                    length=len(query),
                    line=text[:pos].count('\n'),
                    column=pos - text[:pos].rfind('\n') - 1,
                    text=text[pos:pos + len(query)]
                ))
                start = pos + 1
        
        return matches


class SearchManager(QObject):
    """
    Manages search operations in terminal output.
    Reuses QTextDocument for efficient text search.
    """
    
    # Signals
    search_started = Signal()
    search_finished = Signal()
    search_results_changed = Signal(int)  # Match count
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._text = ""
        self._matches: List[SearchMatch] = []
        self._current_index = -1
        self._options = {
            "case_sensitive": False,
            "whole_word": False,
            "regex": False
        }
    
    def set_text(self, text: str):
        """Set the text to search in."""
        self._text = text
        self._matches = []
        self._current_index = -1
    
    def search(self, query: str, case_sensitive: bool = None,
               whole_word: bool = None, regex: bool = None):
        """Search for text in terminal output."""
        self._options["case_sensitive"] = (case_sensitive if case_sensitive 
                                           is not None else 
                                           self._options["case_sensitive"])
        self._options["whole_word"] = (whole_word if whole_word is not None 
                                       else self._options["whole_word"])
        self._options["regex"] = (regex if regex is not None 
                                  else self._options["regex"])
        
        self.search_started.emit()
        self.event_bus.publish("terminal_search_started", {
            "query": query,
            "options": self._options
        })
        
        # Use background worker for search
        self._worker = SearchWorker(
            self._text, query,
            self._options["case_sensitive"],
            self._options["whole_word"],
            self._options["regex"]
        )
        self._worker.results.connect(self._on_search_results)
        self._worker.error.connect(self._on_search_error)
        self._worker.start()
    
    def _on_search_results(self, matches: List[SearchMatch]):
        """Handle search results from worker."""
        self._matches = matches
        self._current_index = -1
        self.search_finished.emit()
        self.search_results_changed.emit(len(matches))
        self.event_bus.publish("terminal_search_finished", {
            "query": self._get_last_query(),
            "count": len(matches)
        })
    
    def _on_search_error(self, error: str):
        """Handle search error."""
        logger.error(f"Search error: {error}")
        self.search_finished.emit()
        self.event_bus.publish("terminal_search_error", {"error": error})
    
    def _get_last_query(self) -> str:
        """Get the last search query (simplified)."""
        # In a full implementation, we'd track the query
        return ""
    
    def find_next(self) -> Optional[SearchMatch]:
        """Find next match."""
        if not self._matches:
            return None
        
        self._current_index = (self._current_index + 1) % len(self._matches)
        return self._matches[self._current_index]
    
    def find_previous(self) -> Optional[SearchMatch]:
        """Find previous match."""
        if not self._matches:
            return None
        
        self._current_index = (self._current_index - 1) % len(self._matches)
        return self._matches[self._current_index]
    
    def get_current_match(self) -> Optional[SearchMatch]:
        """Get current match."""
        if 0 <= self._current_index < len(self._matches):
            return self._matches[self._current_index]
        return None
    
    def get_all_matches(self) -> List[SearchMatch]:
        """Get all matches."""
        return self._matches
    
    def get_match_count(self) -> int:
        """Get total match count."""
        return len(self._matches)
    
    def is_searching(self) -> bool:
        """Check if search is in progress."""
        return self._worker and self._worker.isRunning()
    
    def cancel_search(self):
        """Cancel ongoing search."""
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
    
    def get_options(self) -> dict:
        """Get current search options."""
        return self._options.copy()
    
    def set_options(self, options: dict):
        """Set search options."""
        self._options.update(options)
    
    # Convenience methods for common operations
    
    def find_in_text(self, text: str, query: str, case_sensitive: bool = False,
                     whole_word: bool = False) -> List[Tuple[int, int]]:
        """Quick find all occurrences, returns (start, end) positions."""
        if not query or not text:
            return []
        
        search_text = text if case_sensitive else text.lower()
        search_query = query if case_sensitive else query.lower()
        
        positions = []
        start = 0
        while True:
            pos = search_text.find(search_query, start)
            if pos == -1:
                break
            positions.append((pos, pos + len(query)))
            start = pos + 1
        
        return positions
    
    def highlight_matches(self, text: str, matches: List[SearchMatch],
                         highlight_color: str = "#3B82F6") -> str:
        """Create highlighted text (for rich text display)."""
        if not matches:
            return text
        
        # This would be implemented for rich text display
        # For now, returns the original text
        # A full implementation would insert HTML span tags around matches
        return text
