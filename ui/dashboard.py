# -*- coding: utf-8 -*-
"""
Dashboard -- v2.0.0  Professional Welcome Dashboard

Two-column IDE home screen. Left (65%) has hero card, recent/pinned projects,
recent files. Right (35%) has AI center, workspace overview, system status,
tips, quick actions.

Heavy data (workspace stats, provider status, system metrics) loads
asynchronously in worker threads. All UI updates via EventBus signals.
Never blocks the Qt main thread.
"""

from __future__ import annotations
import json, os, platform, threading, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QGraphicsOpacityEffect, QGridLayout,
    QSpacerItem,
)
from PySide6.QtCore import (
    Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QPoint,
    QParallelAnimationGroup,
)
from PySide6.QtGui import QCursor, QFont

from core.logger import setup_logger
from ui.design_system import get_design_system, Spacing, Radius, FontSize, FontWeight

logger = setup_logger(__name__)

# ---------------------------------------------------------------------
# LANGUAGE COLOR MAP
# ---------------------------------------------------------------------
LANG_COLORS: Dict[str, str] = {
    "python": "#3B82F6", "javascript": "#F59E0B", "typescript": "#3B82F6",
    "rust": "#EF4444",   "go": "#10B981",          "java": "#F59E0B",
    "cpp": "#8B5CF6",    "c": "#8B5CF6",            "csharp": "#8B5CF6",
    "html": "#EF4444",   "css": "#3B82F6",           "json": "#10B981",
    "yaml": "#F59E0B",   "toml": "#F59E0B",          "markdown": "#8E8E98",
    "bash": "#10B981",   "sh": "#10B981",
}

LANG_EXT: Dict[str, str] = {
    ".py": "Python",    ".js": "JavaScript", ".ts": "TypeScript",
    ".rs": "Rust",      ".go": "Go",          ".java": "Java",
    ".cpp": "C++",      ".c": "C",            ".cs": "C#",
    ".html": "HTML",    ".css": "CSS",        ".json": "JSON",
    ".yaml": "YAML",    ".yml": "YAML",       ".toml": "TOML",
    ".md": "Markdown",  ".sh": "Bash",        ".bash": "Bash",
    ".tsx": "TypeScript", ".jsx": "JavaScript",
}

# Short badge text per extension
LANG_BADGE: Dict[str, str] = {
    ".py": "PY",  ".js": "JS",  ".ts": "TS",  ".rs": "RS",  ".go": "GO",
    ".java": "JV", ".cpp": "C+", ".c": "C ",  ".cs": "C#",  ".html": "HT",
    ".css": "CS",  ".json": "{}", ".yaml": "YL", ".yml": "YL", ".md": "MD",
    ".sh": "SH",  ".tsx": "TX", ".jsx": "JX",
}

LANG_EXT_COLOR: Dict[str, str] = {
    ".py": "#3B82F6", ".js": "#F59E0B", ".ts": "#3B82F6", ".rs": "#EF4444",
    ".go": "#10B981", ".java": "#F59E0B", ".cpp": "#8B5CF6", ".c": "#8B5CF6",
    ".cs": "#8B5CF6", ".html": "#EF4444", ".css": "#3B82F6", ".json": "#10B981",
    ".yaml": "#F59E0B", ".yml": "#F59E0B", ".md": "#8E8E98", ".sh": "#10B981",
    ".tsx": "#3B82F6", ".jsx": "#F59E0B",
}

TIPS = [
    ("Ctrl+Shift+P", "Open command palette to search all commands"),
    ("Ctrl+B", "Toggle the file explorer sidebar"),
    ("Ctrl+\\", "Toggle the AI workspace panel"),
    ("Ctrl+`", "Toggle integrated terminal"),
    ("Ctrl+K Ctrl+O", "Open a project folder"),
    ("Ctrl+Shift+F", "Search across all files in workspace"),
    ("Ctrl+Enter", "Submit a new AI engineering task"),
    ("Ctrl+Z / Ctrl+Y", "Undo and redo code changes"),
    ("F5", "Run the current file"),
    ("Ctrl+S", "Save current file"),
    ("Alt+F4", "Exit MyCodingMaster"),
    ("Tip", "Pinned projects always appear at the top of recent projects"),
    ("Tip", "The AI workspace remembers your conversation history per session"),
    ("Tip", "Use Ctrl+Shift+G to open source control and view git changes"),
    ("Tip", "The Engineering Task System can decompose large prompts automatically"),
]

# ---------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------

