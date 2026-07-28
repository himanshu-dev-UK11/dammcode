"""
context_cache.py — Thread-safe LRU cache for ContextPackage objects.

Caches previously built context packages and reuses them when an
identical (prompt + file + mtime fingerprint) request arrives.
Invalidation is file-level: any cached package that included a
changed file is evicted immediately.

Design decisions:
  - Uses collections.OrderedDict for O(1) LRU eviction.
  - All public methods acquire a threading.Lock for thread safety.
  - Cache key is a stable SHA-256 hash of the cache fingerprint string.
  - max_size defaults to 50 packages (tunable at construction time).
"""

from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

from core.logger import setup_logger

if TYPE_CHECKING:
    from ai.context.context_engine import ContextPackage

logger = setup_logger(__name__)

DEFAULT_CACHE_SIZE = 50


@dataclass
class CacheEntry:
    """One slot in the LRU cache."""
    package:    "ContextPackage"
    key:        str
    created_at: datetime = field(default_factory=datetime.utcnow)
    hit_count:  int = 0
    file_paths: List[str] = field(default_factory=list)  # files used to build it


@dataclass
class CacheStats:
    """Snapshot of cache health metrics."""
    size:        int
    max_size:    int
    hits:        int
    misses:      int
    evictions:   int
    hit_rate_pct: float


class ContextCache:
    """
    Thread-safe LRU cache for ContextPackage objects.

    Args:
        max_size: Maximum number of packages to store before evicting
                  the least-recently-used entry.
    """

    def __init__(self, max_size: int = DEFAULT_CACHE_SIZE) -> None:
        self._max_size   = max_size
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock       = threading.Lock()

        # Stats (read without lock is acceptable for monitoring)
        self._hits      = 0
        self._misses    = 0
        self._evictions = 0

        logger.debug(f"ContextCache initialised (max_size={max_size}).")

    # ── Cache key generation ───────────────────────────────────────────────

    @staticmethod
    def make_key(
        prompt:       str,
        current_file: str,
        file_mtimes:  Dict[str, float],
    ) -> str:
        """
        Build a stable SHA-256 cache key.

        The key incorporates the prompt, current file, and the modification
        timestamps of every file in the candidate set so that any file change
        immediately yields a cache miss.
        """
        mtime_part = "|".join(
            f"{p}:{t}"
            for p, t in sorted(file_mtimes.items())
        )
        raw = f"{prompt}::{current_file}::{mtime_part}"
        return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()

    # ── Public API ─────────────────────────────────────────────────────────

    def get(self, key: str) -> Optional["ContextPackage"]:
        """
        Return the cached ContextPackage for *key*, or None on a miss.

        On a hit the entry is moved to the end of the LRU queue
        (most-recently-used).
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                logger.debug(f"Cache MISS — key={key[:12]}…")
                return None

            # Move to most-recently-used position
            self._store.move_to_end(key)
            entry.hit_count += 1
            self._hits += 1
            logger.debug(
                f"Cache HIT — key={key[:12]}… "
                f"(hit #{entry.hit_count}, age={self._age(entry)}s)"
            )
            return entry.package

    def put(
        self,
        key:      str,
        package:  "ContextPackage",
        file_paths: Optional[List[str]] = None,
    ) -> None:
        """
        Store *package* under *key*.

        If the cache is full, the least-recently-used entry is evicted first.
        """
        with self._lock:
            if key in self._store:
                # Update existing entry and move to end
                self._store.move_to_end(key)
                self._store[key].package    = package
                self._store[key].created_at = datetime.utcnow()
                self._store[key].file_paths = file_paths or []
            else:
                # Evict LRU if at capacity
                if len(self._store) >= self._max_size:
                    evicted_key, _ = self._store.popitem(last=False)
                    self._evictions += 1
                    logger.debug(f"Cache evict LRU — key={evicted_key[:12]}…")

                self._store[key] = CacheEntry(
                    package=package,
                    key=key,
                    file_paths=file_paths or [],
                )
                logger.debug(
                    f"Cache PUT — key={key[:12]}… "
                    f"(size now {len(self._store)}/{self._max_size})"
                )

    def invalidate_file(self, path: str) -> int:
        """
        Evict every cache entry that was built using *path*.

        Called when a file changes on disk so stale packages are
        never returned. Returns the number of entries evicted.
        """
        norm = str(Path(path))
        evicted = 0
        with self._lock:
            keys_to_remove = [
                k for k, e in self._store.items()
                if norm in (str(Path(p)) for p in e.file_paths)
            ]
            for k in keys_to_remove:
                del self._store[k]
                evicted += 1
                self._evictions += 1

        if evicted:
            logger.debug(
                f"Cache invalidated {evicted} entries for changed file: {path}"
            )
        return evicted

    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
        logger.debug(f"Cache cleared ({count} entries removed).")

    def stats(self) -> CacheStats:
        """Return a snapshot of cache performance metrics."""
        total = self._hits + self._misses
        hit_rate = round(self._hits / total * 100, 1) if total else 0.0
        return CacheStats(
            size=len(self._store),
            max_size=self._max_size,
            hits=self._hits,
            misses=self._misses,
            evictions=self._evictions,
            hit_rate_pct=hit_rate,
        )

    # ── Internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _age(entry: CacheEntry) -> int:
        """Age of an entry in whole seconds."""
        delta = datetime.utcnow() - entry.created_at
        return int(delta.total_seconds())
