"""
Provider Manager.

Unified management interface for all provider operations,
including Parallel Initialization (Part18), Event System (Part22),
and Automatic Background Recovery (Part17).
"""

import threading
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from core.logger import setup_logger
from core.event_bus import EventBus
from core.exceptions import ProviderError

from ai.providers.base_provider import BaseProvider, ProviderConfig, ProviderStatus
from ai.providers.provider_registry import ProviderRegistry
from ai.providers.provider_health import ProviderHealth
from ai.providers.provider_router import ProviderRouter


logger = setup_logger(__name__)


class ProviderEventTypes:
    """Event types for Part22"""
    CONNECTED = "provider_connected"
    DISCONNECTED = "provider_disconnected"
    FAILED = "provider_failed"
    RECOVERING = "provider_recovering"
    UPDATED = "provider_updated"
    MODEL_ADDED = "model_added"
    MODEL_REMOVED = "model_removed"
    API_CHANGED = "api_changed"
    HEALTH_CHANGED = "health_changed"


class ProviderManager:
    """
    Manages all provider operations for the application.
    
    Responsibilities:
    - Enable/Disable providers
    - Validate API keys
    - Test connections
    - Refresh models
    - Health monitoring
    - Automatic reconnection
    - Event broadcasting
    - Parallel initialization (Part18)
    - Automatic background recovery (Part17)
    - Provider Event System (Part22)
    """
    
    def __init__(self, registry: ProviderRegistry, event_bus: Optional[EventBus] = None):
        self.registry = registry
        self.event_bus = event_bus
        self.router = ProviderRouter(registry)
        self._health = ProviderHealth(registry)
        self._reconnect_threads: Dict[str, threading.Thread] = {}
        self._running = True
        self._lock = threading.Lock()
        self._config_hash: Dict[str, str] = {}
        
        logger.info("ProviderManager initialized")
        
        # Monitor config changes for Part17
        self._initialize_config_hashes()
        
        # Start health monitor and background recovery
        self.monitor_health()
        self._start_background_recovery()

    # ─────────────────────────────────────────────────────────────────────────────
    # Part17: Automatic Background Recovery & Config Monitoring
    # ─────────────────────────────────────────────────────────────────────────────
    def _initialize_config_hashes(self) -> None:
        """Store initial config hashes to detect changes later"""
        for name, provider in self.registry.get_all_providers().items():
            config_str = f"{provider.config.api_key or ''}-{provider.config.endpoint}-{provider.config.enabled}"
            self._config_hash[name] = hashlib.sha256(config_str.encode()).hexdigest()
    
    def _check_config_changes(self) -> None:
        """Check if any provider's config changed (Part17)"""
        for name, provider in self.registry.get_all_providers().items():
            config_str = f"{provider.config.api_key or ''}-{provider.config.endpoint}-{provider.config.enabled}"
            new_hash = hashlib.sha256(config_str.encode()).hexdigest()
            
            if new_hash != self._config_hash.get(name, ""):
                logger.info(f"Config changed for {name}, reconnecting...")
                self._config_hash[name] = new_hash
                self._fire_event(ProviderEventTypes.API_CHANGED, {"provider": name})
                
                # Trigger refresh in background
                def refresh_job():
                    try:
                        self._fire_event(ProviderEventTypes.RECOVERING, {"provider": name})
                        if provider.connect():
                            provider.refresh_models()
                            self._fire_event(ProviderEventTypes.CONNECTED, {"provider": name})
                    except Exception as e:
                        logger.error(f"Failed to reconnect {name}: {e}")
                
                threading.Thread(target=refresh_job, daemon=True).start()
    
    def _start_background_recovery(self) -> None:
        """Start background thread for config monitoring"""
        def recovery_loop():
            while self._running:
                try:
                    self._check_config_changes()
                    time.sleep(5)  # check every 5 seconds
                except Exception as e:
                    logger.error(f"Recovery loop error: {e}")
        
        threading.Thread(target=recovery_loop, daemon=True).start()
        logger.info("Background recovery started")

    # ─────────────────────────────────────────────────────────────────────────────
    # Part18: Parallel Initialization
    # ─────────────────────────────────────────────────────────────────────────────
    def initialize_all_providers_parallel(self) -> None:
        """Initialize all providers in parallel (Part18)"""
        providers = self.registry.get_all_providers()
        
        def initialize_provider(name: str, provider: BaseProvider):
            logger.info(f"Initializing {name} in background...")
            try:
                # Record initial state
                provider._update_status(ProviderStatus.CONNECTING)
                self._fire_event(ProviderEventTypes.RECOVERING, {"provider": name})
                
                # Connect
                if provider.connect():
                    # Refreshes models
                    models = provider.refresh_models()
                    provider._set_models(models)
                    
                    # Update health metrics
                    metrics = self._health.get_metrics(name)
                    if metrics:
                        metrics.last_sync = datetime.utcnow()
                        metrics.last_ping = datetime.utcnow()
                        metrics.available_models_count = len(models)
                        metrics.cached_valid_api_key = True
                        metrics.status = ProviderStatus.CONNECTED
                    
                    self._fire_event(ProviderEventTypes.CONNECTED, {"provider": name, "model_count": len(models)})
                    logger.info(f"Successfully initialized {name}")
                else:
                    provider._update_status(ProviderStatus.DISCONNECTED)
                    logger.warning(f"Failed to connect {name} during parallel init")
                    
            except Exception as e:
                logger.error(f"Parallel init error for {name}: {e}")
                provider._update_status(ProviderStatus.ERROR, str(e))
                self._fire_event(ProviderEventTypes.FAILED, {"provider": name, "error": str(e)})
        
        # Start a thread per provider
        for name, provider in providers.items():
            if provider.config.enabled:
                thread = threading.Thread(target=initialize_provider, args=(name, provider), daemon=True)
                thread.start()
                self._reconnect_threads[name] = thread
        
        logger.info(f"Parallel initialization started for {len(providers)} providers")

    # ─────────────────────────────────────────────────────────────────────────────
    # Provider Control
    # ─────────────────────────────────────────────────────────────────────────────

    def enable_provider(self, provider_name: str) -> bool:
        """Enable a provider."""
        success = self.registry.enable_provider(provider_name)
        if success:
            self._fire_event("provider_enabled", {"provider": provider_name})
        return success

    def disable_provider(self, provider_name: str) -> bool:
        """Disable a provider."""
        provider = self.registry.get_provider(provider_name)
        if not provider:
            return False
        
        provider.disconnect()
        success = self.registry.disable_provider(provider_name)
        if success:
            self._fire_event("provider_disabled", {"provider": provider_name})
        return success

    def validate_api_key(self, provider_name: str, api_key: str) -> bool:
        """
        Validate an API key for a provider.
        
        Args:
            provider_name: Name of the provider
            api_key: API key to validate
            
        Returns:
            True if key is valid, False otherwise
        """
        provider = self.registry.get_provider(provider_name)
        if not provider:
            return False
        
        # Create temporary provider with provided API key
        temp_config = ProviderConfig(
            provider_name=provider.config.provider_name,
            endpoint=provider.config.endpoint,
            auth_type=provider.config.auth_type,
            api_key=api_key,
            enabled=True,
            timeout_seconds=10,
        )
        
        temp_provider = type(provider)(temp_config)
        
        try:
            # Try a minimal request (like listing models or checking auth)
            return temp_provider.test_connection()
        except Exception as e:
            logger.error(f"API key validation failed for {provider_name}: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────────────

    def test_connection(self, provider_name: str) -> bool:
        """Test connection to a provider."""
        provider = self.registry.get_provider(provider_name)
        if not provider:
            return False
        
        success = provider.test_connection()
        if success:
            provider._update_status(ProviderStatus.CONNECTED)
        else:
            provider._update_status(ProviderStatus.ERROR, "Connection failed")
        return success

    # ─────────────────────────────────────────────────────────────────────────────
    # Model Management
    # ─────────────────────────────────────────────────────────────────────────────

    def refresh_models(self, provider_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Refresh available models for provider(s).
        
        Args:
            provider_name: Specific provider or None for all
            
        Returns:
            Dict mapping provider names to model IDs
        """
        if provider_name:
            provider = self.registry.get_provider(provider_name)
            if not provider:
                return {}
            
            try:
                models = provider.refresh_models()
                provider._set_models(models)
                return {provider_name: [m.get("id", m.get("name", "")) for m in models]}
            except Exception as e:
                logger.error(f"Failed to refresh models for {provider_name}: {e}")
                return {provider_name: []}
        
        # Refresh all
        return self.registry.refresh_all_models()

    def register_models(self, provider_name: str, models: List[Dict[str, Any]]) -> None:
        """
        Register models for a provider.
        
        Args:
            provider_name: Provider name
            models: List of model definitions
        """
        provider = self.registry.get_provider(provider_name)
        if not provider:
            return
        
        provider._set_models(models)
        logger.info(f"Registered {len(models)} models for {provider_name}")

    # ─────────────────────────────────────────────────────────────────────────────
    # Health Monitoring
    # ─────────────────────────────────────────────────────────────────────────────

    def get_health_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get health status for all providers.
        
        Returns:
            Dict mapping provider names to health info
        """
        return self._health.get_all_health()

    def monitor_health(self) -> None:
        """Start background health monitoring."""
        def monitor_loop():
            while self._running:
                try:
                    self._check_health()
                    time.sleep(60)  # Check every 60 seconds
                except Exception as e:
                    logger.error(f"Health monitor error: {e}")
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        logger.info("Health monitoring started")

    def _check_health(self) -> None:
        """Check health of all providers."""
        for provider_name, provider in self.registry.get_all_providers().items():
            try:
                if provider.config.enabled:
                    if not provider.is_connected():
                        self._attempt_reconnect(provider)
                    
                    # Update health metrics
                    status = provider.get_status()
                    self._health.record_status(provider_name, status)
                    
            except Exception as e:
                logger.error(f"Health check failed for {provider_name}: {e}")

    def _attempt_reconnect(self, provider: BaseProvider) -> bool:
        """Attempt to reconnect to a provider."""
        provider_name = provider.config.provider_name
        
        # Don't reconnect too frequently
        last_attempt = self._health.get_last_attempt(provider_name)
        if last_attempt:
            elapsed = (datetime.utcnow() - last_attempt).total_seconds()
            if elapsed < 30:  # Minimum 30 seconds between attempts
                return False
        
        self._health.record_attempt(provider_name)
        
        try:
            if provider.connect():
                provider._update_status(ProviderStatus.CONNECTED)
                self._fire_event("provider_connected", {"provider": provider_name})
                return True
        except Exception as e:
            logger.error(f"Reconnection failed for {provider_name}: {e}")
            provider._update_status(ProviderStatus.ERROR, str(e))
        
        return False

    # ─────────────────────────────────────────────────────────────────────────────
    # Event Broadcasting
    # ─────────────────────────────────────────────────────────────────────────────

    def _fire_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Fire an event to the event bus."""
        if self.event_bus:
            self.event_bus.publish(f"provider_{event_type}", data)
        logger.debug(f"Event fired: provider_{event_type}")

    # ─────────────────────────────────────────────────────────────────────────────
    # Shutdown
    # ─────────────────────────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Shutdown the provider manager."""
        self._running = False
        
        # Disconnect all providers
        for provider in self.registry.get_all_providers().values():
            provider.disconnect()
        
        logger.info("ProviderManager shutdown complete")
