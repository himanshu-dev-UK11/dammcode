"""
Base Provider Interface.

Defines the contract all AI providers must implement.
"""

import asyncio
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from core.logger import setup_logger
from enum import Enum

class AuthenticationType(Enum):
    """Supported authentication methods."""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    OAUTH = "oauth"
    CUSTOM = "custom"

class ProviderStatus(Enum):
    """Provider connection status."""
    UNKNOWN = "unknown"
    UNINITIALIZED = "uninitialized"
    CONNECTING = "connecting"
    CHECKING = "checking"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    AUTHENTICATION_FAILED = "authentication_failed"
    API_MISSING = "api_missing"
    OFFLINE = "offline"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    ERROR = "error"

@dataclass
class ProviderConfig:
    """Configuration for a provider instance."""
    provider_name: str
    endpoint: str
    auth_type: AuthenticationType
    api_key: Optional[str] = None
    enabled: bool = True
    priority: int = 0
    default_model: str = ""
    connection_status: ProviderStatus = ProviderStatus.UNINITIALIZED
    timeout_seconds: int = 30
    retry_count: int = 3
    supports_streaming: bool = False
    supports_tool_calling: bool = False
    supports_vision: bool = False
    supports_function_calling: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for JSON serialization."""
        return {
            "provider_name": self.provider_name,
            "endpoint": self.endpoint,
            "auth_type": self.auth_type.value,
            "api_key": self.api_key,
            "enabled": self.enabled,
            "priority": self.priority,
            "default_model": self.default_model,
            "connection_status": self.connection_status.value,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "supports_streaming": self.supports_streaming,
            "supports_tool_calling": self.supports_tool_calling,
            "supports_vision": self.supports_vision,
            "supports_function_calling": self.supports_function_calling,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderConfig":
        """Create config from dictionary."""
        return cls(
            provider_name=data.get("provider_name", ""),
            endpoint=data.get("endpoint", ""),
            auth_type=AuthenticationType(data.get("auth_type", "none")),
            api_key=data.get("api_key"),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 0),
            default_model=data.get("default_model", ""),
            connection_status=ProviderStatus(data.get("connection_status", "uninitialized")),
            timeout_seconds=data.get("timeout_seconds", 30),
            retry_count=data.get("retry_count", 3),
            supports_streaming=data.get("supports_streaming", False),
            supports_tool_calling=data.get("supports_tool_calling", False),
            supports_vision=data.get("supports_vision", False),
            supports_function_calling=data.get("supports_function_calling", False),
        )


class ProviderEvent:
    """Event fired by provider state changes."""
    
    def __init__(
        self,
        provider_name: str,
        event_type: str,
        status: Optional[ProviderStatus] = None,
        error: Optional[str] = None,
        models_refreshed: Optional[List[str]] = None,
    ):
        self.provider_name = provider_name
        self.event_type = event_type
        self.status = status
        self.error = error
        self.models_refreshed = models_refreshed or []


class BaseProvider(ABC):
    """
    Abstract base class for all AI providers.
    
    Ensures uniform interface across all providers and handles:
    - API key management
    - Retry logic
    - Connection status tracking
    - Background thread management
    """
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.logger = setup_logger(f"provider.{config.provider_name}")
        self._models: Dict[str, Dict[str, Any]] = {}
        self._event_callbacks: List[Callable[[ProviderEvent], None]] = []
        self._lock = threading.Lock()

    # ─────────────────────────────────────────────────────────────────────────────
    # Core Methods
    # ─────────────────────────────────────────────────────────────────────────────

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the provider.
        
        Returns True if connection successful, False otherwise.
        Should be implemented using background thread for network operations.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the provider."""
        pass

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate a response from the provider.
        
        Args:
            prompt: The user prompt
            model_id: Model to use (uses default if not specified)
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            The generated response string
        """
        pass

    @abstractmethod
    def stream_response(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> str:
        """
        Stream a response from the provider.
        
        Args:
            prompt: The user prompt
            model_id: Model to use (uses default if not specified)
            system_prompt: Optional system prompt
            on_chunk: Callback for each chunk
            **kwargs: Additional provider-specific parameters
            
        Returns:
            The complete generated response string
        """
        pass

    # ─────────────────────────────────────────────────────────────────────────────
    # Model Management
    # ─────────────────────────────────────────────────────────────────────────────

    @abstractmethod
    def refresh_models(self) -> List[Dict[str, Any]]:
        """
        Fetch available models from the provider.
        
        Returns:
            List of model descriptions with id, name, context_window, etc.
        """
        pass

    def get_models(self) -> Dict[str, Dict[str, Any]]:
        """Get cached models."""
        with self._lock:
            return dict(self._models)

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific model by ID."""
        with self._lock:
            return self._models.get(model_id)

    def _set_models(self, models: List[Dict[str, Any]]) -> None:
        """Set models from provider refresh (internal use)."""
        with self._lock:
            self._models = {m.get("id", m.get("name", "")): m for m in models}

    # ─────────────────────────────────────────────────────────────────────────────
    # Health & Status
    # ─────────────────────────────────────────────────────────────────────────────

    def get_status(self) -> ProviderStatus:
        """Get current connection status."""
        return self.config.connection_status

    def is_connected(self) -> bool:
        """Check if provider is connected."""
        return self.config.connection_status == ProviderStatus.CONNECTED

    def is_available(self) -> bool:
        """Check if provider is enabled and connected."""
        return self.config.enabled and self.is_connected()

    def test_connection(self) -> bool:
        """
        Test provider connectivity.
        
        Should be implemented efficiently without full connection setup.
        """
        try:
            if self.is_connected():
                return True
            if self.connect():
                self.disconnect()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────────────
    # Capabilities
    # ─────────────────────────────────────────────────────────────────────────────

    def supports_streaming(self) -> bool:
        """Check if provider supports streaming responses."""
        return self.config.supports_streaming

    def supports_tool_calling(self) -> bool:
        """Check if provider supports tool/function calling."""
        return self.config.supports_tool_calling

    def supports_vision(self) -> bool:
        """Check if provider supports image input."""
        return self.config.supports_vision

    def supports_function_calling(self) -> bool:
        """Check if provider supports function calling."""
        return self.config.supports_function_calling

    # ─────────────────────────────────────────────────────────────────────────────
    # Event System
    # ─────────────────────────────────────────────────────────────────────────────

    def on_event(self, callback: Callable[[ProviderEvent], None]) -> None:
        """Register an event callback."""
        self._event_callbacks.append(callback)

    def _fire_event(self, event: ProviderEvent) -> None:
        """Fire an event to all registered callbacks."""
        for callback in self._event_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Event callback failed: {e}")

    def _update_status(self, status: ProviderStatus, error: Optional[str] = None) -> None:
        """Update provider status and fire event."""
        self.config.connection_status = status
        self._fire_event(ProviderEvent(
            provider_name=self.config.provider_name,
            event_type="status_changed",
            status=status,
            error=error,
        ))

    # ─────────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────────

    def _get_model_id(self, model_id: Optional[str] = None) -> str:
        """Get model ID, using default if not specified."""
        if model_id:
            return model_id
        if self.config.default_model:
            return self.config.default_model
        models = self.get_models()
        if models:
            return list(models.keys())[0]
        raise ValueError(f"No model specified and no default for {self.config.provider_name}")

    def _run_async(self, coro) -> Any:
        """Run async coroutine in a thread-safe manner."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.config.provider_name}, status={self.config.connection_status.value})"
