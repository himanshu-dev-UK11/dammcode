"""
Base Model interface.

Ensures all models implement standard methods and uniform error handling.
"""

from core.logger import setup_logger
from core.exceptions import ModelTimeoutError

class BaseModel:
    """
    Abstract base class for AI models.
    """
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.logger = setup_logger(f"model.{provider_name}")
        
    def generate_response(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement generate_response")
