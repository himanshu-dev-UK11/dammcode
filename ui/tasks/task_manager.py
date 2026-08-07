"""
Task Manager — Task System Manager

Manages tasks, their execution, and persistence.
"""
import json
import uuid
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable
from PySide6.QtCore import QObject, Signal, QSettings

from ui.tasks.task import Task, TaskStatus, TaskType, TaskExecutionRecord
from core.logger import setup_logger
from core.event_bus import EventBus

logger = setup_logger(__name__)


class TaskManager(QObject):
    """
    Manages tasks: creation, execution, history, favorites, pins.
    Integrates with terminal system and EventBus.
    """
    
    # Signals
    task_created = Signal(str)  # task_id
    task_deleted = Signal(str)  # task_id
    task_started = Signal(str)  # task_id
    task_finished = Signal(str, int, Optional[int])  # task_id, exit_code, duration_ms
    task_failed = Signal(str, int)  # task_id, exit_code
    task_cancelled = Signal(str)  # task_id
    task_history_updated = Signal()
    task_status_changed = Signal(str, str)  # task_id, new_status
    
    def __init__(self, event_bus, terminal_panel, workspace_manager):
        super().__init__()
        self.event_bus = event_bus
        self.terminal_panel = terminal_panel
        self.workspace_manager = workspace_manager
        
        self.tasks: Dict[str, Task] = {}
        self.task_history: List[TaskExecutionRecord] = []
        self.task_order: List[str] = []
        
        self._config_dir = Path("config")
        self._tasks_file = self._config_dir / "tasks.json"
        self._history_file = self._config_dir / "task_history.json"
        
        # Settings
        self.settings = QSettings("MyCodingMaster", "Tasks")
        
        # Subscribe to events
        self.event_bus.subscribe("task_execute_requested", self._on_execute_task)
        self.event_bus.subscribe("task_cancel_requested", self._on_cancel_task)
        self.event_bus.subscribe("workspace_loaded", self._on_workspace_loaded)
        
        # Load tasks and history
        self.load_tasks()
        self.load_history()
    
    def _on_workspace_loaded(self, data: dict):
        """Update working directory when workspace changes."""
        context = data.get("context")
        if context:
            self.default_working_dir = Path(context.root_path)
    
    def _on_execute_task(self, data: dict):
        """Execute a task by ID."""
        task_id = data.get("task_id")
        if task_id and task_id in self.tasks:
            self.execute_task(task_id)
    
    def _on_cancel_task(self, data: dict):
        """Cancel a running task."""
        task_id = data.get("task_id")
        if task_id and task_id in self.tasks:
            self.cancel_task(task_id)
    
    # Task Creation Methods
    
    def create_task(self, name: str, command: str, task_type: TaskType = TaskType.CUSTOM,
                   working_directory: Optional[str] = None, shell: str = "cmd",
                   description: str = "") -> Task:
        """Create a new task."""
        task_id = str(uuid.uuid4())
        
        if working_directory is None:
            working_directory = str(self.default_working_dir) if hasattr(self, 'default_working_dir') else str(Path.cwd())
        
        task = Task(
            id=task_id,
            name=name,
            command=command,
            task_type=task_type,
            working_directory=working_directory,
            shell=shell,
            description=description,
            order=len(self.tasks)
        )
        
        self.tasks[task_id] = task
        self.task_order.append(task_id)
        
        logger.info(f"Created task: {name}")
        self.event_bus.publish("task_created", {"task_id": task_id, "task": task.to_dict()})
        self.task_created.emit(task_id)
        
        self.save_tasks()
        return task
    
    def create_default_task(self, name: str, command: str, task_type: TaskType) -> Task:
        """Create a default task (auto-detected project task)."""
        return self.create_task(
            name=name,
            command=command,
            task_type=task_type,
            description=f"Auto-detected {task_type.value} task"
        )
    
    def create_custom_task(self, name: str, command: str,
                          working_directory: Optional[str] = None,
                          shell: str = "cmd", description: str = "") -> Task:
        """Create a custom task."""
        return self.create_task(
            name=name,
            command=command,
            task_type=TaskType.CUSTOM,
            working_directory=working_directory,
            shell=shell,
            description=description
        )
    
    # Task Management Methods
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return list(self.tasks.values())
    
    def get_tasks_by_type(self, task_type: TaskType) -> List[Task]:
        """Get tasks of a specific type."""
        return [t for t in self.tasks.values() if t.task_type == task_type]
    
    def get_running_tasks(self) -> List[Task]:
        """Get all running tasks."""
        return [t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]
    
    def get_pinned_tasks(self) -> List[Task]:
        """Get pinned tasks (sorted by order)."""
        pinned = [t for t in self.tasks.values() if t.is_pinned]
        pinned.sort(key=lambda t: t.order)
        return pinned
    
    def get_favorite_tasks(self) -> List[Task]:
        """Get favorite tasks."""
        return [t for t in self.tasks.values() if t.is_favorite]
    
    def update_task(self, task_id: str, **kwargs) -> bool:
        """Update a task's properties."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        self.event_bus.publish("task_updated", {"task_id": task_id, "task": task.to_dict()})
        self.save_tasks()
        return True
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks.pop(task_id)
        if task_id in self.task_order:
            self.task_order.remove(task_id)
        
        logger.info(f"Deleted task: {task.name}")
        self.event_bus.publish("task_deleted", {"task_id": task_id})
        self.task_deleted.emit(task_id)
        
        self.save_tasks()
        return True
    
    def toggle_pin(self, task_id: str) -> bool:
        """Toggle task pinned status."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.is_pinned = not task.is_pinned
        
        self.event_bus.publish("task_pinned", {"task_id": task_id, "is_pinned": task.is_pinned})
        self.save_tasks()
        return True
    
    def toggle_favorite(self, task_id: str) -> bool:
        """Toggle task favorite status."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.is_favorite = not task.is_favorite
        
        self.event_bus.publish("task_favorited", {"task_id": task_id, "is_favorite": task.is_favorite})
        self.save_tasks()
        return True
    
    def set_task_order(self, task_ids: List[str]) -> bool:
        """Set task display order."""
        # Validate all IDs exist
        if not all(tid in self.tasks for tid in task_ids):
            return False
        
        self.task_order = task_ids
        self.save_tasks()
        return True
    
    # Task Execution Methods
    
    def execute_task(self, task_id: str) -> bool:
        """Execute a task in the terminal."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # Update status
        task.status = TaskStatus.RUNNING
        task.start_time = None
        task.end_time = None
        task.exit_code = None
        task.execution_time_ms = None
        
        self.event_bus.publish("task_status_changed", {
            "task_id": task_id,
            "status": task.status.value
        })
        self.task_status_changed.emit(task_id, task.status.value)
        
        # Get working directory
        working_dir = Path(task.working_directory)
        
        # Get terminal and execute
        terminal = self.terminal_panel.get_active_terminal()
        if terminal:
            terminal.execute_command(task.command)
        
        self.event_bus.publish("task_executing", {
            "task_id": task_id,
            "command": task.command,
            "working_directory": str(working_dir)
        })
        
        logger.info(f"Executing task: {task.name} - {task.command}")
        self.task_started.emit(task_id)
        
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.status != TaskStatus.RUNNING:
            return False
        
        task.status = TaskStatus.CANCELLED
        task.exit_code = -1
        
        self.event_bus.publish("task_cancelled", {"task_id": task_id})
        self.task_cancelled.emit(task_id)
        
        logger.info(f"Cancelled task: {task.name}")
        return True
    
    def complete_task(self, task_id: str, exit_code: int, duration_ms: int):
        """Mark a task as completed."""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED if exit_code == 0 else TaskStatus.FAILED
        task.exit_code = exit_code
        task.execution_time_ms = duration_ms
        task.end_time = None
        task.last_execution = None
        task.execution_count += 1
        
        # Create history record
        record = TaskExecutionRecord(
            task_id=task_id,
            task_name=task.name,
            command=task.command,
            working_directory=task.working_directory,
            status="completed" if exit_code == 0 else "failed",
            exit_code=exit_code,
            execution_time_ms=duration_ms,
            execution_time=None
        )
        
        self.task_history.append(record)
        
        self.event_bus.publish("task_finished", {
            "task_id": task_id,
            "exit_code": exit_code,
            "duration_ms": duration_ms
        })
        self.task_finished.emit(task_id, exit_code, duration_ms)
        
        logger.info(f"Task completed: {task.name} (exit code: {exit_code}, {duration_ms}ms)")
        self.save_history()
    
    # History Methods
    
    def get_task_history(self, limit: int = 100) -> List[TaskExecutionRecord]:
        """Get task execution history."""
        return self.task_history[-limit:]
    
    def get_task_history_by_task(self, task_id: str) -> List[TaskExecutionRecord]:
        """Get execution history for a specific task."""
        return [r for r in self.task_history if r.task_id == task_id]
    
    def rerun_task(self, history_id: str) -> Optional[Task]:
        """Rerun a task from history."""
        record = next((r for r in self.task_history if r.task_id == history_id), None)
        if record:
            return self.create_task(
                name=f"{record.task_name} (rerun)",
                command=record.command,
                task_type=TaskType.CUSTOM,
                working_directory=record.working_directory,
                description=f"Rerun from history: {record.execution_time}"
            )
        return None
    
    def clear_history(self):
        """Clear task execution history."""
        self.task_history.clear()
        self.event_bus.publish("task_history_cleared", {})
        self.task_history_updated.emit()
        self.save_history()
    
    # Persistence Methods
    
    def load_tasks(self):
        """Load tasks from file."""
        try:
            if self._tasks_file.exists():
                with open(self._tasks_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                self.tasks = {}
                self.task_order = []
                
                for task_data in data.get("tasks", []):
                    task = Task.from_dict(task_data)
                    self.tasks[task.id] = task
                    self.task_order.append(task.id)
                
                # Sort by order
                self.task_order.sort(key=lambda tid: self.tasks[tid].order)
                
                logger.info(f"Loaded {len(self.tasks)} tasks")
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
            self.tasks = {}
            self.task_order = []
    
    def save_tasks(self):
        """Save tasks to file."""
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            
            task_list = [task.to_dict() for task in self.tasks.values()]
            task_list.sort(key=lambda t: t["order"])
            
            data = {
                "version": "1.0.0",
                "tasks": task_list,
                "task_order": self.task_order
            }
            
            with open(self._tasks_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Saved {len(self.tasks)} tasks")
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")
    
    def load_history(self):
        """Load task history from file."""
        try:
            if self._history_file.exists():
                with open(self._history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                self.task_history = []
                for record_data in data.get("history", []):
                    record = TaskExecutionRecord.from_dict(record_data)
                    self.task_history.append(record)
                
                logger.info(f"Loaded {len(self.task_history)} history records")
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            self.task_history = []
    
    def save_history(self):
        """Save task history to file."""
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            
            history_list = [r.to_dict() for r in self.task_history]
            
            data = {
                "version": "1.0.0",
                "history": history_list[-1000:]  # Keep last 1000
            }
            
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Saved {len(self.task_history)} history records")
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
