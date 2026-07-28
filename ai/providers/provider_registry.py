"""
Provider Registry.

Central registry for managing all available providers.
"""

import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from core.logger import setup_logger
from core.exceptions import ConfigurationError

from ai.providers.base_provider import BaseProvider, ProviderConfig, ProviderStatus
from ai.providers.provider_factory import ProviderFactory


logger = setup_logger(__name__)


class ProviderRegistry:
    """
    Manages registration, lifecycle, and querying of AI providers.
    
    Responsibilities:
    - Track all registered providers
    - Load providers from config directory
    - Manage provider health and availability
    - Provide provider discovery and selection
    """
    
    def __init__(self, config_dir: str = "config/providers"):
        self.config_dir = config_dir
        self._providers: Dict[str, BaseProvider] = {}
        self._config_paths: Dict[str, str] = {}
        self._lock = threading.Lock()
        self._health: Dict[str, Any] = {}
        logger.info(f"ProviderRegistry initialized with config_dir: {config_dir}")
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Provider Registration
    # ─────────────────────────────────────────────────────────────────────────────

    def register_provider(self, provider: BaseProvider, config_path: Optional[str] = None) -> None:
        """Register a provider instance."""
        name = provider.config.provider_name
        with self._lock:
            self._providers[name] = provider
            if config_path:
                self._config_paths[name] = config_path
        logger.info(f"Registered provider: {name}")

    def unregister_provider(self, provider_name: str) -> None:
        """Remove a provider from the registry."""
        with self._lock:
            if provider_name in self._providers:
                provider = self._providers.pop(provider_name)
                provider.disconnect()
                if provider_name in self._config_paths:
                    del self._config_paths[provider_name]
        logger.info(f"Unregistered provider: {provider_name}")

    # ─────────────────────────────────────────────────────────────────────────────
    # Provider Loading
    # ─────────────────────────────────────────────────────────────────────────────

    def load_all_providers(self) -> List[str]:
        """
        Load all providers from the config directory.
        
        Returns:
            List of successfully loaded provider names
        """
        loaded = []
        
        if not os.path.exists(self.config_dir):
            logger.warning(f"Provider config directory not found: {self.config_dir}")
            return loaded
        
        for filename in os.listdir(self.config_dir):
            if filename.endswith('.json'):
                config_path = os.path.join(self.config_dir, filename)
                try:
                    provider = ProviderFactory.create_from_config(config_path)
                    self.register_provider(provider, config_path)
                    loaded.append(provider.config.provider_name)
                except ConfigurationError as e:
                    logger.error(f"Failed to load provider from {config_path}: {e}")
        
        logger.info(f"Loaded {len(loaded)} providers from {self.config_dir}")
        return loaded
    
    def load_provider(self, provider_name: str) -> Optional[BaseProvider]:
        """
        Load a single provider by name.
        
        Args:
            provider_name: Name of the provider (matches config filename)
            
        Returns:
            Provider instance or None if not found/failed
        """
        config_path = os.path.join(self.config_dir, f"{provider_name}.json")
        if not os.path.exists(config_path):
            logger.error(f"Provider config not found: {config_path}")
            return None
        
        try:
            provider = ProviderFactory.create_from_config(config_path)
            self.register_provider(provider, config_path)
            return provider
        except ConfigurationError as e:
            logger.error(f"Failed to load provider {provider_name}: {e}")
            return None
    
    def reload_provider(self, provider_name: str) -> Optional[BaseProvider]:
        """Reload a provider from its config file."""
        self.unregister_provider(provider_name)
        return self.load_provider(provider_name)
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Provider Access
    # ─────────────────────────────────────────────────────────────────────────────

    def get_provider(self, provider_name: str) -> Optional[BaseProvider]:
        """Get a provider by name."""
        return self._providers.get(provider_name)
    
    def get_enabled_providers(self) -> List[BaseProvider]:
        """Get all enabled providers."""
        return [
            p for p in self._providers.values()
            if p.config.enabled
        ]
    
    def get_connected_providers(self) -> List[BaseProvider]:
        """Get all connected providers."""
        return [
            p for p in self._providers.values()
            if p.is_connected()
        ]
    
    def get_available_providers(self) -> List[BaseProvider]:
        """Get enabled and connected providers."""
        return [
            p for p in self._providers.values()
            if p.is_available()
        ]

    def get_all_providers(self) -> Dict[str, BaseProvider]:
        """Get all registered providers."""
        return dict(self._providers)
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Provider Configuration
    # ─────────────────────────────────────────────────────────────────────────────

    def enable_provider(self, provider_name: str) -> bool:
        """Enable a provider."""
        provider = self._providers.get(provider_name)
        if not provider:
            return False
        
        provider.config.enabled = True
        self._save_provider_config(provider)
        logger.info(f"Enabled provider: {provider_name}")
        return True
    
    def disable_provider(self, provider_name: str) -> bool:
        """Disable a provider."""
        provider = self._providers.get(provider_name)
        if not provider:
            return False
        
        provider.config.enabled = False
        self._save_provider_config(provider)
        logger.info(f"Disabled provider: {provider_name}")
        return True
    
    def set_provider_priority(self, provider_name: str, priority: int) -> bool:
        """Set provider priority (higher = preferred)."""
        provider = self._providers.get(provider_name)
        if not provider:
            return False
        
        provider.config.priority = priority
        self._save_provider_config(provider)
        logger.info(f"Set priority {priority} for provider: {provider_name}")
        return True
    
    def set_default_model(self, provider_name: str, model_id: str) -> bool:
        """Set default model for a provider."""
        provider = self._providers.get(provider_name)
        if not provider:
            return False
        
        provider.config.default_model = model_id
        self._save_provider_config(provider)
        logger.info(f"Set default model '{model_id}' for provider: {provider_name}")
        return True
    
    def get_loaded_providers(self) -> List[str]:
        """Get list of loaded provider names."""
        return list(self._providers.keys())
    
    def _save_provider_config(self, provider: BaseProvider) -> None:
        """Save provider config to file."""
        config_path = self._config_paths.get(provider.config.provider_name)
        if not config_path:
            return
        
        config_data = provider.config.to_dict()
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)

    # ─────────────────────────────────────────────────────────────────────────────
    # Health & Status
    # ─────────────────────────────────────────────────────────────────────────────

    def get_provider_health(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get health status for a provider."""
        provider = self._providers.get(provider_name)
        if not provider:
            return None
        
        return {
            "provider_name": provider_name,
            "status": provider.get_status().value,
            "is_connected": provider.is_connected(),
            "is_available": provider.is_available(),
            "last_tested": self._health.get(provider_name, {}).get("last_tested"),
            "success_rate": self._health.get(provider_name, {}).get("success_rate", 1.0),
        }

    def test_all_connections(self) -> Dict[str, bool]:
        """
        Test connections to all providers.
        
        Returns:
            Dict mapping provider names to connection success
        """
        results = {}
        for name, provider in self._providers.items():
            try:
                success = provider.test_connection()
                self._health[name] = {
                    "last_tested": datetime.utcnow().isoformat(),
                    "success_rate": 1.0 if success else 0.0,
                }
                results[name] = success
            except Exception as e:
                logger.error(f"Connection test failed for {name}: {e}")
                results[name] = False
        return results
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Model Discovery
    # ─────────────────────────────────────────────────────────────────────────────

    def refresh_all_models(self) -> Dict[str, List[str]]:
        """
        Refresh models for all providers.
        
        Returns:
            Dict mapping provider names to their model IDs
        """
        results = {}
        for name, provider in self._providers.items():
            try:
                models = provider.refresh_models()
                provider._set_models(models)
                results[name] = [m.get("id", m.get("name", "")) for m in models]
            except Exception as e:
                logger.error(f"Failed to refresh models for {name}: {e}")
                results[name] = []
        return results
    
    def get_all_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all models from all providers.
        
        Returns:
            Dict mapping provider names to list of model info
        """
        result = {}
        for name, provider in self._providers.items():
            models = provider.get_models()
            if models:
                result[name] = list(models.values())
        return result
