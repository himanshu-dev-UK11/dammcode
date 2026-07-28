"""
MyCodingMaster Design System — v1.6.8

Centralized design tokens and style system.
Professional, minimal, fast, modern, AI-first, developer-focused.

Inspired by: Cursor, Linear, Raycast, JetBrains, GitHub Desktop, Warp, Zed
Identity: Unique MyCodingMaster aesthetic
"""
from typing import Dict, Optional
from dataclasses import dataclass
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtCore import QEasingCurve


# ═══════════════════════════════════════════════════════════════════════
# SIDEBAR CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

class ActivityBar:
    """Activity bar configuration - premium IDE style."""
    WIDTH = 48        # Fixed width (more balanced)
    ICON_SIZE = 32    # Button size (refined)
    PADDING = 6       # Internal padding (increased for better breathing)
    SPACING = 4       # Button spacing (improved visual rhythm)


class Sidebar:
    """Sidebar configuration - professional IDE style."""
    MIN_WIDTH = 200
    DEFAULT_WIDTH = 260
    MAX_WIDTH = 480
    COLLAPSED_WIDTH = 48
    HEADER_HEIGHT = 35
    ROW_HEIGHT = 24  # Slightly more breathing room


class Spacing:
    """Consistent spacing scale (4px base unit)."""
    XXS = 2   # 2px  — Tiny gaps
    XS = 4    # 4px  — Minimal spacing
    SM = 8    # 8px  — Small spacing (increased from 6)
    MD = 12   # 12px — Default spacing (increased from 8)
    LG = 16   # 16px — Medium spacing (refined)
    XL = 24   # 24px — Large spacing (refined)
    XXL = 32  # 32px — Extra large (refined)
    XXXL = 40 # 40px — Section spacing (increased)


# ═══════════════════════════════════════════════════════════════════════
# BORDER RADIUS
# ═══════════════════════════════════════════════════════════════════════

class Radius:
    """Professional border radius values."""
    NONE = 0    # Sharp corners
    SM = 3      # Subtle rounding (refined for minimalism)
    MD = 6      # Default rounding
    LG = 8      # Card rounding
    XL = 12     # Dialog rounding (refined)
    ROUND = 20  # Pill shape


# ═══════════════════════════════════════════════════════════════════════
# ELEVATION / SHADOWS
# ═══════════════════════════════════════════════════════════════════════

class Shadow:
    """Subtle elevation shadows."""
    NONE = "none"
    SM = "0 1px 3px rgba(0, 0, 0, 0.12)"
    MD = "0 2px 8px rgba(0, 0, 0, 0.18)"
    LG = "0 4px 16px rgba(0, 0, 0, 0.24)"
    XL = "0 8px 24px rgba(0, 0, 0, 0.32)"


# ═══════════════════════════════════════════════════════════════════════
# TYPOGRAPHY
# ═══════════════════════════════════════════════════════════════════════

class FontFamily:
    """Professional font stacks."""
    # UI Fonts
    UI = '"Inter", "SF Pro Text", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif'
    UI_FALLBACK = "Segoe UI, sans-serif"
    
    # Code Fonts
    CODE = '"JetBrains Mono", "Cascadia Code", "Fira Code", "Consolas", monospace'
    CODE_FALLBACK = "Consolas, monospace"
    
    # Terminal Fonts
    TERMINAL = '"JetBrains Mono", "Cascadia Code", "Consolas", monospace'


class FontSize:
    """Type scale."""
    XXS = 9   # Tiny labels
    XS = 11   # Small labels (increased for better readability)
    SM = 12   # Default UI (increased)
    MD = 13   # Body text (increased)
    LG = 14   # Emphasis
    XL = 16   # Headings (increased)
    XXL = 18  # Large headings
    XXXL = 20 # Hero text (increased)
    
    # Code
    CODE_SM = 11
    CODE_MD = 12
    CODE_LG = 13


class FontWeight:
    """Font weights."""
    LIGHT = 300
    REGULAR = 400
    MEDIUM = 500
    SEMIBOLD = 600
    BOLD = 700