def _relative_time(path: str) -> str:
    """Return human-readable relative modification time for a path."""
    try:
        mtime = Path(path).stat().st_mtime
        diff  = time.time() - mtime
        if diff < 60:
            return "just now"
        if diff < 3600:
            m = int(diff // 60)
            return f"{m}m ago"
        if diff < 86400:
            h = int(diff // 3600)
            return f"{h}h ago"
        d = int(diff // 86400)
        if d < 30:
            return f"{d}d ago"
        w = d // 7
        if w < 8:
            return f"{w}w ago"
        return f"{d // 30}mo ago"
    except Exception:
        return ""


def _section_label(text: str) -> QLabel:
    """Section header label with clear hierarchy."""
    lbl = QLabel(text.upper())
    lbl.setStyleSheet(
        "color: #3B82F6;"
        "font-size: 11px;"
        "font-weight: 600;"
        "letter-spacing: 0.08em;"
        "background: transparent;"
        "margin-bottom: 2px;"
    )
    return lbl


def _meta_label(text: str, color: str = "#8E8E98") -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent;")
    return lbl


def _divider() -> QFrame:
    p = get_design_system().palette
    d = QFrame()
    d.setFrameShape(QFrame.HLine)
    d.setFixedHeight(1)
    d.setStyleSheet(f"background: {p.border_subtle}; border: none;")
    return d


def _lang_badge(lang_short: str, color: str = "#52525C") -> QLabel:
    lbl = QLabel(lang_short)
    lbl.setFixedSize(24, 16)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"color: {color};"
        f"background: transparent;"
        f"border: 1px solid {color};"
        f"border-radius: 3px;"
        f"font-size: 9px;"
        f"font-weight: 700;"
        f"letter-spacing: 0.5px;"
    )
    return lbl


def _status_dot(color: str) -> QLabel:
    d = QLabel("●")
    d.setStyleSheet(f"color: {color}; font-size: 8px; font-weight: 700; background: transparent;")
    d.setFixedWidth(12)
    return d


def _small_btn(text: str, accent: bool = False) -> QPushButton:
    ds = get_design_system(); p = ds.palette
    if accent:
        style = (
            f"QPushButton {{"
            f"  background: {p.accent}; color: #fff; border: none;"
            f"  border-radius: 6px; padding: 8px 12px; font-size: 12px; font-weight: 600;"
            f"}}"
            f"QPushButton:hover {{ background: {p.accent_hover}; }}"
            f"QPushButton:pressed {{ background: {p.accent_active}; }}"
        )
    else:
        style = (
            f"QPushButton {{"
            f"  background: {p.surface_hover}; color: {p.text_secondary};"
            f"  border: 1px solid {p.border};"
            f"  border-radius: 6px; padding: 8px 12px; font-size: 12px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: {p.surface_active}; color: {p.text};"
            f"  border-color: {p.border_hover};"
            f"}}"
            f"QPushButton:pressed {{ background: {p.bg}; }}"
        )
    btn = QPushButton(text)
    btn.setStyleSheet(style)
    btn.setCursor(QCursor(Qt.PointingHandCursor))
    return btn


def _icon_btn(icon_char: str, tooltip: str = "") -> QPushButton:
    ds = get_design_system(); p = ds.palette
    btn = QPushButton(icon_char)
    btn.setFixedSize(24, 24)
    btn.setToolTip(tooltip)
    btn.setStyleSheet(
        f"QPushButton {{"
        f"  background: transparent; border: none;"
        f"  color: {p.text_tertiary}; font-size: 13px;"
        f"  border-radius: 4px;"
        f"}}"
        f"QPushButton:hover {{ color: {p.text}; background: {p.surface_hover}; }}"
    )
    btn.setCursor(QCursor(Qt.PointingHandCursor))
    return btn


def _kv_row(grid: QGridLayout, label: str, value: str, row_idx: int):
    """Add a label+value pair to a QGridLayout row, return the value QLabel."""
    lbl = _meta_label(label)
    val = _meta_label(value, "#E2E2E6")
    grid.addWidget(lbl, row_idx, 0)
    grid.addWidget(val, row_idx, 1)
    return val

# ---------------------------------------------------------------------
# BASE CARD
# ---------------------------------------------------------------------
class _Card(QFrame):
    """Rounded card with 1px border and subtle hover elevation.

    Parameters
    ----------
    accent : bool
        When True, renders a 2px coloured left-border accent strip.
    """
    def __init__(self, parent=None, accent: bool = False):
        super().__init__(parent)
        ds = get_design_system()
        p  = ds.palette
        self._accent      = accent
        self._border      = p.border
        self._border_hov  = p.border_hover
        self._bg          = p.surface
        self._bg_hov      = p.surface_hover
        self.setObjectName("DashCard")
        self._apply_style(False)
        self.setFrameShape(QFrame.NoFrame)

    def _apply_style(self, hovered: bool):
        border = self._border_hov if hovered else self._border
        bg     = self._bg_hov if hovered else self._bg
        accent_strip = (
            "border-left: 2px solid #3B82F6;"
        ) if self._accent else ""
        self.setStyleSheet(
            f"#DashCard {{"
            f"  background-color: {bg};"
            f"  border: 1px solid {border};"
            f"  {accent_strip}"
            f"  border-radius: 10px;"
            f"}}"
        )

    def enterEvent(self, e):
        self._apply_style(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._apply_style(False)
        super().leaveEvent(e)

# ---------------------------------------------------------------------
# TOP HEADER BAR
# ---------------------------------------------------------------------
class _HeaderBar(QWidget):
    """Logo - Version - Workspace Status - Theme - AI Provider."""

    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        ds = get_design_system(); p = ds.palette
        self.setFixedHeight(52)
        self.setStyleSheet(
            f"background: {p.bg_secondary};"
            f"border-bottom: 1px solid {p.border};"
        )
        row = QHBoxLayout(self)
        row.setContentsMargins(16, 0, 16, 0)
        row.setSpacing(12)

        # Logo box + name
        logo_box = QLabel("MCM")
        logo_box.setFixedSize(36, 24)
        logo_box.setAlignment(Qt.AlignCenter)
        logo_box.setStyleSheet(
            f"color: #fff;"
            f"background: {p.accent};"
            f"border-radius: 6px;"
            f"font-size: 10px;"
            f"font-weight: 800;"
            f"letter-spacing: 0.08em;"
        )
        name = QLabel("MyCodingMaster")
        name.setStyleSheet(
            f"color: {p.text}; font-size: 14px; font-weight: 600; background: transparent;"
        )
        self._version = QLabel("v2.0.0")
        self._version.setStyleSheet(
            f"color: {p.accent}; font-size: 11px; font-weight: 500; background: transparent;"
        )

        row.addWidget(logo_box)
        row.addWidget(name)
        row.addWidget(self._version)
        row.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Workspace status pill
        self._ws_pill = self._pill("No workspace", "#52525C")
        row.addWidget(self._ws_pill)

        # Theme pill
        self._theme_pill = self._pill("Dark", p.text_tertiary)
        row.addWidget(self._theme_pill)

        # AI Provider pill  (colored square prefix)
        self._ai_pill = self._pill("  AI: --", "#52525C")
        row.addWidget(self._ai_pill)

        event_bus.subscribe("workspace_loaded",        self._on_ws)
        event_bus.subscribe("workspace_closed",        lambda _: self._ws_pill.setText("No workspace"))
        event_bus.subscribe("provider_status_updated", self._on_provider)

    def _pill(self, text: str, color: str) -> QLabel:
        ds = get_design_system(); p = ds.palette
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {color};"
            f"background: {p.surface};"
            f"border: 1px solid {p.border};"
            f"border-left: 2px solid {color};"
            f"border-radius: 12px;"
            f"padding: 4px 10px;"
            f"font-size: 10px;"
            f"font-weight: 500;"
        )
        return lbl

    def _on_ws(self, data):
        ctx  = data.get("context")
        name = ctx.project_name if ctx and hasattr(ctx, "project_name") else data.get("path", "")
        if name and not ctx:
            name = Path(name).name
        display = name[:24] if name else "Workspace"
        self._ws_pill.setText(f"  {display}")
        ds = get_design_system(); p = ds.palette
        self._ws_pill.setStyleSheet(
            f"color: #10B981;"
            f"background: {p.surface};"
            f"border: 1px solid {p.border};"
            f"border-left: 2px solid #10B981;"
            f"border-radius: 12px;"
            f"padding: 4px 10px;"
            f"font-size: 10px;"
            f"font-weight: 500;"
        )

    def _on_provider(self, data):
        name   = data.get("provider", data.get("name", ""))
        status = data.get("status", "unknown")
        color  = "#10B981" if status == "connected" else "#52525C"
        dot    = "●" if status == "connected" else "○"
        self._ai_pill.setText(f"{dot} AI: {name[:14]}" if name else f"{dot} AI: --")
        ds = get_design_system(); p = ds.palette
        self._ai_pill.setStyleSheet(
            f"color: {color};"
            f"background: {p.surface};"
            f"border: 1px solid {p.border};"
            f"border-left: 2px solid {color};"
            f"border-radius: 12px;"
            f"padding: 4px 10px;"
            f"font-size: 10px;"
            f"font-weight: 500;"
        )

# ---------------------------------------------------------------------
# LEFT COLUMN -- HERO CARD
# ---------------------------------------------------------------------
class _HeroCard(_Card):
    """Welcome back - current workspace - quick open buttons."""
    open_folder      = Signal()
    new_project      = Signal()
    clone_repo       = Signal()
    continue_session = Signal()

    def __init__(self, event_bus):
        super().__init__(accent=True)
        self.event_bus = event_bus
        ds = get_design_system(); p = ds.palette
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        # Greeting row
        top = QHBoxLayout(); top.setSpacing(10)
        self._greeting = QLabel("Welcome back")
        self._greeting.setStyleSheet(
            f"color: {p.text}; font-size: 24px; font-weight: 700; background: transparent;"
        )
        top.addWidget(self._greeting)
        top.addStretch()
        lay.addLayout(top)

        # Workspace info
        self._ws_name   = QLabel("No workspace open")
        self._ws_name.setStyleSheet(
            f"color: {p.text_secondary}; font-size: 14px; font-weight: 500; background: transparent;"
        )
        self._proj_path = _meta_label("--")
        self._proj_path.setStyleSheet(
            f"color: #8E8E98; font-size: 12px; background: transparent;"
        )
        self._last_open = _meta_label("--", "#52525C")
        self._last_open.setStyleSheet(
            f"color: #52525C; font-size: 11px; background: transparent;"
        )
        lay.addWidget(self._ws_name)
        lay.addWidget(self._proj_path)
        lay.addWidget(self._last_open)
        lay.addWidget(_divider())

        # Action buttons row
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        self._btn_open  = _small_btn("> Open Folder", accent=True)
        self._btn_new   = _small_btn("+ New Project")
        self._btn_clone = _small_btn("$ Clone Repo")
        self._btn_cont  = _small_btn("-> Continue")
        for b in (self._btn_open, self._btn_new, self._btn_clone, self._btn_cont):
            btn_row.addWidget(b)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        self._btn_open.clicked.connect(self.open_folder)
        self._btn_new.clicked.connect(self.new_project)
        self._btn_clone.clicked.connect(self.clone_repo)
        self._btn_cont.clicked.connect(self.continue_session)

        event_bus.subscribe("workspace_loaded", self._on_ws)
        event_bus.subscribe("workspace_closed", self._on_ws_closed)

    def _on_ws(self, data):
        ctx  = data.get("context")
        path = data.get("path", "")
        name = ctx.project_name if ctx and hasattr(ctx, "project_name") else Path(path).name
        ds   = get_design_system(); p = ds.palette
        self._ws_name.setText(name)
        self._ws_name.setStyleSheet(
            f"color: #E2E2E6; font-size: 14px; font-weight: 600; background: transparent;"
        )
        truncated = path[:68] + ("..." if len(path) > 68 else "")
        self._proj_path.setText(truncated)
        self._last_open.setText(
            f"Opened {datetime.now().strftime('%b %d, %Y  %H:%M')}"
        )
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        self._greeting.setText(greeting)

    def _on_ws_closed(self, _):
        self._ws_name.setText("No workspace open")
        self._ws_name.setStyleSheet(
            "color: #8E8E98; font-size: 13px; font-weight: 500; background: transparent;"
        )
        self._proj_path.setText("--")
        self._last_open.setText("--")
        self._greeting.setText("Welcome back")

# ---------------------------------------------------------------------
# LEFT COLUMN -- PROJECT ROW
# ---------------------------------------------------------------------
class _ProjectRow(QWidget):
    """One row inside Recent Projects / Pinned Projects lists."""
    open_requested = Signal(str)
    pin_requested  = Signal(str)
    fav_requested  = Signal(str)

    def __init__(self, path: str, pinned: bool = False, parent=None):
        super().__init__(parent)
        self._path   = path
        self._pinned = pinned
        ds = get_design_system(); p = ds.palette
        self.setObjectName("ProjRow")
        self._normal_ss = (
            f"#ProjRow {{ background: transparent; border-radius: 6px; padding: 2px; }}"
        )
        self._hover_ss = (
            f"#ProjRow {{ background: {p.surface_hover}; border-radius: 6px; padding: 2px; }}"
        )
        self.setStyleSheet(self._normal_ss)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(48)

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 0, 8, 0)
        row.setSpacing(8)

        # Language color dot + badge
        ext   = Path(path).suffix.lower()
        color = LANG_EXT_COLOR.get(ext, "#52525C")
        badge_txt = LANG_BADGE.get(ext, "  ")
        dot   = _status_dot(color)
        badge = _lang_badge(badge_txt, color)
        row.addWidget(dot)
        row.addWidget(badge)

        # Text block
        txt = QVBoxLayout(); txt.setSpacing(2)
        name_lbl = QLabel(Path(path).name)
        name_lbl.setStyleSheet(
            f"color: {p.text}; font-size: 13px; font-weight: 500; background: transparent;"
        )
        loc_lbl = QLabel(path[:54] + ("..." if len(path) > 54 else ""))
        loc_lbl.setStyleSheet(
            f"color: #52525C; font-size: 11px; background: transparent;"
        )
        txt.addWidget(name_lbl)
        txt.addWidget(loc_lbl)
        row.addLayout(txt, stretch=1)

        # Relative time
        rel = _relative_time(path)
        if rel:
            time_lbl = _meta_label(rel, "#52525C")
            time_lbl.setFixedWidth(52)
            time_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(time_lbl)

        # Pin button
        pin_char = "+" if not pinned else "x"
        pin_tip  = "Unpin" if pinned else "Pin"
        self._pin_btn = _icon_btn(pin_char, pin_tip)
        self._pin_btn.clicked.connect(lambda: self.pin_requested.emit(self._path))
        row.addWidget(self._pin_btn)

        # Open arrow
        open_btn = _icon_btn("->", "Open project")
        open_btn.clicked.connect(lambda: self.open_requested.emit(self._path))
        row.addWidget(open_btn)

    def enterEvent(self, e):
        self.setStyleSheet(self._hover_ss)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.setStyleSheet(self._normal_ss)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        self.open_requested.emit(self._path)
        super().mousePressEvent(e)


# ---------------------------------------------------------------------
# LEFT COLUMN -- PROJECTS CARD
# ---------------------------------------------------------------------
class _ProjectsCard(_Card):
    """Recent Projects + Pinned Projects sections."""
    open_requested = Signal(str)
    pin_requested  = Signal(str)

    def __init__(self, event_bus, title: str = "Recent Projects", pinned_mode: bool = False):
        super().__init__()
        self.event_bus    = event_bus
        self._pinned_mode = pinned_mode
        ds = get_design_system()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        hdr = QHBoxLayout()
        hdr.addWidget(_section_label(title))
        hdr.addStretch()
        self._count_lbl = _meta_label("0", "#52525C")
        hdr.addWidget(self._count_lbl)
        lay.addLayout(hdr)
        lay.addWidget(_divider())

        # Scrollable list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setMaximumHeight(240)

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: transparent;")
        self._list_lay = QVBoxLayout(self._list_widget)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(4)
        self._list_lay.setAlignment(Qt.AlignTop)
        scroll.setWidget(self._list_widget)
        lay.addWidget(scroll)

        # Empty state
        self._empty_widget = QWidget()
        self._empty_widget.setStyleSheet("background: transparent;")
        empty_lay = QVBoxLayout(self._empty_widget)
        empty_lay.setAlignment(Qt.AlignCenter)
        empty_lay.setSpacing(8)
        empty_lbl = QLabel("[ No recent projects ]")
        empty_lbl.setAlignment(Qt.AlignCenter)
        empty_lbl.setStyleSheet("color: #52525C; font-size: 11px; background: transparent;")
        open_btn = _small_btn("> Open Folder", accent=True)
        open_btn.setFixedWidth(110)
        open_btn.clicked.connect(self._on_empty_open)
        empty_lay.addWidget(empty_lbl)
        empty_lay.addWidget(open_btn, alignment=Qt.AlignCenter)
        self._empty_widget.setVisible(False)
        lay.addWidget(self._empty_widget)

        event_bus.subscribe("recent_projects_updated",  self._on_update)
        event_bus.subscribe("recent_projects_changed",  self._on_changed)
        event_bus.subscribe("pinned_projects_changed",  self._on_pinned_changed)

    def _on_empty_open(self):
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(None, "Open Project Folder")
        if folder:
            self.event_bus.publish("request_open_workspace", {"path": folder})

    def load_projects(self, projects: List[str], pinned: List[str]):
        source = pinned if self._pinned_mode else projects
        self._render(source, pinned)

    def _on_update(self, data):
        projects = data.get("recent", [])
        pinned   = data.get("pinned", [])
        source   = pinned if self._pinned_mode else projects
        self._render(source, pinned)

    def _on_changed(self, data):
        if not self._pinned_mode:
            self._load_from_file()

    def _on_pinned_changed(self, data):
        if self._pinned_mode:
            self._load_from_file()

    def _load_from_file(self):
        try:
            rp = Path("config/recent_projects.json")
            pp = Path("config/pinned_projects.json")
            r  = json.loads(rp.read_text()) if rp.exists() else []
            p  = json.loads(pp.read_text()) if pp.exists() else []
            self._render(p if self._pinned_mode else r, p)
        except Exception:
            pass

    def _render(self, projects: List[str], pinned: List[str]):
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not projects:
            self._empty_widget.setVisible(True)
            self._count_lbl.setText("0")
            return
        self._empty_widget.setVisible(False)
        self._count_lbl.setText(str(len(projects)))
        for path in projects[:20]:
            row = _ProjectRow(path, path in pinned)
            row.open_requested.connect(self.open_requested)
            row.pin_requested.connect(self.pin_requested)
            self._list_lay.addWidget(row)


# ---------------------------------------------------------------------
# LEFT COLUMN -- RECENT FILES
# ---------------------------------------------------------------------
class _RecentFilesCard(_Card):
    file_requested = Signal(str)

    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        ds = get_design_system(); p = ds.palette
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        hdr = QHBoxLayout()
        hdr.addWidget(_section_label("Recent Files"))
        hdr.addStretch()
        self._count_lbl = _meta_label("0", "#52525C")
        hdr.addWidget(self._count_lbl)
        lay.addLayout(hdr)
        lay.addWidget(_divider())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setMaximumHeight(200)

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._lay = QVBoxLayout(self._container)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(2)
        self._lay.setAlignment(Qt.AlignTop)
        scroll.setWidget(self._container)
        lay.addWidget(scroll)

        self._files: List[str] = []
        event_bus.subscribe("file_opened",          self._on_file_opened)
        event_bus.subscribe("recent_files_updated", self._on_update)

    def load_files(self, files: List[str]):
        self._files = files[:20]
        self._render()

    def _on_file_opened(self, data):
        path = data.get("path", "")
        if path and path not in self._files:
            self._files.insert(0, path)
            self._files = self._files[:20]
            self._render()
            self._save()

    def _on_update(self, data):
        self._files = data.get("files", [])
        self._render()

    def _save(self):
        try:
            Path("config/recent_files.json").write_text(
                json.dumps(self._files, indent=2)
            )
        except Exception:
            pass

    def _render(self):
        while self._lay.count():
            item = self._lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._count_lbl.setText(str(len(self._files)))
        ds = get_design_system(); p = ds.palette
        for fpath in self._files:
            row = QWidget()
            row.setObjectName("FileRow")
            row.setStyleSheet(
                f"#FileRow {{ background: transparent; border-radius: 4px; }}"
                f"#FileRow:hover {{ background: {p.surface_hover}; }}"
            )
            row.setCursor(QCursor(Qt.PointingHandCursor))
            row.setFixedHeight(36)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(6, 0, 6, 0)
            rl.setSpacing(8)

            ext       = Path(fpath).suffix.lower()
            color     = LANG_EXT_COLOR.get(ext, "#52525C")
            badge_txt = LANG_BADGE.get(ext, "  ")
            badge     = _lang_badge(badge_txt, color)
            rl.addWidget(badge)

            fname = QLabel(Path(fpath).name)
            fname.setStyleSheet(
                f"color: {p.text}; font-size: 11px; background: transparent;"
            )
            rl.addWidget(fname, stretch=1)

            parent_dir = QLabel(Path(fpath).parent.name)
            parent_dir.setStyleSheet(
                f"color: #52525C; font-size: 10px; background: transparent;"
            )
            rl.addWidget(parent_dir)

            rel = _relative_time(fpath)
            if rel:
                time_lbl = _meta_label(rel, "#3B3B45")
                time_lbl.setFixedWidth(52)
                time_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                rl.addWidget(time_lbl)

            _p = fpath
            row.mousePressEvent = (lambda e, fp=_p: self.file_requested.emit(fp))
            self._lay.addWidget(row)


# ---------------------------------------------------------------------
# RIGHT COLUMN -- AI CENTER
# ---------------------------------------------------------------------
class _AICenterCard(_Card):
    switch_requested = Signal()
    models_requested = Signal()

    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        ds = get_design_system(); p = ds.palette
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        hdr = QHBoxLayout()
        hdr.addWidget(_section_label("AI Center"))
        hdr.addStretch()
        self._connected_badge = QLabel("Connected")
        self._connected_badge.setStyleSheet(
            "color: #10B981; background: transparent;"
            "border: 1px solid #10B981; border-radius: 8px;"
            "padding: 1px 6px; font-size: 9px; font-weight: 600;"
        )
        self._connected_badge.setVisible(False)
        hdr.addWidget(self._connected_badge)
        lay.addLayout(hdr)
        lay.addWidget(_divider())

        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setContentsMargins(0, 0, 0, 0)

        self._provider_val = _kv_row(grid, "Provider",      "--", 0)
        self._model_val    = _kv_row(grid, "Model",         "--", 1)
        self._health_val   = _kv_row(grid, "Health",        "--", 2)
        self._latency_val  = _kv_row(grid, "Latency",       "--", 3)
        self._stream_val   = _kv_row(grid, "Streaming",     "--", 4)
        self._ctx_val      = _kv_row(grid, "Context Window","--", 5)

        # Status row with colored dot prefix
        status_lbl = _meta_label("Status")
        status_row = QHBoxLayout(); status_row.setSpacing(4)
        self._status_dot = _status_dot("#52525C")
        self._status_val = _meta_label("--", "#E2E2E6")
        status_row.addWidget(self._status_dot)
        status_row.addWidget(self._status_val)
        status_row.addStretch()
        status_container = QWidget()
        status_container.setStyleSheet("background: transparent;")
        status_container.setLayout(status_row)
        grid.addWidget(status_lbl,       6, 0)
        grid.addWidget(status_container, 6, 1)

        lay.addLayout(grid)
        lay.addWidget(_divider())

        btns = QHBoxLayout(); btns.setSpacing(8)
        self._sw_btn  = _small_btn("Quick Switch")
        self._mod_btn = _small_btn("Manage Models")
        self._sw_btn.clicked.connect(self.switch_requested)
        self._mod_btn.clicked.connect(self.models_requested)
        btns.addWidget(self._sw_btn)
        btns.addWidget(self._mod_btn)
        btns.addStretch()
        lay.addLayout(btns)

        event_bus.subscribe("provider_status_updated", self._on_provider)
        event_bus.subscribe("models_updated",          self._on_models)

    def _on_provider(self, data):
        name    = data.get("provider",  data.get("name", ""))
        status  = data.get("status",    "--")
        latency = data.get("latency_ms", "--")
        health  = data.get("health_score", "--")
        stream  = data.get("streaming", True)
        ctx     = data.get("context_window", "--")
        connected = status == "connected"
        dot_color = "#10B981" if connected else "#EF4444"

        self._provider_val.setText(name or "--")
        self._health_val.setText(str(health))
        if isinstance(latency, (int, float)):
            self._latency_val.setText(f"{latency}ms")
        else:
            self._latency_val.setText(str(latency))
        self._stream_val.setText("Yes" if stream else "No")
        if isinstance(ctx, int):
            self._ctx_val.setText(f"{ctx:,}")
        else:
            self._ctx_val.setText(str(ctx))
        self._status_val.setText(status.capitalize())
        self._status_val.setStyleSheet(
            f"color: {dot_color}; font-size: 10px; background: transparent;"
        )
        self._status_dot.setStyleSheet(
            f"color: {dot_color}; font-size: 8px; background: transparent;"
        )
        self._connected_badge.setVisible(connected)

    def _on_models(self, data):
        model = data.get("model", data.get("selected_model", ""))
        if model:
            self._model_val.setText(str(model)[:28])

    def update_provider(self, provider_name, model, status, latency, ctx, streaming, health):
        """Called from background thread via EventBus."""
        connected = status == "connected"
        dot_color = "#10B981" if connected else "#EF4444"
        self._provider_val.setText(str(provider_name)[:24])
        self._model_val.setText(str(model)[:28])
        if isinstance(health, (int, float)):
            self._health_val.setText(f"{health}/100")
        else:
            self._health_val.setText(str(health))
        if isinstance(latency, (int, float)):
            self._latency_val.setText(f"{latency}ms")
        else:
            self._latency_val.setText(str(latency))
        self._stream_val.setText("Yes" if streaming else "No")
        if isinstance(ctx, int):
            self._ctx_val.setText(f"{ctx:,}")
        else:
            self._ctx_val.setText(str(ctx))
        self._status_val.setText(status.capitalize())
        self._status_val.setStyleSheet(
            f"color: {dot_color}; font-size: 10px; background: transparent;"
        )
        self._status_dot.setStyleSheet(
            f"color: {dot_color}; font-size: 8px; background: transparent;"
        )
        self._connected_badge.setVisible(connected)


# ---------------------------------------------------------------------
# RIGHT COLUMN -- WORKSPACE OVERVIEW
# ---------------------------------------------------------------------
class _WorkspaceOverviewCard(_Card):
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)
        lay.addWidget(_section_label("Workspace Overview"))
        lay.addWidget(_divider())

        grid = QGridLayout()
        grid.setSpacing(5)
        grid.setContentsMargins(0, 0, 0, 0)

        self._files_val     = _kv_row(grid, "Files",        "--", 0)
        self._folders_val   = _kv_row(grid, "Folders",      "--", 1)
        self._langs_val     = _kv_row(grid, "Languages",    "--", 2)
        self._framework_val = _kv_row(grid, "Framework",    "--", 3)
        self._git_val       = _kv_row(grid, "Git Branch",   "--", 4)
        self._health_val    = _kv_row(grid, "Health Score", "--", 5)
        self._size_val      = _kv_row(grid, "Size",         "--", 6)
        self._type_val      = _kv_row(grid, "Project Type", "--", 7)
        lay.addLayout(grid)

        event_bus.subscribe("workspace_statistics_updated",          self._on_stats)
        event_bus.subscribe("workspace_loaded",                      self._on_ws)
        event_bus.subscribe("project_intelligence_scan_completed",   self._on_intel)

    def _on_ws(self, data):
        ctx = data.get("context")
        if ctx:
            if hasattr(ctx, "file_count"):
                self._files_val.setText(str(ctx.file_count))
            if hasattr(ctx, "folder_count"):
                self._folders_val.setText(str(ctx.folder_count))

    def _on_stats(self, data):
        self._files_val.setText(str(data.get("files",        "--")))
        self._folders_val.setText(str(data.get("folders",    "--")))
        self._langs_val.setText(str(data.get("languages",    "--")))
        self._framework_val.setText(str(data.get("framework","--")))
        self._git_val.setText(str(data.get("git_branch",     "--")))
        score = data.get("health_score", "--")
        if isinstance(score, (int, float)):
            self._health_val.setText(f"{score}/100")
        else:
            self._health_val.setText(str(score))
        self._size_val.setText(str(data.get("size",          "--")))
        self._type_val.setText(str(data.get("project_type",  "--")))

    def _on_intel(self, data):
        intel = data.get("intelligence")
        if not intel:
            return
        if hasattr(intel, "architecture") and intel.architecture:
            self._type_val.setText(intel.architecture)
        if hasattr(intel, "language_stats") and intel.language_stats:
            d = (intel.language_stats.to_dict()
                 if hasattr(intel.language_stats, "to_dict") else {})
            langs = ", ".join(list(d.keys())[:4]) if d else "--"
            self._langs_val.setText(langs)
        if hasattr(intel, "health") and intel.health:
            self._health_val.setText(f"{intel.health.score}/100")


