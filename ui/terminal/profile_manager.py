"""
Terminal Profiles Manager — v2.0

Manages terminal profiles (shell configurations).
Supports:
- Multiple shell profiles (CMD, PowerShell, Git Bash, WSL, Ubuntu, MSYS2)
- Custom executable support
- Profile preferences persistence
- Virtual environment detection and activation
- Working directory profiles
"""
from PySide6.QtCore import QObject, Signal, QSettings
from pathlib import Path
import subprocess
import shutil
import os
from typing import Dict, List, Optional, Any
from core.logger import setup_logger

logger = setup_logger(__name__)


class TerminalProfile:
    """Represents a terminal shell profile configuration."""
    
    def __init__(self, name: str, command: str, args: List[str] = None,
                 icon: str = "terminal", working_dir: Path = None,
                 is_default: bool = False, enabled: bool = True):
        self.name = name
        self.command = command
        self.args = args or []
        self.icon = icon
        self.working_dir = working_dir
        self.is_default = is_default
        self.enabled = enabled
        self.last_used = None
        self.environment = {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "command": self.command,
            "args": self.args,
            "icon": self.icon,
            "working_dir": str(self.working_dir) if self.working_dir else None,
            "is_default": self.is_default,
            "enabled": self.enabled,
            "last_used": self.last_used,
            "environment": self.environment
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TerminalProfile":
        """Create from dictionary."""
        profile = cls(
            name=data["name"],
            command=data["command"],
            args=data.get("args", []),
            icon=data.get("icon", "terminal"),
            working_dir=Path(data["working_dir"]) if data.get("working_dir") else None,
            is_default=data.get("is_default", False),
            enabled=data.get("enabled", True)
        )
        profile.last_used = data.get("last_used")
        profile.environment = data.get("environment", {})
        return profile
    
    def get_command_line(self, working_dir: Path = None) -> List[str]:
        """Get the full command line for execution."""
        cmd = [self.command] + self.args
        if working_dir:
            # Add working directory argument if supported
            if "bash" in self.command.lower() or "wsl" in self.command.lower():
                cmd.extend(["-c", f"cd '{working_dir}' && exec bash -l"])
            elif "powershell" in self.command.lower():
                cmd.extend(["-NoExit", f"-Command", f"cd '{working_dir}'"])
        return cmd


class ProfileManager(QObject):
    """
    Manages terminal profiles and shell configurations.
    Reuses SettingsManager for persistence.
    """
    
    # Signals
    profile_changed = Signal(str)  # Profile name
    profile_added = Signal(str)  # Profile name
    profile_removed = Signal(str)  # Profile name
    profiles_updated = Signal()
    
    def __init__(self, event_bus, settings_manager=None):
        super().__init__()
        self.event_bus = event_bus
        self._settings_manager = settings_manager
        
        # Settings
        self._settings = QSettings("MyCodingMaster", "Terminal_Profiles")
        self._profiles_file = Path("config/terminal_profiles.json")
        
        # Profiles storage
        self._profiles: Dict[str, TerminalProfile] = {}
        self._active_profile: str = None
        self._available_shells: List[str] = []
        
        # Load profiles
        self._load_profiles()
        self._detect_available_shells()
    
    def _load_profiles(self):
        """Load profiles from settings or file."""
        # Load from QSettings first
        profile_names = self._settings.value("profiles", [], str)
        
        for name in profile_names:
            try:
                data = self._settings.value(f"profile_{name}", {})
                if isinstance(data, dict):
                    profile = TerminalProfile.from_dict(data)
                    self._profiles[name] = profile
            except Exception as e:
                logger.warning(f"Failed to load profile {name}: {e}")
        
        # If no profiles loaded, create defaults
        if not self._profiles:
            self._create_default_profiles()
        
        # Set active profile
        active_name = self._settings.value("active_profile", "cmd", str)
        if active_name in self._profiles:
            self._active_profile = active_name
        elif self._profiles:
            self._active_profile = list(self._profiles.keys())[0]
        
        logger.info(f"Loaded {len(self._profiles)} profiles, active: {self._active_profile}")
    
    def _create_default_profiles(self):
        """Create default profiles for common shells."""
        default_profiles = [
            TerminalProfile(
                name="cmd",
                command="cmd.exe",
                args=[],
                icon="terminal",
                is_default=True
            ),
            TerminalProfile(
                name="powershell",
                command="powershell.exe",
                args=["-NoExit"],
                icon="terminal",
                is_default=False
            ),
            TerminalProfile(
                name="git_bash",
                command="bash.exe",
                args=["--login"],
                icon="git",
                is_default=False
            ),
            TerminalProfile(
                name="wsl",
                command="wsl.exe",
                args=["--distribution", "Ubuntu"],
                icon="linux",
                is_default=False
            ),
            TerminalProfile(
                name="ubuntu",
                command="ubuntu.exe",
                args=[],
                icon="linux",
                is_default=False
            ),
            TerminalProfile(
                name="msys2",
                command="bash.exe",
                args=["--login", "-i"],
                icon="terminal",
                is_default=False
            )
        ]
        
        for profile in default_profiles:
            self._profiles[profile.name] = profile
    
    def _detect_available_shells(self):
        """Detect shells available on the system."""
        self._available_shells = []
        
        shell_checks = {
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "git_bash": "bash.exe",
            "wsl": "wsl.exe",
            "ubuntu": "ubuntu.exe",
            "msys2": "msys2.exe"
        }
        
        for name, command in shell_checks.items():
            if self._is_command_available(command):
                self._available_shells.append(name)
                if name in self._profiles:
                    self._profiles[name].enabled = True
        
        # Save detected shells
        self._settings.setValue("available_shells", self._available_shells)
        logger.info(f"Detected shells: {self._available_shells}")
    
    def _is_command_available(self, command: str) -> bool:
        """Check if a command is available in PATH."""
        try:
            result = subprocess.run(["where", command], 
                                   capture_output=True, text=True, shell=True)
            return result.returncode == 0
        except:
            # Fallback for non-Windows
            try:
                result = subprocess.run(["which", command],
                                       capture_output=True, text=True)
                return result.returncode == 0
            except:
                return False
    
    def get_profile(self, name: str) -> Optional[TerminalProfile]:
        """Get a profile by name."""
        return self._profiles.get(name)
    
    def get_active_profile(self) -> Optional[TerminalProfile]:
        """Get the currently active profile."""
        if self._active_profile and self._active_profile in self._profiles:
            return self._profiles[self._active_profile]
        return None
    
    def set_active_profile(self, name: str):
        """Set the active profile."""
        if name in self._profiles:
            self._active_profile = name
            self._settings.setValue("active_profile", name)
            self.profile_changed.emit(name)
            self.event_bus.publish("terminal_profile_changed", {
                "profile": name
            })
            logger.info(f"Active profile set to: {name}")
    
    def get_available_profiles(self) -> List[TerminalProfile]:
        """Get all available profiles."""
        return list(self._profiles.values())
    
    def get_enabled_profiles(self) -> List[TerminalProfile]:
        """Get all enabled profiles."""
        return [p for p in self._profiles.values() if p.enabled]
    
    def add_profile(self, name: str, command: str, args: List[str] = None,
                   icon: str = "terminal", working_dir: Path = None):
        """Add a new profile."""
        if name in self._profiles:
            logger.warning(f"Profile '{name}' already exists")
            return False
        
        profile = TerminalProfile(
            name=name,
            command=command,
            args=args or [],
            icon=icon,
            working_dir=working_dir
        )
        
        self._profiles[name] = profile
        self._save_profile(name)
        
        # Update settings
        profile_names = self._settings.value("profiles", [], str)
        if name not in profile_names:
            profile_names.append(name)
            self._settings.setValue("profiles", profile_names)
        
        self.profile_added.emit(name)
        self.profiles_updated.emit()
        logger.info(f"Added profile: {name}")
        return True
    
    def remove_profile(self, name: str):
        """Remove a profile."""
        if name not in self._profiles:
            logger.warning(f"Profile '{name}' not found")
            return False
        
        if self._active_profile == name:
            # Switch to another profile first
            other_profiles = [n for n in self._profiles.keys() if n != name]
            if other_profiles:
                self.set_active_profile(other_profiles[0])
            else:
                self._active_profile = None
        
        del self._profiles[name]
        self._settings.remove(f"profile_{name}")
        
        # Update settings
        profile_names = self._settings.value("profiles", [], str)
        if name in profile_names:
            profile_names.remove(name)
            self._settings.setValue("profiles", profile_names)
        
        self.profile_removed.emit(name)
        self.profiles_updated.emit()
        logger.info(f"Removed profile: {name}")
        return True
    
    def update_profile(self, name: str, **kwargs):
        """Update profile settings."""
        if name not in self._profiles:
            return False
        
        profile = self._profiles[name]
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        self._save_profile(name)
        self.profiles_updated.emit()
        return True
    
    def _save_profile(self, name: str):
        """Save a profile to settings."""
        if name in self._profiles:
            profile = self._profiles[name]
            self._settings.setValue(f"profile_{name}", profile.to_dict())
    
    def get_shell_command(self, profile_name: str = None,
                         working_dir: Path = None) -> List[str]:
        """Get the command line for a profile."""
        if profile_name is None:
            profile_name = self._active_profile
        
        profile = self.get_profile(profile_name)
        if not profile:
            # Fallback to default
            if "cmd" in self._profiles:
                profile = self._profiles["cmd"]
            else:
                return ["cmd.exe"]
        
        return profile.get_command_line(working_dir)
    
    def get_working_directory(self, profile_name: str = None) -> Path:
        """Get the working directory for a profile."""
        profile = self.get_profile(profile_name or self._active_profile)
        if profile and profile.working_dir:
            return profile.working_dir
        return Path.cwd()
    
    def set_working_directory(self, path: Path, profile_name: str = None):
        """Set the working directory for a profile."""
        if profile_name is None:
            profile_name = self._active_profile
        
        if profile_name in self._profiles:
            self._profiles[profile_name].working_dir = path
            self._save_profile(profile_name)
    
    def detect_virtual_environment(self, directory: Path) -> Optional[str]:
        """Detect virtual environment in a directory."""
        venv_paths = [
            directory / ".venv" / "Scripts" / "activate.bat",
            directory / ".venv" / "bin" / "activate",
            directory / "venv" / "Scripts" / "activate.bat",
            directory / "venv" / "bin" / "activate",
            directory / "conda" / "Scripts" / "activate.bat",
        ]
        
        for path in venv_paths:
            if path.exists():
                return str(path.parent)
        
        return None
    
    def activate_venv_command(self, venv_path: Path, shell: str = "cmd") -> str:
        """Generate the command to activate a virtual environment."""
        if shell == "cmd":
            return f'call "{venv_path / "Scripts" / "activate.bat"}"'
        elif shell == "powershell":
            return f'Source "{venv_path / "Scripts" / "Activate.ps1"}"'
        elif shell in ["bash", "wsl"]:
            return f'source "{venv_path / "bin" / "activate"}"'
        return ""
    
    def get_profiles_dict(self) -> Dict[str, dict]:
        """Get all profiles as dictionaries."""
        return {name: profile.to_dict() for name, profile in self._profiles.items()}
    
    def get_available_shell_list(self) -> List[str]:
        """Get list of available shell names."""
        return self._available_shells.copy()
    
    def is_shell_available(self, shell_name: str) -> bool:
        """Check if a shell is available on the system."""
        return shell_name in self._available_shells
