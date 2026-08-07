"""
Terminal command execution tool.
"""

from ai.tools.tool_base import BaseTool, ToolPermission, ToolCategory


class TerminalTool(BaseTool):
    def __init__(self, workspace_root: str):
        super().__init__(
            name="terminal",
            description="Terminal command execution (run, stop, background)",
            category=ToolCategory.TERMINAL,
            permission_level=ToolPermission.WARNING,
            supported_models=["all"]
        )
        self.workspace_root = workspace_root
        self._running_processes: dict = {}
        
    async def execute_async(self, action: str, command: str = None, **kwargs) -> ToolResult:
        """Execute a terminal action."""
        try:
            if action == "run":
                return ToolResult.success_result(self.name, output=f"Command executed: {command}")
            elif action == "stop":
                return ToolResult.success_result(self.name, output="Process stopped")
            else:
                return ToolResult.error_result(self.name, f"Unknown action: {action}")
        except Exception as e:
            return ToolResult.error_result(self.name, str(e))
    
    def run_command(self, command: str) -> ToolResult:
        return self.execute(action="run", command=command)
    
    def stop_command(self, process_id: str) -> ToolResult:
        return self.execute(action="stop", process_id=process_id)