# ---------------------------------------------------------------------
# RIGHT COLUMN -- SYSTEM STATUS
# ---------------------------------------------------------------------
class _SystemStatusCard(_Card):
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)
        lay.addWidget(_section_label("System Status"))
        lay.addWidget(_divider())

        grid = QGridLayout()
        grid.setSpacing(5)
        grid.setContentsMargins(0, 0, 0, 0)

        self._cpu_val    = _kv_row(grid, "CPU",             "--%",  0)
        self._mem_val    = _kv_row(grid, "Memory",          "--",   1)
        self._tasks_val  = _kv_row(grid, "Running Tasks",   "0",    2)
        self._jobs_val   = _kv_row(grid, "Background Jobs", "0",    3)
        self._prov_val   = _kv_row(grid, "Providers",       "0",    4)
        self._models_val = _kv_row(grid, "Loaded Models",   "0",    5)
        lay.addLayout(grid)

        event_bus.subscribe("system_status_updated",   self._on_status)
        event_bus.subscribe("execution_status_update", self._on_exec)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._sample_system)
        self._timer.start(3000)

    @staticmethod
    def _cpu_bar(pct: float) -> str:
        """Return an ASCII bar like [####......] 40% for given percent 0-100."""
        filled = int(pct / 10)
        empty  = 10 - filled
        bar    = "#" * filled + "." * empty
        return f"[{bar}] {pct:.0f}%"

    def _sample_system(self):
        """Non-blocking system metrics sampled on main thread (lightweight)."""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            bar = self._cpu_bar(cpu)
            self._cpu_val.setText(bar)
            color = "#EF4444" if cpu > 80 else "#10B981" if cpu < 40 else "#F59E0B"
            self._cpu_val.setStyleSheet(
                f"color: {color}; font-size: 10px; background: transparent;"
            )
            used_mb  = mem.used  // (1024 * 1024)
            total_mb = mem.total // (1024 * 1024)
            self._mem_val.setText(f"{used_mb:,} / {total_mb:,} MB")
        except ImportError:
            self._cpu_val.setText("--")
            self._mem_val.setText("--")
        except Exception:
            pass

    def _on_status(self, data):
        self._prov_val.setText(str(data.get("providers",       0)))
        self._models_val.setText(str(data.get("models",        0)))
        self._jobs_val.setText(str(data.get("background_jobs", 0)))

    def _on_exec(self, data):
        running = data.get("running_tasks", 0)
        self._tasks_val.setText(str(running))
        color = "#10B981" if running == 0 else "#3B82F6"
        self._tasks_val.setStyleSheet(
            f"color: {color}; font-size: 10px; background: transparent;"
        )


