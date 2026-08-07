"""
Terminal History Storage — v1.0

Persistent storage for AI terminal command execution history.
Stores command, timing, workspace, exit code, and output preview.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json

from core.logger import setup_logger


logger = setup_logger(__name__)


@dataclass
class AICommandHistoryEntry:
    """Represents a single AI terminal command execution."""
    request_id: str
    command: str
    timestamp: datetime
    workspace: str
    exit_code: int
    duration_ms: int
    status: str  # pending, approved, cancelled, running, completed, failed
    output_preview: str = ""
    error_preview: str = ""
    reason: str = ""
    impact: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "request_id": self.request_id,
            "command": self.command,
            "timestamp": self.timestamp.isoformat(),
            "workspace": self.workspace,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "output_preview": self.output_preview,
            "error_preview": self.error_preview,
            "reason": self.reason,
            "impact": self.impact
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AICommandHistoryEntry":
        """Create from dictionary."""
        return cls(
            request_id=data.get("request_id", ""),
            command=data.get("command", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp", "")),
            workspace=data.get("workspace", ""),
            exit_code=data.get("exit_code", 0),
            duration_ms=data.get("duration_ms", 0),
            status=data.get("status", ""),
            output_preview=data.get("output_preview", ""),
            error_preview=data.get("error_preview", ""),
            reason=data.get("reason", ""),
            impact=data.get("impact", "")
        )


class TerminalHistoryStorage:
    """
    Manages AI terminal command history with persistent storage.
    
    Features:
    - Unlimited history (capped for memory safety)
    - Search by command, workspace, status
    - Filter by date range
    - Export to CSV/JSON
    - Stats and analytics
    """
    
    def __init__(self, storage_file: Path = None):
        self.storage_file = storage_file or Path("config/ai_terminal_history.json")
        self._entries: List[AICommandHistoryEntry] = []
        self._max_entries = 10000
        self._load_history()
    
    def _load_history(self):
        """Load history from storage file."""
        if not self.storage_file.exists():
            self._entries = []
            return
        
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            entries = []
            for item in data.get("history", []):
                try:
                    entry = AICommandHistoryEntry.from_dict(item)
                    entries.append(entry)
                except Exception as e:
                    logger.warning(f"Failed to load history entry: {e}")
            
            self._entries = entries[-self._max_entries:]
            logger.info(f"Loaded {len(self._entries)} history entries")
            
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            self._entries = []
    
    def _save_history(self):
        """Save history to storage file."""
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "history": [e.to_dict() for e in self._entries]
            }
            
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def add_entry(self, entry: AICommandHistoryEntry):
        """Add a history entry."""
        self._entries.append(entry)
        
        # Enforce max size
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        
        self._save_history()
    
    def get_entry(self, request_id: str) -> Optional[AICommandHistoryEntry]:
        """Get entry by request ID."""
        for entry in self._entries:
            if entry.request_id == request_id:
                return entry
        return None
    
    def get_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        workspace: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[AICommandHistoryEntry]:
        """Get filtered history entries."""
        result = self._entries[offset:]
        
        # Filter by status
        if status:
            result = [e for e in result if e.status == status]
        
        # Filter by workspace
        if workspace:
            result = [e for e in result if workspace in e.workspace]
        
        # Search in command
        if search:
            search_lower = search.lower()
            result = [e for e in result if search_lower in e.command.lower()]
        
        # Limit results
        if limit:
            result = result[:limit]
        
        return result
    
    def get_recent_commands(self, count: int = 10) -> List[AICommandHistoryEntry]:
        """Get most recent commands."""
        return self._entries[-count:] if self._entries else []
    
    def get_completed_commands(self, count: int = 10) -> List[AICommandHistoryEntry]:
        """Get recently completed commands."""
        completed = [e for e in self._entries if e.status == "completed"]
        return completed[-count:] if completed else []
    
    def get_failed_commands(self, count: int = 10) -> List[AICommandHistoryEntry]:
        """Get recently failed commands."""
        failed = [e for e in self._entries if e.status == "failed"]
        return failed[-count:] if failed else []
    
    def get_stats(self) -> Dict:
        """Get history statistics."""
        total = len(self._entries)
        completed = len([e for e in self._entries if e.status == "completed"])
        failed = len([e for e in self._entries if e.status == "failed"])
        cancelled = len([e for e in self._entries if e.status == "cancelled"])
        
        total_duration = sum(e.duration_ms for e in self._entries if e.duration_ms > 0)
        avg_duration = total_duration / completed if completed > 0 else 0
        
        return {
            "total_commands": total,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "success_rate": (completed / total * 100) if total > 0 else 0,
            "total_duration_ms": total_duration,
            "average_duration_ms": avg_duration
        }
    
    def clear_history(self):
        """Clear all history."""
        self._entries = []
        self._save_history()
        logger.info("AI terminal history cleared")
    
    def export_to_json(self, filepath: Path = None) -> Path:
        """Export history to JSON file."""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = Path(f"ai_terminal_history_{timestamp}.json")
        
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "exported_at": datetime.now().isoformat(),
                "stats": self.get_stats(),
                "history": [e.to_dict() for e in self._entries]
            }
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export history: {e}")
            raise
    
    def export_to_csv(self, filepath: Path = None) -> Path:
        """Export history to CSV file."""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = Path(f"ai_terminal_history_{timestamp}.csv")
        
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            lines = []
            lines.append("request_id,timestamp,command,workspace,exit_code,duration_ms,status")
            
            for entry in self._entries:
                # Escape quotes and newlines in command
                command = entry.command.replace('"', '""')
                workspace = entry.workspace.replace('"', '""')
                lines.append(
                    f'"{entry.request_id}",'
                    f'"{entry.timestamp.isoformat()}",'
                    f'"{command}",'
                    f'"{workspace}",'
                    f'{entry.exit_code},'
                    f'{entry.duration_ms},'
                    f'{entry.status}'
                )
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export history to CSV: {e}")
            raise
