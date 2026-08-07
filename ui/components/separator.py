"""
Professional Separator Component — v1.6.5

Subtle dividers for visual hierarchy.
"""
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt
from ui.design_system import get_design_system


class Separator(QFrame):
    """Professional horizontal or vertical separator."""
    def __init__(self, orientation: Qt.Orientation = Qt.Horizontal, parent=None):
        super().__init__(parent)
        self.ds = get_design_system()
        self._setup_style(orientation)
        
    def _setup_style(self, orientation: Qt.Orientation):
        """Apply design system styles."""
        p = self.ds.palette
        
        if orientation == Qt.Horizontal:
            self.setFrameShape(QFrame.HLine)
            self.setFixedHeight(1)
        else:
            self.setFrameShape(QFrame.VLine)
            self.setFixedWidth(1)
            
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {p.border_subtle};
                border: none;
            }}
        """)
        self.setFrameShadow(QFrame.Plain)
