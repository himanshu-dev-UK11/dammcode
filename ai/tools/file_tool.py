"""
File operations tool.
"""

from ai.tools.tool_base import BaseTool, ToolPermission, ToolCategory


class FileTool(BaseTool):
    def __init__(self, workspace_root: str):
        super().__init__(
            name="file",
            description="File operations (read, write, create, delete, rename)",
            category=ToolCategory.FILE,
            permission_level=ToolPermission.SAFE,
            supported_models=["all"]
        )
        self.workspace_root = workspace_root
        
    async def execute_async(self, action: str, path: str, content: str = None) -> ToolResult:
        """Execute a file action."""
        try:
            if action == "read":
                full_path = f"{self.workspace_root}/{path}" if self.workspace_root else path
                with open(full_path, 'r', encoding='utf-8') as f:
                    return ToolResult.success_result(self.name, output=f.read())
            elif action == "write":
                full_path = f"{self.workspace_root}/{path}" if self.workspace_root else path
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return ToolResult.success_result(self.name, output=f"Written to {path}")
            else:
                return ToolResult.error_result(self.name, f"Unknown action: {action}")
        except Exception as e:
            return ToolResult.error_result(self.name, str(e))
    
    def read_file(self, path: str) -> ToolResult:
        return self.execute(action="read", path=path)
    
    def write_file(self, path: str, content: str) -> ToolResult:
        return self.execute(action="write", path=path, content=content)
