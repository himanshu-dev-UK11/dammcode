"""
Model Catalog.

Permanent catalog of ALL officially supported models in MyCodingMaster.
Each model has a profile, provider, and metadata, with
capabilities (Part15) and quality profiles (Part23).
"""

from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from core.logger import setup_logger
from ai.models.model_profile import ModelProfile, ModelQualityProfile
from ai.models.model_capabilities import ModelCapabilities

logger = setup_logger(__name__)


class ModelState(Enum):
    """All possible model states."""
    READY = "Ready"
    CONNECTED = "Connected"
    INSTALLED = "Installed"
    API_REQUIRED = "API Required"
    API_MISSING = "API Missing"
    AUTH_FAILED = "Authentication Failed"
    OFFLINE = "Offline"
    DISCONNECTED = "Disconnected"
    DOWNLOADING = "Downloading"
    DISABLED = "Disabled"
    UNSUPPORTED = "Unsupported"
    UNKNOWN = "Unknown"
    
    @classmethod
    def get_icon(cls, state: 'ModelState') -> str:
        """Get status icon for model state (Part7)"""
        icon_map = {
            cls.READY: "✅",
            cls.CONNECTED: "🔵",
            cls.API_REQUIRED: "🟡",
            cls.API_MISSING: "🟡",
            cls.DISCONNECTED: "🟠",
            cls.OFFLINE: "🔴",
            cls.UNSUPPORTED: "⚫",
            cls.DOWNLOADING: "⏳",
            cls.AUTH_FAILED: "🔴",
        }
        return icon_map.get(state, "❓")


@dataclass
class CatalogEntry:
    """Single entry in the model catalog."""
    profile: ModelProfile
    state: ModelState = ModelState.UNKNOWN
    is_officially_supported: bool = True


class ModelCatalog:
    """
    Permanent catalog of all supported models.
    
    Separates the concept of:
    1. Officially supported models (always in catalog)
    2. Currently available models (state depends on connectivity/config)
    """
    
    def __init__(self):
        self._catalog: Dict[str, CatalogEntry] = {}
        self._load_official_models()
        logger.info("ModelCatalog initialized with official models")
        
    def _load_official_models(self):
        """
        Dynamically loads models from providers. 
        Hardcoded model lists have been removed per architecture guidelines.
        """
        # Providers will populate the catalog at runtime during discovery.
        logger.info(f"Loaded {len(self._catalog)} official models into catalog")
        
    def get_entry(self, model_name: str) -> Optional[CatalogEntry]:
        """Get a catalog entry by model name."""
        return self._catalog.get(model_name)
        
    def get_all_entries(self) -> List[CatalogEntry]:
        """Get all catalog entries."""
        return list(self._catalog.values())
        
    def get_entries_by_provider(self, provider_name: str) -> List[CatalogEntry]:
        """Get all entries for a specific provider."""
        return [e for e in self._catalog.values() if e.profile.provider == provider_name]
        
    def update_model_state(self, model_name: str, state: ModelState):
        """Update the state of a model."""
        if model_name in self._catalog:
            self._catalog[model_name].state = state
            logger.debug(f"Updated model state: {model_name} -> {state.value}")
            
    def add_custom_model(self, profile: ModelProfile) -> str:
        """Add a custom user-defined model to the catalog."""
        entry = CatalogEntry(
            profile=profile,
            state=ModelState.UNKNOWN,
            is_officially_supported=False
        )
        self._catalog[profile.name] = entry
        logger.info(f"Added custom model to catalog: {profile.name}")
        return profile.name