# ---------------------------------------------------------------------
# RIGHT COLUMN -- TIPS CARD
# ---------------------------------------------------------------------
class _TipsCard(_Card):
    def __init__(self, event_bus):
        super().__init__()
        ds = get_design_system(); p = ds.palette
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        hdr = QHBoxLayout()
        hdr.addWidget(_section_label("Tips & Shortcuts"))
        hdr.addStretch()
        self._index_lbl = _meta_label(f"1 / {len(TIPS)}", "#52525C")
        hdr.addWidget(self._index_lbl)
        nxt = QPushButton("Next ->")
        nxt.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {p.text_tertiary};"
            f"  border: none; font-size: 10px; padding: 0; }}"
            f"QPushButton:hover {{ color: {p.text}; }}"
        )
        nxt.setCursor(QCursor(Qt.PointingHandCursor))
        hdr.addWidget(nxt)
        lay.addLayout(hdr)
        lay.addWidget(_divider())

        # Keyboard shortcut display
        self._kbd = QLabel("")
        self._kbd.setStyleSheet(
            f"background: {p.surface_hover};"
            f"color: {p.accent};"
            f"border: 1px solid {p.border};"
            f"border-radius: 3px;"
            f"padding: 2px 8px;"
            f"font-size: 10px;"
            f"font-weight: 600;"
            f"font-family: Consolas, monospace;"
        )
        self._desc = QLabel("")
        self._desc.setWordWrap(True)
        self._desc.setStyleSheet(
            f"color: {p.text_secondary}; font-size: 11px; background: transparent;"
        )
        lay.addWidget(self._kbd)
        lay.addWidget(self._desc)

        self._idx = 0
        self._show_tip()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_tip)
        self._timer.start(8000)
        nxt.clicked.connect(self._next_tip)

    def _show_tip(self):
        kbd, desc = TIPS[self._idx % len(TIPS)]
        # Format keyboard shortcut with brackets to look like a real kbd
        if kbd.startswith("Tip"):
            self._kbd.setText("Tip")
        else:
            self._kbd.setText(f"[{kbd}]")
        self._desc.setText(desc)
        self._index_lbl.setText(
            f"{(self._idx % len(TIPS)) + 1} / {len(TIPS)}"
        )

    def _next_tip(self):
        self._idx += 1
        self._show_tip()


