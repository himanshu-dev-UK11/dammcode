"""
Documentation Indexer — automatically indexes project documentation.

This module indexes:
- README files
- Documentation in markdown files
- Code comments (docstrings)
- API documentation
- Architecture notes

The index can be used for:
- Context generation for AI prompts
- Documentation coverage analysis
- Auto-generated API docs
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from core.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class DocumentationEntry:
    """Represents a documentation entry."""
    path: str
    title: str
    content: str
    entry_type: str  # readme, doc, comment, api, architecture
    language: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "path": self.path,
            "title": self.title,
            "content": self.content,
            "entry_type": self.entry_type,
            "language": self.language,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "tags": self.tags,
        }


class DocumentationIndexer:
    """
    Indexes documentation across a project.
    
    This indexer scans for documentation in multiple formats:
    - README.md files
    - docs/ directory markdown files
    - Code comments (docstrings)
    - Architecture decision records
    """
    
    # README file names
    README_NAMES = [
        "README.md", "README.rst", "README.txt", "README",
        "readme.md", "readme.rst", "readme.txt",
    ]
    
    # Documentation patterns
    DOC_PATTERNS = [
        "docs/**/*.md",
        "docs/**/*.rst",
        "docs/**/*.txt",
        "doc/**/*.md",
        "doc/**/*.rst",
    ]
    
    # Architecture notes patterns
    ARCHITECTURE_NAMES = [
        "ARCHITECTURE.md", "ARCHITECTURE.rst",
        "ADR/**/*.md", "adr/**/*.md",
        "docs/decisions/**/*.md",
    ]
    
    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path).resolve()
        self.index: List[DocumentationEntry] = []
        
    def index(self) -> List[DocumentationEntry]:
        """
        Index all documentation in the project.
        
        Returns:
            List of DocumentationEntry objects
        """
        logger.info(f"Indexing documentation for: {self.project_path}")
        
        # Reset index
        self.index = []
        
        # Index README files
        self._index_readmes()
        
        # Index documentation files
        self._index_docs()
        
        # Index architecture notes
        self._index_architecture()
        
        # Index code comments (optional - can be slow)
        # self._index_comments()
        
        logger.info(f"Indexed {len(self.index)} documentation entries")
        
        return self.index
    
    def _index_readmes(self):
        """Index all README files."""
        for readme_name in self.README_NAMES:
            for readme_path in self.project_path.rglob(readme_name):
                self._index_readme(readme_path)
                
    def _index_readme(self, file_path: Path):
        """Index a single README file."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Extract title (first # heading)
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else file_path.name
            
            # Truncate long content
            truncated_content = self._truncate_content(content)
            
            entry = DocumentationEntry(
                path=str(file_path.relative_to(self.project_path)),
                title=title,
                content=truncated_content,
                entry_type="readme",
                language=self._detect_language_for_file(file_path),
                tags=["readme", "overview"],
            )
            
            self.index.append(entry)
            
        except Exception as e:
            logger.warning(f"Error indexing README {file_path}: {e}")
    
    def _index_docs(self):
        """Index documentation files in docs directory."""
        for pattern in self.DOC_PATTERNS:
            for doc_path in self.project_path.rglob(pattern):
                # Skip if already indexed as README
                if doc_path.name in self.README_NAMES:
                    continue
                    
                self._index_doc(doc_path)
                
    def _index_doc(self, file_path: Path):
        """Index a single documentation file."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Extract title (first # heading or filename)
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else file_path.stem
            
            # Truncate content
            truncated_content = self._truncate_content(content)
            
            # Determine entry type based on path
            entry_type = "doc"
            if "architecture" in str(file_path).lower():
                entry_type = "architecture"
            elif "api" in str(file_path).lower():
                entry_type = "api"
                
            # Extract tags
            tags = [entry_type]
            if "tutorial" in str(file_path).lower():
                tags.append("tutorial")
            if "guide" in str(file_path).lower():
                tags.append("guide")
                
            entry = DocumentationEntry(
                path=str(file_path.relative_to(self.project_path)),
                title=title,
                content=truncated_content,
                entry_type=entry_type,
                language=self._detect_language_for_file(file_path),
                tags=tags,
            )
            
            self.index.append(entry)
            
        except Exception as e:
            logger.warning(f"Error indexing doc {file_path}: {e}")
    
    def _index_architecture(self):
        """Index architecture decision records and notes."""
        for arch_name in self.ARCHITECTURE_NAMES:
            if "**" in arch_name:
                # Pattern with subdirectories
                base_dir = arch_name.split("**")[0].rstrip("/")
                for arch_path in self.project_path.rglob(base_dir + "*.md"):
                    self._index_architecture_file(arch_path)
            else:
                # Single file
                arch_path = self.project_path / arch_name
                if arch_path.exists():
                    self._index_architecture_file(arch_path)
                    
    def _index_architecture_file(self, file_path: Path):
        """Index a single architecture file."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Extract title
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else file_path.stem
            
            # Truncate content
            truncated_content = self._truncate_content(content)
            
            entry = DocumentationEntry(
                path=str(file_path.relative_to(self.project_path)),
                title=title,
                content=truncated_content,
                entry_type="architecture",
                language=self._detect_language_for_file(file_path),
                tags=["architecture", "adr"],
            )
            
            self.index.append(entry)
            
        except Exception as e:
            logger.warning(f"Error indexing architecture {file_path}: {e}")
    
    def _index_comments(self):
        """Index code comments (optional - can be slow)."""
        # This is a simplified implementation
        # A full implementation would parse source files and extract docstrings
        
        patterns = ["*.py", "*.js", "*.ts", "*.java", "*.c", "*.cpp", "*.go", "*.rs", "*.php", "*.rb", "*.cs"]
        
        for pattern in patterns:
            for file_path in self.project_path.rglob(pattern):
                self._index_file_comments(file_path)
                
    def _index_file_comments(self, file_path: Path):
        """Index comments in a single file."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            # Detect comment style
            ext = file_path.suffix.lower()
            comment_prefix = self._get_comment_prefix(ext)
            
            for i, line in enumerate(lines, 1):
                if line.strip().startswith(comment_prefix):
                    # Extract comment content
                    comment = line.strip()[len(comment_prefix):].strip()
                    
                    if len(comment) > 10:  # Skip very short comments
                        entry = DocumentationEntry(
                            path=str(file_path.relative_to(self.project_path)),
                            title=f"Line {i}",
                            content=comment,
                            entry_type="comment",
                            language=self._detect_language_for_file(file_path),
                            line_start=i,
                            line_end=i,
                            tags=["comment"],
                        )
                        self.index.append(entry)
                        
        except Exception as e:
            logger.warning(f"Error indexing comments {file_path}: {e}")
    
    def _get_comment_prefix(self, ext: str) -> str:
        """Get comment prefix for a file extension."""
        prefix_map = {
            '.py': '#',
            '.js': '//',
            '.ts': '//',
            '.java': '//',
            '.c': '//',
            '.cpp': '//',
            '.go': '//',
            '.rs': '//',
            '.php': '//',
            '.rb': '#',
            '.cs': '//',
            '.sh': '#',
            '.bash': '#',
        }
        return prefix_map.get(ext, '#')
    
    def _truncate_content(self, content: str, max_length: int = 5000) -> str:
        """Truncate content to a maximum length."""
        if len(content) <= max_length:
            return content
        return content[:max_length] + f"\n... [truncated, original length: {len(content)} characters]..."
    
    def _detect_language_for_file(self, file_path: Path) -> Optional[str]:
        """Detect language for a file."""
        ext = file_path.suffix.lower()
        extension_map = {
            '.md': 'Markdown',
            '.rst': 'reStructuredText',
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
        }
        return extension_map.get(ext)
    
    def get_readme(self) -> Optional[DocumentationEntry]:
        """Get the main README entry."""
        for entry in self.index:
            if entry.entry_type == "readme":
                return entry
        return None
    
    def get_architecture_docs(self) -> List[DocumentationEntry]:
        """Get all architecture documentation."""
        return [e for e in self.index if e.entry_type == "architecture"]
    
    def get_api_docs(self) -> List[DocumentationEntry]:
        """Get all API documentation."""
        return [e for e in self.index if e.entry_type == "api"]
    
    def get_docs_by_tag(self, tag: str) -> List[DocumentationEntry]:
        """Get documentation entries with a specific tag."""
        return [e for e in self.index if tag in e.tags]
    
    def search_docs(self, query: str) -> List[DocumentationEntry]:
        """Search documentation for a query."""
        query_lower = query.lower()
        results = []
        
        for entry in self.index:
            if query_lower in entry.title.lower() or query_lower in entry.content.lower():
                results.append(entry)
                
        return results
    
    def get_coverage_stats(self) -> Dict[str, object]:
        """Get documentation coverage statistics."""
        readme_count = sum(1 for e in self.index if e.entry_type == "readme")
        architecture_count = sum(1 for e in self.index if e.entry_type == "architecture")
        doc_count = sum(1 for e in self.index if e.entry_type == "doc")
        
        return {
            "total_entries": len(self.index),
            "readmes": readme_count,
            "architecture_docs": architecture_count,
            "general_docs": doc_count,
            "languages": list(set(e.language for e in self.index if e.language)),
        }
    
    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "project_path": str(self.project_path),
            "entries": [e.to_dict() for e in self.index],
            "coverage": self.get_coverage_stats(),
        }