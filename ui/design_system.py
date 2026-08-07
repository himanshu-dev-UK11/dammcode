"""
MyCodingMaster Design System — v2.0 (Premium Redesign)

Centralized design tokens and style system.
Professional, minimal, fast, modern, AI-first, developer-focused.

Inspired by: Cursor, Linear, Raycast, JetBrains, GitHub Desktop, Warp, Zed
Identity: Unique MyCodingMaster aesthetic — calm, premium, unified.
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
    WIDTH = 48        # Fixed width
    ICON_SIZE = 32    # Button size
    PADDING = 6       # Internal padding
    SPACING = 4       # Button spacing


class Sidebar:
    """Sidebar configuration - professional IDE style."""
    MIN_WIDTH = 200
    DEFAULT_WIDTH = 260
    MAX_WIDTH = 480
    COLLAPSED_WIDTH = 48
    HEADER_HEIGHT = 35
    ROW_HEIGHT = 24


class Spacing:
    """Consistent spacing scale (4px base unit)."""
    XXS = 2   # 2px  — Tiny gaps
    XS = 4    # 4px  — Minimal spacing
    SM = 8    # 8px  — Small spacing
    MD = 12   # 12px — Default spacing
    LG = 16   # 16px — Medium spacing
    XL = 24   # 24px — Large spacing
    XXL = 32  # 32px — Extra large
    XXXL = 40 # 40px — Section spacing


# ═══════════════════════════════════════════════════════════════════════
# BORDER RADIUS
# ═══════════════════════════════════════════════════════════════════════

class Radius:
    """Professional border radius values — refined for premium feel (8-10px system)."""
    NONE = 0    # Sharp corners
    SM = 6      # Subtle rounding (buttons, inputs)
    MD = 8      # Default rounding (cards, panels)
    LG = 10     # Card rounding (dialogs, dropdowns)
    XL = 12     # Large rounding (modals, popovers)
    XXL = 16    # Extra-large (command palette)
    ROUND = 24  # Pill shape


# ═══════════════════════════════════════════════════════════════════════
# ELEVATION / SHADOWS
# ═══════════════════════════════════════════════════════════════════════

class Shadow:
    """Subtle elevation shadows."""
    NONE = "none"
    SM = "0 1px 2px rgba(0, 0, 0, 0.12), 0 0 1px rgba(0, 0, 0, 0.08)"
    MD = "0 2px 6px rgba(0, 0, 0, 0.16), 0 0 1px rgba(0, 0, 0, 0.08)"
    LG = "0 4px 12px rgba(0, 0, 0, 0.20), 0 0 1px rgba(0, 0, 0, 0.06)"
    XL = "0 8px 24px rgba(0, 0, 0, 0.28), 0 0 2px rgba(0, 0, 0, 0.08)"


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
    """Type scale — refined for sharp hierarchy."""
    XXS = 9   # Tiny labels
    XS = 11   # Small labels, status text
    SM = 12   # Default UI text
    MD = 13   # Body text
    LG = 14   # Emphasis, section titles
    XL = 16   # Headings
    XXL = 18  # Large headings
    XXXL = 20 # Hero text
    
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
    
    # Surfaces — layered depth system
    bg: str              # Deepest background (application canvas)
    bg_secondary: str    # Raised surface (activity bar, panel backgrounds)
    surface: str         # Card / input surface (elevated controls)
    surface_hover: str   # Hover state for surfaces
    surface_active: str  # Active/selected state
    
    # UI Elements
    sidebar: str         # Sidebar body background
    editor_bg: str       # Editor background (focus area)
    toolbar: str         # Toolbar background
    terminal_bg: str     # Terminal background
    statusbar: str       # Status bar background
    
    # Borders
    border: str          # Default border
    border_subtle: str   # Subtle dividers (hairline separators)
    border_hover: str    # Hovered borders
    border_focus: str    # Focused input borders
    
    # Text — 4-level hierarchy
    text: str            # Primary text (high contrast)
    text_secondary: str  # Secondary text (labels, descriptions)
    text_tertiary: str   # Muted text (placeholders, hints)
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
# THEME DEFINITIONS — Refined Premium Palettes
# ═══════════════════════════════════════════════════════════════════════

class Themes:
    """Professional theme collection — handcrafted for developer comfort."""
    
    DARK = ColorPalette(
        # Primary — Purple/violet accent matching reference
        primary="#8B5CF6",
        primary_hover="#A78BFA",
        primary_active="#7C3AED",
        primary_text="#FFFFFF",
        
        # Surfaces — layered depth: 5 distinct levels (darker, more premium)
        # Level 0: Deepest (app canvas)
        bg="#0B0B10",
        # Level 1: Raised panels (activity bar, sidebar header, dock title)
        bg_secondary="#131318",
        # Level 2: Cards / inputs / dropdowns
        surface="#1A1A22",
        # Level 3: Hover state
        surface_hover="#23232E",
        # Level 4: Active / pressed / selected state
        surface_active="#2D2D3C",
        
        # UI Elements — harmonized with surface layers
        sidebar="#111116",
        editor_bg="#0E0E14",
        toolbar="#131318",
        terminal_bg="#09090D",
        statusbar="#4C1D95",  # Purple status bar background
        
        # Borders — ultra-subtle for clean separation
        border="#2A2A38",
        border_subtle="#1E1E28",
        border_hover="#3A3A4C",
        border_focus="#8B5CF6",
        
        # Text — refined 4-level hierarchy with proper contrast
        text="#E4E4ED",
        text_secondary="#9898A8",
        text_tertiary="#636375",
        text_disabled="#3E3E4C",
        
        # States
        hover="#23232E",
        selection="#3B2A5A",
        selection_inactive="#1E1E28",
        focus_ring="#8B5CF6",
        
        # Semantic — muted but clear
        error="#F87171",
        error_bg="#2E1414",
        warning="#FBBF24",
        warning_bg="#2E2510",
        success="#34D399",
        success_bg="#0F2A1E",
        info="#60A5FA",
        info_bg="#142033",
        
        # Accent — purple/violet (matches reference image)
        accent="#8B5CF6",
        accent_hover="#A78BFA",
        accent_active="#7C3AED",
        
        # Syntax highlighting — balanced, VSCode-inspired with purple tint
        syntax_keyword="#C084FC",
        syntax_string="#86EFAC",
        syntax_comment="#4B5563",
        syntax_number="#FBBF24",
        syntax_function="#60A5FA",
        syntax_class="#FCD34D",
        syntax_operator="#94A3B8",
        syntax_bracket="#FDE68A",
    )
    
    LIGHT = ColorPalette(
        # Primary
        primary="#4F6AE6",
        primary_hover="#6580EF",
        primary_active="#3D56CC",
        primary_text="#FFFFFF",
        
        # Surfaces
        bg="#F8F8FA",
        bg_secondary="#F0F0F4",
        surface="#FFFFFF",
        surface_hover="#ECECF0",
        surface_active="#E0E0E8",
        
        # UI Elements
        sidebar="#F0F0F4",
        editor_bg="#FFFFFF",
        toolbar="#F8F8FA",
        terminal_bg="#FAFAFA",
        statusbar="#F0F0F4",
        
        # Borders
        border="#DCDCE4",
        border_subtle="#E8E8F0",
        border_hover="#C8C8D4",
        border_focus="#4F6AE6",
        
        # Text
        text="#1C1C28",
        text_secondary="#6B6B80",
        text_tertiary="#9898AC",
        text_disabled="#C0C0CC",
        
        # States
        hover="#ECECF0",
        selection="#D6DEFF",
        selection_inactive="#E8E8F0",
        focus_ring="#4F6AE6",
        
        # Semantic
        error="#DC2626",
        error_bg="#FEF2F2",
        warning="#D97706",
        warning_bg="#FFFBEB",
        success="#059669",
        success_bg="#F0FDF4",
        info="#4F6AE6",
        info_bg="#EFF3FF",
        
        # Accent
        accent="#4F6AE6",
        accent_hover="#6580EF",
        accent_active="#3D56CC",
        
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
        
        bg="#1E2127",
        bg_secondary="#21252B",
        surface="#282C34",
        surface_hover="#2C323C",
        surface_active="#323842",
        
        sidebar="#1E2127",
        editor_bg="#282C34",
        toolbar="#21252B",
        terminal_bg="#1B1F23",
        statusbar="#21252B",
        
        border="#181A1F",
        border_subtle="#1E2127",
        border_hover="#3E4451",
        border_focus="#61AFEF",
        
        text="#ABB2BF",
        text_secondary="#7F848E",
        text_tertiary="#5C6370",
        text_disabled="#3E4451",
        
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
        bg_secondary="#0D1117",
        surface="#161B22",
        surface_hover="#1C2128",
        surface_active="#21262D",
        
        sidebar="#0D1117",
        editor_bg="#0D1117",
        toolbar="#0D1117",
        terminal_bg="#010409",
        statusbar="#0D1117",
        
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
        
        bg="#242933",
        bg_secondary="#2E3440",
        surface="#3B4252",
        surface_hover="#434C5E",
        surface_active="#4C566A",
        
        sidebar="#242933",
        editor_bg="#2E3440",
        toolbar="#2E3440",
        terminal_bg="#242933",
        statusbar="#2E3440",
        
        border="#3B4252",
        border_subtle="#2E3440",
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
        """Global application stylesheet — complete premium design."""
        p = self.palette
        return f"""
        /* Global Reset & Base */
        * {{
            font-family: {FontFamily.UI_FALLBACK};
            font-size: {FontSize.SM}px;
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
            border-bottom: 1px solid {p.border_subtle};
            font-size: {FontSize.XS}px;
            font-weight: {FontWeight.SEMIBOLD};
            letter-spacing: 0.04em;
        }}
        
        QDockWidget::close-button, QDockWidget::float-button {{
            border: none;
            background: transparent;
            padding: {Spacing.XXS}px;
            width: 14px;
            height: 14px;
            border-radius: {Radius.SM}px;
        }}
        
        QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
            background-color: {p.surface_hover};
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
            background-color: {p.border_subtle};
            width: 1px;
            height: 1px;
        }}
        
        QMainWindow::separator:hover {{
            background-color: {p.accent};
        }}
        
        /* ToolTip — compact, premium feel */
        QToolTip {{
            background-color: {p.surface};
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
            padding: {Spacing.XS}px 0;
        }}
        
        QMenu::item {{
            padding: {Spacing.SM}px {Spacing.XL}px;
            border-radius: {Radius.SM}px;
            margin: 1px {Spacing.XS}px;
            color: {p.text};
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
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
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
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {p.surface};
            color: {p.text_secondary};
            border: 1px solid {p.border};
            border-radius: {Radius.SM}px;
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
        
        QPushButton:disabled {{
            color: {p.text_disabled};
            border-color: {p.border_subtle};
            background-color: transparent;
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
            border-radius: {Radius.SM}px;
            padding: {Spacing.XS}px {Spacing.SM}px;
            selection-background-color: {p.selection};
            selection-color: {p.text};
            font-size: {FontSize.SM}px;
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
            font-size: {FontSize.SM}px;
        }}
        
        /* ComboBox */
        QComboBox {{
            background-color: {p.surface};
            color: {p.text};
            border: 1px solid {p.border};
            border-radius: {Radius.SM}px;
            padding: {Spacing.XS}px {Spacing.SM}px;
            min-width: 100px;
            min-height: 24px;
            font-size: {FontSize.SM}px;
        }}
        
        QComboBox:hover {{
            border-color: {p.border_hover};
        }}
        
        QComboBox:focus {{
            border-color: {p.focus_ring};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 18px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            width: 0;
            height: 0;
            border-left: 3px solid transparent;
            border-right: 3px solid transparent;
            border-top: 4px solid {p.text_tertiary};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {p.surface};
            border: 1px solid {p.border};
            border-radius: {Radius.SM}px;
            padding: {Spacing.XS}px;
            selection-background-color: {p.surface_hover};
            outline: none;
            font-size: {FontSize.SM}px;
        }}
        
        /* Labels */
        QLabel {{
            color: {p.text};
            font-size: {FontSize.SM}px;
            background-color: transparent;
        }}
        
        QLabel.muted {{
            color: {p.text_tertiary};
            font-size: {FontSize.XS}px;
        }}
        
        QLabel.heading {{
            font-size: {FontSize.LG}px;
            font-weight: {FontWeight.SEMIBOLD};
            color: {p.text};
        }}
        
        /* List Widgets / Tree Widgets */
        QListWidget, QTreeWidget, QListView, QTreeView {{
            background-color: {p.sidebar};
            border: none;
            outline: none;
            selection-background-color: {p.surface_hover};
            selection-color: {p.text};
            color: {p.text};
            font-size: {FontSize.SM}px;
        }}
        
        QListWidget::item, QListView::item {{
            padding: {Spacing.XS}px {Spacing.MD}px;
            border-radius: {Radius.SM}px;
            margin: 1px {Spacing.XS}px;
            min-height: 24px;
        }}
        
        QListWidget::item:hover, QListView::item:hover {{
            background-color: {p.surface_hover};
        }}
        
        QListWidget::item:selected, QListView::item:selected {{
            background-color: {p.surface_active};
            color: {p.text};
        }}
        
        QTreeWidget::item, QTreeView::item {{
            padding: {Spacing.XS}px {Spacing.SM}px;
            min-height: 24px;
        }}
        
        QTreeWidget::item:hover, QTreeView::item:hover {{
            background-color: {p.surface_hover};
        }}
        
        QTreeWidget::item:selected, QTreeView::item:selected {{
            background-color: {p.surface_active};
            color: {p.text};
        }}
        
        QTreeWidget::item:selected:!active, QTreeView::item:selected:!active {{
            background-color: {p.selection_inactive};
            color: {p.text};
        }}
        
        QTreeWidget::branch, QTreeView::branch {{
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
            font-size: {FontSize.SM}px;
            spacing: {Spacing.XS}px;
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
        
        /* Radio Buttons */
        QRadioButton {{
            color: {p.text};
            font-size: {FontSize.SM}px;
        }}
        
        QRadioButton::indicator {{
            width: 14px;
            height: 14px;
            border: 1px solid {p.border};
            border-radius: 7px;
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
            width: 14px;
            height: 14px;
            border-radius: 7px;
            margin: -5px 0;
        }}
        
        QSlider::handle:horizontal:hover {{
            background-color: {p.accent};
        }}
        
        /* Progress Bar */
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
        
        /* Status Bar */
        QStatusBar {{
            background-color: {p.statusbar};
            border-top: 1px solid {p.border_subtle};
            color: {p.text_secondary};
            font-size: {FontSize.XS}px;
            padding: 0 {Spacing.SM}px;
            min-height: 24px;
            max-height: 24px;
        }}
        
        QStatusBar::item {{
            border: none;
        }}
        
        /* ToolBar */
        QToolBar {{
            background-color: {p.toolbar};
            border: none;
            border-bottom: 1px solid {p.border_subtle};
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
            padding: {Spacing.XS}px {Spacing.SM}px;
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
        
        QToolButton::menu-indicator {{
            subcontrol-origin: padding;
            subcontrol-position: center right;
            padding-right: {Spacing.XS}px;
            image: none;
            width: 0;
            height: 0;
            border-left: 3px solid transparent;
            border-right: 3px solid transparent;
            border-top: 4px solid {p.text_tertiary};
        }}
        
        QToolButton::menu-indicator:hover {{
            border-top-color: {p.text};
        }}
        
        /* Group Boxes */
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
        
        /* Splitter — ultra-thin, accent on hover */
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
