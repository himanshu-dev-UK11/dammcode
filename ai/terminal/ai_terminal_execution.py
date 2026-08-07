"""
AI Terminal Execution — v1.0

Extends TerminalExecutor to support AI command execution requests.
Handles the complete execution pipeline from request to completion.
"""

from PySide6.QtCore import QObject, QProcess, Signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import time
import json

from core.logger import setup_logger
from core.event_bus import EventBus
from ai.terminal.ai_terminal_manager import AITerminalManager, TerminalExecutionRequest


logger = setup_logger(__name__)


class AITerminalExecution(QObject):
    """
    Handles AI terminal execution requests through the terminal executor.
    
    Reuses:
    - TerminalExecutor (ui/terminal/terminal_executor.py)
    - AITerminalManager (ai/terminal/ai_terminal_manager.py)
    - EventBus for event distribution
    """
    
    def __init__(self, event_bus: EventBus, terminal_executor, terminal_manager):
        super().__init__()
        self.event_bus = event_bus
        self.terminal_executor = terminal_executor
        self.terminal_manager = terminal_manager
        self._logger = logger
        
        # Subscribe to AI terminal events
        self.event_bus.subscribe("ai_terminal_request", self._on_ai_terminal_request)
        self.event_bus.subscribe("terminal_execution_approved", self._on_execution_approved)
        self.event_bus.subscribe("terminal_execution_cancelled", self._on_execution_cancelled)
        
        logger.info("AITerminalExecution initialized")

    def _on_ai_terminal_request(self, data: dict):
        """Handle AI terminal request event."""
        request_id = data.get("request_id")
        command = data.get("command")
        working_directory = data.get("working_directory", str(Path.cwd()))
        reason = data.get("reason", "")
        impact = data.get("impact", "")
        approval_required = data.get("approval_required", True)
        
        # Execute through terminal executor
        self._execute_command(request_id, command, working_directory, reason, impact)

    def _execute_command(self, request_id: str, command: str, working_directory: str, 
                         reason: str, impact: str):
        """Execute the command through the terminal executor."""
        try:
            working_dir = Path(working_directory)
            
            # Start process
            process = QProcess()
            process.setWorkingDirectory(str(working_dir))
            
            # Split command and arguments
            parts = command.split()
            program = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            # Connect signals
            process.readyReadStandardOutput.connect(
                lambda: self._on_process_output(request_id, process, "stdout")
            )
            process.readyReadStandardError.connect(
                lambda: self._on_process_output(request_id, process, "stderr")
            )
            process.finished.connect(
                lambda code, status: self._on_process_finished(request_id, code, status)
            )
            
            # Start process
            process.start(program, args)
            
            if not process.waitForStarted(5000):
                self.event_bus.publish("terminal_execution_failed", {
                    "request_id": request_id,
                    "error": "Failed to start process"
                })
                return
            
            self.event_bus.publish("terminal_execution_started", {
                "request_id": request_id,
                "command": command,
                "working_directory": working_directory,
                "pid": process.processId()
            })
            
            # Store process reference for cancellation
            if not hasattr(self, '_active_processes'):
                self._active_processes = {}
            self._active_processes[request_id] = process
            
        except Exception as e:
            self._logger.error(f"Failed to execute command: {e}")
            self.event_bus.publish("terminal_execution_failed", {
                "request_id": request_id,
                "error": str(e)
            })

    def _on_process_output(self, request_id: str, process: QProcess, stream: str):
        """Handle process output."""
        if stream == "stdout":
            output = process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        else:
            output = process.readAllStandardError().data().decode('utf-8', errors='replace')
        
        self.event_bus.publish("terminal_output_stream", {
            "request_id": request_id,
            "output": output,
            "stream": stream
        })

    def _on_process_finished(self, request_id: str, exit_code: int, status):
        """Handle process completion."""
        try:
            process = self._active_processes.get(request_id)
            if process:
                del self._active_processes[request_id]
            
            # Collect remaining output
            stdout = ""
            stderr = ""
            if process:
                try:
                    stdout = process.readAllStandardOutput().data().decode('utf-8', errors='replace')
                    stderr = process.readAllStandardError().data().decode('utf-8', errors='replace')
                except:
                    pass
            
            status_str = "completed" if exit_code == 0 else "failed"
            
            self.event_bus.publish("terminal_execution_finished", {
                "request_id": request_id,
                "exit_code": exit_code,
                "status": status_str,
                "output": stdout,
                "error": stderr,
                "duration_ms": 0  # Would need to track start time
            })
            
        except Exception as e:
            self._logger.error(f"Error in process finished: {e}")

    def _on_execution_approved(self, data: dict):
        """Handle execution approved event."""
        request_id = data.get("request_id")
        command = data.get("command")
        self._logger.info(f"Execution approved: {request_id} - {command[:50]}...")

    def _on_execution_cancelled(self, data: dict):
        """Handle execution cancelled event."""
        request_id = data.get("request_id")
        self._logger.info(f"Execution cancelled: {request_id}")
        
        # Cancel process if running
        process = self._active_processes.get(request_id)
        if process and process.state() == QProcess.Running:
            process.terminate()
            process.waitForFinished(3000)
            if process.state() == QProcess.Running:
                process.kill()

    def cancel_execution(self, request_id: str) -> bool:
        """Cancel an execution by request ID."""
        process = self._active_processes.get(request_id)
        if process:
            process.terminate()
            process.waitForFinished(3000)
            if process.state() == QProcess.Running:
                process.kill()
            del self._active_processes[request_id]
            return True
        return False
