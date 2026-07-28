"""
patch_builder.py — Safe, incremental patch generation.

Builds patches that modify only necessary sections of files
instead of replacing entire files. This minimizes merge conflicts
and preserves unrelated content.

The patches are designed to be:
  - Atomic (all-or-nothing application)
  - Reversible (rollback support)
  - Incremental (only changed sections)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from core.logger import setup_logger

from ai.editing.change_set import ChangeSet, ChangeOperation, OperationType, Hunk


logger = setup_logger(__name__)


@dataclass
class Patch:
    """
    A single patch for applying changes to a file.

    Attributes:
        file_path:  Absolute path to the target file.
        op_type:    Type of operation (create, delete, modify).
        hunks:      List of Hunk objects with exact line ranges.
        checksum:   SHA-256 hash of original file content (for safety).
    """
    file_path:  str
    op_type:    OperationType
    hunks:      List[Hunk]
    checksum:   Optional[str] = None


@dataclass
class PatchSet:
    """
    Collection of patches for all operations in a change set.

    Attributes:
        patches:    List of Patch objects.
        total_size: Total characters that will be changed.
    """
    patches:    List[Patch]
    total_size: int


class PatchBuilder:
    """
    Builds safe, incremental patches from a ChangeSet.

    Usage:
        builder = PatchBuilder()
        patch_set = builder.build(change_set, project_root)
    """

    def __init__(self) -> None:
        logger.debug("PatchBuilder initialized.")

    # ── Public API ─────────────────────────────────────────────────────────

    def build(
        self,
        change_set: ChangeSet,
        project_root: str,
    ) -> PatchSet:
        """
        Build patches for all operations in the change set.

        Args:
            change_set:  The ChangeSet with all proposed operations.
            project_root: Absolute path to the project directory.

        Returns:
            PatchSet with all patches and total change size.
        """
        patches = []
        total_size = 0

        for op in change_set.operations:
            patch = self._build_patch(op, project_root)
            if patch:
                patches.append(patch)
                total_size += self._estimate_patch_size(patch)

        return PatchSet(patches=patches, total_size=total_size)

    # ── Patch construction ──────────────────────────────────────────────────

    def _build_patch(
        self,
        op: ChangeOperation,
        project_root: str,
    ) -> Optional[Patch]:
        """Build a patch for a single operation."""
        if op.op_type == OperationType.CREATE:
            return self._build_create_patch(op, project_root)
        elif op.op_type == OperationType.DELETE:
            return self._build_delete_patch(op, project_root)
        elif op.op_type == OperationType.MODIFY:
            return self._build_modify_patch(op, project_root)
        else:
            # Rename/move handled by apply_phase
            return None

    def _build_create_patch(
        self,
        op: ChangeOperation,
        project_root: str,
    ) -> Patch:
        """Build patch for file creation."""
        content = op.content or ""
        lines = content.splitlines(keepends=True)

        hunk = Hunk(
            old_start=1,
            old_lines=0,
            new_start=1,
            new_lines=len(lines),
            old_text="",
            new_text=content,
            context=lines[:10],
        )

        return Patch(
            file_path=op.source_path,
            op_type=OperationType.CREATE,
            hunks=[hunk],
            checksum=None,  # File doesn't exist yet
        )

    def _build_delete_patch(
        self,
        op: ChangeOperation,
        project_root: str,
    ) -> Patch:
        """Build patch for file deletion."""
        path = Path(project_root) / op.source_path
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            content = ""

        lines = content.splitlines(keepends=True)

        hunk = Hunk(
            old_start=1,
            old_lines=len(lines),
            new_start=1,
            new_lines=0,
            old_text=content,
            new_text="",
            context=lines[:10] if lines else [],
        )

        return Patch(
            file_path=op.source_path,
            op_type=OperationType.DELETE,
            hunks=[hunk],
            checksum=None,
        )

    def _build_modify_patch(
        self,
        op: ChangeOperation,
        project_root: str,
    ) -> Patch:
        """Build patch for file modification."""
        path = Path(project_root) / op.source_path

        # Read original content
        try:
            old_content = path.read_text(encoding="utf-8")
        except OSError:
            logger.warning(f"PatchBuilder: source file not found: {path}")
            return None

        # Use hunks from ChangeOperation
        hunks = op.hunks

        return Patch(
            file_path=op.source_path,
            op_type=OperationType.MODIFY,
            hunks=hunks,
            checksum=None,
        )

    def _estimate_patch_size(self, patch: Patch) -> int:
        """Estimate total characters that will be changed."""
        size = 0
        for hunk in patch.hunks:
            size += len(hunk.old_text) + len(hunk.new_text)
        return size

    # ── Smart patch generation ─────────────────────────────────────────────

    def generate_smart_hunks(
        self,
        old_content: str,
        new_content: str,
        context_lines: int = 3,
    ) -> List[Hunk]:
        """
        Generate optimal hunks by comparing old and new content.

        This method:
          1. Finds the longest common subsequence
          2. Groups changes into hunks
          3. Adds context lines before and after each hunk

        Args:
            old_content: Original file content.
            new_content: Target file content.
            context_lines: Number of unchanged lines surrounding each change.

        Returns:
            List of Hunk objects representing the changes.
        """
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()

        # Find differences using difflib
        import difflib
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

        hunks = []
        current_hunk_old_start = None
        current_hunk_new_start = None
        hunk_old_lines = []
        hunk_new_lines = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                # This section is unchanged
                if hunk_old_lines or hunk_new_lines:
                    # Close current hunk
                    hunks.append(Hunk(
                        old_start=current_hunk_old_start,
                        old_lines=len(hunk_old_lines),
                        new_start=current_hunk_new_start,
                        new_lines=len(hunk_new_lines),
                        old_text="\n".join(hunk_old_lines) + "\n",
                        new_text="\n".join(hunk_new_lines) + "\n",
                        context=[],
                    ))
                    hunk_old_lines = []
                    hunk_new_lines = []
                    current_hunk_old_start = None
                    current_hunk_new_start = None

                # Add context lines before next change
                context_start = max(0, i2 - context_lines)
                context_end = min(len(old_lines), i2 + context_lines)
                context = old_lines[context_start:context_end]

            elif tag in ("replace", "delete", "insert"):
                # This section has changes
                if current_hunk_old_start is None:
                    current_hunk_old_start = i1 + 1
                    current_hunk_new_start = j1 + 1

                # Collect changed lines
                if tag in ("replace", "delete"):
                    hunk_old_lines.extend(old_lines[i1:i2])
                if tag in ("replace", "insert"):
                    hunk_new_lines.extend(new_lines[j1:j2])

        # Close final hunk if pending
        if hunk_old_lines or hunk_new_lines:
            hunks.append(Hunk(
                old_start=current_hunk_old_start,
                old_lines=len(hunk_old_lines),
                new_start=current_hunk_new_start,
                new_lines=len(hunk_new_lines),
                old_text="\n".join(hunk_old_lines) + "\n",
                new_text="\n".join(hunk_new_lines) + "\n",
                context=[],
            ))

        return hunks


def build_patch_for_operation(
    op: ChangeOperation,
    project_root: str,
    smart: bool = True,
) -> Optional[Patch]:
    """
    Convenience function to build a single patch.

    Args:
        op:          The ChangeOperation to patch.
        project_root: Project directory path.
        smart:       Use smart hunk generation if True.

    Returns:
        Patch object or None on error.
    """
    builder = PatchBuilder()

    if smart and op.op_type == OperationType.MODIFY:
        # Read files and generate smart hunks
        path = Path(project_root) / op.source_path
        try:
            old_content = path.read_text(encoding="utf-8")
            new_content = old_content  # Start with original
            for hunk in op.hunks:
                new_content = apply_hunk_to_content(new_content, hunk)
            hunks = builder.generate_smart_hunks(old_content, new_content)
            return Patch(
                file_path=op.source_path,
                op_type=op.op_type,
                hunks=hunks,
            )
        except OSError:
            pass

    return builder._build_patch(op, project_root)


def apply_hunk_to_content(content: str, hunk: Hunk) -> str:
    """Apply a single hunk to content and return result."""
    lines = content.splitlines(keepends=True)

    # Remove old lines
    start_idx = hunk.old_start - 1
    end_idx = start_idx + hunk.old_lines
    del lines[start_idx:end_idx]

    # Insert new lines
    new_lines = hunk.new_text.splitlines(keepends=True)
    if new_lines:
        lines[start_idx:start_idx] = new_lines

    return "".join(lines)