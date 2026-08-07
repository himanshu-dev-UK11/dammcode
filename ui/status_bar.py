"""
Bottom Status Bar — v1.0 (Premium Purple Accent)

Clean 24px status bar matching the reference design.
Purple/violet background with light text.
Shows: [AI Status] [Workspace] [Branch] ─── [Ln:Col] [Lang] [Indent] [Version]
"""

from PySide6.QtWidgets import QStatusBar, QLabel, QWidget, QHBoxLayout, QFrame
from PySide6.QtCore import Qt
from pathlib import Path
from ui.design_system import Spacing


class StatusBarColors:
    """Color constants for the purple status bar — tuned for readability."""
    BG = "#4C1D95"
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#E9D5FF"
    TEXT_TERTIARY = "#C4B5FD"
    ACCENT_SUCCESS = "#34D399"
    ACCENT_WARNING = "#FBBF24"
    ACCENT_ERROR = "#F87171"
    ACCENT_INFO = "#93C5FD"


def _separator_label() -> QLabel:
    """Subtle dot separator between status sections."""
    from ui.design_system import FontSize
    lbl = QLabel("·")
    lbl.setStyleSheet(f"color: {StatusBarColors.TEXT_TERTIARY}; background-color: transparent; padding: 0 6px; font-size: {FontSize.XS}px;")
    return lbl


class StatusChip(QLabel):
    """A small inline badge in the status bar — tuned for purple background."""
    def __init__(self, text: str = "", accent: bool = False):
        super().__init__(text)
        self._accent = accent
        self._color = StatusBarColors.TEXT_SECONDARY
        self._update_style()

    def _update_style(self):
        from ui.design_system import FontSize
        color = self._color
        weight = "600" if self._accent else "500"
        self.setStyleSheet(f"""
            color: {color};
            background-color: transparent;
            font-size: {FontSize.XS}px;
            padding: 0 6px;
            font-weight: {weight};
        """)

    def set_accent(self, on: bool):
        self._accent = on
        self._update_style()

    def set_color(self, color: str):
        """Set a custom text color (e.g. for error/warning/success states)."""
        self._color = color
        self._update_style()


