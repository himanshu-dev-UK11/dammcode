"""
Run Manager — v1.6

Intelligent project execution system.
Automatically detects project type and executes with appropriate command.

Supported Languages/Frameworks:
- Python (standard scripts, Django, FastAPI, Flask)
- Node.js/JavaScript (standard scripts, React, Vite, Next.js)
- TypeScript (ts-node, tsx)
- Flutter/Dart
- Rust (Cargo)
- Go
- C/C++ (compile then execute)
- Java (compile then execute)
- C# (.NET)
- PHP
- Ruby
- Shell scripts
"""
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from PySide6.QtCore import QObject, QProcess, Signal
from core.logger import setup_logger

logger = setup_logger(__name__)


class RunConfiguration:
    """Represents a run configuration for a file or project."""
    def __init__(self, name: str, command: List[str], working_dir: Path, env: Optional[Dict[str, str]] = None):
        self.name = name
        self.command = command
        self.working_dir = working_dir
        self.env = env or {}


class RunManager(QObject):
    """
    Manages project and file execution.
    Auto-detects run commands based on file type and project structure.
    """
    output_received = Signal(str)  # output text
    error_received = Signal(str)   # error text
    process_started = Signal(str)  # command
    process_finished = Signal(int) # exit code
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self.current_process: Optional[QProcess] = None
        self.workspace_root: Optional[Path] = None
        
        # Subscribe to events
        self.event_bus.subscribe("workspace_loaded", self._on_workspace_loaded)
        self.event_bus.subscribe("run_requested", self._on_run_requested)
        self.event_bus.subscribe("stop_requested", self._on_stop_requested)
        
    def _on_workspace_loaded(self, data):
        """Update workspace root when workspace is loaded."""
        context = data.get("context")
        if context:
            self.workspace_root = Path(context.root_path)
            
    def _on_run_requested(self, data):
        """Handle run request from UI."""
        file_path = data.get("file_path")
        if file_path:
            self.run_file(Path(file_path))
        elif self.workspace_root:
            self.run_project(self.workspace_root)
            
    def _on_stop_requested(self, data):
        """Stop currently running process."""
        self.stop_process()
        
    def run_file(self, file_path: Path):
        """Run a single file."""
        if not file_path.exists():
            self.event_bus.publish("log_message", {"message": f"File not found: {file_path}"})
            return
            
        config = self.detect_file_run_config(file_path)
        if config:
            self.execute(config)
        else:
            self.event_bus.publish("log_message", {
                "message": f"Unable to determine how to run: {file_path.name}"
            })
            
    def run_project(self, project_root: Path):
        """Run entire project."""
        config = self.detect_project_run_config(project_root)
        if config:
            self.execute(config)
        else:
            self.event_bus.publish("log_message", {
                "message": "Unable to determine how to run project. Please configure a custom run command."
            })
            
    def detect_file_run_config(self, file_path: Path) -> Optional[RunConfiguration]:
        """Detect how to run a single file based on its extension."""
        ext = file_path.suffix.lower()
        name = file_path.stem
        parent = file_path.parent
        
        # Python
        if ext == ".py":
            return RunConfiguration(
                name=f"Python: {file_path.name}",
                command=["python", str(file_path)],
                working_dir=parent
            )
            
        # JavaScript/Node.js
        if ext in [".js", ".mjs"]:
            return RunConfiguration(
                name=f"Node: {file_path.name}",
                command=["node", str(file_path)],
                working_dir=parent
            )
            
        # TypeScript
        if ext == ".ts":
            # Try tsx first (faster), fallback to ts-node
            return RunConfiguration(
                name=f"TypeScript: {file_path.name}",
                command=["tsx", str(file_path)],  # Falls back to ts-node if tsx not found
                working_dir=parent
            )
            
        # Dart
        if ext == ".dart":
            return RunConfiguration(
                name=f"Dart: {file_path.name}",
                command=["dart", "run", str(file_path)],
                working_dir=parent
            )
            
        # Rust (single file)
        if ext == ".rs":
            return RunConfiguration(
                name=f"Rust: {file_path.name}",
                command=["rustc", str(file_path), "&&", f"./{name}"],
                working_dir=parent
            )
            
        # Go
        if ext == ".go":
            return RunConfiguration(
                name=f"Go: {file_path.name}",
                command=["go", "run", str(file_path)],
                working_dir=parent
            )
            
        # C
        if ext == ".c":
            return RunConfiguration(
                name=f"C: {file_path.name}",
                command=["gcc", str(file_path), "-o", name, "&&", f"./{name}"],
                working_dir=parent
            )
            
        # C++
        if ext in [".cpp", ".cc", ".cxx"]:
            return RunConfiguration(
                name=f"C++: {file_path.name}",
                command=["g++", str(file_path), "-o", name, "&&", f"./{name}"],
                working_dir=parent
            )
            
        # Java
        if ext == ".java":
            return RunConfiguration(
                name=f"Java: {file_path.name}",
                command=["javac", str(file_path), "&&", "java", name],
                working_dir=parent
            )
            
        # C#
        if ext == ".cs":
            return RunConfiguration(
                name=f"C#: {file_path.name}",
                command=["dotnet", "run"],
                working_dir=parent
            )
            
        # PHP
        if ext == ".php":
            return RunConfiguration(
                name=f"PHP: {file_path.name}",
                command=["php", str(file_path)],
                working_dir=parent
            )
            
        # Ruby
        if ext == ".rb":
            return RunConfiguration(
                name=f"Ruby: {file_path.name}",
                command=["ruby", str(file_path)],
                working_dir=parent
            )
            
        # Shell scripts
        if ext in [".sh", ".bash"]:
            return RunConfiguration(
                name=f"Bash: {file_path.name}",
                command=["bash", str(file_path)],
                working_dir=parent
            )
            
        # PowerShell
        if ext == ".ps1":
            return RunConfiguration(
                name=f"PowerShell: {file_path.name}",
                command=["powershell", "-ExecutionPolicy", "Bypass", "-File", str(file_path)],
                working_dir=parent
            )
            
        # Batch
        if ext in [".bat", ".cmd"]:
            return RunConfiguration(
                name=f"Batch: {file_path.name}",
                command=[str(file_path)],
                working_dir=parent
            )
            
        return None
        
    def detect_project_run_config(self, project_root: Path) -> Optional[RunConfiguration]:
        """Detect how to run a project based on its structure and configuration files."""
        
        # Flutter
        if (project_root / "pubspec.yaml").exists():
            with open(project_root / "pubspec.yaml", "r") as f:
                content = f.read()
                if "flutter:" in content:
                    return RunConfiguration(
                        name="Flutter Run",
                        command=["flutter", "run"],
                        working_dir=project_root
                    )
                else:
                    # Pure Dart project
                    return RunConfiguration(
                        name="Dart Run",
                        command=["dart", "run"],
                        working_dir=project_root
                    )
                    
        # Django
        if (project_root / "manage.py").exists():
            return RunConfiguration(
                name="Django Development Server",
                command=["python", "manage.py", "runserver"],
                working_dir=project_root
            )
            
        # FastAPI (check for main.py with FastAPI import)
        main_py = project_root / "main.py"
        if main_py.exists():
            try:
                with open(main_py, "r") as f:
                    content = f.read()
                    if "from fastapi" in content or "import fastapi" in content:
                        return RunConfiguration(
                            name="FastAPI Server",
                            command=["uvicorn", "main:app", "--reload"],
                            working_dir=project_root
                        )
            except Exception:
                pass
                
        # Node.js projects
        package_json = project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r") as f:
                    pkg = json.load(f)
                    scripts = pkg.get("scripts", {})
                    
                    # Check for common scripts
                    if "dev" in scripts:
                        return RunConfiguration(
                            name="npm run dev",
                            command=["npm", "run", "dev"],
                            working_dir=project_root
                        )
                    elif "start" in scripts:
                        return RunConfiguration(
                            name="npm start",
                            command=["npm", "start"],
                            working_dir=project_root
                        )
            except Exception:
                pass
                
        # Rust (Cargo)
        if (project_root / "Cargo.toml").exists():
            return RunConfiguration(
                name="Cargo Run",
                command=["cargo", "run"],
                working_dir=project_root
            )
            
        # Go
        if (project_root / "go.mod").exists():
            return RunConfiguration(
                name="Go Run",
                command=["go", "run", "."],
                working_dir=project_root
            )
            
        # .NET
        csproj_files = list(project_root.glob("*.csproj"))
        if csproj_files:
            return RunConfiguration(
                name=".NET Run",
                command=["dotnet", "run"],
                working_dir=project_root
            )
            
        # Maven
        if (project_root / "pom.xml").exists():
            return RunConfiguration(
                name="Maven Run",
                command=["mvn", "spring-boot:run"],  # Assuming Spring Boot
                working_dir=project_root
            )
            
        # Gradle
        if (project_root / "build.gradle").exists() or (project_root / "build.gradle.kts").exists():
            return RunConfiguration(
                name="Gradle Run",
                command=["gradle", "run"],
                working_dir=project_root
            )
            
        # Python script (check for main.py or app.py)
        for entry_point in ["main.py", "app.py", "run.py"]:
            if (project_root / entry_point).exists():
                return RunConfiguration(
                    name=f"Python: {entry_point}",
                    command=["python", entry_point],
                    working_dir=project_root
                )
                
        return None
        
    def execute(self, config: RunConfiguration):
        """Execute a run configuration."""
        if self.current_process and self.current_process.state() != QProcess.NotRunning:
            self.event_bus.publish("log_message", {
                "message": "A process is already running. Stop it first."
            })
            return
        
        # Clean up previous process if exists
        if self.current_process:
            self.current_process.deleteLater()
            self.current_process = None
            
        self.current_process = QProcess()
        self.current_process.setWorkingDirectory(str(config.working_dir))
        
        # Set environment
        if config.env:
            env = self.current_process.processEnvironment()
            for key, value in config.env.items():
                env.insert(key, value)
            self.current_process.setProcessEnvironment(env)
            
        # Connect signals
        self.current_process.readyReadStandardOutput.connect(self._on_output)
        self.current_process.readyReadStandardError.connect(self._on_error)
        self.current_process.finished.connect(self._on_finished)
        self.current_process.finished.connect(lambda: self._cleanup_process())
        
        # Start process
        program = config.command[0]
        args = config.command[1:]
        
        logger.info(f"Executing: {' '.join(config.command)} in {config.working_dir}")
        self.event_bus.publish("log_message", {
            "message": f"▶ {config.name}: {' '.join(config.command)}"
        })
        
        self.current_process.start(program, args)
        self.process_started.emit(' '.join(config.command))
    
    def _cleanup_process(self):
        """Clean up finished process."""
        if self.current_process:
            # Schedule for deletion after event loop
            proc = self.current_process
            self.current_process = None
            proc.deleteLater()
        
    def stop_process(self):
        """Stop currently running process."""
        if self.current_process and self.current_process.state() != QProcess.NotRunning:
            logger.info("Terminating process...")
            self.current_process.terminate()
            
            # If it doesn't terminate gracefully, kill it
            if not self.current_process.waitForFinished(3000):
                logger.warning("Process did not terminate, killing...")
                self.current_process.kill()
                
            self.event_bus.publish("log_message", {"message": "⏹ Process stopped"})
            
    def _on_output(self):
        """Handle stdout from process."""
        if self.current_process:
            data = self.current_process.readAllStandardOutput().data().decode('utf-8', errors='replace')
            self.output_received.emit(data)
            self.event_bus.publish("process_output", {"output": data, "stream": "stdout"})
            
    def _on_error(self):
        """Handle stderr from process."""
        if self.current_process:
            data = self.current_process.readAllStandardError().data().decode('utf-8', errors='replace')
            self.error_received.emit(data)
            self.event_bus.publish("process_output", {"output": data, "stream": "stderr"})
            
    def _on_finished(self, exit_code, exit_status):
        """Handle process completion."""
        self.process_finished.emit(exit_code)
        
        if exit_code == 0:
            msg = f"✓ Process finished successfully (exit code {exit_code})"
        else:
            msg = f"✗ Process finished with error (exit code {exit_code})"
            
        self.event_bus.publish("log_message", {"message": msg})
        self.event_bus.publish("process_finished", {"exit_code": exit_code})
