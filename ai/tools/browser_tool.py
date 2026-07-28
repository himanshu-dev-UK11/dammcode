"""
Web search tool.
"""

from ai.tools.base_tool import BaseTool

class BrowserTool(BaseTool):
    def __init__(self):
        super().__init__("browser")
        
    def search(self, query: str) -> list:
        self.logger.info(f"Searching web for: {query}")
        return []
