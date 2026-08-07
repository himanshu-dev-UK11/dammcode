"""
Language Statistics — calculates language breakdown for a project.

This module analyzes a project and calculates:
- Percentage of code per language
- Total lines of code per language
- File counts per language

This is used for:
- Project overview
- Resource allocation
- Language-specific optimizations
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from core.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class LanguageStats:
    """Statistics for a single language."""
    language: str
    file_count: int = 0
    line_count: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    percentage: float = 0.0
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "language": self.language,
            "file_count": self.file_count,
            "line_count": self.line_count,
            "code_lines": self.code_lines,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
            "percentage": self.percentage,
        }


class LanguageStatistics:
    """
    Calculates language statistics for a project.
    
    This class analyzes all source files in a project and calculates
    statistics for each programming language.
    """
    
    # Mapping of extensions to language names
    EXTENSION_MAP: Dict[str, str] = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'JavaScript',
        '.tsx': 'TypeScript',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C',
        '.hpp': 'C++',
        '.go': 'Go',
        '.rs': 'Rust',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.cs': 'C#',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.tsv': 'TSQL',
        '.pl': 'Perl',
        '.pm': 'Perl',
        '.r': 'R',
        '.R': 'R',
        '.m': 'Objective-C',
        '.mm': 'Objective-C',
        '.sh': 'Bash',
        '.bash': 'Bash',
        '.zsh': 'Zsh',
        '.fish': 'Fish',
        '.ps1': 'PowerShell',
        '.cmd': 'Batch',
        '.bat': 'Batch',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.less': 'Less',
        '.json': 'JSON',
        '.xml': 'XML',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.md': 'Markdown',
        '.rst': 'reStructuredText',
        '.txt': 'Text',
        '.sql': 'SQL',
        '.graphql': 'GraphQL',
        '.proto': 'Protocol Buffers',
    }
    
    # Comment patterns for different languages
    COMMENT_PATTERNS: Dict[str, Tuple[str, str]] = {
        'Python': ('#', None),
        'JavaScript': ('//', '/* */'),
        'TypeScript': ('//', '/* */'),
        'Java': ('//', '/* */'),
        'C': ('//', '/* */'),
        'C++': ('//', '/* */'),
        'Go': ('//', '/* */'),
        'Rust': ('//', '/* */'),
        'PHP': ('//', '/* */'),
        'Ruby': ('#', None),
        'C#': ('//', '/* */'),
        'Swift': ('//', '/* */'),
        'Kotlin': ('//', '/* */'),
        'Scala': ('//', '/* */'),
        'Bash': ('#', None),
        'Zsh': ('#', None),
        'Fish': ('#', None),
        'PowerShell': ('#', None),
        'Batch': ('REM', None),
        'SQL': ('--', None),
    }
    
    # Blank line patterns
    BLANK_PATTERNS = ['', ' ', '\t']
    
    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path).resolve()
        self.language_stats: Dict[str, LanguageStats] = {}
        self.total_lines = 0
        self.total_files = 0
        
    def calculate(self) -> Dict[str, LanguageStats]:
        """
        Calculate language statistics for the project.
        
        Returns:
            Dictionary mapping language names to LanguageStats
        """
        logger.info(f"Calculating language statistics for: {self.project_path}")
        
        # Reset stats
        self.language_stats = {}
        self.total_lines = 0
        self.total_files = 0
        
        # Find all source files
        patterns = [
            "*.py", "*.js", "*.ts", "*.jsx", "*.tsx",
            "*.java", "*.c", "*.cpp", "*.h", "*.hpp",
            "*.go", "*.rs", "*.php", "*.rb", "*.cs",
            "*.swift", "*.kt", "*.scala",
            "*.sh", "*.bash", "*.zsh", "*.fish",
            "*.ps1", "*.cmd", "*.bat",
            "*.html", "*.css", "*.scss", "*.less",
            "*.json", "*.xml", "*.yaml", "*.yml",
            "*.md", "*.rst", "*.sql", "*.graphql",
            "*.proto",
        ]
        
        # Process each file
        for pattern in patterns:
            for file_path in self.project_path.rglob(pattern):
                self._process_file(file_path)
                
        # Calculate percentages
        self._calculate_percentages()
        
        logger.info(f"Language statistics calculated: {len(self.language_stats)} languages")
        
        return self.language_stats
    
    def _process_file(self, file_path: Path):
        """Process a single file to calculate language statistics."""
        ext = file_path.suffix.lower()
        language = self.EXTENSION_MAP.get(ext, "Unknown")
        
        # Initialize language stats if not exists
        if language not in self.language_stats:
            self.language_stats[language] = LanguageStats(language=language)
            
        stats = self.language_stats[language]
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            stats.file_count += 1
            stats.line_count += len(lines)
            self.total_lines += len(lines)
            self.total_files += 1
            
            # Analyze lines
            for line in lines:
                stripped = line.strip()
                
                if not stripped:
                    stats.blank_lines += 1
                elif self._is_comment(stripped, language):
                    stats.comment_lines += 1
                else:
                    stats.code_lines += 1
                    
        except Exception as e:
            logger.warning(f"Error processing file {file_path}: {e}")
            
    def _is_comment(self, line: str, language: str) -> bool:
        """Check if a line is a comment."""
        comment_start, comment_block = self.COMMENT_PATTERNS.get(language, ('#', None))
        
        if line.startswith(comment_start):
            return True
            
        if comment_block:
            if line.startswith(comment_block.split()[0]):
                return True
                
        return False
    
    def _calculate_percentages(self):
        """Calculate percentage for each language."""
        if self.total_lines == 0:
            return
            
        for stats in self.language_stats.values():
            stats.percentage = round((stats.line_count / self.total_lines) * 100, 2)
            
    def get_primary_language(self) -> Optional[str]:
        """Get the primary (most used) language."""
        if not self.language_stats:
            return None
            
        return max(self.language_stats.keys(), key=lambda x: self.language_stats[x].line_count)
    
    def get_language_percentages(self) -> Dict[str, float]:
        """Get language percentages as a dictionary."""
        return {lang: stats.percentage for lang, stats in self.language_stats.items()}
    
    def get_top_languages(self, limit: int = 5) -> List[Tuple[str, LanguageStats]]:
        """Get top N languages by line count."""
        sorted_langs = sorted(
            self.language_stats.items(),
            key=lambda x: x[1].line_count,
            reverse=True
        )
        return sorted_langs[:limit]
    
    def get_total_stats(self) -> Dict[str, int]:
        """Get total statistics."""
        return {
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "total_languages": len(self.language_stats),
        }
    
    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "project_path": str(self.project_path),
            "languages": {
                lang: stats.to_dict()
                for lang, stats in self.language_stats.items()
            },
            "total_lines": self.total_lines,
            "total_files": self.total_files,
            "primary_language": self.get_primary_language(),
        }