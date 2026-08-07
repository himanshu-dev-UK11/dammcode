"""
AI Terminal Manager — v1.0

Deeply integrates AI system with the Integrated Terminal.
Enables AI to request terminal execution, stream output, analyze results,
and assist users with safe command execution.

Features:
- AI terminal command execution
- User approval workflow
- Live output streaming
- Output analysis for errors/warnings
- Command history storage
- Terminal actions from AI chat
- Safe command filter for dangerous commands
- Workspace awareness
- Terminal status tracking
- EventBus event publishing
"""

from PySide6.QtCore import QObject, Signal, QSettings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import time
import json

from core.logger import setup_logger
from core.event_bus import EventBus
from core.workspace_manager import WorkspaceManager
from ai.terminal.terminal_approval_panel import TerminalApprovalPanel


logger = setup_logger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Data Models
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class TerminalExecutionRequest:
    """Request from AI to execute a terminal command."""
    request_id: str
    command: str
    working_directory: Path
    reason: str
    impact: str
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, approved, cancelled, running, completed, failed
    execution_time_ms: int = 0
    exit_code: int = None
    output: str = ""
    error_output: str = ""
    approval_required: bool = True


@dataclass
class TerminalCommandHistoryRecord:
    """Record of a terminal command executed by AI."""
    request_id: str
    command: str
    timestamp: datetime
    workspace: str
    exit_code: int
    duration_ms: int
    status: str
    output_preview: str = ""


# ──────────────────────────────────────────────────────────────────────────────
# Safe Command Filter
# ──────────────────────────────────────────────────────────────────────────────

DANGEROUS_COMMAND_PATTERNS = [
    # System modification/destruction
    r"^\s*rmdir\s",           # Remove directory
    r"^\s*del(\s|$)",         # Delete files
    r"^\s*format\s",          # Format disk
    r"^\s*diskpart\s",        # Disk partitioning
    r"^\s*shutdown\s",        # System shutdown
    r"^\s*reboot\s",          # System reboot
    r"^\s*reg\s+delete\s",    # Registry deletion
    r"^\s*system\s+reset\s",  # System reset
    
    # Potentially dangerous file operations
    r"^\s*rm\s+-rf\s",        # Recursive directory removal
    r"^\s*rd\s+/s\s+/q\s",    # Windows recursive delete
    r"^\s*rm\s+-rf\s+/",      # Dangerous rm with root
    r"^\s*del\s+/s\s+/f\s+/q", # Windows force delete
    
    # Network attacks
    r"^\s*nmap\s",            # Network scanning
    r"^\s*sqlmap\s",          # SQL injection tool
    
    # System utilities
    r"^\s*mkcert\s",          # Certificate creation
    r"^\s*net\s+use\s",       # Network connection
    
    # Configuration changes
    r"^\s*chkntfs\s",         # Check disk
    r"^\s*defrag\s",          # Disk defragmentation
]


# ──────────────────────────────────────────────────────────────────────────────
# AI Terminal Manager
# ──────────────────────────────────────────────────────────────────────────────

