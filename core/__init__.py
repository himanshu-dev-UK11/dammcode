"""
MyCodingMaster Core — v1.8.5

Core infrastructure:
- Event Bus
- Logger
- Error Manager
- Resource Manager
- Config Validator
- Performance Watchdog
- Workspace Manager
- Editor Manager
- File Operations
- File Watcher
- Exceptions
- Session Manager
- LSP Manager
"""

from .logger import setup_logger, get_logger, set_global_log_level, clean_old_logs
from .event_bus import EventBus
from .exceptions import (
    MyCodingMasterError,
    ModelTimeoutError,
    ToolExecutionError,
    ConfigurationError,
    ProviderError,
)
from .error_manager import (
    ErrorManager,
    get_error_manager,
    ErrorRecord,
    ErrorSeverity,
)
from .resource_manager import (
    ResourceManager,
    get_resource_manager,
    ResourceRecord,
    ResourceType,
)
from .config_validator import (
    ConfigValidator,
    get_config_validator,
)
from .performance_watchdog import (
    PerformanceWatchdog,
    get_performance_watchdog,
    PerformanceSnapshot,
)
from .workspace_manager import WorkspaceManager, Workspace
from .editor_manager import EditorManager
from .file_operations import FileOperations
from .file_watcher import FileWatcher
from .session_manager import SessionManager
