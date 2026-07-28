"""
Git Status Manager — v2.2

Manages git status detection and decoration for files in the Explorer.
"""
from pathlib import Path
from typing import Dict, Optional, Set
from PySide6.QtCore import QObject, Signal, QProcess
from core.logger import setup_logger

logger = setup_logger(__name__)


class GitStatus:
    """Represents the git status of a file."""
    
    STATUS_MODIFIED = "modified"
    STATUS_ADDED = "added"
    STATUS_DELETED = "deleted"
    STATUS_RENAMED = "renamed"
    STATUS_COPIED = "copied"
    STATUS_UNTRACKED = "untracked"
    STATUS_IGNORED = "ignored"
    STATUS_CONFLICTED = "conflicted"
    STATUS_STAGED = "staged"
    STATUS_CLEAN = "clean"
    
    def __init__(self, status: str = STATUS_CLEAN):
        self.status = status
        self.staged = False
    
    def __eq__(self, other):
        if isinstance(other, str):
            return self.status == other
        return self.status == other.status if isinstance(other, GitStatus) else False
    
    def __hash__(self):
        return hash(self.status)
    
    def to_dict(self) -> dict:
        return {"status": self.status, "staged": self.staged}
    
    @classmethod
    def from_dict(cls, data: dict) -> "GitStatus":
        status = cls(data.get("status", cls.STATUS_CLEAN))
        status.staged = data.get("staged", False)
        return status


class GitStatusManager(QObject):
    """
    Manages git status detection and provides file decorations.
    Uses git CLI for status detection.
    """
    
    # Signals
    status_updated = Signal(str, GitStatus)  # path, status
    status_batch_updated = Signal(dict)  # {path: status}
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._status_cache: Dict[str, GitStatus] = {}
        self._git_root: Optional[Path] = None
        self._is_git_repo = False
    
    def set_git_root(self, root: Path):
        """Set the git repository root directory."""
        self._git_root = root
        self._is_git_repo = (root / ".git").exists()
        
        if self._is_git_repo:
            logger.info(f"Git repository detected at: {root}")
        else:
            logger.debug(f"Not a git repository: {root}")
    
    def is_git_repo(self) -> bool:
        """Check if we're in a git repository."""
        return self._is_git_repo
    
    def get_status(self, path: Path) -> GitStatus:
        """Get git status for a file."""
        if not self._is_git_repo:
            return GitStatus(GitStatus.STATUS_CLEAN)
        
        # Check cache
        path_str = str(path.resolve())
        if path_str in self._status_cache:
            return self._status_cache[path_str]
        
        # Get status
        status = self._detect_status(path)
        self._status_cache[path_str] = status
        self.status_updated.emit(path_str, status)
        
        return status
    
    def _detect_status(self, path: Path) -> GitStatus:
        """Detect git status for a file using git CLI."""
        try:
            if not self._git_root:
                return GitStatus(GitStatus.STATUS_CLEAN)
            
            # Get relative path from git root
            rel_path = path.relative_to(self._git_root)
            rel_path_str = str(rel_path).replace("\\", "/")
            
            # Get git status output
            process = QProcess()
            process.setProcessChannelMode(QProcess.MergedChannels)
            process.start("git", ["status", "--porcelain", rel_path_str])
            process.waitForFinished()
            
            output = process.readAllStandardOutput().data().decode('utf-8')
            
            if not output.strip():
                return GitStatus(GitStatus.STATUS_CLEAN)
            
            # Parse git status output
            for line in output.strip().split('\n'):
                if not line:
                    continue
                    
                # Format: XY path
                # X = staged status, Y = unstaged status
                if len(line) >= 2:
                    staged_code = line[0]
                    unstaged_code = line[1]
                    file_path = line[3:]
                    
                    if file_path == rel_path_str or file_path.endswith(rel_path_str):
                        return self._parse_status_codes(staged_code, unstaged_code)
            
            return GitStatus(GitStatus.STATUS_UNTRACKED)
            
        except Exception as e:
            logger.error(f"Failed to get git status for {path}: {e}")
            return GitStatus(GitStatus.STATUS_CLEAN)
    
    def _parse_status_codes(self, staged: str, unstaged: str) -> GitStatus:
        """Parse git status codes."""
        # Status codes:
        #   M = modified
        #   A = added
        #   D = deleted
        #   R = renamed
        #   C = copied
        #   U = unmerged/untracked
        #   ?? = untracked
        
        if staged == '?' and unstaged == '?':
            return GitStatus(GitStatus.STATUS_UNTRACKED)
        
        status = GitStatus(GitStatus.STATUS_CLEAN)
        
        # Staged status
        if staged == 'M':
            status.staged = True
            status.status = GitStatus.STATUS_MODIFIED
        elif staged == 'A':
            status.staged = True
            status.status = GitStatus.STATUS_ADDED
        elif staged == 'D':
            status.staged = True
            status.status = GitStatus.STATUS_DELETED
        elif staged == 'R':
            status.staged = True
            status.status = GitStatus.STATUS_RENAMED
        elif staged == 'C':
            status.staged = True
            status.status = GitStatus.STATUS_COPIED
        
        # Unstaged status
        if unstaged == 'M':
            status.status = GitStatus.STATUS_MODIFIED
        elif unstaged == 'D':
            status.status = GitStatus.STATUS_DELETED
        elif unstaged == 'U':
            status.status = GitStatus.STATUS_CONFLICTED
        
        return status
    
    def batch_update_status(self, paths: list) -> Dict[str, GitStatus]:
        """Update status for multiple files at once."""
        if not self._is_git_repo:
            return {str(p): GitStatus(GitStatus.STATUS_CLEAN) for p in paths}
        
        results = {}
        
        try:
            # Get git status for all files
            rel_paths = []
            for path in paths:
                try:
                    rel_path = path.relative_to(self._git_root)
                    rel_paths.append(str(rel_path).replace("\\", "/"))
                except ValueError:
                    # Path not under git root
                    results[str(path.resolve())] = GitStatus(GitStatus.STATUS_CLEAN)
            
            if not rel_paths:
                return results
            
            # Call git status once for all files
            process = QProcess()
            process.setProcessChannelMode(QProcess.MergedChannels)
            process.start("git", ["status", "--porcelain"] + rel_paths)
            process.waitForFinished()
            
            output = process.readAllStandardOutput().data().decode('utf-8')
            
            # Parse output
            status_map = {}
            for line in output.strip().split('\n'):
                if not line or len(line) < 2:
                    continue
                    
                file_path = line[3:] if len(line) > 3 else ""
                if file_path:
                    staged_code = line[0]
                    unstaged_code = line[1]
                    status = self._parse_status_codes(staged_code, unstaged_code)
                    status_map[file_path] = status
            
            # Map back to full paths
            for path in paths:
                try:
                    rel_path = str(path.relative_to(self._git_root).replace("\\", "/"))
                    results[str(path.resolve())] = status_map.get(rel_path, GitStatus(GitStatus.STATUS_CLEAN))
                except ValueError:
                    results[str(path.resolve())] = GitStatus(GitStatus.STATUS_CLEAN)
            
            # Update cache
            self._status_cache.update(results)
            self.status_batch_updated.emit(results)
            
        except Exception as e:
            logger.error(f"Failed to batch update git status: {e}")
        
        return results
    
    def clear_cache(self):
        """Clear the status cache."""
        self._status_cache.clear()
    
    def invalidate_path(self, path: Path):
        """Invalidate status for a specific path."""
        path_str = str(path.resolve())
        if path_str in self._status_cache:
            del self._status_cache[path_str]
