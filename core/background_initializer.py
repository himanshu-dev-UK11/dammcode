"""
Background Initialization System

Manages initialization of heavy systems in background threads after the UI is shown.
Provides progress tracking and enables features as they become ready.
"""

from PySide6.QtCore import QThread, Signal, QObject
from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import time

from core.logger import setup_logger

logger = setup_logger(__name__)


class InitState(Enum):
    """Initialization state for a component."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class InitTask:
    """Represents a background initialization task."""
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: int = 0  # Higher priority runs first
    dependencies: List[str] = field(default_factory=list)
    state: InitState = InitState.PENDING
    result: Any = None
    error: Optional[Exception] = None
    duration_ms: float = 0.0


class BackgroundInitWorker(QThread):
    """Worker thread for background initialization."""
    
    task_started = Signal(str)  # task_name
    task_completed = Signal(str, object)  # task_name, result
    task_failed = Signal(str, Exception)  # task_name, error
    all_completed = Signal()
    progress_updated = Signal(int, int)  # completed, total
    
    def __init__(self, tasks: List[InitTask]):
        super().__init__()
        self.tasks = {task.name: task for task in tasks}
        self.completed_tasks: set = set()
        self.failed_tasks: set = set()
        self._stop_requested = False
        
    def run(self):
        """Execute all tasks respecting dependencies and priority."""
        logger.info(f"Background initialization started with {len(self.tasks)} tasks")
        
        # Sort by priority (higher first)
        task_list = sorted(self.tasks.values(), key=lambda t: t.priority, reverse=True)
        
        for task in task_list:
            if self._stop_requested:
                logger.info("Background initialization stopped")
                break
            
            # Check if dependencies are met
            if not self._dependencies_met(task):
                logger.warning(f"Task '{task.name}' skipped due to unmet dependencies")
                task.state = InitState.SKIPPED
                continue
            
            # Execute task
            self._execute_task(task)
            
            # Update progress
            completed = len(self.completed_tasks) + len(self.failed_tasks)
            self.progress_updated.emit(completed, len(self.tasks))
        
        logger.info(f"Background initialization completed: {len(self.completed_tasks)} succeeded, {len(self.failed_tasks)} failed")
        self.all_completed.emit()
    
    def _dependencies_met(self, task: InitTask) -> bool:
        """Check if all dependencies are completed."""
        for dep_name in task.dependencies:
            if dep_name not in self.completed_tasks:
                return False
        return True
    
    def _execute_task(self, task: InitTask):
        """Execute a single task."""
        try:
            logger.info(f"Background task starting: {task.name}")
            task.state = InitState.IN_PROGRESS
            self.task_started.emit(task.name)
            
            start_time = time.perf_counter()
            result = task.func(*task.args, **task.kwargs)
            duration = (time.perf_counter() - start_time) * 1000
            
            task.result = result
            task.duration_ms = duration
            task.state = InitState.COMPLETED
            self.completed_tasks.add(task.name)
            
            logger.info(f"Background task completed: {task.name} ({duration:.2f}ms)")
            self.task_completed.emit(task.name, result)
            
        except Exception as e:
            task.error = e
            task.state = InitState.FAILED
            self.failed_tasks.add(task.name)
            
            logger.error(f"Background task failed: {task.name} - {str(e)}")
            self.task_failed.emit(task.name, e)
    
    def stop(self):
        """Request the worker to stop."""
        self._stop_requested = True


class BackgroundInitializer(QObject):
    """
    Manages background initialization of heavy systems.
    
    Usage:
        initializer = BackgroundInitializer()
        
        # Add tasks
        initializer.add_task("providers", init_providers, priority=100)
        initializer.add_task("models", init_models, priority=90, dependencies=["providers"])
        
        # Connect signals
        initializer.task_completed.connect(on_task_done)
        initializer.all_completed.connect(on_all_done)
        
        # Start
        initializer.start()
    """
    
    task_started = Signal(str)
    task_completed = Signal(str, object)
    task_failed = Signal(str, Exception)
    all_completed = Signal()
    progress_updated = Signal(int, int)
    
    def __init__(self):
        super().__init__()
        self.tasks: List[InitTask] = []
        self.worker: Optional[BackgroundInitWorker] = None
        self._is_running = False
        
    def add_task(self, 
                 name: str, 
                 func: Callable, 
                 *args, 
                 priority: int = 0,
                 dependencies: Optional[List[str]] = None,
                 **kwargs):
        """Add a background initialization task."""
        task = InitTask(
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            dependencies=dependencies or []
        )
        self.tasks.append(task)
        logger.debug(f"Added background task: {name} (priority={priority})")
    
    def start(self):
        """Start background initialization."""
        if self._is_running:
            logger.warning("Background initialization already running")
            return
        
        if not self.tasks:
            logger.warning("No background tasks to execute")
            return
        
        self._is_running = True
        
        # Create and configure worker
        self.worker = BackgroundInitWorker(self.tasks)
        self.worker.task_started.connect(self.task_started)
        self.worker.task_completed.connect(self.task_completed)
        self.worker.task_failed.connect(self.task_failed)
        self.worker.all_completed.connect(self._on_all_completed)
        self.worker.progress_updated.connect(self.progress_updated)
        
        # Start worker thread
        logger.info("Starting background initialization worker")
        self.worker.start()
    
    def _on_all_completed(self):
        """Handle completion of all tasks."""
        self._is_running = False
        self.all_completed.emit()
    
    def stop(self):
        """Stop background initialization."""
        if self.worker and self.worker.isRunning():
            logger.info("Stopping background initialization")
            self.worker.stop()
            self.worker.wait(5000)  # Wait up to 5 seconds
    
    def is_running(self) -> bool:
        """Check if initialization is in progress."""
        return self._is_running
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of all tasks."""
        if not self.worker:
            return {"state": "not_started", "tasks": []}
        
        return {
            "state": "running" if self._is_running else "completed",
            "completed": len(self.worker.completed_tasks),
            "failed": len(self.worker.failed_tasks),
            "total": len(self.tasks),
            "tasks": [
                {
                    "name": task.name,
                    "state": task.state.value,
                    "duration_ms": task.duration_ms,
                    "error": str(task.error) if task.error else None
                }
                for task in self.tasks
            ]
        }


# Convenience function to create a task wrapper
def create_init_task(name: str, priority: int = 0, dependencies: Optional[List[str]] = None):
    """
    Decorator to mark a function as a background initialization task.
    
    Usage:
        @create_init_task("providers", priority=100)
        def init_providers(event_bus):
            # ... initialization code ...
            return provider_manager
    """
    def decorator(func):
        func._init_task_name = name
        func._init_task_priority = priority
        func._init_task_dependencies = dependencies or []
        return func
    return decorator
