"""
ai/editing/ — Safe AI Code Editing System (v0.6)

This package provides a complete, model-independent editing pipeline
for AI-generated code changes. Every modification passes through this
system, ensuring safety and undo capability.

Pipeline flow:
  User Request → Planner → Context Engine → Model Manager
    ↓
  Generated Changes → Diff Generator → Preview Window
    ↓
  User Approval → Patch Builder → Validator
    ↓
  Apply Changes → Git Snapshot → Memory Update

Key features:
  - No direct file modifications (all go through this system)
  - Safe incremental patches (not full file replacements)
  - User must approve before changes are applied
  - Automatic rollback points before every edit
  - File locking to prevent concurrent edits
  - Comprehensive edit history for audit and undo

Classes (in order of pipeline):
  ChangeRequest   - Input contract (what AI wants to do)
  ChangeSet       - Collection of operations (output of DiffGenerator)
  DiffGenerator   - Generates diff output for preview
  PatchBuilder    - Builds safe, incremental patches
  PatchValidator  - Validates patches for safety
  ChangePreview   - UI preview window for approval
  ChangeApplier   - Applies approved patches safely
  RollbackManager - Creates checkpoints for undo/restore
  FileLockManager - Prevents concurrent edits
  EditHistory     - Stores edit history for audit/undo
"""

__all__ = [
    "ChangeRequest",
    "ChangeSet",
    "DiffGenerator",
    "PatchBuilder",
    "PatchValidator",
    "ChangePreview",
    "ChangeApplier",
    "RollbackManager",
    "FileLockManager",
    "EditHistory",
]

from ai.editing.change_request import ChangeRequest, ChangeStatus, ChangePriority
from ai.editing.change_set import ChangeSet, ChangeOperation, OperationType, Hunk
from ai.editing.diff_generator import DiffGenerator, DiffResult, DiffSummary
from ai.editing.patch_builder import PatchBuilder, Patch, PatchSet
from ai.editing.patch_validator import PatchValidator, ValidationResult
from ai.editing.change_preview import ChangePreview, PreviewResult
from ai.editing.change_applier import ChangeApplier, ApplyResult
from ai.editing.rollback_manager import RollbackManager, RollbackResult, Checkpoint
from ai.editing.file_lock_manager import FileLockManager, FileLock, LockStatus
from ai.editing.edit_history import EditHistory, EditEntry, load_edit_history

__version__ = "0.6.0"