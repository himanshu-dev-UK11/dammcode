"""
Session Manager — v1.6

Saves and restores editor session state including:
- Open files list
- Cursor positions per file
- Window layout state
- Panel visibility states
- Active file
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from core.logger import setup_logger

logger = setup_logger(__name__)


class SessionManager:
    """
    Manages editor session state persistence.
    """
    def __init__(self, event_bus, session_file: Path = None):
        self.event_bus = event_bus
        self.session_file = session_file or Path.home() / ".mycodingmaster" / "session.json"
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        
    def save_session(self, session_data: dict) -> bool:
        """
        Save session state to file.
        
        Args:
            session_data: Dictionary containing session state
            
        Expected structure:
        {
            "workspace": str,  # Current workspace path
            "open_files": [str],  # List of open file paths
            "active_file": str,  # Currently active file path
            "cursor_positions": {  # Cursor position per file
                "file_path": {"line": int, "column": int}
            },
            "layout": {  # Window layout state
                "explorer_visible": bool,
                "ai_panel_visible": bool,
                "bottom_dock_visible": bool,
                "bottom_dock_height": int,
                "splitter_sizes": [int]
            },
            "panels": {  # Panel states
                "active_explorer_panel": str,  # "explorer", "search", "git", etc.
                "active_dock_tab": int  # 0=terminal, 1=problems, 2=output
            }
        }
        """
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            logger.info(f"Session saved to {self.session_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False
            
    def load_session(self) -> Optional[dict]:
        """
        Load session state from file.
        
        Returns:
            Dictionary containing session state, or None if file doesn't exist
        """
        if not self.session_file.exists():
            logger.debug("No session file found")
            return None
            
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            logger.info(f"Session loaded from {self.session_file}")
            return session_data
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None
            
    def clear_session(self) -> bool:
        """
        Clear/delete the session file.
        """
        try:
            if self.session_file.exists():
                self.session_file.unlink()
                logger.info("Session cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            return False
            
    def get_recent_workspaces(self, max_count: int = 10) -> List[str]:
        """
        Get list of recent workspaces from session history.
        
        Returns:
            List of workspace paths (most recent first)
        """
        history_file = self.session_file.parent / "workspace_history.json"
        
        if not history_file.exists():
            return []
            
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            workspaces = history.get("workspaces", [])
            return workspaces[:max_count]
        except Exception as e:
            logger.error(f"Failed to load workspace history: {e}")
            return []
            
    def add_recent_workspace(self, workspace_path: str):
        """
        Add workspace to recent history.
        """
        history_file = self.session_file.parent / "workspace_history.json"
        
        # Load existing history
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                history = {"workspaces": []}
        else:
            history = {"workspaces": []}
            
        workspaces = history.get("workspaces", [])
        
        # Remove if already exists (to move to front)
        if workspace_path in workspaces:
            workspaces.remove(workspace_path)
            
        # Add to front
        workspaces.insert(0, workspace_path)
        
        # Limit to 20 recent workspaces
        workspaces = workspaces[:20]
        
        history["workspaces"] = workspaces
        
        # Save
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
            logger.debug(f"Added workspace to history: {workspace_path}")
        except Exception as e:
            logger.error(f"Failed to save workspace history: {e}")
            
    def create_session_snapshot(
        self,
        workspace: Optional[str] = None,
        open_files: Optional[List[str]] = None,
        active_file: Optional[str] = None,
        cursor_positions: Optional[Dict[str, Dict[str, int]]] = None,
        layout: Optional[dict] = None,
        panels: Optional[dict] = None
    ) -> dict:
        """
        Create a session snapshot from provided data.
        
        Convenience method to build session_data dictionary.
        """
        return {
            "workspace": workspace or "",
            "open_files": open_files or [],
            "active_file": active_file or "",
            "cursor_positions": cursor_positions or {},
            "layout": layout or {
                "explorer_visible": True,
                "ai_panel_visible": True,
                "bottom_dock_visible": True,
                "bottom_dock_height": 180,
                "splitter_sizes": [240, 860, 320]
            },
            "panels": panels or {
                "active_explorer_panel": "explorer",
                "active_dock_tab": 0
            }
        }
