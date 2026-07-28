"""
Model Registry.

Central registry for managing all available models in the system.

The Model Registry now works in conjunction with the Provider Registry and Model Catalog to:
- Load models from catalog and provider configurations
- Track model health and availability
- Support model-specific routing
- Track model states
"""

from typing import Dict, List, Optional, Any
from core.logger import setup_logger
from ai.models.model_profile import ModelProfile
from ai.models.model_health import ModelHealth
from ai.models.model_catalog import ModelCatalog, ModelState
from ai.providers.provider_registry import ProviderRegistry
from ai.providers.base_provider import ProviderConfig

logger = setup_logger(__name__)

class ModelRegistry:
    """
    Manages registration, lifecycle, and querying of AI models.
    
    The model registry now works with the provider platform to:
    - Load models from catalog and provider configurations
    - Map providers to their available models
    - Track model-specific health metrics
    - Track model states
    """
    def __init__(self, provider_registry: Optional[ProviderRegistry] = None):
        self.provider_registry = provider_registry
        self.catalog = ModelCatalog()
        self._health: Dict[str, ModelHealth] = {}
        self._enabled: Dict[str, bool] = {}
        self._provider_models: Dict[str, List[str]] = {}  # provider -> list of model IDs
        
        logger.info("ModelRegistry initialized with catalog")

    def register_model(self, profile: ModelProfile, enabled: bool = True):
        """Register a new model to the system."""
        if profile.name not in self.catalog._catalog:
            self.catalog.add_custom_model(profile)
        self._health[profile.name] = ModelHealth(model_name=profile.name)
        self._enabled[profile.name] = enabled
        
        # Link to provider if available
        provider_name = profile.provider
        if provider_name:
            if provider_name not in self._provider_models:
                self._provider_models[provider_name] = []
            if profile.name not in self._provider_models[provider_name]:
                self._provider_models[provider_name].append(profile.name)
        
        logger.info(f"Registered model: {profile.name}")

    def register_model_from_provider(self, provider_name: str, model_info: Dict[str, Any]):
        """
        Register a model from provider discovery results.
        
        Args:
            provider_name: Name of the provider
            model_info: Model information from provider
        """
        model_id = model_info.get("id", model_info.get("name", ""))
        model_name = f"{provider_name}:{model_id}"
        
        # Check if model is already in catalog first
        catalog_entry = self.catalog.get_entry(model_name)
        if catalog_entry:
            profile = catalog_entry.profile
        else:
            profile = ModelProfile(
                name=model_name,
                provider=provider_name,
                version=model_info.get("version", "1.0"),
                is_local=model_info.get("type", "cloud") == "local",
                context_window=model_info.get("context_window", 4096),
                max_output_tokens=model_info.get("max_output_tokens", 4096),
                strengths=model_info.get("capabilities", []),
                weaknesses=[],
                supported_languages=model_info.get("supported_languages", ["*"]),
                coding_ability=5,
                reasoning_ability=5,
                cost_per_1k_tokens=0.0,
                average_response_time_ms=0.0,
                availability_score=1.0,
            )
        
        self.register_model(profile, enabled=True)

    def load_models_from_provider(self, provider_name: str) -> List[str]:
        """
        Load all models from a specific provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            List of registered model names
        """
        models = []
        provider = self.provider_registry.get_provider(provider_name) if self.provider_registry else None
        
        # First, get all catalog entries for this provider
        catalog_entries = self.catalog.get_entries_by_provider(provider_name)
        for entry in catalog_entries:
            self.register_model(entry.profile, enabled=True)
            models.append(entry.profile.name)
        
        # Then add any provider-discovered models
        if provider:
            provider_models = provider.get_models()
            for model_id, model_info in provider_models.items():
                model_name = f"{provider_name}:{model_id}"
                if self.catalog.get_entry(model_name) is None:
                    self.register_model_from_provider(provider_name, model_info)
                    models.append(model_name)
        
        return models

    def enable_model(self, model_name: str):
        if model_name in self.catalog._catalog:
            self._enabled[model_name] = True
            self.catalog.update_model_state(model_name, ModelState.READY)

    def disable_model(self, model_name: str):
        if model_name in self.catalog._catalog:
            self._enabled[model_name] = False
            self.catalog.update_model_state(model_name, ModelState.DISABLED)

    def get_profile(self, model_name: str) -> Optional[ModelProfile]:
        entry = self.catalog.get_entry(model_name)
        return entry.profile if entry else None

    def get_health(self, model_name: str) -> Optional[ModelHealth]:
        return self._health.get(model_name)

    def get_all_catalog_models(self) -> List[str]:
        """Return all models in the catalog."""
        return [entry.profile.name for entry in self.catalog.get_all_entries()]

    def get_available_models(self) -> List[str]:
        """Return a list of enabled and healthy models."""
        available = []
        for name in self.get_all_catalog_models():
            entry = self.catalog.get_entry(name)
            if entry and entry.state in [ModelState.READY, ModelState.CONNECTED, ModelState.INSTALLED]:
                available.append(name)
        return available

    def get_models_for_provider(self, provider_name: str) -> List[str]:
        """Get all models in catalog for a specific provider."""
        entries = self.catalog.get_entries_by_provider(provider_name)
        return [e.profile.name for e in entries]

    def get_provider_for_model(self, model_name: str) -> Optional[str]:
        """Get the provider name for a specific model."""
        entry = self.catalog.get_entry(model_name)
        return entry.profile.provider if entry else None
        
    def update_model_state(self, model_name: str, state: ModelState):
        """Update the state of a model in catalog."""
        self.catalog.update_model_state(model_name, state)