class BottomStatusBar(QStatusBar):
    """
    Compact status bar reflecting IDE state.

    Subscribes to:
        workspace_loaded    → workspace path + file counts
        cursor_moved        → Ln / Col / total lines
        file_modified_state → [Unsaved] indicator
        tab_switched        → current file name, language
        task_started        → AI Thinking indicator
        task_completed      → AI Idle
    """
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self.setSizeGripEnabled(False)
        self.setObjectName("BottomStatusBar")

        self.setup_ui()
        self._subscribe()

    def setup_ui(self):
        from ui.design_system import FontSize
        
        self.setStyleSheet(f"""
            QStatusBar#BottomStatusBar {{
                background-color: {StatusBarColors.BG};
                border-top: 1px solid rgba(0, 0, 0, 0.25);
                color: {StatusBarColors.TEXT_SECONDARY};
                font-size: {FontSize.XS}px;
                padding: 0 {Spacing.SM}px;
                min-height: 24px;
                max-height: 24px;
            }}
            QStatusBar#BottomStatusBar::item {{
                border: none;
            }}
        """)

        self._lbl_ai       = StatusChip("● AI: Idle")
        self._lbl_ai.set_color(StatusBarColors.TEXT_SECONDARY)
        self._lbl_ws       = StatusChip("No Workspace")
        self._lbl_branch   = StatusChip("⎇ main")
        self._lbl_provider = StatusChip("")
        self._lbl_provider.setVisible(False)
        self._lbl_file     = StatusChip("")
        self._lbl_file.setVisible(False)
        self._lbl_unsaved  = QLabel("")
        self._lbl_unsaved.setStyleSheet(
            f"color: {StatusBarColors.ACCENT_WARNING}; font-size: {FontSize.XS}px; padding: 0 6px; background-color: transparent; font-weight: 500;"
        )

        self.addWidget(self._lbl_ai)
        self.addWidget(_separator_label())
        self.addWidget(self._lbl_ws)
        self.addWidget(_separator_label())
        self.addWidget(self._lbl_branch)
        self._sep_provider = _separator_label()
        self._sep_provider.setVisible(False)
        self.addWidget(self._sep_provider)
        self.addWidget(self._lbl_provider)
        self._sep_file = _separator_label()
        self._sep_file.setVisible(False)
        self.addWidget(self._sep_file)
        self.addWidget(self._lbl_file)
        self.addWidget(self._lbl_unsaved)

        self._lbl_cursor = StatusChip("Ln 1, Col 1")
        self._lbl_lang   = StatusChip("Plain Text")
        self._lbl_ver    = StatusChip("v1.9")

        self.addPermanentWidget(_separator_label())
        self.addPermanentWidget(self._lbl_cursor)
        self.addPermanentWidget(_separator_label())
        self.addPermanentWidget(self._lbl_lang)
        self.addPermanentWidget(_separator_label())
        self.addPermanentWidget(self._lbl_ver)
        
        self._lbl_project_name = StatusChip("")
        self._lbl_project_name.setVisible(False)
        self._lbl_files = StatusChip("")
        self._lbl_files.setVisible(False)
        self._lbl_lang_summary = StatusChip("")
        self._lbl_lang_summary.setVisible(False)

    def _subscribe(self):
        self.event_bus.subscribe("workspace_loaded",   self._on_workspace)
        self.event_bus.subscribe("workspace_metadata_updated", self._on_workspace_metadata)
        self.event_bus.subscribe("cursor_moved",       self._on_cursor)
        self.event_bus.subscribe("file_modified_state",self._on_modified)
        self.event_bus.subscribe("tab_switched",       self._on_tab_switched)
        self.event_bus.subscribe("task_started",       self._on_task_started)
        self.event_bus.subscribe("task_completed",     self._on_task_done)
        self.event_bus.subscribe("task_failed",        self._on_task_failed)
        self.event_bus.subscribe("ai_provider_changed", self._on_provider_changed)
        self.event_bus.subscribe("ai_model_changed",   self._on_model_changed)
    
    def update_workspace_status(self, path: str, name: str, language: str, 
                                 framework: str, files: int, folders: int):
        """Update workspace status display."""
        # Shorten path
        path_str = str(path)
        if len(path_str) > 36:
            path_str = "…" + path_str[-33:]
        
        self._lbl_ws.setText(path_str)
        self._lbl_ws.set_accent(False)
        
        # Show project metadata
        self._lbl_project_name.setText(f"Project: {name}")
        self._lbl_project_name.set_accent(True)
        self._lbl_project_name.setVisible(True)
        
        self._lbl_files.setText(f"{files} files, {folders} folders")
        self._lbl_files.set_accent(False)
        self._lbl_files.setVisible(True)
        
        self._lbl_lang_summary.setText(f"{language} • {framework}")
        self._lbl_lang_summary.set_accent(False)
        self._lbl_lang_summary.setVisible(True)

    # ── Event handlers ─────────────────────────────
    def _on_workspace(self, data):
        ctx = data.get("context")
        if not ctx:
            return
        self.update_workspace_status(
            str(ctx.root_path),
            getattr(ctx, "project_name", "Unknown"),
            getattr(ctx, "primary_language", "Unknown"),
            getattr(ctx, "framework_name", "Unknown"),
            getattr(ctx, "total_files", 0),
            getattr(ctx, "total_folders", 0)
        )
    
    def _on_workspace_metadata(self, data):
        """Handle workspace metadata update event."""
        path = data.get("path", "")
        name = data.get("project_name", "Unknown")
        language = data.get("primary_language", "Unknown")
        framework = data.get("framework", "Unknown")
        files = data.get("total_files", 0)
        folders = data.get("total_folders", 0)
        
        self.update_workspace_status(path, name, language, framework, files, folders)

    def _on_cursor(self, data):
        line  = data.get("line", 1)
        col   = data.get("col", 1)
        total = data.get("total", 1)
        self._lbl_cursor.setText(f"Ln {line}, Col {col}  ({total} lines)")

    def _on_modified(self, data):
        modified = data.get("modified", False)
        self._lbl_unsaved.setText("● Unsaved" if modified else "")

    def _on_tab_switched(self, data):
        path = data.get("path", "")
        if path:
            name = Path(path).name
            ext  = Path(path).suffix.lower()
            lang = self._detect_lang(ext)
            self._lbl_file.setText(name)
            self._lbl_lang.setText(lang)
            # Show file chip and its separator now that a file is open
            self._lbl_file.setVisible(True)
            self._sep_file.setVisible(True)


    def _on_task_started(self, data):
        self._lbl_ai.setText("● AI: Thinking")
        self._lbl_ai.set_color(StatusBarColors.TEXT_PRIMARY)
        self._lbl_ai.set_accent(True)

    def _on_task_done(self, data):
        self._lbl_ai.setText("● AI: Idle")
        self._lbl_ai.set_color(StatusBarColors.TEXT_SECONDARY)
        self._lbl_ai.set_accent(False)

    def _on_task_failed(self, data):
        self._lbl_ai.setText("● AI: Error")
        self._lbl_ai.set_color(StatusBarColors.ACCENT_ERROR)
        self._lbl_ai.set_accent(True)

    def _on_provider_changed(self, data: dict):
        """Handle provider change event."""
        provider = data.get("provider")
        status = data.get("status", "unknown")

        if provider and status == "connected":
            self._lbl_provider.setText(f"● {provider.upper()}")
            self._lbl_provider.set_color(StatusBarColors.ACCENT_SUCCESS)
            self._lbl_provider.set_accent(True)
            self._lbl_provider.setVisible(True)
            self._sep_provider.setVisible(True)
        elif provider:
            self._lbl_provider.setText(f"● {provider.upper()}")
            self._lbl_provider.set_color(StatusBarColors.ACCENT_ERROR)
            self._lbl_provider.set_accent(True)
            self._lbl_provider.setVisible(True)
            self._sep_provider.setVisible(True)
        else:
            self._lbl_provider.setVisible(False)
            self._sep_provider.setVisible(False)

    def _on_model_changed(self, data: dict):
        """Handle model change event."""
        model = data.get("model")
        provider = data.get("provider")

        if model:
            provider_name = provider.upper() if provider else "Unknown"
            self._lbl_provider.setText(f"● {provider_name}: {model}")
            self._lbl_provider.set_color(StatusBarColors.TEXT_PRIMARY)
            self._lbl_provider.set_accent(True)
            self._lbl_provider.setVisible(True)
            self._sep_provider.setVisible(True)
        elif provider:
            self._lbl_provider.setText(f"● {provider.upper()}")
            self._lbl_provider.set_color(StatusBarColors.TEXT_SECONDARY)
            self._lbl_provider.set_accent(False)
            self._lbl_provider.setVisible(True)
            self._sep_provider.setVisible(True)


    @staticmethod
    def _detect_lang(ext: str) -> str:
        langs = {
            ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
            ".jsx": "React JSX", ".tsx": "React TSX", ".html": "HTML",
            ".css": "CSS", ".json": "JSON", ".md": "Markdown",
            ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML",
            ".rs": "Rust", ".go": "Go", ".cpp": "C++", ".c": "C",
            ".java": "Java", ".cs": "C#", ".rb": "Ruby",
            ".sh": "Shell", ".bat": "Batch", ".ps1": "PowerShell",
            ".sql": "SQL", ".kt": "Kotlin", ".swift": "Swift",
            ".dart": "Dart", ".txt": "Plain Text",
        }
        return langs.get(ext, "Plain Text")
