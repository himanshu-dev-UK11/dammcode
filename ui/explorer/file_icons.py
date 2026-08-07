"""
File Icons Manager — v2.2

Language-specific file icons for the Explorer.
Supports: Python, C/C++, Java, JavaScript, TypeScript, HTML, CSS, JSON, XML,
Markdown, YAML, Rust, Go, PHP, Flutter, Dart, Git, Docker, Images, Videos, Archives, PDF
"""
from pathlib import Path
from typing import Dict, Optional
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt


# Language to icon mapping
FILE_ICONS: Dict[str, str] = {
    # Scripting languages
    ".py": "🐍",  # Python
    ".js": "🟡",  # JavaScript
    ".ts": "🟦",  # TypeScript
    ".jsx": "🟦",  # React
    ".tsx": "🟦",  # React
    ".php": "🐘",  # PHP
    ".rb": "💎",  # Ruby
    ".go": "🐹",  # Go (gopher)
    ".rs": "rust",  # Rust
    
    # Compiled languages
    ".c": "⚙️",  # C
    ".h": "⚙️",  # C header
    ".cpp": "⚙️",  # C++
    ".hpp": "⚙️",  # C++ header
    ".cc": "⚙️",  # C++
    ".hh": "⚙️",  # C++ header
    ".cxx": "⚙️",  # C++
    ".hxx": "⚙️",  # C++ header
    ".java": "☕",  # Java
    ".kt": "🐘",  # Kotlin
    ".scala": "🔬",  # Scala
    
    # Web languages
    ".html": "🌐",  # HTML
    ".htm": "🌐",  # HTML
    ".css": "🎨",  # CSS
    ".scss": "🎨",  # SCSS
    ".sass": "🎨",  # Sass
    ".less": "🎨",  # Less
    ".xml": "📋",  # XML
    ".xsd": "📋",  # XML Schema
    ".xsl": "📋",  # XSL
    ".json": "📝",  # JSON
    ".jsonc": "📝",  # JSONC
    ".yaml": "⚙️",  # YAML
    ".yml": "⚙️",  # YAML
    ".toml": ".toml",  # TOML
    ".ini": "⚙️",  # INI
    
    # Documentation
    ".md": "📄",  # Markdown
    ".markdown": "📄",  # Markdown
    ".rst": "📄",  # ReStructured Text
    ".txt": "📄",  # Text
    ".pdf": "📄",  # PDF
    
    # Config files
    ".env": "⚙️",  # Environment
    ".gitignore": "_git",  # Git ignore
    ".gitattributes": "git",  # Git attributes
    ".editorconfig": "⚙️",  # Editor config
    
    # Docker
    "dockerfile": "🐳",  # Dockerfile
    "docker-compose.yml": "🐳",  # Docker Compose
    ".dockerignore": "🐳",  # Docker ignore
    
    # Git
    ".git": "git",  # Git folder
    
    # Images
    ".png": "🖼️",  # PNG
    ".jpg": "🖼️",  # JPG
    ".jpeg": "🖼️",  # JPEG
    ".gif": "🖼️",  # GIF
    ".bmp": "🖼️",  # BMP
    ".svg": "🎨",  # SVG
    ".ico": "🖼️",  # Icon
    
    # Videos
    ".mp4": "🎬",  # MP4
    ".avi": "🎬",  # AVI
    ".mkv": "🎬",  # MKV
    ".mov": "🎬",  # MOV
    
    # Archives
    ".zip": "📦",  # ZIP
    ".rar": "📦",  # RAR
    ".tar": "📦",  # TAR
    ".gz": "📦",  # GZip
    ".7z": "📦",  # 7-Zip
    
    # Flutter/Dart
    ".dart": "🔵",  # Dart
    "pubspec.yaml": "🔵",  # Flutter
    "pubspec.yml": "🔵",  # Flutter
    
    # Unknown
    "default": "📄",
    "folder_open": "📂",
    "folder_closed": "📁",
    "git_modified": "✨",
    "git_added": "➕",
    "git_deleted": "❌",
    "git_renamed": " ↔️",
    "git_conflicted": "⚠️",
    "git_untracked": "?",
}

# Folder icons
FOLDER_ICONS = {
    "default": "📁",
    "open": "📂",
    "git": "git",
    "src": "📂",
    "tests": "🧪",
    "docs": "📚",
    "config": "⚙️",
    "assets": "🎨",
    "images": "🖼️",
    "videos": "🎬",
    "archives": "📦",
    "venv": "🐍",
    ".venv": "🐍",
    "node_modules": "📦",
    "dist": "📦",
    "build": "📦",
}


def get_file_icon(filename: str, is_folder: bool = False, git_status: str = None) -> str:
    """
    Get the appropriate icon for a file or folder.
    
    Args:
        filename: The filename or folder name
        is_folder: Whether this is a folder
        git_status: Git status for decoration (optional)
    
    Returns:
        Unicode emoji for the icon
    """
    # Handle folder first
    if is_folder:
        folder_name = filename.lower()
        
        # Check for specific folder types
        if folder_name in FOLDER_ICONS:
            return FOLDER_ICONS[folder_name]
        if folder_name.startswith("."):
            return "folder_closed"
        return "folder_closed"
    
    # Get file extension
    ext = Path(filename).suffix.lower()
    stem = Path(filename).stem.lower()
    
    # Check for specific filenames first
    if stem in FILE_ICONS:
        return FILE_ICONS[stem]
    
    # Check for extension
    if ext in FILE_ICONS:
        return FILE_ICONS[ext]
    
    # Return default
    return "default"


def get_git_status_icon(status: str) -> str:
    """Get icon for git status."""
    git_icons = {
        "modified": "✨",
        "added": "➕",
        "deleted": "❌",
        "renamed": "↔️",
        "conflicted": "⚠️",
        "untracked": "?",
        "ignored": "🎨",
    }
    return git_icons.get(status.lower(), "")


def get_file_extension(filename: str) -> str:
    """Get file extension with dot."""
    return Path(filename).suffix.lower()
