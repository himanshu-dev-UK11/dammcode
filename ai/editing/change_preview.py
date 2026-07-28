"""
change_preview.py — Preview window for code changes.

Creates a visual preview showing:
  - Changed files list
  - Diff hunks with line numbers
  - Reason for each change
  - Affected functions
  - Estimated impact

User must approve changes before they are applied.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QTextEdit, QLabel, QPushButton, QFrame, QScrollArea, QSplitter,
    QTreeWidget, QTreeWidgetItem, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from core.logger import setup_logger

from ai.editing.change_request import ChangeRequest, ChangeStatus
from ai.editing.change_set import ChangeSet, OperationType
from ai.editing.diff_generator import DiffResult, DiffSummary


logger = setup_logger(__name__)


@dataclass
class PreviewResult:
    """Result from the preview window."""
    approved:  bool
    changes:   List[Dict[str, Any]]
    timestamp: datetime


class ChangePreview(QWidget):
    """
    Preview window showing proposed code changes.

    Displays:
      - Files changed list with icons
      - Diff view with line numbers
      - Reason and metadata
      - Apply/Reject buttons

    Usage:
        preview = ChangePreview(request, diff_results, summary)
        approved = preview.exec_()
    """

    approved = Signal()
    rejected = Signal()

    def __init__(
        self,
        request: ChangeRequest,
        diff_results: List[DiffResult],
        summary: DiffSummary,
    ):
        super().__init__()
        self.request = request
        self.diff_results = diff_results
        self.summary = summary
        self._user_approved = False

        self.setWindowTitle(f"Code Changes: {request.user_prompt[:50]}...")
        self.setMinimumSize(900, 700)

        logger.debug(
            f"ChangePreview initialized with {summary.total_files} files, "
            f"{summary.total_hunks} hunks."
        )

        self._setup_ui()
        self._populate_data()

    # ── UI Setup ─────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        """Build the preview window UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ── Header ─────────────────────────────────────
        header = self._create_header()
        main_layout.addWidget(header)

        # ── Splitter: Files | Diff ─────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setSizes([300, 600])

        # Files list
        files_widget = self._create_files_panel()
        splitter.addWidget(files_widget)

        # Diff view
        diff_widget = self._create_diff_panel()
        splitter.addWidget(diff_widget)

        main_layout.addWidget(splitter)

        # ── Footer: Buttons ────────────────────────────
        footer = self._create_footer()
        main_layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """Create the header with request info."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #111113;
                border-bottom: 1px solid #252528;
            }
        """)
        widget.setFixedHeight(60)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        # Prompt line
        prompt_label = QLabel(self.request.user_prompt)
        prompt_label.setStyleSheet("""
            color: #E2E2E6;
            font-size: 14px;
            font-weight: 600;
            background-color: transparent;
        """)
        prompt_label.setWordWrap(True)
        layout.addWidget(prompt_label)

        # Meta line
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(16)

        files_label = QLabel(f"{self.summary.total_files} file(s) changed")
        files_label.setStyleSheet("""
            color: #52525C;
            font-size: 11px;
            background-color: transparent;
        """)
        meta_layout.addWidget(files_label)

        added_label = QLabel(f"+{self.summary.lines_added} lines")
        added_label.setStyleSheet("""
            color: #22C55E;
            font-size: 11px;
            font-weight: 600;
            background-color: transparent;
        """)
        meta_layout.addWidget(added_label)

        removed_label = QLabel(f"-{self.summary.lines_removed} lines")
        removed_label.setStyleSheet("""
            color: #EF4444;
            font-size: 11px;
            font-weight: 600;
            background-color: transparent;
        """)
        meta_layout.addWidget(removed_label)

        layout.addLayout(meta_layout)

        return widget

    def _create_files_panel(self) -> QWidget:
        """Create the files changed list panel."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #0D0D0F;
                border-right: 1px solid #252528;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title
        title = QLabel("CHANGED FILES")
        title.setStyleSheet("""
            color: #52525C;
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 0.7px;
            padding: 8px 16px;
            background-color: #111113;
            border-bottom: 1px solid #252528;
        """)
        layout.addWidget(title)

        # File list
        self._file_list = QListWidget()
        self._file_list.setStyleSheet("""
            QListWidget {
                background-color: #0D0D0F;
                border: none;
                padding: 8px;
            }
            QListWidget::item {
                padding: 8px 16px;
                min-height: 32px;
                border-radius: 2px;
            }
            QListWidget::item:hover {
                background-color: #161618;
            }
            QListWidget::item:selected {
                background-color: #1E3A5F;
            }
        """)
        self._file_list.itemSelectionChanged.connect(self._on_file_selected)
        layout.addWidget(self._file_list)

        # Summary stats
        stats_widget = QWidget()
        stats_widget.setStyleSheet("background-color: #111113;")
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(16, 12, 16, 12)
        stats_layout.setSpacing(8)

        # File type breakdown
        create_count = self.summary.files_created
        delete_count = self.summary.files_deleted
        modify_count = self.summary.files_modified

        if create_count > 0:
            create_label = QLabel(f"  + {create_count} new file(s)")
            create_label.setStyleSheet("""
                color: #22C55E;
                font-size: 11px;
                background-color: transparent;
            """)
            stats_layout.addWidget(create_label)

        if delete_count > 0:
            delete_label = QLabel(f"  × {delete_count} deleted file(s)")
            delete_label.setStyleSheet("""
                color: #EF4444;
                font-size: 11px;
                background-color: transparent;
            """)
            stats_layout.addWidget(delete_label)

        if modify_count > 0:
            modify_label = QLabel(f"  ∼ {modify_count} modified file(s)")
            modify_label.setStyleSheet("""
                color: #F59E0B;
                font-size: 11px;
                background-color: transparent;
            """)
            stats_layout.addWidget(modify_label)

        layout.addWidget(stats_widget)

        return widget

    def _create_diff_panel(self) -> QWidget:
        """Create the diff view panel."""
        widget = QWidget()
        widget.setStyleSheet("background-color: #0D0D0F;")

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Diff viewer (read-only text edit with monospace font)
        self._diff_view = QTextEdit()
        self._diff_view.setReadOnly(True)
        self._diff_view.setLineWrapMode(QTextEdit.NoWrap)
        self._diff_view.setFont(QFont("JetBrains Mono", 11))

        self._diff_view.setStyleSheet("""
            QTextEdit {
                background-color: #0D0D0F;
                color: #E2E2E6;
                border: none;
                padding: 16px;
            }
        """)

        layout.addWidget(self._diff_view)

        # Footer info
        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: #111113;")
        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(16, 8, 16, 8)
        info_layout.setSpacing(16)

        # Reason
        reason_label = QLabel(f"Reason: {self.request.reason}")
        reason_label.setStyleSheet("""
            color: #52525C;
            font-size: 10px;
            background-color: transparent;
        """)
        reason_label.setWordWrap(True)
        info_layout.addWidget(reason_label)

        # File count badge
        badge = QLabel(f"{self.summary.total_hunks} hunks")
        badge.setStyleSheet("""
            background-color: #1C1C1F;
            color: #52525C;
            font-size: 9px;
            padding: 2px 8px;
            border-radius: 2px;
            border: 1px solid #252528;
        """)
        info_layout.addWidget(badge)

        layout.addWidget(info_widget)

        return widget

    def _create_footer(self) -> QWidget:
        """Create the action buttons footer."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #111113;
                border-top: 1px solid #252528;
            }
        """)
        widget.setFixedHeight(50)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # Approve button
        approve_btn = QPushButton("Approve Changes")
        approve_btn.setFixedHeight(30)
        approve_btn.setStyleSheet("""
            QPushButton {
                background-color: #22C55E;
                color: #064E3B;
                font-size: 12px;
                font-weight: 600;
                border: none;
                border-radius: 4px;
                padding: 0 24px;
            }
            QPushButton:hover {
                background-color: #16A34A;
            }
            QPushButton:pressed {
                background-color: #15803D;
            }
        """)
        approve_btn.clicked.connect(self._on_approve)
        layout.addWidget(approve_btn)

        # Reject button
        reject_btn = QPushButton("Reject")
        reject_btn.setFixedHeight(30)
        reject_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: #7F1D1D;
                font-size: 12px;
                font-weight: 600;
                border: none;
                border-radius: 4px;
                padding: 0 24px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
            QPushButton:pressed {
                background-color: #B91C1C;
            }
        """)
        reject_btn.clicked.connect(self._on_reject)
        layout.addWidget(reject_btn)

        # Cancel button (for window close)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(30)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: #E5E7EB;
                font-size: 12px;
                font-weight: 500;
                border: none;
                border-radius: 4px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #4B5563;
            }
        """)
        cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(cancel_btn)

        layout.addStretch()

        return widget

    # ── Data Population ──────────────────────────────────────────────────────

    def _populate_data(self) -> None:
        """Populate the UI with change data."""
        self._file_list.clear()

        for diff in self.diff_results:
            # Create list item
            item = QListWidgetItem(self._file_list)

            # Determine icon and text
            if diff.op_type == OperationType.CREATE:
                icon = "+"
                color = "#22C55E"
            elif diff.op_type == OperationType.DELETE:
                icon = "×"
                color = "#EF4444"
            elif diff.op_type == OperationType.MODIFY:
                icon = "∼"
                color = "#F59E0B"
            else:
                icon = "?"
                color = "#52525C"

            text = f"  {icon}  {Path(diff.file_path).name}"
            item.setText(text)
            item.setForeground(QColor(color))
            item.setData(Qt.UserRole, diff)
            item.setSizeHint(item.sizeHint())

            self._file_list.addItem(item)

        # Select first file automatically
        if self._file_list.count() > 0:
            self._file_list.setCurrentRow(0)

    def _on_file_selected(self) -> None:
        """Show diff for selected file."""
        current_item = self._file_list.currentItem()
        if not current_item:
            return

        diff = current_item.data(Qt.UserRole)
        if not diff:
            return

        # Generate diff text
        diff_text = self._generate_diff_text(diff)
        self._diff_view.setPlainText(diff_text)

    def _generate_diff_text(self, diff: DiffResult) -> str:
        """Generate formatted diff text for display."""
        lines = []

        # Header
        lines.append(f"File: {diff.file_path}")
        lines.append("-" * 60)
        lines.append(f"Operation: {diff.op_type.value.upper()}")
        lines.append(f"Lines: +{diff.summary.get('lines_added', 0)} "
                     f"-{diff.summary.get('lines_removed', 0)}")
        lines.append("")

        # Hunks
        for i, hunk in enumerate(diff.hunks):
            lines.append(f"Hunk {i + 1}")
            lines.append("-" * 40)

            if hunk["type"] == "create":
                lines.append(f"+ Added {hunk['added']} lines:")
                lines.append(hunk.get("content", "")[:1000])

            elif hunk["type"] == "delete":
                lines.append(f"- Removed {hunk['removed']} lines:")
                lines.append(hunk.get("content", "")[:1000])

            else:
                for status, text in hunk.get("context", []):
                    if status == "add":
                        lines.append(f"+ {text}")
                    elif status == "remove":
                        lines.append(f"- {text}")
                    else:
                        lines.append(f"  {text}")

            lines.append("")

        return "\n".join(lines)

    # ── Event Handlers ───────────────────────────────────────────────────────

    def _on_approve(self) -> None:
        """User approved the changes."""
        self._user_approved = True
        self.approved.emit()
        self.close()

    def _on_reject(self) -> None:
        """User rejected the changes."""
        self._user_approved = False
        self.rejected.emit()
        self.close()

    def _on_cancel(self) -> None:
        """User cancelled (closed window)."""
        self._user_approved = False
        self.close()

    def exec(self) -> bool:
        """Show the preview and return whether it was approved."""
        self.show()
        return self._user_approved