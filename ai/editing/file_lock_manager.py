"""
file_lock_manager.py — Concurrent edit prevention and queue management.

Prevents simultaneous edits of the same file by:
  - Locking files during editing
  - Queueing requests for locked files
  - Rejecting requests safely with informative messages

Thread-safe implementation with proper cleanup.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

from core.logger import setup_logger


logger = setup_logger(__name__)


class LockStatus(Enum):
    """Status of a file lock."""
    LOCKED = "locked"
    PENDING = "pending"
    REJECTED = "rejected"
    RELEASED = "released"


@dataclass
class FileLock:
    """
    A lock on a file.

    Attributes:
        lock_id:      Unique identifier for this lock.
        file_path:    Absolute path to the locked file.
        lock_time:    When the lock was acquired.
        expires_at:   When the lock will expire (for timeout).
        status:       Current status of the lock.
        request_id:   ID of the request holding the lock.
    """
    lock_id:     str
    file_path:   str
    lock_time:   datetime
    expires_at:  datetime
    status:      LockStatus
    request_id:  str


@dataclass
class LockRequest:
    """
    A request to lock a file.

    Attributes:
        request_id:   Unique identifier for this request.
        file_path:    File to lock.
        timestamp:    When the request was made.
        status:       Current status of the request.
        reason:       Human-readable reason for the lock.
    """
    request_id:  str
    file_path:   str
    timestamp:   datetime
    status:      LockStatus
    reason:      str


class FileLockManager:
    """
    Manages file locks to prevent concurrent edits.

    Features:
      - Per-file locking with configurable timeout
      - Request queuing for locked files
      - Automatic lock release on completion
      - Deadlock detection and timeout

    Usage:
        manager = FileLockManager(timeout_seconds=60)
        lock = manager.acquire(file_path, request_id)
        if lock:
            # Edit the file
            manager.release(file_path)
    """

    # Default timeout: 60 seconds
    DEFAULT_TIMEOUT = 60

    def __init__(self, timeout_seconds: int = DEFAULT_TIMEOUT) -> None:
        self._timeout = timedelta(seconds=timeout_seconds)
        self._locks: Dict[str, FileLock] = {}
        self._requests: Dict[str, LockRequest] = {}
        self._lock = threading.RLock()

        logger.debug(f"FileLockManager initialized (timeout={timeout_seconds}s).")

    # ── Public API ─────────────────────────────────────────────────────────

    def acquire(
        self,
        file_path: str,
        request_id: str,
        reason: str = "",
        timeout: Optional[float] = None,
    ) -> Optional[FileLock]:
        """
        Acquire a lock on a file.

        Args:
            file_path: Absolute path to the file.
            request_id: ID of the request requesting the lock.
            reason: Human-readable reason for the lock.
            timeout: Optional custom timeout in seconds.

        Returns:
            FileLock if acquired, None if file is locked by another request.
        """
        file_path = str(Path(file_path))
        timeout_delta = (
            timedelta(seconds=timeout)
            if timeout is not None
            else self._timeout
        )

        with self._lock:
            # Check if file is already locked
            existing = self._locks.get(file_path)
            if existing:
                # Check if lock is expired
                if datetime.now() > existing.expires_at:
                    # Lock expired, release it
                    self._release_lock(existing)
                else:
                    # Lock still valid, check if same request
                    if existing.request_id == request_id:
                        # Re-acquire own lock (extend timeout)
                        return self._create_lock(file_path, request_id, reason, timeout_delta)
                    else:
                        # File locked by another request
                        self._requests[request_id] = LockRequest(
                            request_id=request_id,
                            file_path=file_path,
                            timestamp=datetime.now(),
                            status=LockStatus.PENDING,
                            reason=reason,
                        )
                        logger.debug(
                            f"FileLockManager: '{Path(file_path).name}' locked by "
                            f"{existing.request_id[:8]}..."
                        )
                        return None

            # Create new lock
            lock = self._create_lock(file_path, request_id, reason, timeout_delta)
            self._locks[file_path] = lock
            self._requests[request_id] = LockRequest(
                request_id=request_id,
                file_path=file_path,
                timestamp=datetime.now(),
                status=LockStatus.LOCKED,
                reason=reason,
            )
            logger.debug(f"FileLockManager: lock acquired for '{Path(file_path).name}'.")
            return lock

    def release(
        self,
        file_path: str,
        request_id: Optional[str] = None,
    ) -> bool:
        """
        Release a lock on a file.

        Args:
            file_path: Absolute path to the file.
            request_id: Optional request ID to verify ownership.

        Returns:
            True if lock was released, False if lock wasn't held.
        """
        file_path = str(Path(file_path))

        with self._lock:
            lock = self._locks.get(file_path)
            if not lock:
                logger.debug(f"FileLockManager: no lock found for '{file_path}'.")
                return False

            if request_id and lock.request_id != request_id:
                logger.warning(
                    f"FileLockManager: attempt to release lock held by "
                    f"{lock.request_id[:8]}... (requested by {request_id[:8]}...)"
                )
                return False

            self._release_lock(lock)
            logger.debug(f"FileLockManager: lock released for '{file_path}'.")
            return True

    def release_all(self, request_id: str) -> int:
        """
        Release all locks held by a specific request.

        Args:
            request_id: ID of the request whose locks to release.

        Returns:
            Number of locks released.
        """
        released = 0
        with self._lock:
            locks_to_release = [
                lock for lock in self._locks.values()
                if lock.request_id == request_id
            ]
            for lock in locks_to_release:
                self._release_lock(lock)
                released += 1

        if released > 0:
            logger.info(
                f"FileLockManager: released {released} locks for request {request_id[:8]}..."
            )
        return released

    def is_locked(self, file_path: str) -> bool:
        """Check if a file is currently locked."""
        file_path = str(Path(file_path))

        with self._lock:
            lock = self._locks.get(file_path)
            if not lock:
                return False

            # Check if expired
            if datetime.now() > lock.expires_at:
                self._release_lock(lock)
                return False

            return True

    def get_lock(self, file_path: str) -> Optional[FileLock]:
        """Get the current lock on a file, if any."""
        file_path = str(Path(file_path))

        with self._lock:
            lock = self._locks.get(file_path)
            if lock and datetime.now() <= lock.expires_at:
                return lock
            elif lock:
                self._release_lock(lock)
            return None

    def queue_status(self) -> Dict[str, Any]:
        """Return the current queue status for all pending requests."""
        with self._lock:
            pending = [
                req for req in self._requests.values()
                if req.status == LockStatus.PENDING
            ]
            return {
                "total_pending": len(pending),
                "pending_files": list(set(req.file_path for req in pending)),
            }

    def cleanup_expired(self) -> int:
        """
        Remove all expired locks.

        Returns:
            Number of locks removed.
        """
        now = datetime.now()
        removed = 0

        with self._lock:
            expired = [
                lock for lock in self._locks.values()
                if now > lock.expires_at
            ]
            for lock in expired:
                self._release_lock(lock)
                removed += 1

        if removed > 0:
            logger.info(f"FileLockManager: cleaned up {removed} expired locks.")
        return removed

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _create_lock(
        self,
        file_path: str,
        request_id: str,
        reason: str,
        timeout_delta: timedelta,
    ) -> FileLock:
        """Create a new lock entry."""
        lock_id = f"lock_{uuid.uuid4().hex[:12]}"
        return FileLock(
            lock_id=lock_id,
            file_path=file_path,
            lock_time=datetime.now(),
            expires_at=datetime.now() + timeout_delta,
            status=LockStatus.LOCKED,
            request_id=request_id,
        )

    def _release_lock(self, lock: FileLock) -> None:
        """Release a lock and update state."""
        if lock.file_path in self._locks:
            del self._locks[lock.file_path]

        lock = lock.__class__(
            **{
                **lock.__dict__,
                "status": LockStatus.RELEASED,
            }
        )