"""
patch_validator.py — Verification and safety checks for patches.

Validates that patches are safe to apply by checking for:
  - Syntax corruption (Python syntax validation)
  - Malformed patches (proper line ranges)
  - Duplicate edits (same section modified twice)
  - Overlapping edits (conflicting changes)

This is the final safety gate before showing changes to the user.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Any

from core.logger import setup_logger

from ai.editing.change_set import ChangeSet, ChangeOperation, Hunk
from ai.editing.patch_builder import Patch, PatchSet


logger = setup_logger(__name__)


@dataclass
class ValidationResult:
    """
    Result of validating a patch or change set.

    Attributes:
        is_valid:     True if all checks passed.
        warnings:     Non-blocking issues to show to user.
        errors:       Blocking issues that prevent application.
        safe_to_apply: True if patch can be safely applied.
    """
    is_valid:       bool
    warnings:       List[str]
    errors:         List[str]
    safe_to_apply:  bool


class PatchValidator:
    """
    Validates patches for safety and correctness.

    Performs multiple validation passes:
      1. Patch syntax validation (line ranges, etc.)
      2. Duplicate edit detection (same file, overlapping hunks)
      3. Overlap detection (conflicting changes)
      4. Syntax validation (for supported languages)
    """

    def __init__(self) -> None:
        logger.debug("PatchValidator initialized.")
        self._supported_syntax_langs = {".py", ".js", ".ts", ".jsx", ".tsx"}

    # ── Public API ─────────────────────────────────────────────────────────

    def validate_change_set(
        self,
        change_set: ChangeSet,
        project_root: str,
    ) -> ValidationResult:
        """
        Validate an entire change set.

        Args:
            change_set:  The ChangeSet to validate.
            project_root: Project directory path.

        Returns:
            ValidationResult with all findings.
        """
        warnings: List[str] = []
        errors: List[str] = []

        # Pass 1: Validate individual hunks
        for op in change_set.operations:
            hunk_results = self._validate_hunks(op.hunks, op.source_path)
            warnings.extend(hunk_results["warnings"])
            errors.extend(hunk_results["errors"])

        # Pass 2: Check for duplicate edits
        dup_results = self._check_duplicates(change_set)
        warnings.extend(dup_results["warnings"])
        errors.extend(dup_results["errors"])

        # Pass 3: Check for overlapping edits
        overlap_results = self._check_overlaps(change_set, project_root)
        warnings.extend(overlap_results["warnings"])
        errors.extend(overlap_results["errors"])

        # Pass 4: Syntax validation (for modified files)
        syntax_results = self._validate_syntax(change_set, project_root)
        warnings.extend(syntax_results["warnings"])
        errors.extend(syntax_results["errors"])

        is_valid = len(errors) == 0
        safe_to_apply = is_valid and len(warnings) < 3

        result = ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            safe_to_apply=safe_to_apply,
        )

        if is_valid:
            logger.info(
                f"PatchValidator: {len(change_set.operations)} operations "
                f"validated — safe to apply."
            )
        else:
            logger.warning(
                f"PatchValidator: {len(errors)} errors, {len(warnings)} warnings."
            )

        return result

    # ── Validation passes ───────────────────────────────────────────────────

    def _validate_hunks(
        self,
        hunks: List[Hunk],
        file_path: str,
    ) -> Dict[str, List[str]]:
        """Validate individual hunks for correctness."""
        warnings: List[str] = []
        errors: List[str] = []

        for i, hunk in enumerate(hunks):
            # Check line ranges are positive
            if hunk.old_start < 1:
                errors.append(f"Hunk {i+1}: old_start must be >= 1")
            if hunk.new_start < 1:
                errors.append(f"Hunk {i+1}: new_start must be >= 1")

            # Check line counts are non-negative
            if hunk.old_lines < 0:
                errors.append(f"Hunk {i+1}: old_lines must be >= 0")
            if hunk.new_lines < 0:
                errors.append(f"Hunk {i+1}: new_lines must be >= 0")

            # Check old and new content have same line count if specified
            if hunk.old_text and hunk.old_lines > 0:
                old_line_count = len(hunk.old_text.splitlines())
                if old_line_count != hunk.old_lines:
                    warnings.append(
                        f"Hunk {i+1}: old_lines count mismatch "
                        f"(expected {hunk.old_lines}, got {old_line_count})"
                    )

            if hunk.new_text and hunk.new_lines > 0:
                new_line_count = len(hunk.new_text.splitlines())
                if new_line_count != hunk.new_lines:
                    warnings.append(
                        f"Hunk {i+1}: new_lines count mismatch "
                        f"(expected {hunk.new_lines}, got {new_line_count})"
                    )

        return {"warnings": warnings, "errors": errors}

    def _check_duplicates(
        self,
        change_set: ChangeSet,
    ) -> Dict[str, List[str]]:
        """Check for duplicate edits of the same file."""
        warnings: List[str] = []
        errors: List[str] = []

        # Group operations by file
        file_ops: Dict[str, List[ChangeOperation]] = {}
        for op in change_set.operations:
            if op.op_type != OperationType.MODIFY:
                continue
            if op.source_path not in file_ops:
                file_ops[op.source_path] = []
            file_ops[op.source_path].append(op)

        # Check for multiple modifications to same file
        for path, ops in file_ops.items():
            if len(ops) > 1:
                warnings.append(
                    f"Multiple modifications to '{path}' — "
                    f"{len(ops)} operations detected"
                )

        return {"warnings": warnings, "errors": errors}

    def _check_overlaps(
        self,
        change_set: ChangeSet,
        project_root: str,
    ) -> Dict[str, List[str]]:
        """Check for overlapping changes within the same file."""
        warnings: List[str] = []
        errors: List[str] = []

        # Group hunks by file
        file_hunks: Dict[str, List[Tuple[int, int, Hunk]]] = {}
        for op in change_set.operations:
            if op.op_type != OperationType.MODIFY:
                continue

            # Build line ranges for each hunk
            ranges = []
            current_line = 1
            for hunk in op.hunks:
                old_end = hunk.old_start + hunk.old_lines - 1
                ranges.append((hunk.old_start, old_end, hunk))
                current_line = old_end + 1

            file_hunks[op.source_path] = ranges

        # Check for overlaps within each file
        for path, ranges in file_hunks.items():
            if len(ranges) < 2:
                continue

            for i in range(len(ranges)):
                for j in range(i + 1, len(ranges)):
                    start1, end1, _ = ranges[i]
                    start2, end2, _ = ranges[j]

                    # Check if ranges overlap
                    if start1 <= end2 and start2 <= end1:
                        warnings.append(
                            f"Overlapping changes in '{path}' at "
                            f"lines {start1}-{end1} and {start2}-{end2}"
                        )

        return {"warnings": warnings, "errors": errors}

    def _validate_syntax(
        self,
        change_set: ChangeSet,
        project_root: str,
    ) -> Dict[str, List[str]]:
        """Validate syntax for modified Python files."""
        warnings: List[str] = []
        errors: List[str] = []

        for op in change_set.operations:
            if op.op_type != OperationType.MODIFY:
                continue

            ext = Path(op.source_path).suffix.lower()
            if ext not in self._supported_syntax_langs:
                continue

            # Read current file content
            path = Path(project_root) / op.source_path
            try:
                original = path.read_text(encoding="utf-8")
            except OSError:
                warnings.append(
                    f"Cannot read '{op.source_path}' for syntax validation"
                )
                continue

            # Apply hunks to get new content
            new_content = original
            for hunk in op.hunks:
                new_content = self._apply_hunk(new_content, hunk)

            # Validate syntax
            try:
                if ext == ".py":
                    ast.parse(new_content, filename=op.source_path)
            except SyntaxError as e:
                errors.append(
                    f"Syntax error in '{op.source_path}' at line {e.lineno}: "
                    f"{e.msg}"
                )

        return {"warnings": warnings, "errors": errors}

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _apply_hunk(self, content: str, hunk: Hunk) -> str:
        """Apply a single hunk to content."""
        lines = content.splitlines(keepends=True)

        start_idx = hunk.old_start - 1
        end_idx = start_idx + hunk.old_lines

        if end_idx > len(lines):
            end_idx = len(lines)
        if start_idx > len(lines):
            start_idx = len(lines)

        del lines[start_idx:end_idx]

        new_lines = hunk.new_text.splitlines(keepends=True)
        if new_lines:
            lines[start_idx:start_idx] = new_lines

        return "".join(lines)


def validate_change_set(
    change_set: ChangeSet,
    project_root: str,
) -> ValidationResult:
    """
    Convenience function to validate a change set.

    Args:
        change_set:  The ChangeSet to validate.
        project_root: Project directory path.

    Returns:
        ValidationResult with validation results.
    """
    validator = PatchValidator()
    return validator.validate_change_set(change_set, project_root)