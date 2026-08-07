"""
Professional Card Component — v1.6.5

Elevated panel with subtle borders and shadows.
"""
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt
from ui.design_system import get_design_system, Spacing, Radius


class Card(QFrame):
    """Professional card/panel component."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ds = get_design_system()
        self._setup_style()
        
    def _setup_style(self):
        """Apply design system styles."""
        p = self.ds.palette
        self.setObjectName("Card")
        self.setStyleSheet(f"""
            #Card {{
                background-color: {p.surface};
                border: 1px solid {p.border};
                border-radius: {Radius.LG}px;
            }}
            
            #Card:hover {{
                border-color: {p.border_hover};
            }}
        """)
        self.setFrameShape(QFrame.NoFrame)
        # Add subtle shadow effect (CSS-like, but using Qt border enhancement)
        self.setAutoFillBackground(True)
