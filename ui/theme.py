"""
Enhanced Theme System — v2.0 (Premium UI Redesign)

Professional theme management integrated with the design system.
"""
from PySide6.QtWidgets import QApplication
from ui.design_system import get_design_system, set_design_system_theme, Spacing, Radius, FontSize, FontWeight, FontFamily


class ThemeManager:
    """Enhanced theme manager using the design system."""
    def __init__(self, app: QApplication):
        self.app = app
        self.current_theme = "dark"
        self.ds = get_design_system()

    def apply_theme(self, theme_name: str):
        """Apply a specific theme."""
        set_design_system_theme(theme_name)
        self.ds = get_design_system()
        self.current_theme = theme_name
        stylesheet = self._generate_stylesheet()
        self.app.setStyleSheet(stylesheet)
        # Force repaint so inline-QSS widgets re-read updated palette
        for w in self.app.topLevelWidgets():
            w.update()

    def _generate_stylesheet(self) -> str:
        """Generate complete premium application stylesheet."""
        p = self.ds.palette
        return f"""
/* ── Reset & Base ─────────────────────────────────────────────────── */
* {{
    font-family: "Segoe UI", "Inter", -apple-system, sans-serif;
    font-size: {FontSize.SM}px;
    outline: none;
}}

QMainWindow, QDialog {{
    background-color: {p.bg};
    color: {p.text};
    border: none;
}}

QWidget {{
    color: {p.text};
    background-color: transparent;
}}

/* ── Activity Bar (Premium IDE style) ─────────────────────────────── */
QWidget#ActivityBar {{
    background-color: {p.bg_secondary};
    border-right: 1px solid {p.border_subtle};
}}

QWidget#ActivityBar QPushButton {{
    background-color: transparent;
    color: {p.text_tertiary};
    border: none;
    border-radius: {Radius.SM}px;
    font-size: 18px;
    min-width: 40px;
    min-height: 40px;
    max-width: 40px;
    max-height: 40px;
    margin: 2px 0;
}}

QWidget#ActivityBar QPushButton:hover {{
    background-color: {p.surface_hover};
    color: {p.text};
}}

QWidget#ActivityBar QPushButton:pressed {{
    background-color: {p.surface_active};
}}

QWidget#ActivityBar QPushButton:checked {{
    background-color: {p.surface_active};
    color: {p.accent};
    border-left: 2px solid {p.accent};
    border-radius: {Radius.SM}px;
}}

/* ── Sidebar ──────────────────────────────────────────────────────── */
QWidget#PremiumExplorer {{
    background-color: {p.sidebar};
}}

QWidget#PremiumExplorer QWidget {{
    background-color: {p.bg_secondary};
}}

QWidget#PremiumExplorer QSplitter::handle {{
    background-color: {p.border_subtle};
}}

QWidget#PremiumExplorer QSplitter::handle:hover {{
    background-color: {p.accent};
}}

QWidget#PremiumExplorer QSplitter::handle:horizontal {{
    width: 1px;
}}

/* ── Sidebar Header ───────────────────────────────────────────────── */
QWidget#SidebarHeader {{
    background-color: {p.bg_secondary};
    border-bottom: 1px solid {p.border_subtle};
    padding: 0 {Spacing.MD}px;
}}

QWidget#SidebarHeader QToolButton {{
    background-color: transparent;
    color: {p.text_tertiary};
    border: none;
    border-radius: {Radius.SM}px;
    font-size: 16px;
    min-width: 28px;
    min-height: 28px;
    max-width: 28px;
    max-height: 28px;
    padding: 4px;
}}

QWidget#SidebarHeader QToolButton:hover {{
    background-color: {p.surface_hover};
    color: {p.text};
}}

/* ── Main Window Separator (1px hairline) ─────────────────────────── */
QMainWindow::separator {{
    background-color: {p.border_subtle};
    width: 1px;
    height: 1px;
}}

QMainWindow::separator:hover {{
    background-color: {p.accent};
}}

/* ── Menu Bar ─────────────────────────────────────────────────────── */
QMenuBar {{
    background-color: {p.toolbar};
    color: {p.text_secondary};
    border: none;
    border-bottom: 1px solid {p.border};
    padding: 2px {Spacing.SM}px;
    font-size: {FontSize.SM}px;
    min-height: 30px;
    max-height: 30px;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: {Spacing.SM}px {Spacing.LG}px;
    border-radius: {Radius.SM}px;
    margin: 0 2px;
}}

QMenuBar::item:selected {{
    background-color: {p.surface_hover};
    color: {p.text};
}}

/* ── Menus ─────────────────────────────────────────────────────────── */
QMenu {{
    background-color: {p.surface};
    color: {p.text};
    border: 1px solid {p.border};
    border-radius: {Radius.LG}px;
    padding: {Spacing.XS}px 0;
}}

QMenu::item {{
    padding: {Spacing.XS}px {Spacing.LG}px;
    border-radius: {Radius.SM}px;
    margin: 1px {Spacing.XS}px;
    font-size: {FontSize.SM}px;
}}

QMenu::item:selected {{
    background-color: {p.surface_hover};
    color: {p.text};
}}

QMenu::item:disabled {{
    color: {p.text_disabled};
}}

QMenu::separator {{
    height: 1px;
    background-color: {p.border_subtle};
    margin: {Spacing.XS}px {Spacing.MD}px;
}}

QMenu::icon {{
    padding-left: {Spacing.SM}px;
}}

/* ── Toolbar ──────────────────────────────────────────────────────── */
QToolBar#TopToolbar {{
    background-color: {p.toolbar};
    border: none;
    border-bottom: 1px solid {p.border};
    spacing: {Spacing.XS}px;
    padding: 0 {Spacing.MD}px;
    min-height: 38px;
    max-height: 38px;
}}

QToolBar {{
    background-color: {p.toolbar};
    border: none;
    border-bottom: 1px solid {p.border};
    spacing: {Spacing.XS}px;
    padding: 0 {Spacing.SM}px;
}}

QToolBar::separator {{
    background-color: {p.border_subtle};
    width: 1px;
    margin: {Spacing.SM}px {Spacing.SM}px;
}}

QToolButton {{
    background-color: transparent;
    color: {p.text_secondary};
    border: none;
    border-radius: {Radius.SM}px;
    padding: {Spacing.SM}px {Spacing.LG}px;
    font-size: {FontSize.SM}px;
    font-weight: {FontWeight.MEDIUM};
    min-height: 28px;
}}

QToolButton:hover {{
    background-color: {p.surface_hover};
    color: {p.text};
}}

QToolButton:pressed {{
    background-color: {p.surface_active};
}}

QToolButton:checked {{
    background-color: {p.surface_active};
    color: {p.text};
}}

/* ── Activity Bar ─────────────────────────────────────────────────── */
#ActivityBar {{
    background-color: {p.bg_secondary};
    border-right: 1px solid {p.border_subtle};
}}

#ActivityBar QPushButton {{
    background-color: transparent;
    color: {p.text_tertiary};
    border: none;
    border-radius: {Radius.LG}px;
    font-size: 16px;
    min-width: 36px;
    min-height: 36px;
    max-width: 36px;
    max-height: 36px;
}}

#ActivityBar QPushButton:hover {{
    background-color: {p.surface_hover};
    color: {p.text};
}}

#ActivityBar QPushButton:pressed {{
    background-color: {p.surface_active};
}}

/* ── Sidebar ──────────────────────────────────────────────────────── */
#SidebarHeader {{
    background-color: {p.bg_secondary};
    border-bottom: 1px solid {p.border};
}}

/* ── Editor Tab Bar ───────────────────────────────────────────────── */
QTabWidget::pane {{
    border: none;
    background-color: {p.editor_bg};
}}

QTabBar {{
    background-color: {p.bg_secondary};
    qproperty-drawBase: 0;
}}

QTabBar::tab {{
    background-color: {p.bg_secondary};
    color: {p.text_tertiary};
    border: none;
    border-right: 1px solid {p.border_subtle};
    padding: 0px 16px;
    font-size: {FontSize.SM}px;
    font-weight: {FontWeight.REGULAR};
    min-height: 36px;
    max-height: 36px;
}}

QTabBar::tab:hover:!selected {{
    background-color: {p.surface_hover};
    color: {p.text_secondary};
}}

QTabBar::tab:selected {{
    background-color: {p.editor_bg};
    color: {p.text};
    font-weight: {FontWeight.MEDIUM};
    border-bottom: 2px solid {p.accent};
}}

QTabBar::close-button {{
    image: none;
    subcontrol-position: right;
    padding: 3px;
    margin-right: 4px;
    border-radius: {Radius.SM}px;
    width: 16px;
    height: 16px;
}}

QTabBar::close-button:hover {{
    background-color: {p.surface_hover};
}}

QTabBar::tab:pinned {{
    font-weight: {FontWeight.BOLD};
}}

/* ── Status Bar ───────────────────────────────────────────────────── */
QStatusBar#BottomStatusBar {{
    background-color: {p.statusbar};
    color: {p.text_secondary};
    border-top: 1px solid {p.border};
    font-size: {FontSize.XS}px;
    min-height: 24px;
    max-height: 24px;
    padding: 0 {Spacing.SM}px;
}}

QStatusBar#BottomStatusBar::item {{
    border: none;
}}

QStatusBar {{
    background-color: {p.statusbar};
    color: {p.text_secondary};
    border-top: 1px solid {p.border};
    font-size: {FontSize.XS}px;
    min-height: 24px;
    max-height: 24px;
    padding: 0 {Spacing.XS}px;
}}

QStatusBar::item {{
    border: none;
}}

/* ── Dock Widget ──────────────────────────────────────────────────── */
QDockWidget {{
    background-color: {p.bg};
    border: none;
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}

QDockWidget::title {{
    background-color: {p.bg_secondary};
    color: {p.text_secondary};
    padding: {Spacing.SM}px {Spacing.MD}px;
    border-bottom: 1px solid {p.border};
    font-size: {FontSize.XS}px;
    font-weight: {FontWeight.SEMIBOLD};
    text-align: left;
    letter-spacing: 0.04em;
}}

QDockWidget::close-button,
QDockWidget::float-button {{
    border: none;
    background: transparent;
    padding: 1px;
    width: 14px;
    height: 14px;
    border-radius: {Radius.SM}px;
}}

QDockWidget::close-button:hover,
QDockWidget::float-button:hover {{
    background-color: {p.surface_hover};
}}

QDockWidget::float-button {{
    subcontrol-origin: margin;
    subcontrol-position: left center;
    left: {Spacing.XS}px;
}}

QDockWidget::close-button {{
    subcontrol-origin: margin;
    subcontrol-position: right center;
    right: {Spacing.XS}px;
}}

/* ── Splitter (hairline) ──────────────────────────────────────────── */
QSplitter::handle {{
    background-color: {p.border_subtle};
}}

QSplitter::handle:hover {{
    background-color: {p.accent};
}}

QSplitter::handle:horizontal {{
    width: 1px;
}}

QSplitter::handle:vertical {{
    height: 1px;
}}

/* ── Buttons ──────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {p.surface};
    color: {p.text_secondary};
    border: 1px solid {p.border};
    border-radius: {Radius.MD}px;
    padding: {Spacing.SM}px {Spacing.LG}px;
    font-size: {FontSize.SM}px;
    font-weight: {FontWeight.MEDIUM};
    min-height: 28px;
}}

QPushButton:hover {{
    background-color: {p.surface_hover};
    border-color: {p.border_hover};
    color: {p.text};
}}

QPushButton:pressed {{
    background-color: {p.surface_active};
}}

QPushButton:focus {{
    border-color: {p.border_hover};
}}

QPushButton:disabled {{
    color: {p.text_disabled};
    border-color: {p.border_subtle};
    background-color: transparent;
}}

QPushButton[accent="true"] {{
    background-color: {p.accent};
    color: {p.primary_text};
    border: none;
    font-weight: {FontWeight.SEMIBOLD};
}}

QPushButton[accent="true"]:hover {{
    background-color: {p.accent_hover};
}}

/* ── Input Fields ─────────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {p.surface};
    color: {p.text};
    border: 1px solid {p.border};
    border-radius: {Radius.SM}px;
    padding: {Spacing.XS}px {Spacing.SM}px;
    selection-background-color: {p.selection};
    font-size: {FontSize.SM}px;
}}

QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{
    border-color: {p.border_hover};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {p.border_focus};
}}

/* ── Scrollbars — thin, modern, 8px with hover expand feel ───────── */
QScrollBar:vertical {{
    background-color: transparent;
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {p.border};
    border-radius: 4px;
    min-height: 28px;
    margin: 2px 1px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {p.border_hover};
    width: 10px;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 8px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {p.border};
    border-radius: 4px;
    min-width: 28px;
    margin: 1px 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {p.border_hover};
    height: 10px;
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* ── List / Tree Views ────────────────────────────────────────────── */
QListView, QTreeView, QListWidget, QTreeWidget {{
    background-color: {p.sidebar};
    color: {p.text};
    border: none;
    outline: none;
    font-size: {FontSize.SM}px;
    alternate-background-color: transparent;
}}

QListView::item, QTreeView::item,
QListWidget::item, QTreeWidget::item {{
    padding: {Spacing.XS}px {Spacing.MD}px;
    border-radius: {Radius.SM}px;
    border: none;
    min-height: 24px;
}}

QListView::item:hover, QTreeView::item:hover,
QListWidget::item:hover, QTreeWidget::item:hover {{
    background-color: {p.surface_hover};
}}

QListView::item:selected, QTreeView::item:selected,
QListWidget::item:selected, QTreeWidget::item:selected {{
    background-color: {p.surface_active};
    color: {p.text};
}}

QListView::item:selected:!active, QTreeView::item:selected:!active,
QListWidget::item:selected:!active, QTreeWidget::item:selected:!active {{
    background-color: {p.selection_inactive};
    color: {p.text};
}}

QTreeView::branch {{
    background: transparent;
}}

/* ── ComboBox ─────────────────────────────────────────────────────── */
QComboBox {{
    background-color: {p.surface};
    color: {p.text};
    border: 1px solid {p.border};
    border-radius: {Radius.SM}px;
    padding: {Spacing.XS}px {Spacing.SM}px;
    min-height: 24px;
    font-size: {FontSize.SM}px;
}}

QComboBox:hover {{
    border-color: {p.border_hover};
}}

QComboBox:focus {{
    border-color: {p.border_focus};
}}

QComboBox::drop-down {{
    border: none;
    width: 18px;
}}

QComboBox QAbstractItemView {{
    background-color: {p.surface};
    border: 1px solid {p.border};
    border-radius: {Radius.SM}px;
    selection-background-color: {p.surface_hover};
    outline: none;
    font-size: {FontSize.SM}px;
}}

/* ── Labels ───────────────────────────────────────────────────────── */
QLabel {{
    color: {p.text};
    font-size: {FontSize.MD}px;
    background-color: transparent;
}}

/* ── Tooltip ──────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {p.surface_active};
    color: {p.text};
    border: 1px solid {p.border};
    border-radius: {Radius.SM}px;
    padding: 3px {Spacing.SM}px;
    font-size: {FontSize.XS}px;
}}

/* ── CheckBox ─────────────────────────────────────────────────────── */
QCheckBox {{
    color: {p.text};
    spacing: {Spacing.XS}px;
    font-size: {FontSize.SM}px;
}}

QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {p.border};
    border-radius: 3px;
    background-color: {p.surface};
}}

QCheckBox::indicator:hover {{
    border-color: {p.border_hover};
}}

QCheckBox::indicator:checked {{
    background-color: {p.accent};
    border-color: {p.accent};
}}

/* ── Progress Bar ─────────────────────────────────────────────────── */
QProgressBar {{
    background-color: {p.surface};
    border: none;
    border-radius: {Radius.SM}px;
    height: 4px;
    text-align: center;
    font-size: {FontSize.XS}px;
    color: transparent;
}}

QProgressBar::chunk {{
    background-color: {p.accent};
    border-radius: {Radius.SM}px;
}}

/* ── Group Boxes ──────────────────────────────────────────────────── */
QGroupBox {{
    border: 1px solid {p.border};
    border-radius: {Radius.LG}px;
    margin-top: {Spacing.LG}px;
    font-weight: {FontWeight.SEMIBOLD};
    color: {p.text_secondary};
    font-size: {FontSize.SM}px;
    padding-top: {Spacing.MD}px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: {Spacing.MD}px;
    padding: 0 {Spacing.SM}px;
}}
"""

    def apply_dark(self):
        self.apply_theme("dark")

    def apply_light(self):
        self.apply_theme("light")

    def apply_one_dark(self):
        self.apply_theme("one_dark")

    def apply_github_dark(self):
        self.apply_theme("github_dark")

    def apply_nord(self):
        self.apply_theme("nord")

    def toggle(self):
        if self.current_theme == "dark":
            self.apply_light()
        else:
            self.apply_dark()

    def get_current_theme(self) -> str:
        return self.current_theme

    @property
    def is_dark(self) -> bool:
        return self.current_theme in ["dark", "one_dark", "github_dark", "nord"]

    @property
    def colors(self) -> dict:
        p = self.ds.palette
        return {
            "surface0": p.bg,
            "surface1": p.bg_secondary,
            "surface2": p.surface,
            "surface3": p.toolbar,
            "surface4": p.surface_hover,
            "border": p.border,
            "border_hi": p.border_hover,
            "accent": p.accent,
            "text_pri": p.text,
            "text_sec": p.text_secondary,
            "text_muted": p.text_tertiary,
            "success": p.success,
            "warning": p.warning,
            "error": p.error,
        }
