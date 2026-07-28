"""
Base Tool class.
"""

from core.logger import setup_logger

class BaseTool:
    """
    Abstract base class for tools with common security checks and logging.
    """
    def __init__(self, name: str):
        self.name = name
        self.logger = setup_logger(f"tool.{name}")
