"""
Global Error Manager — v1.8.5

Centralized exception handling and recovery:
- Catches all uncaught exceptions
- Logs with full stack trace
- Publishes error events for UI
- Prevents app crashes from single component failures
- Tracks error statistics for diagnostics
"""

import sys
import traceback
from typing import Callable, Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from PySide6.QtCore import QObject, Signal
from core.logger import setup_logger

logger = setup_logger(__name__)


class ErrorSeverity(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


@dataclass
class ErrorRecord:
    timestamp: datetime = field(default_factory=datetime.now)
    severity: ErrorSeverity = ErrorSeverity.ERROR
    message: str = ""
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None
    traceback: Optional[str] = None  # Alias for stack_trace, for diagnostics panel
    component: str = "unknown"
    recoverable: bool = False
    context: Optional[dict] = None


class ErrorManager(QObject):
    """
    Central error manager singleton.
    """

    error_occurred = Signal(ErrorRecord)
    critical_error = Signal(ErrorRecord)

    _instance: Optional["ErrorManager"] = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if ErrorManager._initialized:
            return
        super().__init__()
        self._errors: List[ErrorRecord] = []
        self._max_errors = 1000
        self._handlers: Dict[ErrorSeverity, List[Callable]] = {}
        self._event_bus = None
        self._install_global_hooks()
        ErrorManager._initialized = True

    def set_event_bus(self, event_bus):
        """Set the event bus for communication."""
        self._event_bus = event_bus

    def _install_global_hooks(self):
        """Install global exception hooks."""
        original_excepthook = sys.excepthook

        def _custom_excepthook(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                original_excepthook(exc_type, exc_value, exc_traceback)
                return
            self.handle_exception(exc_type, exc_value, exc_traceback, component="global")

        sys.excepthook = _custom_excepthook

        # Also handle thread exceptions
        import threading
        original_thread_run = threading.Thread.run

        def _thread_run_with_exception_handling(self):
            try:
                original_thread_run(self)
            except Exception as e:
                ErrorManager().handle_exception(
                    type(e), e, e.__traceback__, component=f"thread:{self.name}"
                )

        threading.Thread.run = _thread_run_with_exception_handling

    def handle_exception(
        self,
        exc_type,
        exc_value,
        exc_traceback,
        component: str = "unknown",
        recoverable: bool = True,
    ):
        """Handle an exception with full stack trace."""
        stack_trace = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
        record = ErrorRecord(
            severity=ErrorSeverity.CRITICAL,
            message=str(exc_value),
            exception_type=exc_type.__name__,
            stack_trace=stack_trace,
            component=component,
            recoverable=recoverable,
        )
        self._add_error(record)
        logger.critical(
            f"Uncaught exception in {component}: {exc_value}",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        self.error_occurred.emit(record)
        self.critical_error.emit(record)
        return record

    def report_error(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        component: str = "unknown",
        exc_info: Optional[tuple] = None,
        recoverable: bool = True,
    ):
        """Report an error without raising an exception."""
        stack_trace = None
        exception_type = None
        if exc_info:
            exc_type, exc_value, tb = exc_info
            stack_trace = "".join(traceback.format_exception(exc_type, exc_value, tb))
            exception_type = exc_type.__name__

        record = ErrorRecord(
            severity=severity,
            message=message,
            exception_type=exception_type,
            stack_trace=stack_trace,
            component=component,
            recoverable=recoverable,
        )
        self._add_error(record)
        log_func = {
            ErrorSeverity.DEBUG: logger.debug,
            ErrorSeverity.INFO: logger.info,
            ErrorSeverity.WARNING: logger.warning,
            ErrorSeverity.ERROR: logger.error,
            ErrorSeverity.CRITICAL: logger.critical,
        }[severity]
        log_func(f"Error in {component}: {message}")
        self.error_occurred.emit(record)
        return record

    def _add_error(self, record: ErrorRecord):
        """Add an error record to the history."""
        record.traceback = record.stack_trace  # Set alias for traceback
        self._errors.append(record)
        if len(self._errors) > self._max_errors:
            self._errors.pop(0)

    def get_errors(
        self,
        severity: Optional[ErrorSeverity] = None,
        component: Optional[str] = None,
        limit: int = 100,
    ) -> List[ErrorRecord]:
        """Get error records with optional filters."""
        errors = self._errors
        if severity:
            errors = [e for e in errors if e.severity == severity]
        if component:
            errors = [e for e in errors if e.component == component]
        return errors[-limit:]

    def clear_errors(self):
        """Clear all error history."""
        self._errors.clear()

    def clear_history(self):
        """Alias for clear_errors (for diagnostics panel)."""
        self.clear_errors()

    def get_error_history(self, limit: int = 100):
        """Get the error history (alias for get_errors)."""
        return self.get_errors(limit=limit)

    def save_history(self):
        """Save error history (for shutdown, no-op for now)."""
        # TODO: Implement saving to file if needed
        pass

    def safe_execute(
        self,
        func: Callable,
        component: str = "unknown",
        fallback_return=None,
        recoverable: bool = True,
        *args,
        **kwargs,
    ):
        """
        Safely execute a function, catching all exceptions.

        Args:
            func: Function to execute
            component: Component name for error reporting
            fallback_return: Value to return on error
            recoverable: Whether error is considered recoverable
            *args: Positional args for func
            **kwargs: Keyword args for func

        Returns:
            Result of func or fallback_return
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.handle_exception(
                type(e), e, e.__traceback__, component=component, recoverable=recoverable
            )
            return fallback_return


def get_error_manager() -> ErrorManager:
    """Get the global ErrorManager singleton."""
    return ErrorManager()
