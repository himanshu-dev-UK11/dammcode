"""
Provider Factory.

Creates provider instances from configuration files or provider classes.
"""

import json
import os
from typing import Dict, Optional, Type
from core.logger import setup_logger
from core.exceptions import ConfigurationError

from ai.providers.base_provider import BaseProvider, ProviderConfig, AuthenticationType
from ai.providers.provider_health import ProviderHealth

logger = setup_logger(__name__)


class ProviderFactory:
    """
    Factory for creating provider instances.
    
    Handles:
    - Loading configuration from JSON files
    - Instantiating provider classes
    - Validating provider configurations
    """
    
    # Map of provider names to their implementation classes
    _provider_classes: Dict[str, Type[BaseProvider]] = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseProvider]) -> None:
        """Register a provider implementation."""
        cls._provider_classes[name] = provider_class
        logger.debug(f"Registered provider: {name}")
    
    @classmethod
    def create_from_config(cls, config_path: str) -> BaseProvider:
        """
        Create a provider instance from a configuration file.
        
        Args:
            config_path: Path to the provider configuration JSON file
            
        Returns:
            Configured provider instance
            
        Raises:
            ConfigurationError: If configuration is invalid or provider not found
        """
        if not os.path.exists(config_path):
            raise ConfigurationError(f"Provider config not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return cls.create_from_dict(config_data)
    
    @classmethod
    def create_from_dict(cls, config_data: Dict[str, any]) -> BaseProvider:
        """
        Create a provider instance from a dictionary.
        
        Args:
            config_data: Provider configuration dictionary
            
        Returns:
            Configured provider instance
        """
        provider_name = config_data.get("provider_name", "")
        if not provider_name:
            raise ConfigurationError("Provider config missing 'provider_name'")
        
        # Get provider class
        provider_class = cls._provider_classes.get(provider_name.lower())
        if not provider_class:
            raise ConfigurationError(
                f"Unknown provider: {provider_name}. "
                f"Available: {', '.join(cls._provider_classes.keys())}"
            )
        
        # Create config
        config = ProviderConfig(
            provider_name=config_data.get("provider_name", ""),
            endpoint=config_data.get("endpoint", ""),
            auth_type=AuthenticationType(config_data.get("auth_type", "none")),
            api_key=config_data.get("api_key"),
            enabled=config_data.get("enabled", True),
            priority=config_data.get("priority", 0),
            default_model=config_data.get("default_model", ""),
            timeout_seconds=config_data.get("timeout_seconds", 30),
            retry_count=config_data.get("retry_count", 3),
            supports_streaming=config_data.get("supports_streaming", False),
            supports_tool_calling=config_data.get("supports_tool_calling", False),
            supports_vision=config_data.get("supports_vision", False),
            supports_function_calling=config_data.get("supports_function_calling", False),
        )
        
        # Create and return provider
        provider = provider_class(config)
        logger.info(f"Created provider: {provider_name}")
        return provider
    
    @classmethod
    def create_from_config_obj(cls, config: ProviderConfig) -> BaseProvider:
        """
        Create a provider instance from a ProviderConfig object.
        
        Args:
            config: Provider configuration object
            
        Returns:
            Configured provider instance
        """
        provider_name = config.provider_name
        
        # Get provider class
        provider_class = cls._provider_classes.get(provider_name.lower())
        if not provider_class:
            raise ConfigurationError(
                f"Unknown provider: {provider_name}. "
                f"Available: {', '.join(cls._provider_classes.keys())}"
            )
        
        # Create and return provider
        provider = provider_class(config)
        logger.info(f"Created provider: {provider_name}")
        return provider
    
    @classmethod
    def _get_provider_class(cls, provider_name: str) -> Optional[Type[BaseProvider]]:
        """Get provider class by name."""
        return cls._provider_classes.get(provider_name.lower())
        provider = provider_class(config)
        logger.info(f"Created provider: {provider_name}")
        return provider
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of registered provider names."""
        return list(cls._provider_classes.keys())


def register_standard_providers() -> None:
    """
    Register all standard providers.
    
    Called during application initialization.
    """
    try:
        from ai.providers.ollama_provider import OllamaProvider
        from ai.providers.gemini_provider import GeminiProvider
        from ai.providers.openai_provider import OpenAIProvider
        from ai.providers.anthropic_provider import AnthropicProvider
        from ai.providers.groq_provider import GroqProvider
        from ai.providers.cerebras_provider import CerebrasProvider
        from ai.providers.fireworks_provider import FireworksProvider
        from ai.providers.deepinfra_provider import DeepInfraProvider
        from ai.providers.together_provider import TogetherProvider
        from ai.providers.custom_provider import CustomProvider
        from ai.providers.qwen_provider import QwenProvider
        
        ProviderFactory.register_provider("ollama", OllamaProvider)
        ProviderFactory.register_provider("gemini", GeminiProvider)
        ProviderFactory.register_provider("openai", OpenAIProvider)
        ProviderFactory.register_provider("anthropic", AnthropicProvider)
        ProviderFactory.register_provider("groq", GroqProvider)
        ProviderFactory.register_provider("cerebras", CerebrasProvider)
        ProviderFactory.register_provider("fireworks", FireworksProvider)
        ProviderFactory.register_provider("deepinfra", DeepInfraProvider)
        ProviderFactory.register_provider("together", TogetherProvider)
        ProviderFactory.register_provider("custom", CustomProvider)
        ProviderFactory.register_provider("qwen", QwenProvider)
        
        logger.info("Standard providers registered successfully")
        
    except Exception as e:
        logger.error(f"Failed to register standard providers: {e}")


# Register providers on import
register_standard_providers()
