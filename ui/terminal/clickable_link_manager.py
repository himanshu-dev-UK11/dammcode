"""
Clickable Link Manager — v1.9

Detects and manages clickable links in terminal output.
"""
from PySide6.QtCore import QObject, QUrl
from pathlib import Path
import re
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class LinkInfo:
    """Information about a clickable link."""
    text: str
    start_pos: int
    end_pos: int
    link_type: str  # file_path, stack_trace, url, warning
    data: dict  # Additional data (path, line, url, etc.)


class ClickableLinkManager(QObject):
    """
    Detects clickable links in terminal output.
    Handles file paths, stack traces, URLs, and warnings.
    """
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self.links = []
    
    def detect_links(self, text: str) -> List[LinkInfo]:
        """Detect all clickable links in text."""
        links = []
        
        # Pattern for file paths with line numbers
        file_pattern = r'([A-Za-z]:)?[\\/][^\s]+?\.(py|js|ts|java|cpp|c|h|cc|cxx|go|rs|php|rb|sh|md|txt)(?::(\d+))?'
        
        # Pattern for stack traces
        stack_pattern = r'File\s+"([^"]+)",\s*line\s+(\d+)'
        
        # Pattern for URLs
        url_pattern = r'(https?://[^\s]+)'
        
        # Pattern for warnings
        warning_pattern = r'(WARNING|WARN):?\s*(.*)'
        
        patterns = [
            (file_pattern, "file_path"),
            (stack_pattern, "stack_trace"),
            (url_pattern, "url"),
            (warning_pattern, "warning"),
        ]
        
        for pattern, link_type in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start, end = match.span()
                
                if link_type == "file_path":
                    data = {
                        "path": match.group(1) + match.group(2) if match.group(1) else match.group(2),
                        "line": int(match.group(3)) if match.group(3) else None
                    }
                elif link_type == "stack_trace":
                    data = {
                        "path": match.group(1),
                        "line": int(match.group(2))
                    }
                elif link_type == "url":
                    data = {"url": match.group(1)}
                elif link_type == "warning":
                    data = {"text": match.group(2)}
                else:
                    data = {}
                
                links.append(LinkInfo(
                    text=match.group(0),
                    start=start,
                    end=end,
                    link_type=link_type,
                    data=data
                ))
        
        self.links = links
        return links
    
    def parse_file_path(self, text: str) -> Optional[dict]:
        """Parse file path from text."""
        pattern = r'([A-Za-z]:)?[\\/][^\s]+?\.[a-z]+(?::(\d+))?'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {
                "path": match.group(1) + match.group(2) if match.group(1) else match.group(2),
                "line": int(match.group(3)) if match.group(3) else None
            }
        return None
    
    def parse_stack_trace(self, text: str) -> List[dict]:
        """Parse stack trace from text."""
        pattern = r'File\s+"([^"]+)",\s*line\s+(\d+)'
        results = []
        
        for match in re.finditer(pattern, text):
            results.append({
                "path": match.group(1),
                "line": int(match.group(2))
            })
        
        return results
    
    def parse_warning(self, text: str) -> Optional[dict]:
        """Parse warning from text."""
        pattern = r'(WARNING|WARN):?\s*(.*)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {"text": match.group(2)}
        return None
    
    def get_link_at_position(self, text: str, pos: int) -> Optional[LinkInfo]:
        """Get link at a specific position in text."""
        for link in self.links:
            if link.start_pos <= pos <= link.end_pos:
                return link
        return None
    
    def is_clickable(self, text: str, pos: int) -> bool:
        """Check if position is clickable."""
        return self.get_link_at_position(text, pos) is not None