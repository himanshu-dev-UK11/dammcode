"""
change_applier.py — Safe file modification and application.

Applies approved patches to files with support for:
  - Atomic operations (all-or-nothing)
  - Progress updates via EventBus
  - Failure recovery
  - Git checkpoint creation

This is the final step before changes are committed to the project.
"""

from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from core.logger import setup_logger
from core.event_bus import EventBus

from ai.editing.change_request import ChangeRequest, ChangeStatus
from ai.editing.change_set import ChangeSet, ChangeOperation, OperationType, Hunk
from ai.editing.rollback_manager import RollbackManager


logger = setup_logger(__name__)


@dataclass
class ApplyResult:
    """
    Result of applying a change set.

    Attributes:
        success:        True if all operations succeeded.
        applied_count:  Number of operations successfully applied.
        failed_count:   Number of operations that failed.
        errors:         List of error messages.
        rollback_id:    ID of the rollback point created.
    """
    success:       bool
    applied_count: int
    failed_count:  int
    errors:        List[str]
    rollback_id:   Optional[str]


class ChangeApplier:
    """
    Applies approved patches to files safely.

    Features:
      - Creates rollback points before any changes
      - Processes operations in dependency order
      - Supports atomic operations (rollback on failure)
      - Publishes progress events to EventBus

    Usage:
        applier = ChangeApplier(event_bus, project_root)
        result = applier.apply(change_set, request)
    """

    def __init__(
        self,
        event_bus: EventBus,
        project_root: str,
    ) -> None:
        self.event_bus = event_bus
        self._root = Path(project_root)
        self._rollback_manager = RollbackManager(project_root)

        logger.debug(f"ChangeApplier initialized (root='{self._root.name}').")

    # ── Public API ─────────────────────────────────────────────────────────

    def apply(
        self,
        change_set: ChangeSet,
        request: ChangeRequest,
    ) -> ApplyResult:
        """
        Apply all operations in the change set.

        Args:
            change_set: The ChangeSet with all proposed operations.
            request:    The ChangeRequest being applied.

        Returns:
            ApplyResult with success/failure info.
        """
        if change_set.is_empty():
            logger.warning("ChangeApplier: empty change set — nothing to apply.")
            return ApplyResult(
                success=True,
                applied_count=0,
                failed_count=0,
                errors=[],
                rollback_id=None,
            )

        # Create rollback checkpoint
        rollback_id = self._rollback_manager.create_checkpoint(
            change_set=change_set,
            request_id=request.request_id,
            user_prompt=request.user_prompt,
        )
        request = request.with_rollback_id(rollback_id)

        logger.info(
            f"ChangeApplier: applying {len(change_set.operations)} operations, "
            f"rollback_id={rollback_id[:8]}..."
        )
        self._publish_progress(request, 0, "Creating rollback checkpoint")

        # Sort operations by type and dependencies
        operations = self._sort_operations(change_set.operations)

        # Apply operations
        applied = 0
        failed = 0
        errors: List[str] = []

        for i, op in enumerate(operations):
            try:
                self._apply_operation(op)
                applied += 1
                self._publish_progress(request, int((i + 1) / len(operations) * 100))
            except Exception as exc:
                failed += 1
                errors.append(f"{op.op_type.value.upper()} {op.source_path}: {exc}")
                logger.error(f"ChangeApplier: failed to apply {op.op_type.value} for {op.source_path}: {exc}")

                # Attempt rollback on first failure
                if failed == 1:
                    logger.warning("ChangeApplier: failure detected, initiating rollback.")
                    self._rollback_manager.rollback(rollback_id)
                    return ApplyResult(
                        success=False,
                        applied_count=applied,
                        failed_count=failed,
                        errors=errors,
                        rollback_id=rollback_id,
                    )

        # Update request status
        request = request.with_status(ChangeStatus.APPLIED)

        # Publish completion
        self._publish_progress(request, 100, "Application complete")
        self._publish_complete(request, change_set, applied, failed, errors)

        return ApplyResult(
            success=failed == 0,
            applied_count=applied,
            failed_count=failed,
            errors=errors,
            rollback_id=rollback_id,
        )

    # ── Operation application ────────────────────────────────────────────────

    def _apply_operation(self, op: ChangeOperation) -> None:
        """Apply a single operation."""
        if op.op_type == OperationType.CREATE:
            self._apply_create(op)
        elif op.op_type == OperationType.DELETE:
            self._apply_delete(op)
        elif op.op_type == OperationType.MODIFY:
            self._apply_modify(op)
        elif op.op_type == OperationType.RENAME:
            self._apply_rename(op)
        elif op.op_type == OperationType.MOVE:
            self._apply_move(op)

    def _apply_create(self, op: ChangeOperation) -> None:
        """Create a new file."""
        path = self._root / op.source_path
        path.parent.mkdir(parents=True, exist_ok=True)
        content = op.content or ""
        path.write_text(content, encoding="utf-8")
        logger.info(f"ChangeApplier: created '{op.source_path}' ({len(content)} chars)")

    def _apply_delete(self, op: ChangeOperation) -> None:
        """Delete a file."""
        path = self._root / op.source_path
        if path.exists():
            path.unlink()
            logger.info(f"ChangeApplier: deleted '{op.source_path}'")
        else:
            logger.warning(f"ChangeApplier: file not found for deletion: {op.source_path}")

    def _apply_modify(self, op: ChangeOperation) -> None:
        """Modify a file using hunks."""
        path = self._root / op.source_path
        content = path.read_text(encoding="utf-8")

        # Apply each hunk
        new_content = content
        for hunk in op.hunks:
            new_content = self._apply_hunk(new_content, hunk)

        path.write_text(new_content, encoding="utf-8")
        logger.info(
            f"ChangeApplier: modified '{op.source_path}', "
            f"{len(op.hunks)} hunks applied"
        )

    def _apply_rename(self, op: ChangeOperation) -> None:
        """Rename a file."""
        src = self._root / op.source_path
        dst = self._root / op.dest_path
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
            logger.info(f"ChangeApplier: renamed '{op.source_path}' → '{op.dest_path}'")
        else:
            raise FileNotFoundError(f"Source file not found: {op.source_path}")

    def _apply_move(self, op: ChangeOperation) -> None:
        """Move a file to a new location."""
        self._apply_rename(op)

    # ── Hunk application ─────────────────────────────────────────────────────

    def _apply_hunk(self, content: str, hunk: Hunk) -> str:
        """Apply a single hunk to content."""
        lines = content.splitlines(keepends=True)

        # Remove old lines
        start_idx = hunk.old_start - 1
        end_idx = start_idx + hunk.old_lines

        if start_idx < 0:
            start_idx = 0
        if end_idx > len(lines):
            end_idx = len(lines)

        if start_idx <= end_idx:
            del lines[start_idx:end_idx]

        # Insert new lines
        new_lines = hunk.new_text.splitlines(keepends=True)
        if new_lines:
            lines[start_idx:start_idx] = new_lines

        return "".join(lines)

    # ── Utilities ────────────────────────────────────────────────────────────

    def _sort_operations(self, operations: List[ChangeOperation]) -> List[ChangeOperation]:
        """
        Sort operations to handle dependencies correctly.

        Order: Creates → Deletes → Modifies → Renames → Moves
        """
        by_type: Dict[OperationType, List[ChangeOperation]] = {}

        for op in operations:
            if op.op_type not in by_type:
                by_type[op.op_type] = []
            by_type[op.op_type].append(op)

        # Apply order: create first, then deletes, then modifies
        order = [OperationType.CREATE, OperationType.DELETE, OperationType.MODIFY,
                 OperationType.RENAME, OperationType.MOVE]

        result = []
        for op_type in order:
            result.extend(by_type.get(op_type, []))

        return result

    def _publish_progress(
        self,
        request: ChangeRequest,
        percent: int,
        message: str = "",
    ) -> None:
        """Publish progress event to EventBus."""
        self.event_bus.publish("edit_progress", {
            "request_id": request.request_id,
            "percent": percent,
            "message": message,
            "status": request.status.value,
        })

    def _publish_complete(
        self,
        request: ChangeRequest,
        change_set: ChangeSet,
        applied: int,
        failed: int,
        errors: List[str],
    ) -> None:
        """Publish completion event to EventBus."""
        self.event_bus.publish("edit_complete", {
            "request_id": request.request_id,
            "success": failed == 0,
            "applied": applied,
            "failed": failed,
            "errors": errors,
            "files": change_set.files,
            "rollback_id": request.rollback_id,
        })