class LineHeight:
    """Line heights."""
    TIGHT = 1.2
    NORMAL = 1.5
    RELAXED = 1.6
    LOOSE = 1.8


# ═══════════════════════════════════════════════════════════════════════
# ANIMATION / TRANSITIONS
# ═══════════════════════════════════════════════════════════════════════

class Duration:
    """Animation durations (milliseconds)."""
    INSTANT = 0
    FAST = 100
    NORMAL = 150
    SLOW = 200
    SLOWER = 300


class Easing:
    """Easing curves for smooth animations."""
    LINEAR = QEasingCurve.Linear
    EASE = QEasingCurve.InOutCubic
    EASE_IN = QEasingCurve.InCubic
    EASE_OUT = QEasingCurve.OutCubic
    EASE_IN_OUT = QEasingCurve.InOutCubic


# ═══════════════════════════════════════════════════════════════════════
# COLOR SYSTEM
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ColorPalette:
    """Enhanced color palette with premium IDE styling."""
    # Primary
    primary: str
    primary_hover: str
    primary_active: str
    primary_text: str
    
    # Surfaces
    bg: str              # Main background
    bg_secondary: str    # Secondary background (activity bar, sidebar header)
    surface: str         # Panel surface
    surface_hover: str   # Panel hover state
    surface_active: str  # Panel active/selected state
    
    # UI Elements
    sidebar: str         # Sidebar body background
    editor_bg: str
    toolbar: str
    terminal_bg: str
    statusbar: str
    
    # Borders
    border: str
    border_subtle: str
    border_hover: str
    border_focus: str
    
    # Text
    text: str            # Primary text
    text_secondary: str  # Secondary text
    text_tertiary: str   # Muted text
    text_disabled: str   # Disabled text
    
    # States
    hover: str
    selection: str
    selection_inactive: str
    focus_ring: str
    
    # Semantic
    error: str
    error_bg: str
    warning: str
    warning_bg: str
    success: str
    success_bg: str
    info: str
    info_bg: str
    
    # Accent (brand color)
    accent: str
    accent_hover: str
    accent_active: str
    
    # Syntax highlighting
    syntax_keyword: str
    syntax_string: str
    syntax_comment: str
    syntax_number: str
    syntax_function: str
    syntax_class: str
    syntax_operator: str
    syntax_bracket: str


# ═══════════════════════════════════════════════════════════════════════
# THEME DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════

