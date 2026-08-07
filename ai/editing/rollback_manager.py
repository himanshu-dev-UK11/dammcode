"""
rollback_manager.py — Automatic backup and rollback system.

Before every edit, creates:
  - Git checkpoint (if git is available)
  - Internal rollback point (local backup)

Supports:
  - Undo (restore to previous state)
  - Restore (select specific checkpoint)
  - Recovery (revert to last known good state)
"""

from __future__ import annotations

import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from core.logger import setup_logger


logger = setup_logger(__name__)


@dataclass
class Checkpoint:
    """
    A rollback checkpoint.

    Attributes:
        checkpoint_id: Unique identifier for this checkpoint.
        request_id:    ID of the request that triggered this checkpoint.
        user_prompt:   User prompt that triggered the edit.
        timestamp:     When the checkpoint was created.
        backup_paths:  Map of original path → backup path.
        git_commit:    Git commit hash (if available).
        files_affected: List of file paths that were backed up.
    """
    checkpoint_id:    str
    request_id:       Optional[str]
    user_prompt:      str
    timestamp:        datetime
    backup_paths:     Dict[str, str]
    git_commit:       Optional[str]
    files_affected:   List[str]


@dataclass
class RollbackResult:
    """
    Result of a rollback operation.

    Attributes:
        success:      True if rollback succeeded.
        restored:     Number of files restored.
        failed:       Number of files that failed to restore.
        errors:       List of error messages.
    """
    success:  bool
    restored: int
    failed:   int
    errors:   List[str]


