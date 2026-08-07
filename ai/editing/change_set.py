"""
change_set.py — Collection of file modification operations.

Represents all proposed changes as a set of atomic operations:
- Create new files
- Delete files
- Rename/move files
- Modify files (with specific line ranges)

This is the intermediate format between diff generation and
patch application. It's model-agnostic and serialization-ready.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any


class OperationType(Enum):
    """Types of file operations in a change set."""
    CREATE = "create"
    DELETE = "delete"
    RENAME = "rename"
    MOVE = "move"
    MODIFY = "modify"


@dataclass(frozen=True)
class Hunk:
    """
    A single change hunk for a modified file.

    For modified files, we support multiple hunks to represent
    disjoint changes within the same file.

    Attributes:
        old_start: Starting line number in original file (1-based).
        old_lines: Number of lines in original section.
        new_start: Starting line in new version.
        new_lines: Number of lines in new version.
        old_text:  Original text (before change).
        new_text:  New text (after change).
        context:   Context lines around the change.
    """
    old_start:  int
    old_lines:  int
    new_start:  int
    new_lines:  int
    old_text:   str
    new_text:   str
    context:    List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChangeOperation:
    """
    One atomic operation in the change set.

    Attributes:
        op_type:     Type of operation (create, delete, rename, move, modify).
        source_path: Source file path (for rename/move/modify/delete).
        dest_path:   Destination file path (for create/rename/move).
        hunks:       List of Hunk objects (for MODIFY operations).
        content:     Full content for CREATE operations.
        reason:      Human-readable explanation.
    """
    op_type:    OperationType
    source_path: str
    dest_path:  Optional[str] = None
    hunks:      List[Hunk] = field(default_factory=list)
    content:    Optional[str] = None
    reason:     str = ""

    @classmethod
    def create_file(
        cls,
        path:   str,
        content: str,
        reason: str = "",
    ) -> ChangeOperation:
        """Create a CREATE operation."""
        return cls(
            op_type=OperationType.CREATE,
            source_path=path,
            dest_path=path,
            content=content,
            reason=reason,
        )

    @classmethod
    def delete_file(
        cls,
        path:   str,
        reason: str = "",
    ) -> ChangeOperation:
        """Create a DELETE operation."""
        return cls(
            op_type=OperationType.DELETE,
            source_path=path,
            reason=reason,
        )

    @classmethod
    def rename_file(
        cls,
        source: str,
        dest:   str,
        reason: str = "",
    ) -> ChangeOperation:
        """Create a RENAME operation."""
        return cls(
            op_type=OperationType.RENAME,
            source_path=source,
            dest_path=dest,
            reason=reason,
        )

    @classmethod
    def move_file(
        cls,
        source: str,
        dest:   str,
        reason: str = "",
    ) -> ChangeOperation:
        """Create a MOVE operation."""
        return cls(
            op_type=OperationType.MOVE,
            source_path=source,
            dest_path=dest,
            reason=reason,
        )

    @classmethod
    def modify_file(
        cls,
        path:   str,
        hunks:  List[Hunk],
        reason: str = "",
    ) -> ChangeOperation:
        """Create a MODIFY operation."""
        return cls(
            op_type=OperationType.MODIFY,
            source_path=path,
            hunks=hunks,
            reason=reason,
        )


@dataclass(frozen=True)
class ChangeSet:
    """
    Collection of all proposed file modifications.

    This is the output of DiffGenerator and the input to
    PatchBuilder. It's immutable and can be safely shared
    across threads.

    Attributes:
        operations: List of ChangeOperation objects.
        files:      Unique set of all affected file paths.
        total_hunks: Total number of hunks across all operations.
    """
    operations: List[ChangeOperation]
    files:      List[str]
    total_hunks: int

    @classmethod
    def from_operations(cls, operations: List[ChangeOperation]) -> ChangeSet:
        """Create a ChangeSet from a list of operations."""
        all_files = set()
        total_hunks = 0

        for op in operations:
            all_files.add(op.source_path)
            if op.dest_path:
                all_files.add(op.dest_path)
            total_hunks += len(op.hunks)

        return cls(
            operations=operations,
            files=sorted(all_files),
            total_hunks=total_hunks,
        )

    def is_empty(self) -> bool:
        """Return True if no operations are defined."""
        return len(self.operations) == 0

    def get_operations_by_type(self, op_type: OperationType) -> List[ChangeOperation]:
        """Return all operations of a specific type."""
        return [op for op in self.operations if op.op_type == op_type]

    def get_changes_by_file(self, path: str) -> List[ChangeOperation]:
        """Return all operations affecting a specific file."""
        path = str(Path(path))
        return [
            op for op in self.operations
            if op.source_path == path or op.dest_path == path
        ]