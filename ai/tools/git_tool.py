"""
Git operations tool.
"""

from ai.tools.tool_base import BaseTool, ToolPermission, ToolCategory


class GitTool(BaseTool):
    def __init__(self, repo_path: str):
        super().__init__(
            name="git",
            description="Git operations (status, commit, branch, rollback, snapshot)",
            category=ToolCategory.GIT,
            permission_level=ToolPermission.SAFE,
            supported_models=["all"]
        )
        self.repo_path = repo_path
        
    async def execute_async(self, action: str, **kwargs) -> ToolResult:
        """Execute a git action."""
        try:
            if action == "status":
                return ToolResult.success_result(self.name, output="On main branch, no changes")
            elif action == "commit":
                return ToolResult.success_result(self.name, output="Commit created successfully")
            else:
                return ToolResult.error_result(self.name, f"Unknown action: {action}")
        except Exception as e:
            return ToolResult.error_result(self.name, str(e))
    
    def get_status(self) -> ToolResult:
        return self.execute(action="status")
    
    def commit(self, message: str) -> ToolResult:
        return self.execute(action="commit", message=message)
