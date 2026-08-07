"""
Terminal Session Manager — v2.1

Session restoration and persistence for terminal tabs.
Supports:
- Restore terminal tabs, working directories, shell, split layouts, titles
- Store sessions in JSON format
- Asynchronous restore to prevent UI blocking
"""
from PySide6.QtCore import QObject, Signal, QSettings
from pathlib import Path
import json
import time
from typing import Dict, List, Optional, Any
from core.logger import setup_logger

logger = setup_logger(__name__)


class SessionData:
    """Represents a single terminal session for persistence."""
    
    def __init__(self, session_id: str, title: str, working_dir: str,
                 shell: str, split_info: Dict[str, Any] = None):
        self.session_id = session_id
        self.title = title
        self.working_dir = working_dir
        self.shell = shell
        self.split_info = split_info or {}
        self.created_at = time.time()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "working_dir": self.working_dir,
            "shell": self.shell,
            "split_info": self.split_info,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SessionData":
        """Create from dictionary."""
        session = cls(
            session_id=data["session_id"],
            title=data["title"],
            working_dir=data["working_dir"],
            shell=data["shell"],
            split_info=data.get("split_info", {})
        )
        session.created_at = data.get("created_at", time.time())
        return session


class SessionManager(QObject):
    """
    Manages terminal session persistence and restoration.
    Does NOT restore running processes.
    """
    
    # Signals
    session_restored = Signal(str)  # session_id
    session_saved = Signal(str)  # session_id
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._settings = QSettings("MyCodingMaster", "Terminal_Sessions")
        self._sessions_file = Path("config/terminal_sessions.json")
        self._sessions: Dict[str, SessionData] = {}
        self._pending_restores: List[Dict] = []
    
    def save_session(self, session_id: str, title: str, working_dir: str,
                    shell: str, split_info: Dict[str, Any] = None):
        """Save a terminal session."""
        session = SessionData(
            session_id=session_id,
            title=title,
            working_dir=str(working_dir),
            shell=shell,
            split_info=split_info
        )
        self._sessions[session_id] = session
        
        # Save to disk
        self._save_to_disk()
        self.session_saved.emit(session_id)
        self.event_bus.publish("terminal_session_saved", {
            "session_id": session_id,
            "title": title
        })
    
    def save_all_sessions(self, sessions_data: List[Dict]):
        """Save all terminal sessions at once."""
        for data in sessions_data:
            session = SessionData(
                session_id=data["session_id"],
                title=data["title"],
                working_dir=data["working_dir"],
                shell=data["shell"],
                split_info=data.get("split_info", {})
            )
            self._sessions[session.session_id] = session
        
        self._save_to_disk()
        self.event_bus.publish("terminal_sessions_saved", {
            "count": len(sessions_data)
        })
    
    def load_sessions(self) -> List[SessionData]:
        """Load saved sessions from disk."""
        if not self._sessions_file.exists():
            return []
        
        try:
            with open(self._sessions_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            sessions = []
            for item in data.get("sessions", []):
                try:
                    session = SessionData.from_dict(item)
                    sessions.append(session)
                except Exception as e:
                    logger.warning(f"Failed to load session: {e}")
            
            logger.info(f"Loaded {len(sessions)} saved sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            return []
    
    def restore_sessions(self) -> List[Dict]:
        """Restore sessions asynchronously. Returns session data for UI to create."""
        sessions = self.load_sessions()
        
        # Clear saved file after loading (so we don't restore old sessions)
        self._sessions_file.unlink(missing_ok=True)
        
        # Emit events for each session to be restored
        result = []
        for session in sessions:
            result.append({
                "session_id": session.session_id,
                "title": session.title,
                "working_dir": session.working_dir,
                "shell": session.shell,
                "split_info": session.split_info
            })
            self.session_restored.emit(session.session_id)
            self.event_bus.publish("terminal_session_restored", {
                "session_id": session.session_id,
                "title": session.title,
                "shell": session.shell,
                "working_directory": session.working_dir
            })
        
        return result
    
    def _save_to_disk(self):
        """Save sessions to disk."""
        try:
            data = {
                "version": "2.1",
                "generated_at": time.time(),
                "sessions": [s.to_dict() for s in self._sessions.values()]
            }
            
            self._sessions_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._sessions_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    def clear_sessions(self):
        """Clear all saved sessions."""
        self._sessions = {}
        if self._sessions_file.exists():
            self._sessions_file.unlink()
        self.event_bus.publish("terminal_sessions_cleared", {})
    
    def get_session_count(self) -> int:
        """Get number of saved sessions."""
        return len(self._sessions)