# ---------------------------------------------------------------------
# RIGHT COLUMN -- QUICK ACTIONS
# ---------------------------------------------------------------------
class _QuickActionsCard(_Card):
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)
        lay.addWidget(_section_label("Quick Actions"))
        lay.addWidget(_divider())

        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setContentsMargins(0, 0, 0, 0)

        # 8 actions in 4x2 grid with icon-char prefixes
        actions = [
            ("> Open Folder",  "request_open_workspace", {},  0, 0, True),
            ("/ Search",       "find_requested",         {},  0, 1, False),
            ("# AI Chat",      "toggle_ai_workspace",    {},  1, 0, False),
            (": Commands",     "show_command_palette",   {},  1, 1, False),
            ("* Settings",     "show_settings",          {},  2, 0, False),
            ("_ Terminal",     "toggle_terminal",        {},  2, 1, False),
            ("$ Git",          "show_git",               {},  3, 0, False),
            ("+ Extensions",   "show_extensions",        {},  3, 1, False),
        ]
        for label, event_name, payload, r, c, is_open in actions:
            btn = _small_btn(label, accent=(r == 0 and c == 0))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            if is_open:
                btn.clicked.connect(self._on_open_folder)
            else:
                _e, _p = event_name, payload
                btn.clicked.connect(
                    lambda checked=False, e=_e, p=_p: self.event_bus.publish(e, p)
                )
            grid.addWidget(btn, r, c)

        lay.addLayout(grid)

    def _on_open_folder(self):
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(None, "Open Project Folder")
        if folder:
            self.event_bus.publish("request_open_workspace", {"path": folder})


