"""
Professional Button Components — v1.6.5

Design system compliant buttons with smooth animations.
"""
from PySide6.QtWidgets import QPushButton, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QSize
from PySide6.QtGui import QIcon, QCursor
from ui.design_system import get_design_system, Spacing, Radius, FontSize, FontWeight, Duration


class Button(QPushButton):
    """
    Professional button with hover/press animations.
    """
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.ds = get_design_system()
        self._setup_style()
        self._setup_animations()
        
    def _setup_style(self):
        """Apply design system styles."""
        p = self.ds.palette
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.surface};
                color: {p.text};
                border: 1px solid {p.border};
                border-radius: {Radius.MD}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-size: {FontSize.MD}px;
                font-weight: {FontWeight.MEDIUM};
                min-height: 28px;
            }}
            
            QPushButton:hover {{
                background-color: {p.surface_hover};
                border-color: {p.border_hover};
            }}
            
            QPushButton:pressed {{
                background-color: {p.surface_active};
            }}
            
            QPushButton:focus {{
                border-color: {p.focus_ring};
                outline: none;
            }}
            
            QPushButton:disabled {{
                background-color: {p.surface};
                color: {p.text_disabled};
                border-color: {p.border_subtle};
            }}
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
    def _setup_animations(self):
        """Setup smooth animations."""
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)


class PrimaryButton(Button):
    """Primary action button with accent color."""
    def _setup_style(self):
        p = self.ds.palette
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.accent};
                color: {p.primary_text};
                border: none;
                border-radius: {Radius.MD}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-size: {FontSize.MD}px;
                font-weight: {FontWeight.SEMIBOLD};
                min-height: 28px;
            }}
            
            QPushButton:hover {{
                background-color: {p.accent_hover};
            }}
            
            QPushButton:pressed {{
                background-color: {p.accent_active};
            }}
            
            QPushButton:focus {{
                outline: none;
            }}
            
            QPushButton:disabled {{
                background-color: {p.surface};
                color: {p.text_disabled};
            }}
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))


class SecondaryButton(Button):
    """Secondary button with subtle styling."""
    def _setup_style(self):
        p = self.ds.palette
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {p.text_secondary};
                border: 1px solid {p.border};
                border-radius: {Radius.MD}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-size: {FontSize.MD}px;
                font-weight: {FontWeight.MEDIUM};
                min-height: 28px;
            }}
            
            QPushButton:hover {{
                background-color: {p.hover};
                color: {p.text};
                border-color: {p.border_hover};
            }}
            
            QPushButton:pressed {{
                background-color: {p.surface_active};
            }}
            
            QPushButton:focus {{
                border-color: {p.focus_ring};
                outline: none;
            }}
            
            QPushButton:disabled {{
                color: {p.text_disabled};
                border-color: {p.border_subtle};
            }}
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))


class IconButton(QPushButton):
    """Icon-only button for toolbar actions."""
    def __init__(self, icon: QIcon = None, tooltip: str = "", parent=None):
        super().__init__(parent)
        self.ds = get_design_system()
        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(16, 16))
        if tooltip:
            self.setToolTip(tooltip)
        self._setup_style()
        
    def _setup_style(self):
        p = self.ds.palette
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {Radius.MD}px;
                padding: {Spacing.SM}px;
                min-width: 28px;
                min-height: 28px;
                max-width: 28px;
                max-height: 28px;
            }}
            
            QPushButton:hover {{
                background-color: {p.hover};
            }}
            
            QPushButton:pressed {{
                background-color: {p.surface_active};
            }}
            
            QPushButton:disabled {{
                opacity: 0.4;
            }}
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))
