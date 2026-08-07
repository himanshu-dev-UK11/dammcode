"""
diff_generator.py — Professional diff generation from change requests.

Generates human-readable diffs that show exactly what changed:
- Line-by-line comparison
- Added/removed/modified markers
- Line numbers for easy reference
- File summary statistics

The output is designed to be displayed in a UI preview window
before the user approves changes.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from core.logger import setup_logger

from ai.editing.change_request import ChangeRequest, ChangeStatus
from ai.editing.change_set import ChangeSet, ChangeOperation, OperationType, Hunk

logger = setup_logger(__name__)


@dataclass
class DiffResult:
    """
    Complete diff output for a single file.

    Attributes:
        file_path:     Absolute path to the file.
        op_type:       Type of operation (create, delete, modify).
        old_content:   Original file content (None for create).
        new_content:   New file content (None for delete).
        hunks:         List of individual change hunks.
        summary:       File-level statistics.
    """
    file_path:     str
    op_type:       OperationType
    old_content:   str | None
    new_content:   str | None
    hunks:         List[Dict[str, Any]]
    summary:       Dict[str, int]


@dataclass
class DiffSummary:
    """
    Summary of all changes across the change set.

    Attributes:
        total_files:     Number of files affected.
        files_created:   Files being created.
        files_deleted:   Files being deleted.
        files_modified:  Files being modified.
        total_hunks:     Total number of change hunks.
        lines_added:     Total lines added.
        lines_removed:   Total lines removed.
    """
    total_files:    int
    files_created:  int
    files_deleted:  int
    files_modified: int
    total_hunks:    int
    lines_added:    int
    lines_removed:  int


class DiffGenerator:
    """
    Generates professional diffs from ChangeRequest objects.

    The generator supports:
      - Text-based file comparison using Python's difflib
      - Line-by-line diff with added/removed markers
      - Summary statistics for UI display

    Usage:
        generator = DiffGenerator()
        diff = generator.generate(request, change_set)
    """

    def __init__(self) -> None:
        logger.debug("DiffGenerator initialized.")

    # ── Public API ─────────────────────────────────────────────────────────

    def generate(
        self,
        request:  ChangeRequest,
        change_set: ChangeSet,
    ) -> List[DiffResult]:
        """
        Generate diff results for all operations in the change set.

        Args:
            request:  The ChangeRequest (original user prompt + AI changes).
            change_set: The ChangeSet with all proposed operations.

        Returns:
            List of DiffResult objects, one per file operation.
        """
        if change_set.is_empty():
            logger.warning("DiffGenerator: empty change set — no diffs generated.")
            return []

        diffs = []
        for op in change_set.operations:
            diff = self._generate_file_diff(op)
            if diff:
                diffs.append(diff)

        logger.info(
            f"DiffGenerator: {len(diffs)} files processed, "
            f"{change_set.total_hunks} hunks generated."
        )
        return diffs

    def generate_summary(self, diffs: List[DiffResult]) -> DiffSummary:
        """
        Create an overall summary from a list of diff results.

        Args:
            diffs: List of DiffResult objects from generate().

        Returns:
            DiffSummary with aggregate statistics.
        """
        files_created = 0
        files_deleted = 0
        files_modified = 0
        total_hunks = 0
        lines_added = 0
        lines_removed = 0

        for diff in diffs:
            if diff.op_type == OperationType.CREATE:
                files_created += 1
                if diff.new_content:
                    lines = diff.new_content.splitlines()
                    lines_added += len(lines)
                    total_hunks += 1
            elif diff.op_type == OperationType.DELETE:
                files_deleted += 1
                if diff.old_content:
                    lines = diff.old_content.splitlines()
                    lines_removed += len(lines)
                    total_hunks += 1
            elif diff.op_type == OperationType.MODIFY:
                files_modified += 1
                total_hunks += len(diff.hunks)
                for hunk in diff.hunks:
                    lines_added += hunk.get("added", 0)
                    lines_removed += hunk.get("removed", 0)

        total_files = files_created + files_deleted + files_modified

        return DiffSummary(
            total_files=total_files,
            files_created=files_created,
            files_deleted=files_deleted,
            files_modified=files_modified,
            total_hunks=total_hunks,
            lines_added=lines_added,
            lines_removed=lines_removed,
        )

    # ── File-level diff generation ──────────────────────────────────────────

    def _generate_file_diff(self, op: ChangeOperation) -> DiffResult | None:
        """Generate diff for a single operation."""
        if op.op_type == OperationType.CREATE:
            return self._generate_create_diff(op)
        elif op.op_type == OperationType.DELETE:
            return self._generate_delete_diff(op)
        elif op.op_type == OperationType.MODIFY:
            return self._generate_modify_diff(op)
        else:
            # Rename and move are logical — show as delete + create
            return None

    def _generate_create_diff(self, op: ChangeOperation) -> DiffResult:
        """Generate diff for a file creation operation."""
        path = op.source_path
        new_content = op.content or ""

        hunks = []
        if new_content:
            lines = new_content.splitlines()
            hunks.append({
                "type": "create",
                "added": len(lines),
                "removed": 0,
                "content": new_content[:500] + ("..." if len(new_content) > 500 else ""),
            })

        summary = {
            "lines_added": len(new_content.splitlines()),
            "lines_removed": 0,
            "file_size": len(new_content),
        }

        return DiffResult(
            file_path=path,
            op_type=op.op_type,
            old_content=None,
            new_content=new_content,
            hunks=hunks,
            summary=summary,
        )

    def _generate_delete_diff(self, op: ChangeOperation) -> DiffResult:
        """Generate diff for a file deletion operation."""
        path = op.source_path
        old_content = self._read_file(path)

        hunks = []
        if old_content:
            lines = old_content.splitlines()
            hunks.append({
                "type": "delete",
                "added": 0,
                "removed": len(lines),
                "content": old_content[:500] + ("..." if len(old_content) > 500 else ""),
            })

        summary = {
            "lines_added": 0,
            "lines_removed": len(old_content.splitlines()) if old_content else 0,
            "file_size": len(old_content) if old_content else 0,
        }

        return DiffResult(
            file_path=path,
            op_type=op.op_type,
            old_content=old_content,
            new_content=None,
            hunks=hunks,
            summary=summary,
        )

    def _generate_modify_diff(self, op: ChangeOperation) -> DiffResult:
        """Generate diff for a file modification operation."""
        path = op.source_path
        old_content = self._read_file(path)
        new_content = self._apply_hunks(old_content, op.hunks)

        if old_content is None:
            logger.warning(f"DiffGenerator: source file not found: {path}")
            return None

        # Generate unified diff
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff_lines = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{Path(path).name}",
            tofile=f"b/{Path(path).name}",
            lineterm="",
        ))

        # Parse diff into structured hunks
        hunks = self._parse_unified_diff(diff_lines, old_content, new_content)

        summary = {
            "lines_added": sum(h.get("added", 0) for h in hunks),
            "lines_removed": sum(h.get("removed", 0) for h in hunks),
            "file_size": len(new_content),
        }

        return DiffResult(
            file_path=path,
            op_type=op.op_type,
            old_content=old_content,
            new_content=new_content,
            hunks=hunks,
            summary=summary,
        )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _read_file(self, path: str) -> str | None:
        """Read file content, return None if not found."""
        try:
            return Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            logger.debug(f"DiffGenerator: cannot read '{path}': {exc}")
            return None

    def _apply_hunks(self, content: str, hunks: List[Hunk]) -> str:
        """Apply hunks to content and return modified content."""
        if not hunks:
            return content

        lines = content.splitlines(keepends=True)
        result = lines.copy()

        # Process hunks in reverse order to maintain line indices
        for hunk in reversed(hunks):
            # Remove old lines
            if hunk.old_lines > 0:
                del result[hunk.old_start - 1:hunk.old_start - 1 + hunk.old_lines]

            # Insert new lines
            new_lines = hunk.new_text.splitlines(keepends=True)
            if new_lines or hunk.new_lines > 0:
                result[hunk.old_start - 1:hunk.old_start - 1] = new_lines

        return "".join(result)

    def _parse_unified_diff(
        self,
        diff_lines: List[str],
        old_content: str,
        new_content: str,
    ) -> List[Dict[str, Any]]:
        """
        Parse unified diff lines into structured hunks.

        Returns a list of dicts with:
          - added:   lines added count
          - removed: lines removed count
          - context: preview of the change
        """
        hunks = []
        current_hunk = None

        for line in diff_lines:
            if line.startswith("@@"):
                # New hunk header
                if current_hunk:
                    hunks.append(current_hunk)

                # Parse @@ -old_start,old_lines +new_start,new_lines @@
                import re
                match = re.match(r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@", line)
                if match:
                    current_hunk = {
                        "old_start": int(match.group(1)),
                        "old_lines": int(match.group(2)),
                        "new_start": int(match.group(3)),
                        "new_lines": int(match.group(4)),
                        "added": 0,
                        "removed": 0,
                        "context": [],
                    }
            elif current_hunk:
                if line.startswith("+"):
                    current_hunk["added"] += 1
                    current_hunk["context"].append(("add", line[1:]))
                elif line.startswith("-"):
                    current_hunk["removed"] += 1
                    current_hunk["context"].append(("remove", line[1:]))
                elif line.startswith(" "):
                    current_hunk["context"].append(("context", line[1:]))

        if current_hunk:
            hunks.append(current_hunk)

        return hunks