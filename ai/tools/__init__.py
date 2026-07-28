"""
Tools module — v1.5

Universal Tool Calling Engine components.
"""

from ai.tools.tool_base import BaseTool, ToolResult, ToolContext, ToolPermission, ToolCategory
from ai.tools.tool_registry import ToolRegistry
from ai.tools.tool_manager import ToolManager, ExecuteToolConfig
from ai.tools.tool_scheduler import ToolScheduler, ScheduledTask
from ai.tools.tool_history import ToolHistory, ExecutionRecord
from ai.tools.tool_result import ExtendedToolResult, ToolResultCollector
from ai.tools.tool_permission import PermissionPolicy, PermissionLevel

from ai.tools.file_tool import FileTool
from ai.tools.git_tool import GitTool
from ai.tools.terminal_tool import TerminalTool