"""
Shell Manager — v1.9

Manages shell configuration and virtual environment detection.
"""
from PySide6.QtCore import QObject, QSettings
from pathlib import Path
import shutil
import os


class ShellConfig:
    """Configuration for a shell."""
    
    def __init__(self, name: str, command: str, icon: str = "", available: bool = False):
        self.name = name
        self.command = command
        self.icon = icon
        self.available = available


class ShellManager(QObject):
    """
    Manages shell configuration and detection.
    Tracks user's preferred shell and virtual environments.
    """
    
    def __init__(self, event_bus, working_dir: Path = None):
        super().__init__()
        self.event_bus = event_bus
        self.working_dir = working_dir or Path.cwd()
        self.settings = QSettings("MyCodingMaster", "Terminal")
        self.preferred_shell = self.settings.value("preferred_shell", "cmd")
        
        # Define available shells
        self.shells = {
            "cmd": ShellConfig("cmd", "cmd.exe", "💻"),
            "powershell": ShellConfig("powershell", "powershell.exe", "🔧"),
            "bash": ShellConfig("bash", "bash", "🐱"),
            "wsl": ShellConfig("wsl", "wsl.exe", "🐧"),
            "ubuntu": ShellConfig("ubuntu", "ubuntu.exe", "🟣")
        }
        
        # Detect available shells
        self._detect_available_shells()
    
    def _detect_available_shells(self):
        """Detect which shells are available on the system."""
        for name, config in self.shells.items():
            if shutil.which(config.command):
                config.available = True
    
    def get_shell(self, name: str) -> ShellConfig:
        """Get shell configuration by name."""
        return self.shells.get(name)
    
    def get_available_shells(self) -> list:
        """Get list of available shell names."""
        return [name for name, config in self.shells.items() if config.available]
    
    def get_preferred_shell(self) -> str:
        """Get user's preferred shell."""
        return self.preferred_shell
    
    def set_preferred_shell(self, shell: str):
        """Set user's preferred shell."""
        if shell in self.shells and self.shells[shell].available:
            self.preferred_shell = shell
            self.settings.setValue("preferred_shell", shell)
    
    def get_shell_command(self, shell: str, working_dir: Path) -> tuple:
        """
        Get command list and environment for a shell.
        Returns (command_list, environment_dict)
        """
        config = self.shells.get(shell, self.shells["cmd"])
        command = [config.command]
        
        # Setup environment
        env = os.environ.copy()
        env["PWD"] = str(working_dir)
        
        # If shell needs initialization, add flags
        if shell == "powershell":
            command.extend(["-NoExit"])
        elif shell == "bash":
            command.extend(["--login"])
        
        return command, env
    
    def detect_virtualenv(self, path: Path) -> tuple:
        """
        Detect virtual environment in a directory.
        Returns (env_type, env_path, activation_command)
        """
        # Check for .venv
        venv_paths = [path / ".venv", path / "venv"]
        for venv_path in venv_paths:
            if venv_path.exists():
                if (venv_path / "pyvenv.cfg").exists():
                    # Python venv
                    if self._is_windows():
                        activate_cmd = f"{venv_path}\\Scripts\\activate"
                    else:
                        activate_cmd = f"source {venv_path}/bin/activate"
                    return ("venv", str(venv_path), activate_cmd)
        
        # Check for conda
        conda_meta = path / ".conda"
        if conda_meta.exists() or (path / "conda-meta").exists():
            # Try to get environment name
            env_name = path.name
            return ("conda", str(path), f"conda activate {env_name}")
        
        # Check for poetry
        if (path / "poetry.lock").exists() or (path / "pyproject.toml").exists():
            return ("poetry", str(path), "poetry shell")
        
        # Check for pipenv
        if (path / "Pipfile.lock").exists():
            return ("pipenv", str(path), "pipenv shell")
        
        return (None, None, None)
    
    def _is_windows(self) -> bool:
        """Check if running on Windows."""
        import platform
        return platform.system() == "Windows"
    
    def activate_virtualenv(self, path: Path) -> str:
        """Get activation command for virtual environment."""
        env_type, env_path, activation_cmd = self.detect_virtualenv(path)
        return activation_cmd