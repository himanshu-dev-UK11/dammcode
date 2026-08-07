"""
File Preview Widget — v2.3

Widget for displaying file previews in the Explorer.
Supports: Image, Markdown, Text, JSON preview without opening editor tab.
"""
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QScrollArea
from PySide6.QtCore import Qt
import json

logger = setup_logger(__name__)


class FilePreviewWidget(QWidget):
    """Widget for displaying file previews."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path: Optional[Path] = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.scroll)
        
        self.content_widget = QWidget()
        self.scroll.setWidget(self.content_widget)
        
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
    
    def set_file(self, path: Path) -> bool:
        """Set the file to preview."""
        self._current_path = path
        
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        suffix = path.suffix.lower()
        
        try:
            # Images
            if suffix in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".ico"}:
                self._preview_image(path)
            
            # Markdown
            elif suffix in {".md", ".markdown"}:
                self._preview_markdown(path)
            
            # JSON
            elif suffix in {".json"}:
                self._preview_json(path)
            
            # Text/Code files
            else:
                self._preview_text(path)
            
            return True
            
        except Exception as e:
            label = QLabel(f"Error loading preview: {e}")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #FF5555;")
            self.content_layout.addWidget(label)
            return False
    
    def _preview_image(self, path: Path):
        """Preview an image file."""
        from PySide6.QtGui import QPixmap
        
        try:
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                label = QLabel(f"Unable to load image: {path.name}")
                label.setAlignment(Qt.AlignCenter)
                self.content_layout.addWidget(label)
                return
            
            label = QLabel()
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
            
            # Scale large images
            if pixmap.width() > 800 or pixmap.height() > 600:
                label.setScaledContents(True)
            
            self.content_layout.addWidget(label)
            
        except Exception as e:
            label = QLabel(f"Error loading image: {e}")
            label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(label)
    
    def _preview_markdown(self, path: Path):
        """Preview a markdown file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Convert markdown to HTML
            try:
                import markdown
                html = markdown.markdown(content)
            except ImportError:
                html = f"<pre>{content}</pre>"
            
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
            self.content_layout.addWidget(preview)
            
        except Exception as e:
            label = QLabel(f"Error loading markdown: {e}")
            self.content_layout.addWidget(label)
    
    def _preview_json(self, path: Path):
        """Preview a JSON file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Try to parse and format JSON
            try:
                data = json.loads(content)
                formatted = json.dumps(data, indent=2, ensure_ascii=False)
            except json.JSONDecodeError as e:
                formatted = content
            
            from PySide6.QtWidgets import QTextEdit
            preview = QTextEdit()
            preview.setReadOnly(True)
            preview.setPlainText(formatted)
            preview.setStyleSheet("font-family: 'Consolas', 'Monaco', monospace;")
            self.content_layout.addWidget(preview)
            
        except Exception as e:
            label = QLabel(f"Error loading JSON: {e}")
            self.content_layout.addWidget(label)
    
    def _preview_text(self, path: Path):
        """Preview a text/code file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            from PySide6.QtWidgets import QTextEdit
            preview = QTextEdit()
            preview.setReadOnly(True)
            preview.setPlainText(content)
            preview.setStyleSheet("font-family: 'Consolas', 'Monaco', monospace;")
            self.content_layout.addWidget(preview)
            
        except Exception as e:
            label = QLabel(f"Error loading file: {e}")
            self.content_layout.addWidget(label)
    
    def clear(self):
        """Clear the preview."""
        self._current_path = None
        
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def get_current_path(self) -> Optional[Path]:
        """Get current previewed file path."""
        return self._current_path