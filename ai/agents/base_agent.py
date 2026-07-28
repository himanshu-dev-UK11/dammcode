"""
Base Agent class.

Provides common functionality for all agents like logging, error handling,
and event bus integration.
"""

from core.logger import setup_logger

class BaseAgent:
    """
    Abstract base class for all AI agents.
    """
    def __init__(self, name: str, event_bus):
        self.name = name
        self.event_bus = event_bus
        self.logger = setup_logger(f"agent.{name}")
        self.logger.info(f"{name} agent initialized.")
        
    def handle_error(self, error: Exception):
        """
        Standardized error handling to prevent silent failures.
        """
        self.logger.error(f"Error in {self.name}: {str(error)}", exc_info=True)