class Themes:
    """Professional theme collection."""
    
    DARK = ColorPalette(
        # Primary
        primary="#3B82F6",
        primary_hover="#60A5FA",
        primary_active="#2563EB",
        primary_text="#FFFFFF",
        
        # Surfaces - refined for premium feel
        bg="#1E1E1E",
        bg_secondary="#1E1E1E",
        surface="#252526",
        surface_hover="#2A2D2E",
        surface_active="#37373D",
        
        # UI Elements
        sidebar="#1E1E1E",
        editor_bg="#1E1E1E",
        toolbar="#1E1E1E",
        terminal_bg="#1E1E1E",
        statusbar="#007ACC",
        
        # Borders - refined for subtle separation
        border="#3E3E42",
        border_subtle="#2D2D30",
        border_hover="#4E5358",
        border_focus="#3B82F6",
        
        # Text - professional contrast
        text="#CCCCCC",
        text_secondary="#AAAAAAAA",
        text_tertiary="#888888",
        text_disabled="#555555",
        
        # States
        hover="#2A2D2E",
        selection="#37373D",
        selection_inactive="#2D2D30",
        focus_ring="#3B82F6",
        
        # Semantic
        error="#F44336",
        error_bg="#2D1515",
        warning="#FF9800",
        warning_bg="#2D2415",
        success="#4CAF50",
        success_bg="#152D23",
        info="#2196F3",
        info_bg="#152535",
        
        # Accent
        accent="#3B82F6",
        accent_hover="#60A5FA",
        accent_active="#2563EB",
        
        # Syntax highlighting
        syntax_keyword="#569CD6",
        syntax_string="#CE9178",
        syntax_comment="#6A9955",
        syntax_number="#B5CEA8",
        syntax_function="#DCDCAA",
        syntax_class="#4EC9B0",
        syntax_operator="#CCCCCC",
        syntax_bracket="#FFCC66",
    )
    
    LIGHT = ColorPalette(
        # Primary
        primary="#2563EB",
        primary_hover="#3B82F6",
        primary_active="#1D4ED8",
        primary_text="#FFFFFF",
        
        # Surfaces
        bg="#FFFFFF",
        bg_secondary="#F9FAFB",
        surface="#FFFFFF",
        surface_hover="#F3F4F6",
        surface_active="#E5E7EB",
        
        # UI Elements
        sidebar="#F9FAFB",
        editor_bg="#FFFFFF",
        toolbar="#F9FAFB",
        terminal_bg="#FAFAFA",
        statusbar="#F3F4F6",
        
        # Borders
        border="#E5E7EB",
        border_subtle="#F3F4F6",
        border_hover="#D1D5DB",
        border_focus="#2563EB",
        
        # Text
        text="#111827",
        text_secondary="#6B7280",
        text_tertiary="#9CA3AF",
        text_disabled="#D1D5DB",
        
        # States
        hover="#F3F4F6",
        selection="#DBEAFE",
        selection_inactive="#F3F4F6",
        focus_ring="#2563EB",
        
        # Semantic
        error="#DC2626",
        error_bg="#FEF2F2",
        warning="#D97706",
        warning_bg="#FFFBEB",
        success="#059669",
        success_bg="#F0FDF4",
        info="#2563EB",
        info_bg="#EFF6FF",
        
        # Accent
        accent="#2563EB",
        accent_hover="#3B82F6",
        accent_active="#1D4ED8",
        
        # Syntax
        syntax_keyword="#7C3AED",
        syntax_string="#059669",
        syntax_comment="#9CA3AF",
        syntax_number="#D97706",
        syntax_function="#2563EB",
        syntax_class="#CA8A04",
        syntax_operator="#0891B2",
        syntax_bracket="#DB2777",
    )
    
    ONE_DARK = ColorPalette(
        primary="#61AFEF",
        primary_hover="#7DC1F7",
        primary_active="#4A9EE0",
        primary_text="#FFFFFF",
        
        bg="#282C34",
        bg_secondary="#21252B",
        surface="#282C34",
        surface_hover="#2C323C",
        surface_active="#323842",
        
        sidebar="#21252B",
        editor_bg="#282C34",
        toolbar="#21252B",
        terminal_bg="#1E2127",
        statusbar="#21252B",
        
        border="#181A1F",
        border_subtle="#21252B",
        border_hover="#3E4451",
        border_focus="#61AFEF",
        
        text="#ABB2BF",
        text_secondary="#5C6370",
        text_tertiary="#3E4451",
        text_disabled="#2C323C",
        
        hover="#2C323C",
        selection="#3E4451",
        selection_inactive="#2C323C",
        focus_ring="#61AFEF",
        
        error="#E06C75",
        error_bg="#3B2C32",
        warning="#E5C07B",
        warning_bg="#3B3830",
        success="#98C379",
        success_bg="#2E3B33",
        info="#61AFEF",
        info_bg="#2C3540",
        
        accent="#61AFEF",
        accent_hover="#7DC1F7",
        accent_active="#4A9EE0",
        
        syntax_keyword="#C678DD",
        syntax_string="#98C379",
        syntax_comment="#5C6370",
        syntax_number="#D19A66",
        syntax_function="#61AFEF",
        syntax_class="#E5C07B",
        syntax_operator="#56B6C2",
        syntax_bracket="#ABB2BF",
    )
    
    GITHUB_DARK = ColorPalette(
        primary="#1F6FEB",
        primary_hover="#388BFD",
        primary_active="#1158C7",
        primary_text="#FFFFFF",
        
        bg="#0D1117",
        bg_secondary="#010409",
        surface="#161B22",
        surface_hover="#1C2128",
        surface_active="#21262D",
        
        sidebar="#0D1117",
        editor_bg="#0D1117",
        toolbar="#010409",
        terminal_bg="#010409",
        statusbar="#010409",
        
        border="#30363D",
        border_subtle="#21262D",
        border_hover="#484F58",
        border_focus="#1F6FEB",
        
        text="#C9D1D9",
        text_secondary="#8B949E",
        text_tertiary="#6E7681",
        text_disabled="#484F58",
        
        hover="#1C2128",
        selection="#1F6FEB26",
        selection_inactive="#21262D",
        focus_ring="#1F6FEB",
        
        error="#F85149",
        error_bg="#2D1515",
        warning="#D29922",
        warning_bg="#2D2515",
        success="#3FB950",
        success_bg="#1B2D1F",
        info="#1F6FEB",
        info_bg="#1B2535",
        
        accent="#1F6FEB",
        accent_hover="#388BFD",
        accent_active="#1158C7",
        
        syntax_keyword="#FF7B72",
        syntax_string="#A5D6FF",
        syntax_comment="#8B949E",
        syntax_number="#79C0FF",
        syntax_function="#D2A8FF",
        syntax_class="#FFA657",
        syntax_operator="#FF7B72",
        syntax_bracket="#C9D1D9",
    )
    
    NORD = ColorPalette(
        primary="#88C0D0",
        primary_hover="#A3D4E3",
        primary_active="#6FADC4",
        primary_text="#2E3440",
        
        bg="#2E3440",
        bg_secondary="#242933",
        surface="#3B4252",
        surface_hover="#434C5E",
        surface_active="#4C566A",
        
        sidebar="#2E3440",
        editor_bg="#2E3440",
        toolbar="#242933",
        terminal_bg="#2E3440",
        statusbar="#242933",
        
        border="#434C5E",
        border_subtle="#3B4252",
        border_hover="#4C566A",
        border_focus="#88C0D0",
        
        text="#ECEFF4",
        text_secondary="#D8DEE9",
        text_tertiary="#81A1C1",
        text_disabled="#4C566A",
        
        hover="#3B4252",
        selection="#434C5E",
        selection_inactive="#3B4252",
        focus_ring="#88C0D0",
        
        error="#BF616A",
        error_bg="#3D2D30",
        warning="#EBCB8B",
        warning_bg="#3D3930",
        success="#A3BE8C",
        success_bg="#303D30",
        info="#88C0D0",
        info_bg="#2D3540",
        
        accent="#88C0D0",
        accent_hover="#A3D4E3",
        accent_active="#6FADC4",
        
        syntax_keyword="#81A1C1",
        syntax_string="#A3BE8C",
        syntax_comment="#616E88",
        syntax_number="#B48EAD",
        syntax_function="#88C0D0",
        syntax_class="#EBCB8B",
        syntax_operator="#81A1C1",
        syntax_bracket="#ECEFF4",
    )


