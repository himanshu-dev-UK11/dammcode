"""
File Preview Manager — v2.3

Manages file preview functionality in the Explorer.
Supports: Image, Markdown, Text, JSON preview without opening editor tab.
"""
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QScrollArea, QHBoxLayout
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWebEngineWidgets import QWebEngineView
import json
import markdown

from core.logger import setup_logger

logger = setup_logger(__name__)


class FilePreviewManager:
    """
    Manages file preview functionality.
    Supports previewing images, markdown, text, and JSON files without opening editor tabs.
    """
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self._current_preview_path: Optional[Path] = None
        self._preview_widget: Optional[QWidget] = None
    
    def can_preview(self, path: Path) -> bool:
        """Check if a file can be previewed."""
        if not path.is_file():
            return False
        
        extensions = {
            # Images
            ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".ico",
            # Text/Code
            ".txt", ".md", ".py", ".js", ".ts", ".json", ".xml", ".html", ".css",
            ".yml", ".yaml", ".csv", ".log", ".sql",
        }
        return path.suffix.lower() in extensions or path.name in {"Dockerfile"}
    
    def preview_file(self, path: Path) -> QWidget:
        """Create a preview widget for the file."""
        self._current_preview_path = path
        return self._create_preview_widget(path)
    
    def _create_preview_widget(self, path: Path) -> QWidget:
        """Create the preview widget based on file type."""
        suffix = path.suffix.lower()
        
        # Images
        if suffix in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".ico"}:
            return self._create_image_preview(path)
        
        # Markdown
        elif suffix in {".md", ".markdown"}:
            return self._create_markdown_preview(path)
        
        # JSON
        elif suffix in {".json"}:
            return self._create_json_preview(path)
        
        # Text/Code files
        else:
            return self._create_text_preview(path)
    
    def _create_image_preview(self, path: Path) -> QWidget:
        """Create image preview widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        try:
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                label = QLabel(f"Unable to load image: {path.name}")
                label.setAlignment(Qt.AlignCenter)
                layout.addWidget(label)
            else:
                # Create scroll area for large images
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                
                image_label = QLabel()
                image_label.setPixmap(pixmap)
                image_label.setAlignment(Qt.AlignCenter)
                
                scroll.setWidget(image_label)
                layout.addWidget(scroll)
        except Exception as e:
            label = QLabel(f"Error loading image: {e}")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
        
        return widget
    
    def _create_markdown_preview(self, path: Path) -> QWidget:
        """Create markdown preview widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Convert markdown to HTML
            html = markdown.markdown(content)
            
            # Create web view or text edit
            from PySide6.QtWidgets import QTextEdit
            preview = QTextEdit()
            preview.setReadOnly(True)
            preview.setHtml(f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                        h1 {{ font-size: 24px; margin-bottom: 16px; }}
                        h2 {{ font-size: 20px; margin-top: 24px; margin-bottom: 12px; }}
                        h3 {{ font-size: 16px; margin-top: 20px; margin-bottom: 8px; }}
                        pre {{ background-color: #2d2d2d; padding: 12px; border-radius: 4px; overflow-x: auto; }}
                        code {{ font-family: 'Consolas', 'Monaco', monospace; background-color: #2d2d2d; padding: 2px 4px; border-radius: 2px; }}
                        a {{ color: #007acc; }}
                    </style>
                </head>
                <body>{html}</body>
                </html>
            """)
            layout.addWidget(preview)
        except Exception as e:
            label = QLabel(f"Error loading markdown: {e}")
            layout.addWidget(label)
        
        return widget
    
    def _create_json_preview(self, path: Path) -> QWidget:
        """Create JSON preview widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Try to parse and format JSON
            data = json.loads(content)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            
            from PySide6.QtWidgets import QTextEdit
            preview = QTextEdit()
            preview.setReadOnly(True)
            preview.setPlainText(formatted)
            preview.setStyleSheet("font-family: 'Consolas', 'Monaco', monospace;")
            layout.addWidget(preview)
        except json.JSONDecodeError as e:
            label = QLabel(f"Invalid JSON: {e}")
            layout.addWidget(label)
        except Exception as e:
            label = QLabel(f"Error loading JSON: {e}")
            layout.addWidget(label)
        
        return widget
    
    def _create_text_preview(self, path: Path) -> QWidget:
        """Create text/code preview widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            from PySide6.QtWidgets import QTextEdit
            preview = QTextEdit()
            preview.setReadOnly(True)
            preview.setPlainText(content)
            preview.setStyleSheet("font-family: 'Consolas', 'Monaco', monospace;")
            layout.addWidget(preview)
        except Exception as e:
            label = QLabel(f"Error loading file: {e}")
            layout.addWidget(label)
        
        return widget
    
    def clear_preview(self):
        """Clear current preview."""
        self._current_preview_path = None
    
    def get_current_preview_path(self) -> Optional[Path]:
        """Get current previewed file path."""
        return self._current_preview_path