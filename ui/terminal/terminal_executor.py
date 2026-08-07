"""
Terminal Executor — v1.9

Executes commands via the integrated terminal.
Integrates with RunManager, WorkspaceManager, and Editor.
"""
from PySide6.QtCore import QObject, QProcess, QSettings
from pathlib import Path
import time
import json
from core.logger import setup_logger

logger = setup_logger(__name__)


class TerminalProcess:
    """Represents a process running in the terminal."""
    
    def __init__(self, process_id: str):
        self.process_id = process_id
        self.command = ""
        self.working_dir = Path.cwd()
        self.pid = 0
        self.start_time = None
        self.exit_code = None
        self.duration_ms = 0
        self.is_running = False
        self.status = "pending"  # pending, running, completed, failed
        self.output_lines = []
        self.error_lines = []


class TerminalExecutor(QObject):
    """
    Executes commands through the integrated terminal.
    Reuses RunManager and WorkspaceManager.
    """
    
    def __init__(self, event_bus, workspace_manager):
        super().__init__()
        self.event_bus = event_bus
        self.workspace_manager = workspace_manager
        self.settings = QSettings("MyCodingMaster", "Terminal")
        
        self.processes = {}  # process_id -> TerminalProcess
        self.current_process = None
        self._process_counter = 0
        
        # Subscribe to events
        self.event_bus.subscribe("run_current_file_requested", self._on_run_current_file)
        self.event_bus.subscribe("run_project_requested", self._on_run_project)
        self.event_bus.subscribe("build_project_requested", self._on_build_project)
        self.event_bus.subscribe("stop_process_requested", self._on_stop_process)
        self.event_bus.subscribe("restart_process_requested", self._on_restart_process)
        
        # Load previous command history
        self._load_command_history()
    
    def _generate_process_id(self) -> str:
        """Generate unique process ID."""
        self._process_counter += 1
        return f"proc-{time.time_ns()}-{self._process_counter}"
    
    def execute_command(self, command: str, working_dir: Path, shell: str = "cmd") -> str:
        """Execute a command in the terminal."""
        process_id = self._generate_process_id()
        
        process = TerminalProcess(process_id)
        process.command = command
        process.working_dir = working_dir
        process.is_running = True
        process.start_time = time.time()
        process.status = "running"
        
        self.processes[process_id] = process
        self.current_process = process
        
        # Publish event
        self.event_bus.publish("process_started", {
            "process_id": process_id,
            "command": command,
            "working_directory": str(working_dir),
            "shell": shell
        })
        
        return process_id
    
    def _on_run_current_file(self, data: dict):
        """Run the current file in the editor."""
        editor_tabs = data.get("editor_tabs")
        if not editor_tabs:
            self.event_bus.publish("log_message", {"message": "No editor tabs available"})
            return
        
        current_editor = editor_tabs.get_current_editor()
        if not current_editor or not current_editor.file_path:
            self.event_bus.publish("log_message", {"message": "No file is currently open"})
            return
        
        file_path = Path(current_editor.file_path)
        self.run_file(file_path)
    
    def _on_run_project(self, data: dict):
        """Run the current project."""
        workspace = self.workspace_manager.get_current_workspace()
        if workspace:
            self.run_project(Path(workspace.root_path))
        else:
            self.event_bus.publish("log_message", {"message": "No workspace loaded"})
    
    def _on_build_project(self, data: dict):
        """Build the current project."""
        workspace = self.workspace_manager.get_current_workspace()
        if workspace:
            self.build_project(Path(workspace.root_path))
        else:
            self.event_bus.publish("log_message", {"message": "No workspace loaded"})
    
    def _on_stop_process(self, data: dict):
        """Stop the currently running process."""
        if self.current_process and self.current_process.is_running:
            self.stop_process(self.current_process.process_id)
    
    def _on_restart_process(self, data: dict):
        """Restart the last executed command."""
        if self.current_process:
            self.execute_command(
                self.current_process.command,
                self.current_process.working_dir,
                "cmd"
            )
        else:
            self.event_bus.publish("log_message", {"message": "No previous command to restart"})
    
    def run_file(self, file_path: Path):
        """Run a single file using RunManager."""
        from core.run_manager import RunManager
        from PySide6.QtCore import QCoreApplication
        
        # Create RunManager
        run_manager = RunManager(self.event_bus)
        run_manager.workspace_root = file_path.parent
        
        # Run the file
        run_manager.run_file(file_path)
        
        # Store command for restart
        self.last_run_command = {
            "command": f"python {file_path}",
            "working_dir": file_path.parent
        }
    
    def run_project(self, project_root: Path):
        """Run a project using RunManager."""
        from core.run_manager import RunManager
        from PySide6.QtCore import QCoreApplication
        
        run_manager = RunManager(self.event_bus)
        run_manager.workspace_root = project_root
        run_manager.run_project(project_root)
        
        self.last_run_command = {
            "command": "Project run command",
            "working_dir": project_root
        }
    
    def build_project(self, project_root: Path):
        """Build a project using RunManager."""
        from core.run_manager import RunManager
        from PySide6.QtCore import QCoreApplication
        
        run_manager = RunManager(self.event_bus)
        run_manager.workspace_root = project_root
        
        # Detect build system and run appropriate command
        build_cmd = self._detect_build_command(project_root)
        if build_cmd:
            self.execute_command(build_cmd, project_root)
        else:
            self.event_bus.publish("log_message", {
                "message": "Unable to detect build system. Supported: Cargo, Gradle, Maven, CMake, NPM, Yarn, PNPM, Flutter"
            })
    
    def _detect_build_command(self, project_root: Path) -> str:
        """Detect build system and return appropriate command."""
        # Flutter
        if (project_root / "pubspec.yaml").exists():
            return "flutter build"
        
        # Rust (Cargo)
        if (project_root / "Cargo.toml").exists():
            return "cargo build"
        
        # Gradle
        if (project_root / "build.gradle").exists() or (project_root / "build.gradle.kts").exists():
            return "gradle build"
        
        # Maven
        if (project_root / "pom.xml").exists():
            return "mvn package"
        
        # CMake
        if (project_root / "CMakeLists.txt").exists():
            return "cmake --build ."
        
        # NPM
        if (project_root / "package.json").exists():
            return "npm run build"
        
        # Yarn
        if (project_root / "yarn.lock").exists():
            return "yarn build"
        
        # PNPM
        if (project_root / "pnpm-lock.yaml").exists():
            return "pnpm build"
        
        return ""
    
    def stop_process(self, process_id: str):
        """Stop a running process."""
        if process_id not in self.processes:
            return
        
        process = self.processes[process_id]
        process.is_running = False
        process.status = "cancelled"
        process.duration_ms = int((time.time() - process.start_time) * 1000)
        
        self.event_bus.publish("process_finished", {
            "process_id": process_id,
            "exit_code": -1,
            "status": "cancelled"
        })
        
        if self.current_process and self.current_process.process_id == process_id:
            self.current_process = None
    
    def restart_process(self):
        """Restart the last executed command."""
        if hasattr(self, 'last_run_command') and self.last_run_command:
            self.execute_command(
                self.last_run_command["command"],
                self.last_run_command["working_dir"],
                "cmd"
            )
        else:
            self.event_bus.publish("log_message", {"message": "No previous command to restart"})
    
    def _save_command_history(self):
        """Save command history to settings."""
        history = []
        if hasattr(self, 'last_run_command') and self.last_run_command:
            history.append(self.last_run_command)
        
        self.settings.setValue("terminal/command_history", json.dumps(history))
    
    def _load_command_history(self):
        """Load command history from settings."""
        history_json = self.settings.value("terminal/command_history", "[]")
        try:
            history = json.loads(history_json)
            if history:
                self.last_run_command = history[-1]
        except:
            pass