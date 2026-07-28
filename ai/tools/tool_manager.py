"""
Tool Manager — v1.5

Central manager for all tool execution through the Universal Tool Calling Engine.
"""

import asyncio
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from core.logger import setup_logger
from core.event_bus import EventBus

from ai.tools.tool_base import BaseTool, ToolResult, ToolContext, ToolPermission, ToolCategory
from ai.tools.tool_registry import ToolRegistry
from ai.tools.tool_scheduler import ToolScheduler
from ai.tools.tool_history import ToolHistory


logger = setup_logger(__name__)


@dataclass
class ExecuteToolConfig:
    """Configuration for tool execution."""
    tool_name: str
    action: str
    context: Optional[ToolContext] = None
    params: Dict[str, Any] = None
    requires_confirmation: bool = False
    timeout_seconds: int = 30
    retry_count: int = 0
    priority: int = 0
    on_start: Optional[Callable[[ToolResult], None]] = None
    on_complete: Optional[Callable[[ToolResult], None]] = None


class ToolManager:
    """
    Central manager for tool execution.
    
    Responsibilities:
    - Execute tools through the scheduler
    - Validate tool permissions
    - Track tool execution history
    - Provide standardized results
    - Handle tool cancellation
    
    Every tool execution must flow through this manager.
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self.registry = ToolRegistry()
        self.scheduler = ToolScheduler()
        self.history = ToolHistory()
        self._logger = logger
        self._running_tools: Dict[str, BaseTool] = {}
        self._shutdown = False
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Registration
    # ─────────────────────────────────────────────────────────────────────────────

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the manager."""
        self.registry.register_tool(tool)
        self._logger.info(f"Registered tool: {tool.name}")
    
    def unregister_tool(self, name: str) -> None:
        """Remove a tool from the registry."""
        self.registry.unregister_tool(name)
    
    def register_default_tools(self, workspace_root: Optional[str] = None) -> None:
        """Register default tools with proper dependencies."""
        # Import and register default tools
        try:
            from ai.tools.file_tool import FileTool
            file_tool = FileTool(workspace_root=workspace_root)
            self.register_tool(file_tool)
        except ImportError:
            self._logger.warning("FileTool not available")
        
        try:
            from ai.tools.git_tool import GitTool
            git_tool = GitTool(repo_path=workspace_root)
            self.register_tool(git_tool)
        except ImportError:
            self._logger.warning("GitTool not available")
        
        try:
            from ai.tools.terminal_tool import TerminalTool
            terminal_tool = TerminalTool(workspace_root=workspace_root)
            self.register_tool(terminal_tool)
        except ImportError:
            self._logger.warning("TerminalTool not available")
        
        try:
            from ai.tools.browser_tool import BrowserTool
            browser_tool = BrowserTool()
            self.register_tool(browser_tool)
        except ImportError:
            self._logger.warning("BrowserTool not available")
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Execution
    # ─────────────────────────────────────────────────────────────────────────────

    def execute_tool(self, tool_name: str, action: str, **kwargs) -> ToolResult:
        """
        Execute a tool and return a standardized result.
        
        Args:
            tool_name: Name of the tool to execute
            action: Method name to call on the tool
            **kwargs: Arguments to pass to the tool
            
        Returns:
            ToolResult with execution result
        """
        return self.execute_tool_async(tool_name, action, **kwargs)
    
    def execute_tool_async(self, tool_name: str, action: str, **kwargs) -> ToolResult:
        """Execute a tool asynchronously."""
        config = ExecuteToolConfig(
            tool_name=tool_name,
            action=action,
            params=kwargs,
        )
        return self.execute_tool_config(config)
    
    def execute_tool_config(self, config: ExecuteToolConfig) -> ToolResult:
        """Execute a tool with full configuration."""
        # Check if tool exists
        tool = self.registry.get_tool(config.tool_name)
        if not tool:
            return ToolResult.error_result(
                config.tool_name,
                f"Tool '{config.tool_name}' not found. Available: {self.registry.list_tools()}"
            )
        
        # Set context
        if config.context:
            tool.set_context(config.context)
        
        # Execute the action
        method = getattr(tool, config.action, None)
        if not method:
            return ToolResult.error_result(
                config.tool_name,
                f"Tool '{config.tool_name}' has no action '{config.action}'"
            )
        
        try:
            # Run async method
            result = self._run_async(method(**config.params))
            
            # Record in history
            self.history.record_result(result)
            
            # Publish event
            if self.event_bus:
                self.event_bus.publish("tool_executed", {
                    "tool_name": config.tool_name,
                    "action": config.action,
                    "success": result.success,
                    "execution_time_ms": result.execution_time_ms,
                })
            
            return result
            
        except Exception as e:
            self._logger.error(f"Tool execution error: {e}")
            return ToolResult.error_result(config.tool_name, str(e))
    
    def execute_tool_with_context(self, tool_name: str, context: ToolContext, 
                                  action: str, **kwargs) -> ToolResult:
        """Execute a tool with full context."""
        config = ExecuteToolConfig(
            tool_name=tool_name,
            action=action,
            context=context,
            params=kwargs,
        )
        return self.execute_tool_config(config)
    
    def _run_async(self, coro) -> Any:
        """Run async coroutine in a thread-safe manner."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Scheduling
    # ─────────────────────────────────────────────────────────────────────────────

    def schedule_tool(self, tool_name: str, action: str, **kwargs) -> str:
        """
        Schedule a tool for queued execution.
        
        Args:
            tool_name: Name of the tool
            action: Method to call
            **kwargs: Tool arguments
            
        Returns:
            Task ID for the scheduled tool
        """
        task_id = self.scheduler.schedule(tool_name, action, **kwargs)
        self._logger.info(f"Scheduled tool: {tool_name} (task_id: {task_id[:8]})")
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled or running task."""
        return self.scheduler.cancel(task_id)
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get all pending scheduled tasks."""
        return self.scheduler.get_pending()
    
    def get_running_tasks(self) -> List[Dict[str, Any]]:
        """Get all currently running tasks."""
        return self.scheduler.get_running()
    
    # ─────────────────────────────────────────────────────────────────────────────
    # History
    # ─────────────────────────────────────────────────────────────────────────────

    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get tool execution history."""
        return self.history.get_history(limit)
    
    def get_tool_stats(self, tool_name: str) -> Dict[str, Any]:
        """Get statistics for a tool."""
        return self.history.get_stats(tool_name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall tool execution statistics."""
        return self.history.get_overall_stats()
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Validation
    # ─────────────────────────────────────────────────────────────────────────────

    def can_execute(self, tool_name: str) -> bool:
        """Check if a tool can be executed."""
        return self.registry.can_execute(tool_name)
    
    def requires_confirmation(self, tool_name: str) -> bool:
        """Check if a tool requires user confirmation."""
        tool = self.registry.get_tool(tool_name)
        if not tool:
            return False
        return tool.requires_confirmation
    
    def get_permission_level(self, tool_name: str) -> str:
        """Get the permission level for a tool."""
        tool = self.registry.get_tool(tool_name)
        if not tool:
            return "unknown"
        return tool.permission_level.value
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Get tool manager status."""
        return {
            "registered_tools": len(self.registry.list_tools()),
            "pending_tasks": len(self.get_pending_tasks()),
            "running_tasks": len(self.get_running_tasks()),
            "history_size": self.history.get_history_size(),
            "shutdown": self._shutdown,
        }
    
    def get_all_tools_metadata(self) -> List[Dict[str, Any]]:
        """Get metadata for all registered tools."""
        return self.registry.get_all_metadata()
    
    def get_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get tools in a category."""
        tools = self.registry.get_tools_by_category(ToolCategory(category))
        return [tool.get_metadata() for tool in tools]
    
    def get_tools_by_permission(self, permission: str) -> List[Dict[str, Any]]:
        """Get tools with a permission level."""
        tools = self.registry.get_tools_by_permission(ToolPermission(permission))
        return [tool.get_metadata() for tool in tools]
    
    def shutdown(self) -> None:
        """Shutdown the tool manager."""
        self._shutdown = True
        
        # Cancel all running tasks
        for task in self.get_running_tasks():
            self.cancel_task(task["task_id"])
        
        self._logger.info("Tool manager shutdown complete")
