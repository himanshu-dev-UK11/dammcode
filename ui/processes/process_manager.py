"""
Process Manager — Process Management System

Manages running processes, resource monitoring, and debug console.
"""
import json
import time
import uuid
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QSettings, QTimer

from ui.processes.process import Process, ProcessStatus, ProcessType, DebugMessage, ResourceUsage
from core.logger import setup_logger
from core.event_bus import EventBus

logger = setup_logger(__name__)


class ProcessManager(QObject):
    """
    Manages running processes, debug console, and resource monitoring.
    Integrates with terminal system and EventBus.
    """
    
    # Signals
    process_created = Signal(str)  # process_id
    process_updated = Signal(str)  # process_id
    process_killed = Signal(str)  # process_id
    process_restarted = Signal(str)  # process_id
    debug_console_updated = Signal()
    resource_usage_updated = Signal(object)  # ResourceUsage object
    
    def __init__(self, event_bus, terminal_panel, workspace_manager):
        super().__init__()
        self.event_bus = event_bus
        self.terminal_panel = terminal_panel
        self.workspace_manager = workspace_manager
        
        self.processes: Dict[str, Process] = {}
        self.debug_messages: List[DebugMessage] = []
        self.resource_history: List[ResourceUsage] = []
        
        self._config_dir = Path("config")
        self._processes_file = self._config_dir / "processes.json"
        self._debug_messages_file = self._config_dir / "debug_messages.json"
        
        # Settings
        self.settings = QSettings("MyCodingMaster", "ProcessManager")
        
        # Background monitoring timer
        self._monitor_timer = QTimer(self)
        self._monitor_timer.timeout.connect(self._update_resources)
        self._monitor_timer.start(2000)  # Update every 2 seconds
        
        # Subscribe to events
        self.event_bus.subscribe("process_started", self._on_process_started)
        self.event_bus.subscribe("process_output", self._on_process_output)
        self.event_bus.subscribe("process_finished", self._on_process_finished)
        self.event_bus.subscribe("debug_message", self._on_debug_message)
        self.event_bus.subscribe("workspace_loaded", self._on_workspace_loaded)
        
        # Load saved data
        self.load_processes()
        self.load_debug_messages()
    
    def _on_workspace_loaded(self, data: dict):
        """Update working directory when workspace changes."""
        context = data.get("context")
        if context:
            self.default_working_dir = Path(context.root_path)
    
    def _on_process_started(self, data: dict):
        """Handle process start event."""
        process_id = data.get("process_id")
        if process_id and process_id in self.processes:
            process = self.processes[process_id]
            process.status = ProcessStatus.RUNNING
            process.start_time = datetime.now()
            process.pid = data.get("pid")
            process.terminal_id = data.get("terminal_id")
            process.session_id = data.get("session_id")
            
            self.event_bus.publish("process_started", {"process_id": process_id})
            self.process_created.emit(process_id)
    
    def _on_process_output(self, data: dict):
        """Handle process output."""
        process_id = data.get("process_id")
        output = data.get("output", "")
        stream = data.get("stream", "stdout")
        
        if process_id and process_id in self.processes:
            process = self.processes[process_id]
            
            # Update resource usage from output analysis
            self._update_resources_from_output(process, output)
    
    def _on_process_finished(self, data: dict):
        """Handle process finish event."""
        process_id = data.get("process_id")
        exit_code = data.get("exit_code", 0)
        duration_ms = data.get("duration_ms")
        
        if process_id and process_id in self.processes:
            process = self.processes[process_id]
            process.status = ProcessStatus.COMPLETED if exit_code == 0 else ProcessStatus.FAILED
            process.exit_code = exit_code
            process.end_time = datetime.now()
            process.duration_ms = duration_ms
            
            # If not already saved, save to history
            if process.status == ProcessStatus.COMPLETED:
                self._save_process_to_history(process)
            
            self.event_bus.publish("process_finished", {
                "process_id": process_id,
                "exit_code": exit_code,
                "duration_ms": duration_ms
            })
            self.process_updated.emit(process_id)
    
    def _on_debug_message(self, data: dict):
        """Handle debug message."""
        message = DebugMessage(
            message_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            level=data.get("level", "INFO"),
            source=data.get("source", "runtime"),
            message=data.get("message", ""),
            file=data.get("file"),
            line=data.get("line"),
            stack_trace=data.get("stack_trace")
        )
        
        self.debug_messages.append(message)
        self.debug_messages = self.debug_messages[-5000:]  # Keep last 5000
        
        self.event_bus.publish("debug_console_updated", {})
        self.debug_console_updated.emit()
        self._save_debug_messages()
    
    # Process Management Methods
    
    def create_process(self, name: str, command: str, working_directory: str,
                      shell: str = "cmd", process_type: ProcessType = ProcessType.FOREGROUND,
                      is_background: bool = False, long_running: bool = False) -> Process:
        """Create a new process."""
        process_id = str(uuid.uuid4())
        
        process = Process(
            process_id=process_id,
            name=name,
            command=command,
            working_directory=working_directory,
            shell=shell,
            process_type=process_type,
            is_background=is_background,
            long_running=long_running,
            start_time=datetime.now()
        )
        
        self.processes[process_id] = process
        
        logger.info(f"Created process: {name} (PID: {process_id[:8]})")
        self.event_bus.publish("process_created", {"process_id": process_id, "process": process.to_dict()})
        self.process_created.emit(process_id)
        
        return process
    
    def start_process(self, process_id: str, pid: int = None) -> bool:
        """Mark a process as started."""
        if process_id not in self.processes:
            return False
        
        process = self.processes[process_id]
        process.status = ProcessStatus.RUNNING
        process.start_time = datetime.now()
        process.pid = pid
        
        self.event_bus.publish("process_started", {"process_id": process_id, "pid": pid})
        self.process_created.emit(process_id)
        return True
    
    def stop_process(self, process_id: str) -> bool:
        """Stop a running process."""
        if process_id not in self.processes:
            return False
        
        process = self.processes[process_id]
        if process.status != ProcessStatus.RUNNING:
            return False
        
        process.status = ProcessStatus.STOPPED
        process.end_time = datetime.now()
        
        self.event_bus.publish("process_stopped", {"process_id": process_id})
        self.process_updated.emit(process_id)
        return True
    
    def kill_process(self, process_id: str) -> bool:
        """Kill a running process."""
        if process_id not in self.processes:
            return False
        
        process = self.processes[process_id]
        process.status = ProcessStatus.KILLED
        process.exit_code = -1
        process.end_time = datetime.now()
        
        self.event_bus.publish("process_killed", {"process_id": process_id})
        self.process_killed.emit(process_id)
        return True
    
    def restart_process(self, process_id: str) -> bool:
        """Restart a process."""
        if process_id not in self.processes:
            return False
        
        process = self.processes[process_id]
        old_process = self.processes.pop(process_id)
        
        # Create new process instance
        new_process = Process(
            process_id=str(uuid.uuid4()),
            name=old_process.name,
            command=old_process.command,
            working_directory=old_process.working_directory,
            shell=old_process.shell,
            process_type=old_process.process_type,
            is_background=old_process.is_background,
            long_running=old_process.long_running,
            start_time=datetime.now()
        )
        
        self.processes[new_process.process_id] = new_process
        
        self.event_bus.publish("process_restarted", {"process_id": process_id, "new_process_id": new_process.process_id})
        self.process_restarted.emit(process_id)
        self.process_created.emit(new_process.process_id)
        return True
    
    # Process Query Methods
    
    def get_process(self, process_id: str) -> Optional[Process]:
        """Get a process by ID."""
        return self.processes.get(process_id)
    
    def get_all_processes(self) -> List[Process]:
        """Get all processes."""
        return list(self.processes.values())
    
    def get_running_processes(self) -> List[Process]:
        """Get all running processes."""
        return [p for p in self.processes.values() if p.status == ProcessStatus.RUNNING]
    
    def get_completed_processes(self) -> List[Process]:
        """Get completed processes."""
        return [p for p in self.processes.values() if p.status == ProcessStatus.COMPLETED]
    
    def get_failed_processes(self) -> List[Process]:
        """Get failed processes."""
        return [p for p in self.processes.values() if p.status == ProcessStatus.FAILED]
    
    def get_killed_processes(self) -> List[Process]:
        """Get killed processes."""
        return [p for p in self.processes.values() if p.status == ProcessStatus.KILLED]
    
    def get_background_processes(self) -> List[Process]:
        """Get background processes."""
        return [p for p in self.processes.values() if p.is_background or p.process_type == ProcessType.BACKGROUND]
    
    def get_foreground_processes(self) -> List[Process]:
        """Get foreground processes."""
        return [p for p in self.processes.values() if not p.is_background and p.process_type != ProcessType.BACKGROUND]
    
    def get_long_running_processes(self) -> List[Process]:
        """Get long running processes."""
        return [p for p in self.processes.values() if p.long_running]
    
    def get_processes_by_terminal(self, terminal_id: str) -> List[Process]:
        """Get processes running in a specific terminal."""
        return [p for p in self.processes.values() if p.terminal_id == terminal_id]
    
    # Search Methods
    
    def search_processes(self, query: str) -> List[Process]:
        """Search processes by PID, name, command, or directory."""
        query_lower = query.lower()
        
        results = []
        for process in self.processes.values():
            if query_lower in str(process.pid or "").lower():
                results.append(process)
            elif query_lower in process.name.lower():
                results.append(process)
            elif query_lower in process.command.lower():
                results.append(process)
            elif query_lower in process.working_directory.lower():
                results.append(process)
        
        return results
    
    def filter_processes(self, status: Optional[ProcessStatus] = None,
                        process_type: Optional[ProcessType] = None,
                        is_background: Optional[bool] = None) -> List[Process]:
        """Filter processes by criteria."""
        processes = list(self.processes.values())
        
        if status:
            processes = [p for p in processes if p.status == status]
        if process_type:
            processes = [p for p in processes if p.process_type == process_type]
        if is_background is not None:
            processes = [p for p in processes if p.is_background == is_background]
        
        return processes
    
    # Debug Console Methods
    
    def get_debug_messages(self, limit: int = 100, level: Optional[str] = None) -> List[DebugMessage]:
        """Get debug messages."""
        messages = self.debug_messages[-limit:]
        
        if level:
            messages = [m for m in messages if m.level == level]
        
        return messages
    
    def get_debug_messages_by_source(self, source: str) -> List[DebugMessage]:
        """Get debug messages from a specific source."""
        return [m for m in self.debug_messages if m.source == source]
    
    def get_debug_messages_by_level(self, level: str) -> List[DebugMessage]:
        """Get debug messages by log level."""
        return [m for m in self.debug_messages if m.level == level]
    
    def clear_debug_messages(self):
        """Clear all debug messages."""
        self.debug_messages.clear()
        self.event_bus.publish("debug_console_updated", {})
        self.debug_console_updated.emit()
    
    def add_debug_message(self, level: str, message: str, source: str = "runtime",
                         file: str = None, line: int = None, stack_trace: str = None):
        """Add a debug message."""
        self._on_debug_message({
            "level": level,
            "message": message,
            "source": source,
            "file": file,
            "line": line,
            "stack_trace": stack_trace
        })
    
    # Resource Monitoring Methods
    
    def get_resource_usage(self) -> Optional[ResourceUsage]:
        """Get current resource usage."""
        if self.resource_history:
            return self.resource_history[-1]
        return None
    
    def get_resource_history(self, limit: int = 100) -> List[ResourceUsage]:
        """Get resource usage history."""
        return self.resource_history[-limit:]
    
    def _update_resources(self):
        """Update resource usage (called by timer)."""
        cpu_usage = self._get_cpu_usage()
        memory_mb, memory_percent = self._get_memory_usage()
        process_count = len(self.processes)
        running_tasks = len(self.get_running_processes())
        terminal_count = len(self.terminal_panel.get_all_terminals()) if self.terminal_panel else 0
        
        usage = ResourceUsage(
            timestamp=datetime.now(),
            cpu_usage=cpu_usage,
            memory_usage_mb=memory_mb,
            memory_usage_percent=memory_percent,
            process_count=process_count,
            running_tasks=running_tasks,
            terminal_count=terminal_count
        )
        
        self.resource_history.append(usage)
        self.resource_history = self.resource_history[-1000:]  # Keep last 1000
        
        self.event_bus.publish("resource_usage_updated", usage.to_dict())
        self.resource_usage_updated.emit(usage)
    
    def _update_resources_from_output(self, process: Process, output: str):
        """Update process resources from output analysis."""
        # Simple CPU/memory estimation based on output patterns
        import random
        process.cpu_usage = random.uniform(0, 10)  # Simulated
        process.memory_usage_mb = random.uniform(10, 100)  # Simulated
    
    # Resource Helper Methods (Platform-specific)
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0
        except Exception:
            return 0.0
    
    def _get_memory_usage(self) -> tuple:
        """Get current memory usage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.used / (1024 * 1024), memory.percent
        except ImportError:
            return 0.0, 0.0
        except Exception:
            return 0.0, 0.0
    
    # Persistence Methods
    
    def _save_process_to_history(self, process: Process):
        """Save completed process to history."""
        # This would persist completed process data
        pass
    
    def load_processes(self):
        """Load processes from file."""
        try:
            if self._processes_file.exists():
                with open(self._processes_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                for process_data in data.get("processes", []):
                    process = Process.from_dict(process_data)
                    self.processes[process.process_id] = process
                
                logger.info(f"Loaded {len(self.processes)} processes from history")
        except Exception as e:
            logger.error(f"Failed to load processes: {e}")
            self.processes = {}
    
    def save_processes(self):
        """Save processes to file."""
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            
            process_list = [p.to_dict() for p in self.processes.values()]
            
            data = {
                "version": "1.0.0",
                "processes": process_list[-1000:]  # Keep last 1000
            }
            
            with open(self._processes_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Saved {len(self.processes)} processes")
        except Exception as e:
            logger.error(f"Failed to save processes: {e}")
    
    def load_debug_messages(self):
        """Load debug messages from file."""
        try:
            if self._debug_messages_file.exists():
                with open(self._debug_messages_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                self.debug_messages = []
                for msg_data in data.get("messages", []):
                    msg = DebugMessage.from_dict(msg_data)
                    self.debug_messages.append(msg)
                
                logger.info(f"Loaded {len(self.debug_messages)} debug messages")
        except Exception as e:
            logger.error(f"Failed to load debug messages: {e}")
            self.debug_messages = []
    
    def _save_debug_messages(self):
        """Save debug messages to file."""
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            
            message_list = [m.to_dict() for m in self.debug_messages]
            
            data = {
                "version": "1.0.0",
                "messages": message_list[-5000:]  # Keep last 5000
            }
            
            with open(self._debug_messages_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Saved {len(self.debug_messages)} debug messages")
        except Exception as e:
            logger.error(f"Failed to save debug messages: {e}")
