"""
Process Manager — v1.9

Manages terminal processes, lifecycle, and resource monitoring.
"""
from PySide6.QtCore import QObject, QSettings, QProcess
from pathlib import Path
import time
import psutil


class ProcessInfo:
    """Information about a running process."""
    
    def __init__(self, process_id: str, command: str, pid: int, working_dir: Path):
        self.process_id = process_id
        self.command = command
        self.pid = pid
        self.working_dir = working_dir
        self.start_time = time.time()
        self.exit_code = None
        self.duration_ms = 0
        self.cpu_percent = 0.0
        self.memory_bytes = 0
        self.is_running = True
        self.status = "running"  # running, queued, completed, cancelled


class ProcessManager(QObject):
    """
    Manages terminal processes, lifecycle, and resource monitoring.
    Tracks CPU, memory, duration, and process tree.
    """
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self.processes = {}  # process_id -> ProcessInfo
        self.settings = QSettings("MyCodingMaster", "Terminal")
    
    def create_process(self, shell_config: dict, working_dir: Path) -> ProcessInfo:
        """Create a new process and return its info."""
        process_id = f"proc-{len(self.processes) + 1}"
        
        info = ProcessInfo(
            process_id=process_id,
            command=shell_config.get("command", ""),
            pid=0,  # Will be set when process starts
            working_dir=working_dir
        )
        
        self.processes[process_id] = info
        return info
    
    def start_process(self, process_id: str, qprocess: QProcess) -> bool:
        """Start a QProcess and track its info."""
        if process_id not in self.processes:
            return False
        
        info = self.processes[process_id]
        info.pid = qprocess.processId()
        info.status = "running"
        
        self.event_bus.publish("process_started", {
            "process_id": process_id,
            "command": info.command,
            "pid": info.pid,
            "working_directory": str(info.working_dir)
        })
        
        return True
    
    def finish_process(self, process_id: str, exit_code: int):
        """Mark process as finished."""
        if process_id not in self.processes:
            return
        
        info = self.processes[process_id]
        info.is_running = False
        info.exit_code = exit_code
        info.duration_ms = int((time.time() - info.start_time) * 1000)
        info.status = "completed" if exit_code == 0 else "failed"
        
        # Update resource usage
        try:
            if info.pid:
                process = psutil.Process(info.pid)
                info.cpu_percent = process.cpu_percent()
                info.memory_bytes = process.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        
        self.event_bus.publish("process_finished", {
            "process_id": process_id,
            "exit_code": exit_code,
            "duration_ms": info.duration_ms,
            "cpu_percent": info.cpu_percent,
            "memory_bytes": info.memory_bytes
        })
    
    def stop_process(self, process_id: str) -> bool:
        """Stop a running process."""
        if process_id not in self.processes:
            return False
        
        info = self.processes[process_id]
        info.status = "cancelled"
        
        # In a full implementation, send termination signal
        return True
    
    def get_process_info(self, process_id: str) -> ProcessInfo:
        """Get process information."""
        return self.processes.get(process_id)
    
    def get_all_processes(self) -> list:
        """Get all process information."""
        return list(self.processes.values())
    
    def update_resource_usage(self, process_id: str):
        """Update CPU and memory usage for a process."""
        if process_id not in self.processes:
            return
        
        info = self.processes[process_id]
        if not info.is_running or not info.pid:
            return
        
        try:
            process = psutil.Process(info.pid)
            info.cpu_percent = process.cpu_percent()
            info.memory_bytes = process.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass