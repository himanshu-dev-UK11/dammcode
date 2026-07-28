"""
AI Provider Platform.

A provider-based architecture that allows unlimited local or cloud providers
to be added without modifying the IDE core.

Provides:
- Base Provider Interface
- Provider Registry & Discovery
- Provider Manager & Router
- Universal API Layer
"""

from ai.providers.base_provider import BaseProvider, ProviderConfig, ProviderStatus
from ai.providers.provider_registry import ProviderRegistry
from ai.providers.provider_manager import ProviderManager
from ai.providers.provider_router import ProviderRouter
from ai.providers.provider_factory import ProviderFactory
from ai.providers.provider_health import ProviderHealth
from ai.providers.provider_discovery import ProviderDiscovery

__all__ = [
    "BaseProvider",
    "ProviderConfig",
    "ProviderStatus",
    "ProviderRegistry",
    "ProviderManager",
    "ProviderRouter",
    "ProviderFactory",
    "ProviderHealth",
    "ProviderDiscovery",
]