class AITerminalManager(QObject):
    """
    Manages AI terminal execution with safety, approval, and analysis.
    
    Reuses:
    - Integrated Terminal (terminal_executor.py, terminal_manager.py)
    - WorkspaceManager (current workspace tracking)
    - EventBus (event distribution)
    - Logger (logging)
    """
    
    # Signals for thread-safe UI updates
    request_created = Signal(str)  # request_id
    request_updated = Signal(str)  # request_id
    execution_started = Signal(str)  # request_id
    execution_completed = Signal(str)  # request_id
    execution_failed = Signal(str, str)  # request_id, error
    
    def __init__(self, event_bus: EventBus, workspace_manager: WorkspaceManager):
        super().__init__()
        self.event_bus = event_bus
        self.workspace_manager = workspace_manager
        self.settings = QSettings("MyCodingMaster", "AITerminal")
        
        # State
        self._requests: Dict[str, TerminalExecutionRequest] = {}
        self._history: List[TerminalCommandHistoryRecord] = []
        self._current_request: Optional[str] = None
        
        # Load history
        self._load_history()
        
        # Subscribe to terminal events
        self.event_bus.subscribe("terminal_output", self._on_terminal_output)
        self.event_bus.subscribe("terminal_error", self._on_terminal_error)
        self.event_bus.subscribe("process_started", self._on_process_started)
        self.event_bus.subscribe("process_finished", self._on_process_finished)
        
        logger.info("AITerminalManager initialized")

    # ──────────────────────────────────────────────────────────────────────────────
    # Command Execution Request
    # ──────────────────────────────────────────────────────────────────────────────

    def create_execution_request(
        self,
        command: str,
        working_directory: Optional[Path] = None,
        reason: str = "",
        impact: str = ""
    ) -> str:
        """
        Create a terminal execution request from AI.
        
        Args:
            command: The terminal command to execute
            working_directory: Working directory for the command
            reason: Why this command is being executed
            impact: Estimated impact of the command
            
        Returns:
            Request ID for tracking
        """
        # Determine working directory
        if working_directory is None:
            workspace = self.workspace_manager.active_workspace
            if workspace:
                working_directory = workspace.path
            else:
                working_directory = Path.cwd()
        
        # Generate request ID
        request_id = f"ai-exec-{int(time.time() * 1000)}"
        
        # Create request
        request = TerminalExecutionRequest(
            request_id=request_id,
            command=command.strip(),
            working_directory=working_directory,
            reason=reason,
            impact=impact if impact else "Standard terminal execution"
        )
        
        # Check if approval is needed
        if not self._requires_approval(command):
            request.approval_required = False
            request.status = "approved"
        
        self._requests[request_id] = request
        self._current_request = request_id
        
        # Publish event
        self.event_bus.publish("ai_terminal_request", {
            "request_id": request_id,
            "command": command,
            "working_directory": str(working_directory),
            "reason": reason,
            "impact": impact,
            "status": request.status,
            "approval_required": request.approval_required
        })
        
        self.request_created.emit(request_id)
        logger.info(f"Created terminal execution request: {request_id} - {command[:50]}...")
        
        return request_id

    def _requires_approval(self, command: str) -> bool:
        """Check if command requires user approval based on safety filter."""
        import re
        
        command_lower = command.lower().strip()
        
        for pattern in DANGEROUS_COMMAND_PATTERNS:
            if re.search(pattern, command_lower, re.IGNORECASE):
                return True
        
        return False

    def approve_execution(self, request_id: str) -> bool:
        """
        Approve a pending execution request.
        
        Args:
            request_id: The request to approve
            
        Returns:
            True if approved, False if request not found or already processed
        """
        if request_id not in self._requests:
            return False
        
        request = self._requests[request_id]
        if request.status not in ("pending", "approved"):
            return False
        
        request.status = "approved"
        self._save_history()
        
        self.event_bus.publish("terminal_execution_approved", {
            "request_id": request_id,
            "command": request.command
        })
        
        self._execute_command(request)
        return True

    def cancel_execution(self, request_id: str) -> bool:
        """
        Cancel a pending execution request.
        
        Args:
            request_id: The request to cancel
            
        Returns:
            True if cancelled, False if request not found
        """
        if request_id not in self._requests:
            return False
        
        request = self._requests[request_id]
        if request.status != "pending":
            return False
        
        request.status = "cancelled"
        
        self.event_bus.publish("terminal_execution_cancelled", {
            "request_id": request_id,
            "command": request.command
        })
        
        logger.info(f"Cancelled terminal execution: {request_id}")
        return True

    # ──────────────────────────────────────────────────────────────────────────────
    # Execution
    # ──────────────────────────────────────────────────────────────────────────────

    def _execute_command(self, request: TerminalExecutionRequest):
        """Execute the approved command in the terminal."""
        if request.status != "approved":
            return
        
        request.status = "running"
        request.start_time = time.time()
        
        self.event_bus.publish("terminal_execution_started", {
            "request_id": request.request_id,
            "command": request.command,
            "working_directory": str(request.working_directory)
        })
        
        self.execution_started.emit(request.request_id)
        logger.info(f"Executing terminal command: {request.command}")
        
        # Execute via RunManager
        self._run_via_run_manager(request)

    def _run_via_run_manager(self, request: TerminalExecutionRequest):
        """Execute command using RunManager."""
        from core.run_manager import RunManager
        
        run_manager = RunManager(self.event_bus)
        run_manager.workspace_root = request.working_dir
        
        # Detect and run appropriate command
        if request.command.startswith("python "):
            file_path = Path(request.command[7:]).resolve()
            if file_path.exists():
                run_manager.run_file(file_path)
            else:
                self._complete_execution(request.request_id, 1, "File not found")
        elif request.command.startswith("npm "):
            run_manager.execute_project_command("npm", request.command[4:])
        elif request.command.startswith("yarn "):
            run_manager.execute_project_command("yarn", request.command[5:])
        else:
            # Generic command execution
            run_manager.execute_generic_command(request.command, request.working_directory)

    # ──────────────────────────────────────────────────────────────────────────────
    # Event Handlers
    # ──────────────────────────────────────────────────────────────────────────────

    def _on_terminal_output(self, data: dict):
        """Handle terminal output event."""
        if not self._current_request:
            return
        
        request = self._requests.get(self._current_request)
        if not request or request.status != "running":
            return
        
        output = data.get("output", "")
        request.output += output
        
        # Stream to AI chat
        self.event_bus.publish("terminal_output_stream", {
            "request_id": request.request_id,
            "output": output,
            "stream": "stdout"
        })

    def _on_terminal_error(self, data: dict):
        """Handle terminal error event."""
        if not self._current_request:
            return
        
        request = self._requests.get(self._current_request)
        if not request or request.status != "running":
            return
        
        error = data.get("error", "")
        request.error_output += error
        
        # Stream to AI chat
        self.event_bus.publish("terminal_output_stream", {
            "request_id": request.request_id,
            "output": error,
            "stream": "stderr"
        })

    def _on_process_started(self, data: dict):
        """Handle process started event."""
        process_id = data.get("process_id", "")
        if not self._current_request:
            return
        
        request = self._requests.get(self._current_request)
        if request:
            request.pid = data.get("pid", 0)
            self.request_updated.emit(request.request_id)

    def _on_process_finished(self, data: dict):
        """Handle process finished event."""
        if not self._current_request:
            return
        
        request = self._requests.get(self._current_request)
        if not request:
            return
        
        request.exit_code = data.get("exit_code", 0)
        request.duration_ms = int((time.time() - request.start_time) * 1000)
        request.status = "completed" if request.exit_code == 0 else "failed"
        
        # Save history
        self._save_history_record(request)
        
        self.event_bus.publish("terminal_execution_finished", {
            "request_id": request.request_id,
            "command": request.command,
            "exit_code": request.exit_code,
            "duration_ms": request.duration_ms,
            "output": request.output,
            "error": request.error_output
        })
        
        self.execution_completed.emit(request.request_id)
        
        # Auto-analyze if failed
        if request.status == "failed":
            self._analyze_execution(request.request_id)
        
        self._current_request = None

    # ──────────────────────────────────────────────────────────────────────────────
    # Analysis
    # ──────────────────────────────────────────────────────────────────────────────

    def _analyze_execution(self, request_id: str):
        """Analyze execution output for errors and warnings."""
        if request_id not in self._requests:
            return
        
        request = self._requests[request_id]
        
        self.event_bus.publish("terminal_analysis_started", {
            "request_id": request_id
        })
        
        analysis = {
            "has_compiler_errors": False,
            "has_runtime_errors": False,
            "has_warnings": False,
            "error_types": [],
            "warnings": [],
            "suggested_fixes": [],
            "stack_traces": []
        }
        
        # Analyze output
        output = request.output + "\n" + request.error_output
        
        if output:
            # Detect Python errors
            if "Traceback" in output or "Exception" in output or "Error:" in output:
                analysis["has_runtime_errors"] = True
                analysis["error_types"].append("PythonException")
                
                # Extract stack trace
                lines = output.split("\n")
                in_traceback = False
                for line in lines:
                    if "Traceback" in line:
                        in_traceback = True
                    if in_traceback:
                        analysis["stack_traces"].append(line)
                        if line.strip() and line.strip().startswith("File ") and "line " in line:
                            # Found line number, suggest fix
                            analysis["suggested_fixes"].append(f"Check the line mentioned in the stack trace")
                            break
            
            # Detect compilation errors
            if "error" in output.lower() and ("CMake" in output or "make" in output or "build" in output):
                analysis["has_compiler_errors"] = True
                analysis["error_types"].append("CompilationError")
                analysis["suggested_fixes"].append("Check compiler error messages and fix syntax issues")
            
            # Detect warnings
            if "warning" in output.lower():
                analysis["has_warnings"] = True
                # Extract warning messages
                for line in output.split("\n"):
                    if "warning" in line.lower():
                        analysis["warnings"].append(line.strip())
                        if "deprecated" in line.lower():
                            analysis["suggested_fixes"].append("Consider updating deprecated APIs")
                        elif "unused" in line.lower():
                            analysis["suggested_fixes"].append("Remove or use the unused variables/imports")
        
        request.metadata = analysis
        
        self.event_bus.publish("terminal_analysis_finished", {
            "request_id": request_id,
            "analysis": analysis
        })
        
        logger.info(f"Analysis completed for {request_id}: {len(analysis['error_types'])} error types found")
        
        return analysis

    # ──────────────────────────────────────────────────────────────────────────────
    # History
    # ──────────────────────────────────────────────────────────────────────────────

    def _save_history_record(self, request: TerminalExecutionRequest):
        """Save execution record to history."""
        record = TerminalCommandHistoryRecord(
            request_id=request.request_id,
            command=request.command,
            timestamp=request.timestamp,
            workspace=str(request.working_directory),
            exit_code=request.exit_code or -1,
            duration_ms=request.duration_ms,
            status=request.status,
            output_preview=request.output[:200]  # Preview only
        )
        
        self._history.append(record)
        
        # Keep only last 1000 records
        if len(self._history) > 1000:
            self._history = self._history[-1000:]

    def _load_history(self):
        """Load history from settings."""
        history_json = self.settings.value("terminal/execution_history", "[]")
        try:
            data = json.loads(history_json)
            for item in data:
                record = TerminalCommandHistoryRecord(
                    request_id=item.get("request_id", ""),
                    command=item.get("command", ""),
                    timestamp=datetime.fromisoformat(item.get("timestamp", "")),
                    workspace=item.get("workspace", ""),
                    exit_code=item.get("exit_code", 0),
                    duration_ms=item.get("duration_ms", 0),
                    status=item.get("status", ""),
                    output_preview=item.get("output_preview", "")
                )
                self._history.append(record)
        except Exception as e:
            logger.error(f"Failed to load history: {e}")

    def _save_history(self):
        """Save history to settings."""
        try:
            data = {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "history": [
                    {
                        "request_id": r.request_id,
                        "command": r.command,
                        "timestamp": r.timestamp.isoformat(),
                        "workspace": r.workspace,
                        "exit_code": r.exit_code,
                        "duration_ms": r.duration_ms,
                        "status": r.status,
                        "output_preview": r.output_preview
                    }
                    for r in self._history
                ]
            }
            
            self.settings.setValue("terminal/execution_history", json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def get_execution_history(self, limit: int = 100) -> List[TerminalCommandHistoryRecord]:
        """Get execution history."""
        return self._history[-limit:]

    def get_execution_by_id(self, request_id: str) -> Optional[TerminalExecutionRequest]:
        """Get execution request by ID."""
        return self._requests.get(request_id)

    def get_all_executions(self) -> List[TerminalExecutionRequest]:
        """Get all execution requests."""
        return list(self._requests.values())

    def get_active_execution(self) -> Optional[TerminalExecutionRequest]:
        """Get currently active execution."""
        if self._current_request:
            return self._requests.get(self._current_request)
        return None

    # ──────────────────────────────────────────────────────────────────────────────
    # Terminal Actions
    # ──────────────────────────────────────────────────────────────────────────────

    def run_again(self, request_id: str) -> str:
        """Run the same command again."""
        if request_id not in self._requests:
            return "Request not found"
        
        request = self._requests[request_id]
        new_request_id = self.create_execution_request(
            command=request.command,
            working_directory=request.working_directory,
            reason=f"Re-execution of: {request.reason}",
            impact=request.impact
        )
        return new_request_id

    def copy_command(self, request_id: str) -> str:
        """Get command text for copying."""
        if request_id not in self._requests:
            return ""
        return self._requests[request_id].command

    def open_terminal(self, working_directory: Optional[Path] = None):
        """Open terminal in specified directory."""
        if working_directory is None:
            workspace = self.workspace_manager.active_workspace
            if workspace:
                working_directory = workspace.path
            else:
                working_directory = Path.cwd()
        
        self.event_bus.publish("open_terminal_requested", {
            "working_directory": str(working_directory)
        })

    def open_output(self, request_id: str):
        """Open output view for a request."""
        if request_id not in self._requests:
            return
        
        request = self._requests[request_id]
        self.event_bus.publish("show_terminal_output", {
            "request_id": request_id,
            "command": request.command,
            "output": request.output,
            "error": request.error_output,
            "exit_code": request.exit_code
        })

    def open_related_file(self, request_id: str):
        """Open file mentioned in output (e.g., error locations)."""
        if request_id not in self._requests:
            return
        
        request = self._requests[request_id]
        
        # Look for file references in output
        import re
        
        # Python file references: File "filename.py"
        pattern = r'File\s+"([^"]+)"'
        matches = re.findall(pattern, request.output + request.error_output)
        
        if matches:
            # Open first file found
            file_path = matches[0]
            self.event_bus.publish("open_file_requested", {
                "path": file_path
            })
            return
        
        # C/C++ references: file.c:X:
        pattern = r'([^\s:]+)\.([a-z]+):\d+:'
        matches = re.findall(pattern, request.output + request.error_output)
        
        if matches:
            file_path = matches[0][0] + "." + matches[0][1]
            self.event_bus.publish("open_file_requested", {
                "path": file_path
            })

    # ──────────────────────────────────────────────────────────────────────────────
    # Status
    # ──────────────────────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Get terminal manager status."""
        return {
            "pending_requests": len([r for r in self._requests.values() if r.status == "pending"]),
            "running_requests": len([r for r in self._requests.values() if r.status == "running"]),
            "completed_requests": len([r for r in self._requests.values() if r.status == "completed"]),
            "failed_requests": len([r for r in self._requests.values() if r.status == "failed"]),
            "history_size": len(self._history),
            "current_request": self._current_request
        }

    def shutdown(self):
        """Shutdown the manager."""
        self.settings.sync()
        logger.info("AITerminalManager shutdown complete")
