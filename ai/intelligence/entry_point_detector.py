"""
Entry Point Detector — automatically detects application entry points.

This module detects common entry point files for different frameworks
and technologies:
- Python: main.py, app.py, run.py, server.py
- JavaScript: index.js, server.js, app.js
- React/Next.js: index.tsx, app.tsx
- Flutter: main.dart
- Android: MainActivity.java, MainApplication.java
- iOS: main.m, AppDelegate.m
- C/C++: main.c, main.cpp, WinMain.c
- Java: Main.java
- C#: Program.cs
- Go: main.go
- Rust: main.rs
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from core.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class EntryPoint:
    """Represents a detected entry point."""
    path: str
    language: str
    framework: Optional[str] = None
    confidence: float = 0.0
    entry_type: str = "application"  # application, library, test, cli
    main_function: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "path": self.path,
            "language": self.language,
            "framework": self.framework,
            "confidence": self.confidence,
            "entry_type": self.entry_type,
            "main_function": self.main_function,
            "description": self.description,
        }


class EntryPointDetector:
    """
    Detects entry points for different frameworks and technologies.
    
    This detector scans for common entry point patterns and analyzes
    the content to confirm and provide additional information about
    the entry point.
    """
    
    # Entry point patterns by language/framework
    ENTRY_PATTERNS: Dict[str, List[Dict]] = {
        "python": [
            {
                "files": ["main.py", "app.py", "run.py", "server.py", "wsgi.py"],
                "function_patterns": ["def main", "app = Flask", "app = FastAPI", "app = Django", "async def main"],
                "confidence": 0.9,
                "entry_type": "application",
            },
            {
                "files": ["__main__.py"],
                "function_patterns": ["if __name__ == '__main__'"],
                "confidence": 0.8,
                "entry_type": "application",
            },
            {
                "files": ["cli.py", "command.py"],
                "function_patterns": ["def main", "argparse", "click"],
                "confidence": 0.7,
                "entry_type": "cli",
            },
            {
                "files": ["test_*.py", "*_test.py"],
                "function_patterns": ["def test_", "pytest", "unittest"],
                "confidence": 0.5,
                "entry_type": "test",
            },
        ],
        "javascript": [
            {
                "files": ["index.js", "app.js", "server.js", "main.js"],
                "function_patterns": ["app.listen", "server.listen", "export default", "module.exports"],
                "confidence": 0.9,
                "entry_type": "application",
            },
            {
                "files": ["index.ts", "app.ts", "main.ts"],
                "function_patterns": ["app.listen", "server.listen", "export default", "module.exports"],
                "confidence": 0.8,
                "entry_type": "application",
            },
            {
                "files": ["test.js", "test.ts", "spec.js", "spec.ts"],
                "function_patterns": ["describe(", "it(", "test(", "jest"],
                "confidence": 0.7,
                "entry_type": "test",
            },
        ],
        "typescript": [
            {
                "files": ["index.ts", "app.ts", "main.ts"],
                "function_patterns": ["app.listen", "server.listen", "export default", "module.exports"],
                "confidence": 0.9,
                "entry_type": "application",
            },
        ],
        "react": [
            {
                "files": ["index.tsx", "app.tsx"],
                "function_patterns": ["ReactDOM.render", "createRoot", "export default"],
                "confidence": 0.9,
                "entry_type": "application",
            },
        ],
        "flutter": [
            {
                "files": ["main.dart"],
                "function_patterns": ["void main()", "runApp"],
                "confidence": 0.95,
                "entry_type": "application",
            },
        ],
        "android": [
            {
                "files": ["MainActivity.java", "MainActivity.kt"],
                "function_patterns": ["onCreate", "extends Activity", "class MainActivity"],
                "confidence": 0.8,
                "entry_type": "application",
            },
        ],
        "ios": [
            {
                "files": ["main.m", "main.swift"],
                "function_patterns": ["int main", "UIApplicationMain", "@main"],
                "confidence": 0.85,
                "entry_type": "application",
            },
        ],
        "c": [
            {
                "files": ["main.c"],
                "function_patterns": ["int main", "void main"],
                "confidence": 0.95,
                "entry_type": "application",
            },
        ],
        "cpp": [
            {
                "files": ["main.cpp", "WinMain.cpp"],
                "function_patterns": ["int main", "int WinMain"],
                "confidence": 0.95,
                "entry_type": "application",
            },
        ],
        "java": [
            {
                "files": ["Main.java"],
                "function_patterns": ["public static void main", "public static void main\\(String\\[\\]"],
                "confidence": 0.9,
                "entry_type": "application",
            },
        ],
        "csharp": [
            {
                "files": ["Program.cs"],
                "function_patterns": ["static void Main", "async Task Main", "var builder = WebApplication"],
                "confidence": 0.9,
                "entry_type": "application",
            },
        ],
        "go": [
            {
                "files": ["main.go"],
                "function_patterns": ["func main\\(\\)", "package main"],
                "confidence": 0.95,
                "entry_type": "application",
            },
        ],
        "rust": [
            {
                "files": ["main.rs"],
                "function_patterns": ["fn main\\(\\)", "#\\[tokio::main\\]"],
                "confidence": 0.95,
                "entry_type": "application",
            },
        ],
    }
    
    # Framework detection patterns
    FRAMEWORK_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
        "flask": [
            ("*.py", "Flask\\("),
            ("*.py", "from flask import"),
        ],
        "django": [
            ("*.py", "from django"),
            ("*.py", "import django"),
            ("settings.py", None),
        ],
        "fastapi": [
            ("*.py", "FastAPI\\("),
            ("*.py", "from fastapi"),
        ],
        "express": [
            ("*.js", "express\\("),
            ("*.js", "const express ="),
        ],
        "next": [
            ("*.js", "next\\("),
            ("next.config.js", None),
        ],
        "react": [
            ("*.tsx", "React.createElement"),
            ("*.tsx", "import React"),
        ],
        "spring": [
            ("*.java", "@SpringBootApplication"),
            ("pom.xml", None),
        ],
        "fastapi": [
            ("*.py", "FastAPI\\("),
            ("*.py", "uvicorn.run"),
        ],
    }
    
    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path).resolve()
        self.detected_entries: List[EntryPoint] = []
        
    def detect(self) -> List[EntryPoint]:
        """
        Detect all entry points in the project.
        
        Returns:
            List of EntryPoint objects
        """
        logger.info(f"Detecting entry points for: {self.project_path}")
        
        # Reset entries
        self.detected_entries = []
        
        # Check all languages
        for language, patterns in self.ENTRY_PATTERNS.items():
            self._detect_language_entries(language, patterns)
            
        # Detect framework-specific entries
        self._detect_framework_entries()
        
        # Sort by confidence
        self.detected_entries.sort(key=lambda x: x.confidence, reverse=True)
        
        logger.info(f"Detected {len(self.detected_entries)} entry points")
        
        return self.detected_entries
    
    def _detect_language_entries(self, language: str, patterns: List[Dict]):
        """Detect entry points for a specific language."""
        for pattern in patterns:
            for file_pattern in pattern["files"]:
                for file_path in self.project_path.rglob(file_pattern):
                    entry = self._analyze_entry(file_path, language, pattern)
                    if entry:
                        self.detected_entries.append(entry)
                        
    def _analyze_entry(self, file_path: Path, language: str, pattern: Dict) -> Optional[EntryPoint]:
        """Analyze a file to confirm it's an entry point."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Check if any function pattern matches
            main_function = None
            for func_pattern in pattern["function_patterns"]:
                if re.search(func_pattern, content):
                    # Extract function name
                    match = re.search(r'(?:def|fun|func)\s+(\w+)\s*\(', content)
                    if match:
                        main_function = match.group(1)
                    break
                    
            # Determine entry type
            entry_type = pattern.get("entry_type", "application")
            
            # Detect framework
            framework = self._detect_framework_for_file(file_path)
            
            # Build description
            description = f"Entry point for {language} {entry_type} application"
            if framework:
                description += f" using {framework}"
                
            return EntryPoint(
                path=str(file_path.relative_to(self.project_path)),
                language=language,
                framework=framework,
                confidence=pattern["confidence"],
                entry_type=entry_type,
                main_function=main_function,
                description=description,
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
            return None
    
    def _detect_framework_for_file(self, file_path: Path) -> Optional[str]:
        """Detect framework for a specific file."""
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            for pattern_file, pattern_text in patterns:
                if pattern_file == "*" or file_path.name == pattern_file:
                    if pattern_text is None or re.search(pattern_text, content):
                        return framework
                        
        return None
    
    def _detect_framework_entries(self):
        """Detect framework-specific entry points."""
        # Check for common framework entry points
        framework_patterns = {
            "next": "app/page.tsx",
            "svelte": "src/main.js",
            "vue": "src/main.js",
            "angular": "src/main.ts",
        }
        
        for framework, entry_file in framework_patterns.items():
            entry_path = self.project_path / entry_file
            if entry_path.exists():
                entry = EntryPoint(
                    path=entry_file,
                    language=self._detect_language_for_file(entry_path),
                    framework=framework,
                    confidence=0.9,
                    entry_type="application",
                    description=f"Entry point for {framework} application",
                )
                self.detected_entries.append(entry)
                
    def _detect_language_for_file(self, file_path: Path) -> str:
        """Detect language for a file."""
        ext = file_path.suffix.lower()
        extension_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.kt': 'Kotlin',
            '.go': 'Go',
            '.rs': 'Rust',
        }
        return extension_map.get(ext, "Unknown")
    
    def get_primary_entry_point(self) -> Optional[EntryPoint]:
        """Get the primary (highest confidence) entry point."""
        if not self.detected_entries:
            return None
        return self.detected_entries[0]
    
    def get_entry_points_by_type(self, entry_type: str) -> List[EntryPoint]:
        """Get entry points of a specific type."""
        return [e for e in self.detected_entries if e.entry_type == entry_type]
    
    def get_entry_points_by_framework(self, framework: str) -> List[EntryPoint]:
        """Get entry points for a specific framework."""
        return [e for e in self.detected_entries if e.framework == framework]
    
    def get_entry_points_by_language(self, language: str) -> List[EntryPoint]:
        """Get entry points for a specific language."""
        return [e for e in self.detected_entries if e.language == language]
    
    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "project_path": str(self.project_path),
            "entry_points": [e.to_dict() for e in self.detected_entries],
            "primary_entry_point": self.get_primary_entry_point().to_dict() if self.get_primary_entry_point() else None,
        }