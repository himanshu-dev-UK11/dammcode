"""
Terminal Manager — v1.9

Manages multiple terminal tabs, sessions, and process lifecycle.
Extends existing TerminalWidget instead of replacing it.
"""
from PySide6.QtCore import QObject, Signal, QSettings
from pathlib import Path
import uuid


class TerminalSession:
    """Represents a single terminal session with its own state."""
    
    def __init__(self, session_id: str, working_dir: Path, shell: str = "cmd"):
        self.session_id = session_id
        self.working_dir = working_dir
        self.shell = shell
        self.title = f"Term {session_id[:8]}"
        self.is_running = False
        self.exit_code = None
        self.pid = None
        self.created_at = None
        self.last_active = None


class TerminalManager(QObject):
    """
    Manages terminal sessions, tabs, and process lifecycle.
    Reuses existing TerminalWidget - does NOT create new system.
    """
    # Signals
    session_created = Signal(str)  # session_id
    session_closed = Signal(str)   # session_id
    session_activated = Signal(str) # session_id
    output_received = Signal(str, str)  # session_id, output
    process_started = Signal(str, str, int)  # session_id, command, pid
    process_finished = Signal(str, int, int)  # session_id, exit_code, duration_ms
    directory_changed = Signal(str, str)  # session_id, new_directory
    
    def __init__(self, event_bus, working_dir: Path = None):
        super().__init__()
        self.event_bus = event_bus
        self.working_dir = working_dir or Path.cwd()
        self.sessions = {}  # session_id -> TerminalSession
        self.closed_sessions = []  # Store last 10 closed for reopen
        self.active_session_id = None
        self.session_counter = 0
        self.settings = QSettings("MyCodingMaster", "Terminal")
        
    def create_session(self, working_dir: Path = None, shell: str = "cmd") -> str:
        """Create a new terminal session and return its ID."""
        self.session_counter += 1
        session_id = f"term-{uuid.uuid4().hex[:8]}"
        
        session = TerminalSession(
            session_id=session_id,
            working_dir=working_dir or self.working_dir,
            shell=shell
        )
        
        self.sessions[session_id] = session
        self.active_session_id = session_id
        
        self.event_bus.publish("terminal_created", {
            "session_id": session_id,
            "shell": shell,
            "working_directory": str(session.working_dir)
        })
        
        self.session_created.emit(session_id)
        return session_id
    
    def close_session(self, session_id: str):
        """Close a terminal session."""
        if session_id not in self.sessions:
            return
            
        session = self.sessions.pop(session_id)
        session.is_running = False
        
        # Store in closed sessions (max 10)
        self.closed_sessions.append(session)
        if len(self.closed_sessions) > 10:
            self.closed_sessions.pop(0)
        
        # Activate another session if this was active
        if self.active_session_id == session_id:
            remaining = list(self.sessions.keys())
            if remaining:
                self.active_session_id = remaining[0]
                self.session_activated.emit(self.active_session_id)
            else:
                self.active_session_id = None
        
        self.event_bus.publish("terminal_closed", {
            "session_id": session_id,
            "exit_code": session.exit_code
        })
        
        self.session_closed.emit(session_id)
    
    def reopen_session(self, index: int = -1) -> str:
        """Reopen the most recently closed session."""
        if not self.closed_sessions:
            return None
            
        session = self.closed_sessions.pop(index)
        session_id = f"term-{uuid.uuid4().hex[:8]}"
        
        new_session = TerminalSession(
            session_id=session_id,
            working_dir=session.working_dir,
            shell=session.shell
        )
        new_session.title = session.title
        
        self.sessions[session_id] = new_session
        self.active_session_id = session_id
        
        self.session_created.emit(session_id)
        return session_id
    
    def activate_session(self, session_id: str):
        """Activate a terminal session."""
        if session_id in self.sessions:
            self.active_session_id = session_id
            self.session_activated.emit(session_id)
    
    def get_session(self, session_id: str) -> TerminalSession:
        """Get a terminal session by ID."""
        return self.sessions.get(session_id)
    
    def get_active_session(self) -> TerminalSession:
        """Get the currently active session."""
        if self.active_session_id and self.active_session_id in self.sessions:
            return self.sessions[self.active_session_id]
        return None
    
    def get_all_sessions(self) -> list:
        """Get all active sessions."""
        return list(self.sessions.values())
    
    def set_session_title(self, session_id: str, title: str):
        """Set custom title for a terminal session."""
        if session_id in self.sessions:
            self.sessions[session_id].title = title
    
    def set_session_directory(self, session_id: str, directory: Path):
        """Set working directory for a session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.working_dir = directory
            self.directory_changed.emit(session_id, str(directory))
    
    def update_process_info(self, session_id: str, pid: int, command: str, is_running: bool = True):
        """Update process information for a session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.pid = pid
            session.is_running = is_running
            if is_running:
                self.process_started.emit(session_id, command, pid)
    
    def finish_process(self, session_id: str, exit_code: int):
        """Mark process as finished."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.is_running = False
            session.exit_code = exit_code
            self.process_finished.emit(session_id, exit_code, 0)
    
    def get_shell_list(self) -> list:
        """Get list of available shells."""
        return ["cmd", "powershell", "bash", "wsl", "ubuntu"]
    
    def detect_available_shells(self) -> list:
        """Detect shells available on the system."""
        import shutil
        
        available = []
        shell_commands = {
            "cmd": "cmd.exe",
            "powershell": "powershell",
            "bash": "bash",
            "wsl": "wsl",
            "ubuntu": "ubuntu"
        }
        
        for name, command in shell_commands.items():
            if shutil.which(command):
                available.append(name)
        
        return available