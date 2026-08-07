"""
Custom application exceptions.

Provides clear, recognizable error types for easier debugging and crash reporting.
"""

class MyCodingMasterError(Exception):
    """Base exception for all application errors."""
    pass

class ModelTimeoutError(MyCodingMasterError):
    """Raised when an AI model takes too long to respond."""
    pass

class ToolExecutionError(MyCodingMasterError):
    """Raised when a tool (e.g., terminal, file) fails to execute."""
    pass

class ConfigurationError(MyCodingMasterError):
    """Raised when configuration is invalid or missing."""
    pass

class ProviderError(MyCodingMasterError):
    """Raised when a provider operation fails."""
    pass
