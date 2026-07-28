"""
Resource Manager — v1.8.5

Tracks and manages application resources:
- Threads
- Processes
- File handles
- Network connections
- Timers
- Memory usage
- Auto-cleanup on shutdown
"""

import sys
import gc
import threading
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from PySide6.QtCore import QObject, Signal, QTimer
from core.logger import setup_logger
from core.error_manager import get_error_manager

logger = setup_logger(__name__)
error_manager = get_error_manager()


class ResourceType(Enum):
    THREAD = "thread"
    PROCESS = "process"
    FILE_HANDLE = "file_handle"
    TIMER = "timer"
    NETWORK = "network"


@dataclass
class ResourceRecord:
    resource_id: str
    resource_type: ResourceType
    created_at: datetime
    metadata: dict
    owner: str = "unknown"


class ResourceManager(QObject):
    """
    Tracks and manages all application resources.
    """

    resource_leak_detected = Signal(ResourceRecord)
    cleanup_performed = Signal(int)

    _instance: Optional["ResourceManager"] = None
    _initialized = False

    def __init__(self):
        if ResourceManager._initialized:
            return
        super().__init__()
        self._resources: Dict[str, ResourceRecord] = {}
        self._process = psutil.Process()
        self._cleanup_timer = QTimer()
        self._cleanup_timer.timeout.connect(self._periodic_cleanup)
        self._cleanup_timer.start(30000)  # 30 seconds
        self._event_bus = None
        ResourceManager._initialized = True

    def set_event_bus(self, event_bus):
        """Set the event bus for communication."""
        self._event_bus = event_bus

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register_resource(
        self,
        resource_id: str,
        resource_type: ResourceType,
        owner: str = "unknown",
        metadata: Optional[dict] = None,
    ):
        """Register a new resource for tracking."""
        record = ResourceRecord(
            resource_id=resource_id,
            resource_type=resource_type,
            created_at=datetime.now(),
            metadata=metadata or {},
            owner=owner,
        )
        self._resources[resource_id] = record
        logger.debug(f"Registered {resource_type.value}: {resource_id} (owner: {owner})")

    def unregister_resource(self, resource_id: str):
        """Unregister a resource when it's no longer needed."""
        if resource_id in self._resources:
            del self._resources[resource_id]
            logger.debug(f"Unregistered resource: {resource_id}")

    def get_resources(
        self, resource_type: Optional[ResourceType] = None
    ) -> List[ResourceRecord]:
        """Get all tracked resources, optionally filtered by type."""
        resources = list(self._resources.values())
        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]
        return resources

    def get_memory_usage(self) -> dict:
        """Get current memory usage statistics."""
        try:
            mem_info = self._process.memory_info()
            return {
                "rss": mem_info.rss,
                "vms": mem_info.vms,
                "percent": self._process.memory_percent(),
            }
        except Exception as e:
            logger.debug(f"Could not get memory usage: {e}")
            return {}

    def get_thread_count(self) -> int:
        """Get current thread count."""
        try:
            return self._process.num_threads()
        except Exception as e:
            logger.debug(f"Could not get thread count: {e}")
            return 0

    def get_open_files(self) -> List[dict]:
        """Get list of open files."""
        try:
            files = self._process.open_files()
            return [{"path": f.path, "fd": f.fd} for f in files]
        except Exception as e:
            logger.debug(f"Could not get open files: {e}")
            return []

    def collect_garbage(self):
        """Force garbage collection."""
        try:
            gc.collect()
            logger.debug("Garbage collection completed")
        except Exception as e:
            logger.debug(f"Garbage collection failed: {e}")

    def _periodic_cleanup(self):
        """Periodic cleanup routine."""
        try:
            self.collect_garbage()
            # Clean up old temp files
            temp_dir = Path("temp")
            if temp_dir.exists():
                import time
                now = time.time()
                cutoff = now - (3600)  # 1 hour
                cleaned = 0
                for item in temp_dir.iterdir():
                    try:
                        if item.stat().st_mtime < cutoff:
                            if item.is_file():
                                item.unlink()
                            elif item.is_dir():
                                import shutil
                                shutil.rmtree(item)
                            cleaned += 1
                    except Exception:
                        pass
                if cleaned > 0:
                    logger.debug(f"Cleaned up {cleaned} old temp items")
        except Exception as e:
            error_manager.handle_exception(
                type(e), e, e.__traceback__, component="resource_manager", recoverable=True
            )

    def cleanup_all(self):
        """Clean up all resources on shutdown."""
        logger.info("Cleaning up all resources...")
        count = len(self._resources)
        self._resources.clear()
        self.collect_garbage()
        self.cleanup_performed.emit(count)
        logger.info(f"Resource cleanup complete: {count} resources released")

    def get_resource_count(self):
        """Get the number of tracked resources."""
        from collections import defaultdict
        counts = defaultdict(int)
        for resource in self._resources.values():
            counts[resource.resource_type] += 1
        return counts

    def get_active_resources(self):
        """Get all active resources (for diagnostics panel)."""
        return list(self._resources.values())


def get_resource_manager() -> ResourceManager:
    """Get the global ResourceManager singleton."""
    return ResourceManager()
