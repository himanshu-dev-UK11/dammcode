"""
Performance Watchdog — v1.8.5

Monitors application performance:
- Memory usage
- CPU usage
- UI responsiveness
- Long operations
- Deadlock detection
- Event loop health
"""

import time
import psutil
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QObject, Signal, QTimer
from core.logger import setup_logger
from core.error_manager import get_error_manager

logger = setup_logger(__name__)
error_manager = get_error_manager()


@dataclass
class PerformanceSnapshot:
    timestamp: datetime
    memory_rss: int
    memory_percent: float
    cpu_percent: float
    thread_count: int
    open_files: int
    event_loop_lag: float


@dataclass
class CurrentMetrics:
    memory_used_mb: float
    memory_percent: float
    cpu_percent: float
    thread_count: int
    object_count: int


class PerformanceWatchdog(QObject):
    """
    Monitors application performance and reports issues.
    """

    health_warning = Signal(str)
    snapshot_taken = Signal(PerformanceSnapshot)

    _instance: Optional["PerformanceWatchdog"] = None
    _initialized = False

    def __init__(self):
        if PerformanceWatchdog._initialized:
            return
        super().__init__()
        self._process = psutil.Process()
        self._snapshots: List[PerformanceSnapshot] = []
        self._max_snapshots = 100
        self._monitor_timer = QTimer()
        self._monitor_timer.timeout.connect(self._take_snapshot)
        self._monitor_interval = 5000  # 5 seconds
        self._ui_lag_threshold = 0.1  # 100ms
        self._last_tick = time.time()
        self._event_bus = None
        PerformanceWatchdog._initialized = True

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def set_event_bus(self, event_bus):
        """Set the event bus for communication."""
        self._event_bus = event_bus

    def start(self):
        """Start monitoring."""
        self._monitor_timer.start(self._monitor_interval)
        logger.info("Performance watchdog started")

    def stop(self):
        """Stop monitoring."""
        self._monitor_timer.stop()
        logger.info("Performance watchdog stopped")

    def _take_snapshot(self):
        """Take a performance snapshot."""
        try:
            now = time.time()
            lag = now - self._last_tick - (self._monitor_interval / 1000.0)
            self._last_tick = now

            mem_info = self._process.memory_info()
            snapshot = PerformanceSnapshot(
                timestamp=datetime.now(),
                memory_rss=mem_info.rss,
                memory_percent=self._process.memory_percent(),
                cpu_percent=self._process.cpu_percent(),
                thread_count=self._process.num_threads(),
                open_files=len(self._process.open_files()),
                event_loop_lag=max(0, lag),
            )

            self._snapshots.append(snapshot)
            if len(self._snapshots) > self._max_snapshots:
                self._snapshots.pop(0)

            self.snapshot_taken.emit(snapshot)

            # Check for issues
            self._check_snapshot(snapshot)

        except Exception as e:
            logger.debug(f"Could not take performance snapshot: {e}")

    def _check_snapshot(self, snapshot: PerformanceSnapshot):
        """Check snapshot for potential issues."""
        warnings = []

        if snapshot.memory_percent > 80:
            warnings.append(f"High memory usage: {snapshot.memory_percent:.1f}%")

        if snapshot.cpu_percent > 90:
            warnings.append(f"High CPU usage: {snapshot.cpu_percent:.1f}%")

        if snapshot.event_loop_lag > self._ui_lag_threshold:
            warnings.append(f"UI lag detected: {snapshot.event_loop_lag*1000:.0f}ms")

        if snapshot.thread_count > 100:
            warnings.append(f"High thread count: {snapshot.thread_count}")

        for warning in warnings:
            logger.warning(warning)
            self.health_warning.emit(warning)

    def get_latest_snapshot(self) -> Optional[PerformanceSnapshot]:
        """Get the most recent snapshot."""
        return self._snapshots[-1] if self._snapshots else None

    def get_current_metrics(self) -> Optional[CurrentMetrics]:
        """Get current performance metrics."""
        import gc
        try:
            mem_info = self._process.memory_info()
            return CurrentMetrics(
                memory_used_mb=mem_info.rss / (1024 * 1024),
                memory_percent=self._process.memory_percent(),
                cpu_percent=self._process.cpu_percent(),
                thread_count=self._process.num_threads(),
                object_count=len(gc.get_objects())
            )
        except Exception as e:
            logger.debug(f"Could not get current metrics: {e}")
            return None

    def get_statistics(self) -> Dict[str, any]:
        """Get performance statistics from stored snapshots."""
        if not self._snapshots:
            return {}

        snapshots = self._snapshots
        return {
            "samples": len(snapshots),
            "memory": {
                "min": min(s.memory_percent for s in snapshots),
                "max": max(s.memory_percent for s in snapshots),
                "avg": sum(s.memory_percent for s in snapshots) / len(snapshots)
            },
            "cpu": {
                "min": min(s.cpu_percent for s in snapshots),
                "max": max(s.cpu_percent for s in snapshots),
                "avg": sum(s.cpu_percent for s in snapshots) / len(snapshots)
            }
        }


def get_performance_watchdog() -> PerformanceWatchdog:
    """Get the global PerformanceWatchdog singleton."""
    return PerformanceWatchdog()
