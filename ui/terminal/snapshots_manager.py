"""
Terminal Snapshots Manager — v2.1

Allows users to save, restore, and export terminal output snapshots.
Snapshots include: output, command, execution time, exit code.
"""
from PySide6.QtCore import QObject, Signal, QSettings
from pathlib import Path
import json
import time
from typing import Dict, List, Optional, Any
from core.logger import setup_logger

logger = setup_logger(__name__)


class TerminalSnapshot:
    """Represents a terminal output snapshot."""
    
    def __init__(self, session_id: str, output: str, command: str,
                 execution_time_ms: int = 0, exit_code: int = 0,
                 timestamp: float = None):
        self.session_id = session_id
        self.output = output
        self.command = command
        self.execution_time_ms = execution_time_ms
        self.exit_code = exit_code
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "output": self.output,
            "command": self.command,
            "execution_time_ms": self.execution_time_ms,
            "exit_code": self.exit_code,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TerminalSnapshot":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            output=data["output"],
            command=data["command"],
            execution_time_ms=data.get("execution_time_ms", 0),
            exit_code=data.get("exit_code", 0),
            timestamp=data.get("timestamp", time.time())
        )


class SnapshotsManager(QObject):
    """
    Manages terminal output snapshots.
    Supports:
    - Save terminal output snapshot
    - Restore snapshot
    - Export snapshot
    - Snapshot metadata (output, command, execution time, exit code)
    """
    
    # Signals
    snapshot_saved = Signal(str)  # session_id
    snapshot_loaded = Signal(str)  # session_id
    snapshot_exported = Signal(str)  # filepath
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._settings = QSettings("MyCodingMaster", "Terminal_Snapshots")
        self._snapshots_file = Path("config/terminal_snapshots.json")
        self._snapshots: Dict[str, TerminalSnapshot] = {}
        self._max_snapshots = 100  # Limit to prevent memory issues
    
    def save_snapshot(self, session_id: str, output: str, command: str,
                     execution_time_ms: int = 0, exit_code: int = 0) -> str:
        """Save a terminal output snapshot."""
        snapshot = TerminalSnapshot(
            session_id=session_id,
            output=output,
            command=command,
            execution_time_ms=execution_time_ms,
            exit_code=exit_code
        )
        
        snapshot_id = f"snapshot-{time.time_ns()}"
        self._snapshots[snapshot_id] = snapshot
        
        # Enforce max snapshots
        if len(self._snapshots) > self._max_snapshots:
            # Remove oldest
            oldest_id = min(self._snapshots.keys(), key=lambda k: self._snapshots[k].timestamp)
            del self._snapshots[oldest_id]
        
        self._save_to_disk()
        self.snapshot_saved.emit(snapshot_id)
        self.event_bus.publish("terminal_snapshot_saved", {
            "snapshot_id": snapshot_id,
            "session_id": session_id,
            "output_lines": len(output.split('\n')),
            "execution_time_ms": execution_time_ms,
            "exit_code": exit_code
        })
        
        return snapshot_id
    
    def load_snapshot(self, snapshot_id: str) -> Optional[TerminalSnapshot]:
        """Load a snapshot by ID."""
        return self._snapshots.get(snapshot_id)
    
    def restore_snapshot(self, snapshot_id: str) -> Optional[TerminalSnapshot]:
        """Restore a snapshot and emit event."""
        snapshot = self.load_snapshot(snapshot_id)
        
        if snapshot:
            self.snapshot_loaded.emit(snapshot_id)
            self.event_bus.publish("terminal_snapshot_loaded", {
                "snapshot_id": snapshot_id,
                "session_id": snapshot.session_id,
                "output_lines": len(snapshot.output.split('\n')),
                "command": snapshot.command,
                "exit_code": snapshot.exit_code
            })
        
        return snapshot
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot."""
        if snapshot_id not in self._snapshots:
            return False
        
        snapshot = self._snapshots.pop(snapshot_id)
        self._save_to_disk()
        
        self.event_bus.publish("terminal_snapshot_deleted", {
            "snapshot_id": snapshot_id,
            "command": snapshot.command
        })
        
        return True
    
    def export_snapshot(self, snapshot_id: str, filepath: Path = None) -> Optional[Path]:
        """Export a snapshot to file."""
        snapshot = self.load_snapshot(snapshot_id)
        if not snapshot:
            return None
        
        if filepath is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = Path(f"terminal_snapshot_{timestamp}.json")
        
        try:
            data = {
                "version": "2.1",
                "generated_at": time.time(),
                "snapshot": snapshot.to_dict()
            }
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            self.snapshot_exported.emit(str(filepath))
            self.event_bus.publish("terminal_snapshot_exported", {
                "snapshot_id": snapshot_id,
                "filepath": str(filepath)
            })
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export snapshot: {e}")
            return None
    
    def export_all_snapshots(self, filepath: Path = None) -> Optional[Path]:
        """Export all snapshots to a single file."""
        if not self._snapshots:
            return None
        
        if filepath is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = Path(f"terminal_snapshots_{timestamp}.json")
        
        try:
            data = {
                "version": "2.1",
                "generated_at": time.time(),
                "count": len(self._snapshots),
                "snapshots": [s.to_dict() for s in self._snapshots.values()]
            }
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            self.snapshot_exported.emit(str(filepath))
            self.event_bus.publish("terminal_all_snapshots_exported", {
                "filepath": str(filepath),
                "count": len(self._snapshots)
            })
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export all snapshots: {e}")
            return None
    
    def get_snapshot(self, snapshot_id: str) -> Optional[TerminalSnapshot]:
        """Get a snapshot by ID."""
        return self._snapshots.get(snapshot_id)
    
    def get_all_snapshots(self) -> List[TerminalSnapshot]:
        """Get all snapshots."""
        return list(self._snapshots.values())
    
    def get_snapshots_by_session(self, session_id: str) -> List[TerminalSnapshot]:
        """Get snapshots for a specific session."""
        return [s for s in self._snapshots.values() if s.session_id == session_id]
    
    def get_snapshot_count(self) -> int:
        """Get total snapshot count."""
        return len(self._snapshots)
    
    def clear_snapshots(self):
        """Clear all snapshots."""
        self._snapshots = {}
        self._save_to_disk()
        self.event_bus.publish("terminal_snapshots_cleared", {})
    
    def _save_to_disk(self):
        """Save snapshots to disk."""
        try:
            data = {
                "version": "2.1",
                "generated_at": time.time(),
                "snapshots": [s.to_dict() for s in self._snapshots.values()]
            }
            
            self._snapshots_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._snapshots_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save snapshots: {e}")
    
    def load_snapshots(self):
        """Load snapshots from disk."""
        if not self._snapshots_file.exists():
            return
        
        try:
            with open(self._snapshots_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for item in data.get("snapshots", []):
                try:
                    snapshot = TerminalSnapshot.from_dict(item)
                    self._snapshots[snapshot_id] = snapshot
                except Exception as e:
                    logger.warning(f"Failed to load snapshot: {e}")
            
            logger.info(f"Loaded {len(self._snapshots)} snapshots")
            
        except Exception as e:
            logger.error(f"Failed to load snapshots: {e}")
