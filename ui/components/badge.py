"""
Professional Badge Components — v1.6.5

Small status indicators and labels.
"""
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from ui.design_system import get_design_system, Spacing, Radius, FontSize, FontWeight


class Badge(QLabel):
    """Professional badge/pill component."""
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.ds = get_design_system()
        self._setup_style()
        
    def _setup_style(self):
        """Apply design system styles."""
        p = self.ds.palette
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {p.surface_active};
                color: {p.text_secondary};
                border: 1px solid {p.border};
                border-radius: {Radius.ROUND}px;
                padding: {Spacing.XXS}px {Spacing.SM}px;
                font-size: {FontSize.XS}px;
                font-weight: {FontWeight.MEDIUM};
            }}
        """)
        self.setAlignment(Qt.AlignCenter)


class StatusBadge(Badge):
    """Status indicator badge with semantic colors."""
    def __init__(self, text: str = "", status: str = "info", parent=None):
        super().__init__(text, parent)
        self.set_status(status)
        
    def set_status(self, status: str):
        """Set badge status (success, warning, error, info)."""
        p = self.ds.palette
        colors = {
            "success": (p.success_bg, p.success),
            "warning": (p.warning_bg, p.warning),
            "error": (p.error_bg, p.error),
            "info": (p.info_bg, p.info),
        }
        bg, text_color = colors.get(status, (p.surface_active, p.text_secondary))
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {text_color};
                border: 1px solid {text_color}40;
                border-radius: {Radius.ROUND}px;
                padding: {Spacing.XXS}px {Spacing.SM}px;
                font-size: {FontSize.XS}px;
                font-weight: {FontWeight.SEMIBOLD};
            }}
        """)