# ---------------------------------------------------------------------
# BACKGROUND DATA LOADER  (kept exactly as-is functionally)
# ---------------------------------------------------------------------
class _DataLoader:
    """Loads heavy data in worker threads, publishes results via EventBus."""

    def __init__(self, event_bus, workspace_manager=None, provider_manager=None):
        self._bus = event_bus
        self._wm  = workspace_manager
        self._pm  = provider_manager

    def load_all(self):
        """Fire all loaders on background threads."""
        threading.Thread(target=self._load_projects,  daemon=True).start()
        threading.Thread(target=self._load_files,     daemon=True).start()
        threading.Thread(target=self._load_ws_stats,  daemon=True).start()
        threading.Thread(target=self._load_providers, daemon=True).start()
        threading.Thread(target=self._load_system,    daemon=True).start()

    def _load_projects(self):
        try:
            rp = Path("config/recent_projects.json")
            pp = Path("config/pinned_projects.json")
            recent = json.loads(rp.read_text()) if rp.exists() else []
            pinned = json.loads(pp.read_text()) if pp.exists() else []
            self._bus.publish("recent_projects_updated", {"recent": recent, "pinned": pinned})
        except Exception as e:
            logger.debug(f"DataLoader projects: {e}")

    def _load_files(self):
        try:
            fp = Path("config/recent_files.json")
            files = json.loads(fp.read_text()) if fp.exists() else []
            self._bus.publish("recent_files_updated", {"files": files})
        except Exception as e:
            logger.debug(f"DataLoader files: {e}")

    def _load_ws_stats(self):
        try:
            if self._wm and self._wm.active_workspace:
                ws   = self._wm.active_workspace
                path = ws.path
                files = dirs = total_size = 0
                langs: Dict[str, int] = {}
                for root, d, f in os.walk(path):
                    d[:] = [
                        x for x in d
                        if not x.startswith(".")
                        and x not in ("__pycache__", "node_modules", ".venv", "venv")
                    ]
                    dirs  += len(d)
                    files += len(f)
                    for fname in f:
                        try:
                            total_size += os.path.getsize(os.path.join(root, fname))
                        except Exception:
                            pass
                        ext = Path(fname).suffix.lower()
                        if ext in LANG_EXT:
                            langs[LANG_EXT[ext]] = langs.get(LANG_EXT[ext], 0) + 1
                top_langs = ", ".join(
                    sorted(langs, key=langs.get, reverse=True)[:3]
                )
                if total_size < 10 ** 6:
                    size_str = f"{total_size // 1024:,} KB"
                else:
                    size_str = f"{total_size // 1024 // 1024:,} MB"
                git_branch = "--"
                try:
                    import subprocess
                    result = subprocess.run(
                        ["git", "branch", "--show-current"],
                        capture_output=True, text=True, cwd=str(path), timeout=2,
                    )
                    if result.returncode == 0:
                        git_branch = result.stdout.strip() or "--"
                except Exception:
                    pass
                self._bus.publish("workspace_statistics_updated", {
                    "files": files, "folders": dirs,
                    "languages": top_langs, "size": size_str,
                    "git_branch": git_branch, "project_type": "--",
                    "framework": "--", "health_score": "--",
                })
        except Exception as e:
            logger.debug(f"DataLoader ws_stats: {e}")

    def _load_providers(self):
        try:
            if self._pm:
                all_prov  = (self._pm._health.get_all_health()
                             if hasattr(self._pm, "_health") else {})
                connected = [n for n, h in all_prov.items()
                             if getattr(h, "is_available", False)]
                self._bus.publish("system_status_updated", {
                    "providers": len(connected),
                    "models": 0,
                    "background_jobs": 0,
                })
                for name in connected[:1]:
                    h = all_prov[name]
                    self._bus.publish("provider_status_updated", {
                        "provider":        name,
                        "status":          "connected",
                        "health_score":    getattr(h, "health_score",    "--"),
                        "latency_ms":      getattr(h, "avg_latency_ms",  "--"),
                        "streaming":       True,
                        "context_window":  "--",
                    })
        except Exception as e:
            logger.debug(f"DataLoader providers: {e}")

    def _load_system(self):
        try:
            import psutil
            cpu  = psutil.cpu_percent(interval=0.5)
            mem  = psutil.virtual_memory()
            used = mem.used  // (1024 * 1024)
            tot  = mem.total // (1024 * 1024)
            self._bus.publish("system_status_updated", {
                "cpu": cpu, "memory_mb": used, "total_memory_mb": tot,
            })
        except Exception:
            pass