# ═══════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM MANAGER
# ═══════════════════════════════════════════════════════════════════════

class DesignSystem:
    """Centralized design system manager."""
    
    def __init__(self, theme_name: str = "dark"):
        self.theme_name = theme_name
        self.palette = self._load_theme(theme_name)
        
    def _load_theme(self, theme_name: str) -> ColorPalette:
        """Load theme by name."""
        themes = {
            "dark": Themes.DARK,
            "light": Themes.LIGHT,
            "one_dark": Themes.ONE_DARK,
            "github_dark": Themes.GITHUB_DARK,
            "nord": Themes.NORD,
        }
        return themes.get(theme_name.lower(), Themes.DARK)
    
    def set_theme(self, theme_name: str):
        """Change active theme."""
        self.theme_name = theme_name
        self.palette = self._load_theme(theme_name)
    
    def get_stylesheet(self, component: str = "global") -> str:
        """Generate stylesheet for component."""
        if component == "global":
            return self._global_stylesheet()
        elif component == "button":
            return self._button_stylesheet()
        elif component == "card":
            return self._card_stylesheet()
        elif component == "input":
            return self._input_stylesheet()
        elif component == "tab":
            return self._tab_stylesheet()
        elif component == "scrollbar":
            return self._scrollbar_stylesheet()
        return ""
    
    def _global_stylesheet(self) -> str:
        """Global application stylesheet — complete redesign."""
        p = self.palette
        return f"""
        /* Global Reset & Base */
        * {{
            font-family: {FontFamily.UI_FALLBACK};
            font-size: {FontSize.MD}px;
            outline: none;
        }}
        
        QMainWindow {{
            background-color: {p.bg};
            color: {p.text};
            border: none;
        }}
        
        QWidget {{
            background-color: transparent;
            color: {p.text};
        }}
        
        /* QDockWidget styles */
        QDockWidget {{
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
            background-color: {p.bg};
            border: none;
        }}
        
        QDockWidget::title {{
            background-color: {p.bg_secondary};
            color: {p.text_secondary};
            padding: {Spacing.SM}px {Spacing.MD}px;
            border-bottom: 1px solid {p.border};
            font-size: {FontSize.SM}px;
            font-weight: {FontWeight.MEDIUM};
        }}
        
        QDockWidget::close-button, QDockWidget::float-button {{
            border: none;
            background: transparent;
            padding: {Spacing.XXS}px;
            width: 16px;
            height: 16px;
        }}
        
        QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
            background-color: {p.surface_hover};
            border-radius: {Radius.SM}px;
        }}
        
        QDockWidget::float-button {{
            subcontrol-origin: margin;
            subcontrol-position: left center;
            left: {Spacing.SM}px;
        }}
        
        QDockWidget::close-button {{
            subcontrol-origin: margin;
            subcontrol-position: right center;
            right: {Spacing.SM}px;
        }}
        
        QMainWindow::separator {{
            background-color: {p.border};
            width: 1px;
            height: 1px;
        }}
        
        QMainWindow::separator:hover {{
            background-color: {p.accent};
        }}
        
        /* ToolTip — compact, premium feel */
        QToolTip {{
            background-color: {p.surface_active};
            color: {p.text};
            border: 1px solid {p.border};
            border-radius: {Radius.SM}px;
            padding: {Spacing.XS}px {Spacing.SM}px;
            font-size: {FontSize.XS}px;
        }}
        
        /* Menus — refined radius, spacing */
        QMenu {{
            background-color: {p.surface};
            border: 1px solid {p.border};
            border-radius: {Radius.LG}px;
            padding: {Spacing.SM}px 0;
        }}
        
        QMenu::item {{
            padding: {Spacing.SM}px {Spacing.XL}px;
            border-radius: {Radius.SM}px;
            margin: 1px {Spacing.SM}px;
            color: {p.text};
            font-size: {FontSize.SM}px;
        }}
        
        QMenu::item:selected {{
            background-color: {p.surface_hover};
            color: {p.text};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {p.border_subtle};
            margin: {Spacing.SM}px {Spacing.LG}px;
        }}
        
        /* Scrollbars — thin, modern, IDE-style */
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
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
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
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        
        /* Buttons */
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
        
        QPushButton:checked {{
            background-color: {p.surface_active};
            color: {p.text};
            border-color: {p.border_hover};
        }}
        
        QPushButton.primary {{
            background-color: {p.accent};
            color: {p.primary_text};
            border: none;
        }}
        
        QPushButton.primary:hover {{
            background-color: {p.accent_hover};
        }}
        
        QPushButton.primary:pressed {{
            background-color: {p.accent_active};
        }}
        
        QPushButton.icon-only {{
            padding: {Spacing.SM}px;
            background-color: transparent;
            border: none;
            color: {p.text_secondary};
        }}
        
        QPushButton.icon-only:hover {{
            background-color: {p.surface_hover};
            color: {p.text};
        }}
        
        /* Input Fields */
        QLineEdit {{
            background-color: {p.surface};
            color: {p.text};
            border: 1px solid {p.border};
            border-radius: {Radius.MD}px;
            padding: {Spacing.SM}px {Spacing.MD}px;
            selection-background-color: {p.selection};
            selection-color: {p.text};
        }}
        
        QLineEdit:hover {{
            border-color: {p.border_hover};
        }}
        
        QLineEdit:focus {{
            border-color: {p.focus_ring};
        }}
        
        QTextEdit, QPlainTextEdit {{
            background-color: {p.editor_bg};
            color: {p.text};
            border: none;
            selection-background-color: {p.selection};
            selection-color: {p.text};
        }}
        
        /* ComboBox */
        QComboBox {{
            background-color: {p.surface};
            color: {p.text};
            border: 1px solid {p.border};
            border-radius: {Radius.MD}px;
            padding: {Spacing.SM}px {Spacing.MD}px;
            min-width: 120px;
        }}
        
        QComboBox:hover {{
            border-color: {p.border_hover};
        }}
        
        QComboBox:focus {{
            border-color: {p.focus_ring};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {p.text_tertiary};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {p.surface};
            border: 1px solid {p.border};
            border-radius: {Radius.MD}px;
            padding: {Spacing.XS}px;
            selection-background-color: {p.surface_hover};
        }}
        
        /* Labels */
        QLabel {{
            color: {p.text};
            font-size: {FontSize.MD}px;
        }}
        
        QLabel.muted {{
            color: {p.text_tertiary};
            font-size: {FontSize.SM}px;
        }}
        
        QLabel.heading {{
            font-size: {FontSize.LG}px;
            font-weight: {FontWeight.SEMIBOLD};
            color: {p.text};
        }}
        
        /* List Widgets / Tree Widgets */
        QListWidget {{
            background-color: {p.surface};
            border: none;
            outline: none;
            selection-background-color: {p.surface_hover};
            selection-color: {p.text};
            color: {p.text};
            font-size: {FontSize.SM}px;
        }}
        
        QListWidget::item {{
            padding: {Spacing.SM}px {Spacing.MD}px;
            border-radius: {Radius.SM}px;
            margin: {Spacing.XXS}px {Spacing.XS}px;
        }}
        
        QListWidget::item:hover {{
            background-color: {p.surface_hover};
        }}
        
        QListWidget::item:selected {{
            background-color: {p.surface_active};
        }}
        
        QTreeWidget {{
            background-color: {p.sidebar};
            border: none;
            outline: none;
            selection-background-color: {p.surface_hover};
            selection-color: {p.text};
            color: {p.text};
            font-size: {FontSize.SM}px;
            padding: {Spacing.XS}px 0;
        }}
        
        QTreeWidget::item {{
            padding: {Spacing.XS}px {Spacing.MD}px;
        }}
        
        QTreeWidget::item:hover {{
            background-color: {p.surface_hover};
        }}
        
        QTreeWidget::item:selected {{
            background-color: {p.surface_active};
        }}
        
        QTreeWidget::branch {{
            background-color: transparent;
        }}
        
        QTreeWidget::branch:has-children:!has-siblings:closed,
        QTreeWidget::branch:closed:has-children:has-siblings {{
            border-image: none;
            image: none;
        }}
        
        QTreeWidget::branch:open:has-children:!has-siblings,
        QTreeWidget::branch:open:has-children:has-siblings {{
            border-image: none;
            image: none;
        }}
        
        /* Checkboxes */
        QCheckBox {{
            color: {p.text};
            font-size: {FontSize.MD}px;
        }}
        
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {p.border};
            border-radius: {Radius.SM}px;
            background-color: {p.surface};
        }}
        
        QCheckBox::indicator:hover {{
            border-color: {p.border_hover};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {p.accent};
            border-color: {p.accent};
        }}
        
        /* Radio Buttons */
        QRadioButton {{
            color: {p.text};
            font-size: {FontSize.MD}px;
        }}
        
        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {p.border};
            border-radius: 8px;
            background-color: {p.surface};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {p.surface};
            border: 2px solid {p.accent};
        }}
        
        /* Sliders */
        QSlider::groove:horizontal {{
            height: 4px;
            background-color: {p.border};
            border-radius: 2px;
        }}
        
        QSlider::handle:horizontal {{
            background-color: {p.text_secondary};
            width: 16px;
            height: 16px;
            border-radius: 8px;
            margin: -6px 0;
        }}
        
        QSlider::handle:horizontal:hover {{
            background-color: {p.accent};
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {p.statusbar};
            border-top: 1px solid {p.border};
            color: {p.text_secondary};
            font-size: {FontSize.XS}px;
            padding: 0 {Spacing.MD}px;
        }}
        
        QStatusBar::item {{
            border: none;
        }}
        
        /* ToolBar */
        QToolBar {{
            background-color: {p.toolbar};
            border: none;
            border-bottom: 1px solid {p.border};
            spacing: {Spacing.XS}px;
            padding: {Spacing.XXS}px {Spacing.SM}px;
        }}
        
        QToolBar::separator {{
            background-color: {p.border_subtle};
            width: 1px;
            margin: {Spacing.SM}px {Spacing.MD}px;
        }}
        
        QToolButton {{
            background-color: transparent;
            color: {p.text_secondary};
            border: none;
            border-radius: {Radius.MD}px;
            padding: {Spacing.SM}px {Spacing.LG}px;
            font-size: {FontSize.SM}px;
            font-weight: {FontWeight.MEDIUM};
        }}
        
        QToolButton:hover {{
            background-color: {p.surface_hover};
            color: {p.text};
            transition: background-color 100ms ease-out;
        }}
        
        QToolButton:pressed {{
            background-color: {p.surface_active};
        }}
        
        QToolButton:checked {{
            background-color: {p.surface_active};
            color: {p.text};
        }}
        
        QToolButton::menu-indicator {{
            subcontrol-origin: padding;
            subcontrol-position: center right;
            padding-right: {Spacing.XS}px;
            image: none;
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid {p.text_tertiary};
        }}
        
        QToolButton::menu-indicator:hover {{
            border-top-color: {p.text};
        }}
        
        /* Dropdown Menu */
        QMenu {{
            background-color: {p.surface};
            border: 1px solid {p.border};
            border-radius: {Radius.LG}px;
            padding: {Spacing.XS}px 0;
        }}
        
        QMenu::item {{
            padding: {Spacing.SM}px {Spacing.LG}px;
            border-radius: {Radius.SM}px;
            margin: {Spacing.XXS}px {Spacing.XS}px;
            color: {p.text};
            font-size: {FontSize.SM}px;
            font-weight: {FontWeight.MEDIUM};
        }}
        
        QMenu::item:selected {{
            background-color: {p.surface_hover};
            color: {p.text};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {p.border_subtle};
            margin: {Spacing.XS}px {Spacing.MD}px;
        }}
        """
    
    def _button_stylesheet(self) -> str:
        return ""  # Now included in global
    
    def _card_stylesheet(self) -> str:
        return ""  # Now included in global
    
    def _input_stylesheet(self) -> str:
        return ""  # Now included in global
    
    def _tab_stylesheet(self) -> str:
        return ""  # Now included in global
    
    def _scrollbar_stylesheet(self) -> str:
        return ""  # Now included in global


# ═══════════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE
# ═══════════════════════════════════════════════════════════════════════

# Singleton instance
_design_system: Optional[DesignSystem] = None


def get_design_system() -> DesignSystem:
    """Get global design system instance."""
    global _design_system
    if _design_system is None:
        _design_system = DesignSystem("dark")
    return _design_system


def set_design_system_theme(theme_name: str):
    """Change global theme."""
    ds = get_design_system()
    ds.set_theme(theme_name)
