"""
ExecutionReportGenerator — human-readable execution reports.

Generates detailed execution reports for tasks including:
- Execution time
- Files modified/created/deleted
- Verification results
- Retry count
- Errors/warnings
- Risk assessment
- Rollback information

Reports are used for:
- User feedback
- Audit trails
- Debugging
- Analytics

Usage:
    reporter = ExecutionReportGenerator()
    report = reporter.generate(task)
    print(report)
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .execution_task import ExecutionTask, ExecutionResult
from .task_state import TaskState


@dataclass
class ExecutionReport:
    """
    Generated execution report.
    
    Attributes:
        task_id:          Task ID
        title:            Task title
        status:           Final status
        start_time:       When execution started
        end_time:         When execution completed
        total_duration_ms: Total execution time
        steps_executed:   Number of steps executed
        files_modified:   List of modified files
        files_created:    List of created files
        files_deleted:    List of deleted files
        errors:           List of errors
        warnings:         List of warnings
        risk_level:       Risk level (low/medium/high/critical)
        rollback_id:      Rollback point ID (if applicable)
        retry_count:      Number of retries
        model_used:       Primary model used
        verification:     Verification summary
        step_details:     Detailed per-step information
    """
    task_id: str
    title: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration_ms: float = 0.0
    steps_executed: int = 0
    files_modified: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    risk_level: str = "low"
    rollback_id: Optional[str] = None
    retry_count: int = 0
    model_used: Optional[str] = None
    verification: Optional[Dict[str, Any]] = None
    step_details: List[Dict[str, Any]] = field(default_factory=list)


class ExecutionReportGenerator:
    """
    Generates human-readable execution reports.
    
    Usage:
        reporter = ExecutionReportGenerator()
        
        # Generate report for a task
        report = reporter.generate(task)
        
        # Format as text
        text = reporter.format_text(report)
        
        # Format as markdown
        markdown = reporter.format_markdown(report)
    """
    
    def __init__(self) -> None:
        self._logger = setup_logger(__name__)
    
    # ── Public API ──────────────────────────────────────────────────────────────
    
    def generate(self, task: ExecutionTask) -> ExecutionReport:
        """
        Generate a report for a task.
        
        Args:
            task: Task to report on
            
        Returns:
            ExecutionReport
        """
        report = ExecutionReport(
            task_id=task.id,
            title=task.task.title or task.task.original_prompt[:50],
            status=task.state.value,
            start_time=task.started_time,
            end_time=task.completed_time,
            total_duration_ms=task.stats.total_duration_ms,
            steps_executed=task.stats.steps_executed,
            files_modified=task.stats.files_modified,
            files_created=task.stats.files_created,
            files_deleted=task.stats.files_deleted,
            errors=[task.error] if task.error else [],
            retry_count=task.stats.retry_count,
            model_used=self._extract_model(task),
            verification=self._extract_verification(task),
            step_details=self._extract_step_details(task),
        )
        
        # Calculate risk level
        report.risk_level = self._calculate_risk(report)
        
        # Generate rollback ID for successful tasks
        if task.state == TaskState.SUCCESS:
            import uuid
            report.rollback_id = str(uuid.uuid4())[:8]
        
        return report
    
    def format_text(self, report: ExecutionReport) -> str:
        """
        Format report as plain text.
        
        Args:
            report: Report to format
            
        Returns:
            Formatted text string
        """
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append(f"EXECUTION REPORT - Task {report.task_id[:8]}")
        lines.append("=" * 60)
        lines.append("")
        
        # Status
        lines.append(f"Status:       {report.status.upper()}")
        lines.append(f"Title:        {report.title}")
        lines.append(f"Risk Level:   {report.risk_level.upper()}")
        lines.append("")
        
        # Timing
        if report.start_time:
            lines.append(f"Started:      {report.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if report.end_time:
            lines.append(f"Completed:    {report.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Duration:     {report.total_duration_ms:.1f} ms")
        lines.append("")
        
        # Execution stats
        lines.append(f"Steps:        {report.steps_executed}")
        lines.append(f"Retries:      {report.retry_count}")
        if report.model_used:
            lines.append(f"Model:        {report.model_used}")
        if report.rollback_id:
            lines.append(f"Rollback ID:  {report.rollback_id}")
        lines.append("")
        
        # Files
        if report.files_modified:
            lines.append("Modified:")
            for f in report.files_modified:
                lines.append(f"  - {f}")
        
        if report.files_created:
            lines.append("Created:")
            for f in report.files_created:
                lines.append(f"  + {f}")
        
        if report.files_deleted:
            lines.append("Deleted:")
            for f in report.files_deleted:
                lines.append(f"  x {f}")
        lines.append("")
        
        # Errors
        if report.errors:
            lines.append("Errors:")
            for error in report.errors:
                lines.append(f"  ❌ {error}")
            lines.append("")
        
        # Warnings
        if report.warnings:
            lines.append("Warnings:")
            for warning in report.warnings:
                lines.append(f"  ⚠️  {warning}")
            lines.append("")
        
        # Step details
        if report.step_details:
            lines.append("Step Details:")
            for step in report.step_details:
                status = "✓" if step.get("success") else "✗"
                lines.append(f"  {status} Step {step.get('index', '?')}: {step.get('text', 'Unknown')}")
            lines.append("")
        
        # Footer
        lines.append("=" * 60)
        lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def format_markdown(self, report: ExecutionReport) -> str:
        """
        Format report as Markdown.
        
        Args:
            report: Report to format
            
        Returns:
            Formatted Markdown string
        """
        lines = []
        
        lines.append(f"# Execution Report: {report.title}")
        lines.append("")
        
        lines.append("## Summary")
        lines.append("")
        lines.append(f"| Property | Value |")
        lines.append(f"|----------|-------|")
        lines.append(f"| Task ID | `{report.task_id}` |")
        lines.append(f"| Status | {self._status_emoji(report.status)} `{report.status.upper()}` |")
        lines.append(f"| Risk Level | {self._risk_emoji(report.risk_level)} `{report.risk_level.upper()}` |")
        lines.append(f"| Duration | {report.total_duration_ms:.1f} ms |")
        lines.append(f"| Steps | {report.steps_executed} |")
        lines.append(f"| Retries | {report.retry_count} |")
        if report.model_used:
            lines.append(f"| Model | `{report.model_used}` |")
        lines.append("")
        
        # Timing
        lines.append("## Timing")
        lines.append("")
        if report.start_time:
            lines.append(f"- **Started:** {report.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if report.end_time:
            lines.append(f"- **Completed:** {report.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Files
        lines.append("## Files Changed")
        lines.append("")
        
        if report.files_created:
            lines.append("### Created")
            for f in report.files_created:
                lines.append(f"- ✅ `{f}`")
            lines.append("")
        
        if report.files_modified:
            lines.append("### Modified")
            for f in report.files_modified:
                lines.append(f"- 📝 `{f}`")
            lines.append("")
        
        if report.files_deleted:
            lines.append("### Deleted")
            for f in report.files_deleted:
                lines.append(f"- ❌ `{f}`")
            lines.append("")
        
        # Errors and warnings
        if report.errors or report.warnings:
            lines.append("## Issues")
            lines.append("")
            
            if report.errors:
                lines.append("### Errors")
                for error in report.errors:
                    lines.append(f"- ❌ {error}")
                lines.append("")
            
            if report.warnings:
                lines.append("### Warnings")
                for warning in report.warnings:
                    lines.append(f"- ⚠️  {warning}")
                lines.append("")
        
        # Verification
        if report.verification:
            lines.append("## Verification")
            lines.append("")
            
            if report.verification.get("success"):
                lines.append("✅ **Verification passed**")
            else:
                lines.append("❌ **Verification failed**")
            
            if report.verification.get("report"):
                lines.append("")
                lines.append("```")
                lines.append(report.verification["report"][:500])
                lines.append("```")
            lines.append("")
        
        # Step details
        if report.step_details:
            lines.append("## Step Details")
            lines.append("")
            
            for step in report.step_details:
                status = "✅" if step.get("success") else "❌"
                lines.append(f"### {status} Step {step.get('index', '?')}")
                lines.append(f"- {step.get('text', 'Unknown')}")
                
                if step.get("duration_ms"):
                    lines.append(f"- Duration: {step['duration_ms']:.1f} ms")
                
                if step.get("model_used"):
                    lines.append(f"- Model: `{step['model_used']}`")
                
                if step.get("tools_used"):
                    lines.append(f"- Tools: {', '.join(step['tools_used'])}")
                lines.append("")
        
        # Footer
        lines.append("---")
        lines.append(f"*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(lines)
    
    # ── Private helpers ─────────────────────────────────────────────────────────
    
    def _extract_model(self, task: ExecutionTask) -> Optional[str]:
        """Extract the primary model used from task results."""
        for result in task.results:
            if result.model_used:
                return result.model_used
        return None
    
    def _extract_verification(self, task: ExecutionTask) -> Optional[Dict[str, Any]]:
        """Extract verification info from task."""
        # In production, this would extract from task.metadata
        # for now, return None
        return None
    
    def _extract_step_details(self, task: ExecutionTask) -> List[Dict[str, Any]]:
        """Extract step details from task results."""
        details = []
        for i, result in enumerate(task.results):
            details.append({
                "index": result.step_index,
                "text": result.step_text,
                "success": result.success,
                "duration_ms": result.duration_ms,
                "model_used": result.model_used,
                "tools_used": result.tools_used,
            })
        return details
    
    def _calculate_risk(self, report: ExecutionReport) -> str:
        """Calculate risk level based on report content."""
        # Start with low risk
        risk = "low"
        
        # Check file operations
        if len(report.files_deleted) > 5:
            risk = "high"
        elif len(report.files_deleted) > 0:
            risk = "medium"
        
        if len(report.files_modified) > 10:
            risk = "high"
        elif len(report.files_modified) > 3:
            risk = "medium"
        
        # Check errors
        if len(report.errors) > 0:
            risk = "high"
        
        # Check verification
        if report.verification and not report.verification.get("success"):
            risk = "high"
        
        return risk
    
    def _status_emoji(self, status: str) -> str:
        """Return emoji for status."""
        emojis = {
            "success": "✅",
            "failed": "❌",
            "cancelled": "🛑",
            "pending": "⏳",
            "running": "🚀",
        }
        return emojis.get(status, "❓")
    
    def _risk_emoji(self, risk: str) -> str:
        """Return emoji for risk level."""
        emojis = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "critical": "🔴",
        }
        return emojis.get(risk, "❓")


def setup_logger(name: str):
    """Simple logger setup for this module."""
    import logging
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