# ---------------------------------------------------------------------
# MAIN DASHBOARD  (two-column layout, public API preserved)
# ---------------------------------------------------------------------
class Dashboard(QWidget):
    """
    Professional IDE home dashboard -- v2.0.0.

    Layout:
      +----------- HeaderBar -----------------------------------------+
      |  [MCM]  MyCodingMaster  v2.0.0       [ws]  [Dark]  [AI: --]  |
      +------------------------+-------------------------------------+
      |   LEFT  65%            |   RIGHT  35%                        |
      |   HeroCard             |   AI Center                         |
      |   Recent Projects      |   Workspace Overview                |
      |   Pinned Projects      |   System Status                     |
      |   Recent Files         |   Tips                              |
      |                        |   Quick Actions                     |
      +------------------------+-------------------------------------+

    All heavy data loaded async. EventBus drives every update.
    Never blocks the Qt main thread.
    """

    open_recent_requested  = Signal(str)
    new_file_requested     = Signal()
    open_project_requested = Signal(str)

    def __init__(self, event_bus,
                 workspace_manager=None,
                 provider_manager=None):
        super().__init__()
        self.event_bus          = event_bus
        self._workspace_manager = workspace_manager
        self._provider_manager  = provider_manager
        self._project_analyzer  = None
        self.setObjectName("Dashboard")
        self._setup_ui()
        self._subscribe_events()

        # Kick off background data load after 100 ms (let UI paint first)
        QTimer.singleShot(100, self._async_load)

    # -- Build UI ------------------------------------------------------
    def _setup_ui(self):
        ds = get_design_system(); p = ds.palette
        self.setStyleSheet(f"#Dashboard {{ background: {p.bg}; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header bar
        self._header = _HeaderBar(self.event_bus)
        root.addWidget(self._header)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"background: {p.bg}; border: none;")

        self._body = QWidget()
        self._body.setStyleSheet(f"background: {p.bg};")
        body_lay = QHBoxLayout(self._body)
        body_lay.setContentsMargins(16, 16, 16, 16)
        body_lay.setSpacing(16)
        body_lay.setAlignment(Qt.AlignTop)

        # -- LEFT column -----------------------------------------------
        left = QWidget()
        left.setStyleSheet("background: transparent;")
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(12)
        left_lay.setAlignment(Qt.AlignTop)

        self._hero      = _HeroCard(self.event_bus)
        self._recent    = _ProjectsCard(self.event_bus, "Recent Projects",  pinned_mode=False)
        self._pinned    = _ProjectsCard(self.event_bus, "Pinned Projects",  pinned_mode=True)
        self._rec_files = _RecentFilesCard(self.event_bus)

        # Hero button wiring
        self._hero.open_folder.connect(self._on_open_folder)
        self._hero.new_project.connect(self._on_new_project)
        self._hero.clone_repo.connect(
            lambda: self.event_bus.publish("clone_repo_requested", {})
        )
        self._hero.continue_session.connect(
            lambda: self.event_bus.publish("restore_session", {})
        )

        # Projects wiring
        self._recent.open_requested.connect(self._on_open_recent)
        self._recent.pin_requested.connect(self._on_pin)
        self._pinned.open_requested.connect(self._on_open_recent)
        self._pinned.pin_requested.connect(self._on_unpin)
        self._rec_files.file_requested.connect(
            lambda fp: self.event_bus.publish("file_open_requested", {"path": fp})
        )

        for w in (self._hero, self._recent, self._pinned, self._rec_files):
            left_lay.addWidget(w)
        left_lay.addStretch()

        # -- RIGHT column ----------------------------------------------
        right = QWidget()
        right.setStyleSheet("background: transparent;")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(12)
        right_lay.setAlignment(Qt.AlignTop)

        self._ai_center   = _AICenterCard(self.event_bus)
        self._ws_overview = _WorkspaceOverviewCard(self.event_bus)
        self._sys_status  = _SystemStatusCard(self.event_bus)
        self._tips        = _TipsCard(self.event_bus)
        self._quick_act   = _QuickActionsCard(self.event_bus)

        self._ai_center.switch_requested.connect(
            lambda: self.event_bus.publish("toggle_ai_workspace", {})
        )
        self._ai_center.models_requested.connect(
            lambda: self.event_bus.publish("show_model_manager", {})
        )

        for w in (self._ai_center, self._ws_overview, self._sys_status,
                  self._tips, self._quick_act):
            right_lay.addWidget(w)
        right_lay.addStretch()

        body_lay.addWidget(left,  stretch=65)
        body_lay.addWidget(right, stretch=35)

        scroll.setWidget(self._body)
        root.addWidget(scroll)

        # Fade-in animation on the body
        self._opacity_effect = QGraphicsOpacityEffect(self._body)
        self._body.setGraphicsEffect(self._opacity_effect)
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_anim.setDuration(220)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)

    def showEvent(self, e):
        super().showEvent(e)
        self._fade_anim.stop()
        self._fade_anim.start()

    # -- Event subscriptions -------------------------------------------
    def _subscribe_events(self):
        self.event_bus.subscribe("workspace_loaded",  self._on_workspace_loaded)
        self.event_bus.subscribe("workspace_closed",  self._on_workspace_closed)
        self.event_bus.subscribe("file_opened",       self._on_file_opened)
        self.event_bus.subscribe(
            "project_intelligence_scan_completed", self._on_intel
        )
        self.event_bus.subscribe("dashboard_loaded", lambda _: None)  # ACK

    # -- Data loading --------------------------------------------------
    def _async_load(self):
        loader = _DataLoader(
            self.event_bus, self._workspace_manager, self._provider_manager
        )
        loader.load_all()
        self.event_bus.publish("dashboard_loaded", {"ts": datetime.now().isoformat()})

    # -- Public helpers ------------------------------------------------
    def set_project_analyzer(self, pa):
        self._project_analyzer = pa

    def set_workspace_manager(self, wm):
        self._workspace_manager = wm

    def set_provider_manager(self, pm):
        self._provider_manager = pm

    def update_statistics(self, file_count, folder_count, line_count=0):
        """Backward-compat method from old Dashboard."""
        self.event_bus.publish("workspace_statistics_updated", {
            "files": file_count, "folders": folder_count,
        })

    def update_system_status(self, cpu, memory, ai_status):
        """Backward-compat from old Dashboard."""
        pass

    # -- Internal event handlers ---------------------------------------
    def _on_workspace_loaded(self, data):
        QTimer.singleShot(300, self._async_load)

    def _on_workspace_closed(self, _):
        pass

    def _on_file_opened(self, data):
        pass  # _RecentFilesCard handles directly

    def _on_intel(self, data):
        pass  # _WorkspaceOverviewCard handles directly

    # -- User actions --------------------------------------------------
    def _on_open_folder(self):
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(None, "Open Project Folder")
        if folder:
            self.open_project_requested.emit(folder)
            self.event_bus.publish("request_open_workspace", {"path": folder})

    def _on_new_project(self):
        self.new_file_requested.emit()

    def _on_open_recent(self, path: str):
        self.open_recent_requested.emit(path)

    def _on_pin(self, path: str):
        self.event_bus.publish("request_pin_project", {"path": path})

    def _on_unpin(self, path: str):
        self.event_bus.publish("request_unpin_project", {"path": path})
