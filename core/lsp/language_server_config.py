"""
Language Server Configuration classes.

Defines configurations for different language servers.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class LanguageServerConfig:
    """Configuration for a language server."""
    
    language_id: str
    name: str
    command: List[str]
    args: List[str] = field(default_factory=list)
    initialization_options: Dict[str, Any] = field(default_factory=dict)
    root_uri: Optional[str] = None
    workspace_folders: List[Dict[str, str]] = field(default_factory=list)
    supported_extensions: List[str] = field(default_factory=list)


# Predefined language server configurations
def get_standard_language_servers() -> Dict[str, LanguageServerConfig]:
    """Get standard language server configurations."""
    return {
        "python": LanguageServerConfig(
            language_id="python",
            name="Pyright",
            command=["pyright-langserver", "--stdio"],
            supported_extensions=[".py"],
        ),
        "javascript": LanguageServerConfig(
            language_id="javascript",
            name="TypeScript Language Server",
            command=["typescript-language-server", "--stdio"],
            supported_extensions=[".js", ".jsx"],
        ),
        "typescript": LanguageServerConfig(
            language_id="typescript",
            name="TypeScript Language Server",
            command=["typescript-language-server", "--stdio"],
            supported_extensions=[".ts", ".tsx"],
        ),
        "cpp": LanguageServerConfig(
            language_id="cpp",
            name="clangd",
            command=["clangd", "--background-index"],
            supported_extensions=[".cpp", ".cc", ".cxx", ".hpp", ".h", ".hxx"],
        ),
        "c": LanguageServerConfig(
            language_id="c",
            name="clangd",
            command=["clangd", "--background-index"],
            supported_extensions=[".c", ".h"],
        ),
        "java": LanguageServerConfig(
            language_id="java",
            name="Eclipse JDT Language Server",
            command=["java", "-jar", "path/to/jdt-language-server.jar"],
            supported_extensions=[".java"],
        ),
        "html": LanguageServerConfig(
            language_id="html",
            name="HTML Language Server",
            command=["vscode-html-language-server", "--stdio"],
            supported_extensions=[".html", ".htm"],
        ),
        "css": LanguageServerConfig(
            language_id="css",
            name="CSS Language Server",
            command=["vscode-css-language-server", "--stdio"],
            supported_extensions=[".css", ".scss", ".less"],
        ),
        "json": LanguageServerConfig(
            language_id="json",
            name="JSON Language Server",
            command=["vscode-json-language-server", "--stdio"],
            supported_extensions=[".json"],
        ),
        "yaml": LanguageServerConfig(
            language_id="yaml",
            name="YAML Language Server",
            command=["yaml-language-server", "--stdio"],
            supported_extensions=[".yaml", ".yml"],
        ),
        "markdown": LanguageServerConfig(
            language_id="markdown",
            name="Markdown Language Server",
            command=["markdown-language-server", "--stdio"],
            supported_extensions=[".md"],
        ),
        "rust": LanguageServerConfig(
            language_id="rust",
            name="rust-analyzer",
            command=["rust-analyzer"],
            supported_extensions=[".rs"],
        ),
        "go": LanguageServerConfig(
            language_id="go",
            name="gopls",
            command=["gopls", "serve"],
            supported_extensions=[".go"],
        ),
        "php": LanguageServerConfig(
            language_id="php",
            name="Intelephense",
            command=["intelephense", "--stdio"],
            supported_extensions=[".php"],
        ),
    }