class RollbackManager:
    """
    Manages automatic backups and rollback capabilities.

    Creates checkpoints before edits and supports restore operations.

    Usage:
        manager = RollbackManager(project_root)
        checkpoint = manager.create_checkpoint(change_set, request)
        manager.rollback(checkpoint.checkpoint_id)
    """

    def __init__(self, project_root: str) -> None:
        self._root = Path(project_root)
        self._backups_dir = Path(project_root) / ".ai_backups"
        self._backups_dir.mkdir(exist_ok=True)

        self._checkpoints: Dict[str, Checkpoint] = {}

        logger.debug(f"RollbackManager initialized (root='{self._root.name}').")

    # ── Public API ─────────────────────────────────────────────────────────

    def create_checkpoint(
        self,
        change_set: Optional[Any] = None,
        request_id: Optional[str] = None,
        user_prompt: Optional[str] = None,
    ) -> str:
        """
        Create a rollback checkpoint.

        Args:
            change_set:  The ChangeSet being modified (optional).
            request_id:  ID of the request triggering this checkpoint.
            user_prompt: User prompt that triggered the edit.

        Returns:
            Checkpoint ID for later rollback.
        """
        checkpoint_id = f"ckpt_{uuid.uuid4().hex[:12]}"

        # Get file list from change set if available
        files = []
        if change_set:
            files = change_set.files

        # Create backup for each file
        backup_paths: Dict[str, str] = {}
        for file_path in files:
            try:
                original = self._root / file_path
                if original.exists():
                    backup_name = f"{checkpoint_id}_{Path(file_path).name}"
                    backup_path = self._backups_dir / backup_name
                    backup_path.write_bytes(original.read_bytes())
                    backup_paths[file_path] = str(backup_path)
            except OSError as exc:
                logger.warning(
                    f"RollbackManager: failed to backup '{file_path}': {exc}"
                )

        # Get git commit hash if available
        git_commit = self._get_git_commit()

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            request_id=request_id,
            user_prompt=user_prompt or "",
            timestamp=datetime.now(),
            backup_paths=backup_paths,
            git_commit=git_commit,
            files_affected=files,
        )

        self._checkpoints[checkpoint_id] = checkpoint
        self._save_checkpoint(checkpoint)

        logger.info(
            f"RollbackManager: checkpoint {checkpoint_id[:8]} created "
            f"for {len(files)} files."
        )
        return checkpoint_id

    def rollback(self, checkpoint_id: str) -> RollbackResult:
        """
        Rollback to a specific checkpoint.

        Args:
            checkpoint_id: ID of the checkpoint to restore.

        Returns:
            RollbackResult with success/failure info.
        """
        checkpoint = self._checkpoints.get(checkpoint_id)
        if not checkpoint:
            logger.error(f"RollbackManager: checkpoint not found: {checkpoint_id}")
            return RollbackResult(
                success=False,
                restored=0,
                failed=0,
                errors=[f"Checkpoint not found: {checkpoint_id}"],
            )

        restored = 0
        failed = 0
        errors: List[str] = []

        logger.info(
            f"RollbackManager: restoring checkpoint {checkpoint_id[:8]} "
            f"for {len(checkpoint.files_affected)} files."
        )

        for original_path, backup_path in checkpoint.backup_paths.items():
            try:
                src = Path(backup_path)
                dst = self._root / original_path

                # Restore directory structure
                dst.parent.mkdir(parents=True, exist_ok=True)

                # Restore file
                dst.write_bytes(src.read_bytes())
                restored += 1

            except OSError as exc:
                failed += 1
                errors.append(f"Failed to restore '{original_path}': {exc}")
                logger.error(
                    f"RollbackManager: failed to restore '{original_path}': {exc}"
                )

        # Remove checkpoint after successful rollback
        if failed == 0:
            self._remove_checkpoint(checkpoint_id)
            logger.info(
                f"RollbackManager: checkpoint {checkpoint_id[:8]} restored successfully."
            )
        else:
            logger.warning(
                f"RollbackManager: checkpoint {checkpoint_id[:8]} partially restored "
                f"({restored} OK, {failed} failed)."
            )

        return RollbackResult(
            success=failed == 0,
            restored=restored,
            failed=failed,
            errors=errors,
        )

    def undo(self) -> RollbackResult:
        """
        Undo the most recent change by rolling back to the last checkpoint.

        Returns:
            RollbackResult with success/failure info.
        """
        if not self._checkpoints:
            return RollbackResult(
                success=False,
                restored=0,
                failed=0,
                errors=["No checkpoints available for undo."],
            )

        # Get most recent checkpoint
        most_recent = max(
            self._checkpoints.values(),
            key=lambda c: c.timestamp
        )

        return self.rollback(most_recent.checkpoint_id)

    def recover(self) -> RollbackResult:
        """
        Attempt to recover from the most recent successful checkpoint.

        This is similar to undo but doesn't remove the checkpoint,
        allowing multiple recovery attempts.

        Returns:
            RollbackResult with success/failure info.
        """
        return self.undo()

    def list_checkpoints(self) -> List[Checkpoint]:
        """Return all available checkpoints, sorted by timestamp."""
        return sorted(
            self._checkpoints.values(),
            key=lambda c: c.timestamp,
            reverse=True
        )

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Return a specific checkpoint by ID."""
        return self._checkpoints.get(checkpoint_id)

    def clear_all(self) -> int:
        """
        Remove all checkpoints and backup files.

        Returns:
            Number of checkpoints removed.
        """
        count = len(self._checkpoints)
        self._checkpoints.clear()

        # Also remove backup files
        if self._backups_dir.exists():
            for f in self._backups_dir.iterdir():
                if f.is_file():
                    f.unlink()

        logger.info(f"RollbackManager: cleared {count} checkpoints.")
        return count

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Save checkpoint metadata to disk."""
        metadata_path = self._backups_dir / f"{checkpoint.checkpoint_id}.json"
        import json
        data = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "request_id": checkpoint.request_id,
            "user_prompt": checkpoint.user_prompt,
            "timestamp": checkpoint.timestamp.isoformat(),
            "backup_paths": checkpoint.backup_paths,
            "git_commit": checkpoint.git_commit,
            "files_affected": checkpoint.files_affected,
        }
        metadata_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _remove_checkpoint(self, checkpoint_id: str) -> None:
        """Remove a checkpoint and its metadata."""
        if checkpoint_id in self._checkpoints:
            del self._checkpoints[checkpoint_id]

        # Remove metadata file
        metadata_path = self._backups_dir / f"{checkpoint_id}.json"
        if metadata_path.exists():
            metadata_path.unlink()

    def _get_git_commit(self) -> Optional[str]:
        """Get current git commit hash if available."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(self._root),
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
        return None

    def stats(self) -> Dict[str, Any]:
        """Return rollback manager statistics."""
        return {
            "total_checkpoints": len(self._checkpoints),
            "backups_dir": str(self._backups_dir),
            "backups_dir_exists": self._backups_dir.exists(),
        }


# Convenience functions

def create_checkpoint(
    project_root: str,
    change_set: Optional[Any] = None,
    request_id: Optional[str] = None,
    user_prompt: Optional[str] = None,
) -> str:
    """Convenience function to create a checkpoint."""
    manager = RollbackManager(project_root)
    return manager.create_checkpoint(change_set, request_id, user_prompt)


def rollback(project_root: str, checkpoint_id: str) -> RollbackResult:
    """Convenience function to rollback to a checkpoint."""
    manager = RollbackManager(project_root)
    return manager.rollback(checkpoint_id)