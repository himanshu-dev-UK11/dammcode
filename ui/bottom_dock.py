
"""
Bottom Dock - Integrated terminal, problems, output, diagnostics panel.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar,
    QPlainTextEdit, QListWidget, QListWidgetItem, QPushButton,
    QLabel, QSizePolicy, QSplitter, QFrame, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QColor, QKeySequence, QShortcut, QFont
from pathlib import Path

DOCK_DEFAULT_HEIGHT = 180
DOCK_MIN_HEIGHT = 26


class ProblemsTab(QWidget):
    """
    Error / warning list.
    """
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._diagnostics = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        from ui.design_system import get_design_system, FontSize
        p = get_design_system().palette
        self._summary = QLabel("No problems detected")
        self._summary.setStyleSheet(f"""
            color: {p.text_tertiary};
            font-size: {FontSize.XS}px;
            padding: 4px 12px;
            background-color: {p.bg_secondary};
            border-bottom: 1px solid {p.border_subtle};
        """)
        layout.addWidget(self._summary)

        self._list = QListWidget()
        self._list.setStyleSheet(f"""
            QListWidget {{
                background-color: {p.bg};
                border: none;
                font-size: {FontSize.SM}px;
                font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
            }}
            QListWidget::item {{
                padding: 2px 8px;
                min-height: 20px;
                border-radius: 3px;
                margin: 0 4px;
            }}
            QListWidget::item:selected {{
                background-color: {p.surface_active};
            }}
            QListWidget::item:hover {{
                background-color: {p.surface_hover};
            }}
        """)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._list)

        self.event_bus.subscribe("problem_added", self._on_problem_added)
        self.event_bus.subscribe("problems_cleared", self._on_cleared)

    def _on_problem_added(self, data: dict):
        level    = data.get("level", "info")
        message  = data.get("message", "")
        file_ref = data.get("file", "")
        line_ref = data.get("line", "")

        icons = {"error": "✕", "warning": "△", "info": "ℹ"}
        colors = {"error": "#EF4444", "warning": "#F59E0B", "info": "#60A5FA"}

        icon  = icons.get(level, "·")
        color = colors.get(level, "#8E8E98")

        loc = f"  {file_ref}:{line_ref}" if file_ref else ""
        text = f"{icon}  {message}{loc}"

        item = QListWidgetItem(text)
        item.setForeground(QColor(color))
        self._list.addItem(item)
        self._update_summary()

    def _on_cleared(self, _):
        self._list.clear()
        self._update_summary()

    def _update_summary(self):
        total = 0
        error_count = 0
        warning_count = 0
        
        for diags in self._diagnostics.values():
            for d in diags:
                total += 1
                severity = d.get("severity", 1)
                if severity == 1:
                    error_count += 1
                elif severity == 2:
                    warning_count += 1
                    
        if total == 0:
            self._summary.setText("No problems detected")
        else:
            parts = []
            if error_count > 0:
                parts.append(f"{error_count} error{'s' if error_count !=1 else ''}")
            if warning_count > 0:
                parts.append(f"{warning_count} warning{'s' if warning_count !=1 else ''}")
            self._summary.setText(", ".join(parts))
            
    def set_diagnostics(self, file_path: str, diagnostics: list):
        self._diagnostics[file_path] = diagnostics
        self._refresh_list()
        
    def _refresh_list(self):
        self._list.clear()
        
        severity_map = {
            1: ("error", "#EF4444", "✕"),
            2: ("warning", "#F59E0B", "△"),
            3: ("info", "#60A5FA", "ℹ"),
            4: ("hint", "#8B5CF6", "⚡"),
        }
        
        for file_path, diags in self._diagnostics.items():
            for diag in diags:
                severity = diag.get("severity", 1)
                level, color, icon = severity_map.get(severity, ("info", "#8E8E98", "·"))
                message = diag.get("message", "")
                range_ = diag.get("range", {})
                start = range_.get("start", {})
                line = start.get("line", 0) + 1

                file_name = Path(file_path).name
                text = f"{icon}  {message}  ({file_name}:{line})"
                item = QListWidgetItem(text)
                item.setData(Qt.UserRole, {"file": file_path, "line": line - 1})
                item.setForeground(QColor(color))
                self._list.addItem(item)
                
        self._update_summary()
        
    def _on_item_double_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data:
            file_path = data.get("file")
            line = data.get("line")
            self.event_bus.publish("file_open_requested", {"path": file_path, "line": line})


class OutputTab(QPlainTextEdit):
    """
    Output / log stream.
    """
    def __init__(self, event_bus):
        super().__init__()
        self.setReadOnly(True)
        self.setObjectName("OutputTab")
        mono = QFont("JetBrains Mono, Cascadia Code, Consolas, Courier New")
        mono.setPointSize(10)
        self.setFont(mono)
        from ui.design_system import get_design_system, FontSize
        p = get_design_system().palette
        self.setStyleSheet(f"""
            #OutputTab {{
                background-color: {p.bg};
                color: {p.text_secondary};
                border: none;
                padding: 6px;
                selection-background-color: {p.selection};
                font-size: {FontSize.SM}px;
            }}
        """)
        event_bus.subscribe("log_message", self._on_log)

    def _on_log(self, data: dict):
        msg = data.get("message", "")
        if msg:
            self.appendPlainText(msg)
            self.ensureCursorVisible()


class DockHeader(QWidget):
    """
    Simple header with title and collapse button.
    """
    toggle_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedHeight(DOCK_MIN_HEIGHT)
        self.setObjectName("DockHeader")
        from ui.design_system import get_design_system, FontSize, FontWeight, Radius
        p = get_design_system().palette
        self.setStyleSheet(f"""
            #DockHeader {{
                background-color: {p.bg_secondary};
                border-top: 1px solid {p.border_subtle};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(0)

        self._lbl = QLabel("TERMINAL")
        self._lbl.setStyleSheet(f"""
            color: {p.text_tertiary};
            font-size: 10px;
            font-weight: {FontWeight.SEMIBOLD};
            letter-spacing: 0.06em;
            background-color: transparent;
        """)
        layout.addWidget(self._lbl)
        layout.addStretch()

        self._btn_collapse = QPushButton("∨")
        self._btn_collapse.setToolTip("Collapse panel  [Ctrl+`]")
        self._btn_collapse.setFixedSize(22, 20)
        self._btn_collapse.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {p.text_tertiary};
                border: none;
                font-size: 12px;
                padding: 0;
                border-radius: {Radius.SM}px;
            }}
            QPushButton:hover {{
                color: {p.text};
                background-color: {p.surface_hover};
            }}
        """)
        self._btn_collapse.clicked.connect(self.toggle_requested.emit)
        layout.addWidget(self._btn_collapse)

    def set_label(self, text: str):
        self._lbl.setText(text.upper())

    def set_collapsed(self, collapsed: bool):
        self._btn_collapse.setText("∧" if collapsed else "∨")


class BottomDock(QWidget):
    """
    Collapsible bottom dock fully integrated with QSplitter.
    """
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._collapsed = False  # Start EXPANDED to show terminal
        self._working_dir = Path.cwd()
        self._main_splitter = None
        self._expanded_height = DOCK_DEFAULT_HEIGHT
        
        self.setObjectName("BottomDock")
        from ui.design_system import get_design_system
        p = get_design_system().palette
        self.setStyleSheet(f"""
            #BottomDock {{
                background-color: {p.bg};
                border-top: 1px solid {p.border_subtle};
            }}
        """)
        
        self._init_terminal_system()
        self.setup_ui()
        
        self.setMinimumHeight(DOCK_MIN_HEIGHT)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.event_bus.subscribe("workspace_loaded", self._on_workspace_loaded)

    def _init_terminal_system(self):
        from ui.terminal.terminal_tab_manager import TerminalTabManager
        from ui.terminal.terminal_toolbar import TerminalToolbar

        self.terminal_manager = TerminalTabManager(self.event_bus, self._working_dir)
        self.toolbar = TerminalToolbar(self)

        self.toolbar.new_terminal_requested.connect(lambda: self.terminal_manager.create_terminal())
        self.toolbar.run_file_requested.connect(self._on_run_file)
        self.toolbar.run_project_requested.connect(self._on_run_project)
        self.toolbar.build_project_requested.connect(self._on_build_project)
        self.toolbar.kill_terminal_requested.connect(self.terminal_manager.kill_current_terminal)
        self.toolbar.restart_terminal_requested.connect(self.terminal_manager.restart_current_terminal)
        self.toolbar.clear_output_requested.connect(self.terminal_manager.clear_current_terminal)
        self.toolbar.search_requested.connect(self._on_search)
        self.toolbar.shell_changed.connect(self._on_shell_changed)
        self.toolbar.directory_changed.connect(self._on_directory_changed)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._header = DockHeader()
        self._header.toggle_requested.connect(self.toggle_collapse)
        layout.addWidget(self._header)

        layout.addWidget(self.toolbar)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._tabs.setTabsClosable(False)
        self._tabs.setMovable(False)
        from ui.design_system import get_design_system, FontSize, FontWeight, Radius, Spacing
        p = get_design_system().palette
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {p.bg};
            }}
            QTabBar {{
                background-color: {p.bg_secondary};
                qproperty-drawBase: 0;
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {p.text_tertiary};
                padding: 2px {Spacing.LG}px;
                border: none;
                border-right: 1px solid {p.border_subtle};
                font-size: {FontSize.XS}px;
                font-weight: {FontWeight.MEDIUM};
                min-width: 70px;
                min-height: 28px;
                max-height: 28px;
                letter-spacing: 0.02em;
            }}
            QTabBar::tab:selected {{
                color: {p.text};
                font-weight: {FontWeight.SEMIBOLD};
                border-bottom: 2px solid {p.accent};
                background-color: {p.bg};
            }}
            QTabBar::tab:hover:!selected {{
                color: {p.text_secondary};
                background-color: {p.surface_hover};
            }}
        """)
        self._tabs.currentChanged.connect(self._on_main_tab_changed)
        layout.addWidget(self._tabs)

        self._tabs.addTab(self.terminal_manager, "TERMINAL")
        
        self._problems = ProblemsTab(self.event_bus)
        self._output = OutputTab(self.event_bus)
        from ui.diagnostics_panel import DiagnosticsTab
        self._diagnostics = DiagnosticsTab(self.event_bus)

        self._tabs.addTab(self._problems, "PROBLEMS")
        self._tabs.addTab(self._output, "OUTPUT")
        self._tabs.addTab(self._diagnostics, "DEBUG CONSOLE")

    def set_main_splitter(self, splitter):
        self._main_splitter = splitter
        
    def _on_main_tab_changed(self, index: int):
        self.toolbar.setVisible(index == 0)
    
    def _on_search(self):
        self.terminal_manager.show_search()
        
    def _on_shell_changed(self, shell: str):
        self.terminal_manager.create_terminal(shell=shell)
        
    def _on_directory_changed(self, directory: str):
        self._working_dir = Path(directory)
        self.terminal_manager.set_working_directory(self._working_dir)
        
    def _on_run_file(self):
        self.event_bus.publish("run_current_file_requested", {
            "editor_tabs": None,
            "use_terminal": True
        })
        
    def _on_run_project(self):
        self.event_bus.publish("run_project_requested", {"use_terminal": True})
        
    def _on_build_project(self):
        self.event_bus.publish("build_project_requested", {"use_terminal": True})
        
    def _on_workspace_loaded(self, data: dict):
        context = data.get("context")
        if context and hasattr(context, "root_path"):
            self._working_dir = Path(context.root_path)
            self.terminal_manager.set_working_directory(self._working_dir)
            self.toolbar.set_working_directory(str(self._working_dir))
            
    def toggle_collapse(self):
        self._collapsed = not self._collapsed
        self._tabs.setVisible(not self._collapsed)
        self.toolbar.setVisible(not self._collapsed)
        self._header.set_collapsed(self._collapsed)
        
        if self._main_splitter:
            sizes = self._main_splitter.sizes()
            if len(sizes) == 2:
                if self._collapsed:
                    self._expanded_height = max(DOCK_MIN_HEIGHT, sizes[1])
                    # Collapsed = keep thin header, give rest back to editor
                    total = sizes[0] + sizes[1]
                    self._main_splitter.setSizes([total - DOCK_MIN_HEIGHT, DOCK_MIN_HEIGHT])
                else:
                    target = self._expanded_height if self._expanded_height > DOCK_MIN_HEIGHT else DOCK_DEFAULT_HEIGHT
                    total = sizes[0] + sizes[1]
                    new_top = max(total - target, 200)
                    self._main_splitter.setSizes([new_top, total - new_top])

    def expand(self):
        if self._collapsed:
            self.toggle_collapse()

    def collapse(self):
        if not self._collapsed:
            self.toggle_collapse()
            
    def show_tab(self, name: str):
        tabs_map = {
            "terminal": 0,
            "problems": 1,
            "output": 2,
            "diagnostics": 3
        }
        idx = tabs_map.get(name.lower(), 0)
        if self._tabs.count() > idx:
            self._tabs.setCurrentIndex(idx)
            self.expand()
            
    def set_lsp_manager(self, lsp_manager):
        if hasattr(self, "_problems"):
            self._lsp_manager = lsp_manager
            self._lsp_manager.diagnostics_received.connect(self._problems.set_diagnostics)
