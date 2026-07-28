"""
Model Center — v1.4

Professional model management interface with intelligent routing.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from core.logger import setup_logger

from ai.providers.provider_registry import ProviderRegistry
from ai.providers.provider_manager import ProviderManager
from ai.models.model_registry import ModelRegistry

logger = setup_logger(__name__)


@dataclass
class ModelCapabilities:
    """Model capabilities derived from configuration."""
    coding: float = 0.0  # 0-5 stars
    reasoning: float = 0.0
    speed: float = 0.0
    context: float = 0.0
    tool_use: float = 0.0
    vision: float = 0.0
    function_calling: float = 0.0
    code_editing: float = 0.0
    streaming: bool = False
    multimodal: bool = False
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "ModelCapabilities":
        """Create capabilities from model config."""
        caps = cls()
        
        # Base scores on provider type and model type
        provider = config.get("provider", "").lower()
        model_type = config.get("type", "local")
        
        # Default scores for provider types
        if "gemini" in provider:
            caps.coding = 4.5
            caps.reasoning = 4.5
            caps.speed = 3.5
            caps.context = 5.0
            caps.tool_use = 4.0
            caps.vision = 4.5
            caps.function_calling = 4.0
            caps.code_editing = 4.5
            caps.streaming = True
            caps.multimodal = True
        elif "openai" in provider:
            caps.coding = 4.5
            caps.reasoning = 4.0
            caps.speed = 4.0
            caps.context = 4.5
            caps.tool_use = 4.0
            caps.vision = 4.0
            caps.function_calling = 4.5
            caps.code_editing = 4.0
            caps.streaming = True
            caps.multimodal = "vision" in config.get("model_id", "")
        elif "anthropic" in provider:
            caps.coding = 4.5
            caps.reasoning = 4.5
            caps.speed = 3.0
            caps.context = 5.0
            caps.tool_use = 4.5
            caps.vision = 4.5
            caps.function_calling = 4.5
            caps.code_editing = 4.5
            caps.streaming = True
            caps.multimodal = True
        elif "ollama" in provider or model_type == "local":
            caps.coding = 4.0
            caps.reasoning = 3.5
            caps.speed = 5.0
            caps.context = 4.0
            caps.tool_use = 3.5
            caps.vision = 2.5
            caps.function_calling = 3.5
            caps.code_editing = 4.0
            caps.streaming = True
            caps.multimodal = False
        else:
            caps.coding = 3.5
            caps.reasoning = 3.0
            caps.speed = 4.0
            caps.context = 3.5
            caps.tool_use = 3.0
            caps.vision = 2.0
            caps.function_calling = 3.0
            caps.code_editing = 3.5
            caps.streaming = True
            caps.multimodal = False
        
        # Adjust based on context window
        context_window = config.get("context_window", 4096)
        if context_window >= 128000:
            caps.context = 5.0
        elif context_window >= 65536:
            caps.context = 4.5
        elif context_window >= 32768:
            caps.context = 4.0
        elif context_window >= 16384:
            caps.context = 3.5
        
        # Adjust based on output tokens
        max_output = config.get("max_output_tokens", 4096)
        if max_output >= 8192:
            caps.speed = min(5.0, caps.speed + 0.5)
        
        # Check capabilities flags
        if config.get("supports_streaming", False):
            caps.streaming = True
        if config.get("supports_vision", False):
            caps.vision = max(caps.vision, 3.5)
            caps.multimodal = True
        if config.get("supports_tool_calling", False):
            caps.tool_use = max(caps.tool_use, 3.5)
        if config.get("supports_function_calling", False):
            caps.function_calling = max(caps.function_calling, 3.5)
        if config.get("supports_code_editing", False):
            caps.code_editing = max(caps.code_editing, 3.5)
        
        return caps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "coding": self.coding,
            "reasoning": self.reasoning,
            "speed": self.speed,
            "context": self.context,
            "tool_use": self.tool_use,
            "vision": self.vision,
            "function_calling": self.function_calling,
            "code_editing": self.code_editing,
            "streaming": self.streaming,
            "multimodal": self.multimodal,
        }


@dataclass
class ModelRating:
    """Rating for a specific use case."""
    use_case: str
    rating: float  # 0-5
    reason: str = ""
    
    def stars(self) -> str:
        """Convert rating to star string."""
        full = int(self.rating)
        half = 1 if self.rating - full >= 0.5 else 0
        empty = 5 - full - half
        return "★" * full + "☆" * half + "○" * empty
    
    def star_html(self) -> str:
        """Convert rating to HTML stars."""
        full = int(self.rating)
        half = 1 if self.rating - full >= 0.5 else 0
        empty = 5 - full - half
        return f'<span style="color:#F59E0B;">★</span>' * full + \
               f'<span style="color:#F59E0B; opacity:0.5;">★</span>' * half + \
               f'<span style="color:#F59E0B; opacity:0.25;">★</span>' * empty


@dataclass
class ModelInfo:
    """Complete model information."""
    model_id: str
    provider: str
    display_name: str
    context_window: int
    max_output_tokens: int
    model_type: str  # local or cloud
    capabilities: ModelCapabilities
    license: str = ""
    cost_type: str = "free"  # free or paid
    priority: int = 0
    version: str = ""
    tags: List[str] = field(default_factory=list)
    
    # Runtime state
    status: str = "unknown"  # connected, disconnected, error
    availability: float = 1.0  # 0-1
    avg_response_time_ms: float = 0.0
    total_requests: int = 0
    success_rate: float = 1.0
    
    def get_rating(self, use_case: str) -> ModelRating:
        """Get rating for a specific use case."""
        caps = self.capabilities
        
        if use_case == "coding":
            rating = (caps.coding * 0.4 + caps.code_editing * 0.3 + 
                     caps.tool_use * 0.15 + caps.function_calling * 0.15)
        elif use_case == "reasoning":
            rating = (caps.reasoning * 0.5 + caps.context * 0.3 + 
                     caps.tool_use * 0.2)
        elif use_case == "speed":
            rating = caps.speed
        elif use_case == "large_context":
            rating = caps.context
        elif use_case == "tool_use":
            rating = (caps.tool_use * 0.5 + caps.function_calling * 0.5)
        elif use_case == "vision":
            rating = caps.vision
        elif use_case == "multimodal":
            rating = 4.0 if caps.multimodal else 0.0
        else:
            rating = 3.0
        
        # Adjust for availability
        rating = rating * self.availability
        
        reasons = {
            "coding": "Strong coding capabilities",
            "reasoning": "Good reasoning performance",
            "speed": "Fast inference",
            "large_context": "Large context window",
            "tool_use": "Tool calling support",
            "vision": "Vision support",
            "multimodal": "Multimodal capabilities",
        }
        
        return ModelRating(use_case, rating, reasons.get(use_case, ""))


class ModelCenter:
    """
    Professional model management center.
    
    Provides:
    - Model discovery and registration
    - Provider grouping (Local, Cloud, Custom, Experimental, Unavailable)
    - Model card display with capabilities
    - Smart model recommendation
    - Privacy mode handling
    """
    
    def __init__(self, provider_registry: ProviderRegistry, 
                 provider_manager: ProviderManager,
                 model_registry: ModelRegistry,
                 config_dir: str = "config/models"):
        self.provider_registry = provider_registry
        self.provider_manager = provider_manager
        self.model_registry = model_registry
        self.config_dir = config_dir
        self._models: Dict[str, ModelInfo] = {}
        self._loaded_models: Dict[str, ModelInfo] = {}
        self._logger = logger
        
        self._load_models()
        self._update_model_statuses()
    
    def _load_models(self) -> None:
        """Load models from configuration directory."""
        if not os.path.exists(self.config_dir):
            self._logger.warning(f"Model config directory not found: {self.config_dir}")
            return
        
        for filename in os.listdir(self.config_dir):
            if filename.endswith('.json'):
                config_path = os.path.join(self.config_dir, filename)
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    model_id = config.get("model_id", filename.replace(".json", ""))
                    provider = config.get("provider", "unknown")
                    
                    model_info = ModelInfo(
                        model_id=model_id,
                        provider=provider,
                        display_name=config.get("display_name", model_id),
                        context_window=config.get("context_window", 4096),
                        max_output_tokens=config.get("max_output_tokens", 4096),
                        model_type=config.get("type", "local"),
                        capabilities=ModelCapabilities.from_config(config),
                        license=config.get("license", "Unknown"),
                        cost_type=config.get("cost_type", "free"),
                        priority=config.get("priority", 0),
                        version=config.get("version", ""),
                        tags=config.get("tags", []),
                    )
                    
                    self._models[model_id] = model_info
                    self._logger.info(f"Loaded model: {model_id} from {provider}")
                    
                except Exception as e:
                    self._logger.error(f"Failed to load model from {config_path}: {e}")
    
    def _update_model_statuses(self) -> None:
        """Update model statuses based on provider health."""
        # Get health data from provider manager
        health_data = self.provider_manager.get_health_status()
        
        for model_id, model in self._models.items():
            provider = model.provider
            provider_health = health_data.get(provider, {})
            
            # Update from provider status
            provider_obj = self.provider_registry.get_provider(provider)
            if provider_obj:
                status = provider_obj.get_status()
                if status:
                    model.status = status.value
                else:
                    model.status = "unknown"
                model.availability = provider_health.get("current_availability", 1.0)
                model.total_requests = provider_health.get("total_requests", 0)
                model.success_rate = provider_health.get("availability_score", 1.0)
                
                # Update avg response time from provider
                if provider_health.get("average_latency_ms"):
                    model.avg_response_time_ms = provider_health["average_latency_ms"]
    
    def get_all_models(self) -> Dict[str, ModelInfo]:
        """Get all registered models."""
        return dict(self._models)
    
    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get a specific model by ID."""
        return self._models.get(model_id)
    
    def get_enabled_models(self) -> Dict[str, ModelInfo]:
        """Get enabled models (from connected providers)."""
        enabled = {}
        for model_id, model in self._models.items():
            provider = self.provider_registry.get_provider(model.provider)
            if provider and provider.is_available():
                enabled[model_id] = model
        return enabled
    
    def get_provider_models(self, provider_name: str) -> List[ModelInfo]:
        """Get all models for a specific provider."""
        return [m for m in self._models.values() if m.provider == provider_name]
    
    def get_models_by_category(self) -> Dict[str, List[ModelInfo]]:
        """
        Group models by category:
        - Local: Local providers (Ollama, custom, etc.)
        - Cloud: Cloud providers (Gemini, OpenAI, etc.)
        - Custom: Custom provider models
        - Experimental: Models with low availability or in testing
        - Unavailable: Models from disconnected providers
        """
        categories = {
            "Local": [],
            "Cloud": [],
            "Custom": [],
            "Experimental": [],
            "Unavailable": [],
        }
        
        for model in self._models.values():
            if model.status == "error" or model.availability <= 0.0:
                categories["Unavailable"].append(model)
            elif model.provider == "custom" or model.provider == "ollama":
                categories["Local"].append(model)
            elif model.model_type == "local":
                categories["Local"].append(model)
            else:
                categories["Cloud"].append(model)
            
            # Experimental: low availability or many failures
            if model.availability < 0.8 or model.success_rate < 0.9:
                if model not in categories["Experimental"]:
                    categories["Experimental"].append(model)
        
        return categories
    
    def recommend_model(self, prompt: str, task_type: str = "coding",
                       preferred_provider: Optional[str] = None,
                       privacy_mode: str = "automatic") -> Optional[ModelInfo]:
        """
        Smart model recommendation based on:
        - Prompt type and requirements
        - Task type (coding, reasoning, translation, etc.)
        - Context size needed
        - Privacy mode (local only, cloud only, automatic)
        - Available models
        - Model ratings
        
        Returns best model or None if no suitable model found.
        """
        # Get eligible models based on privacy mode
        if privacy_mode == "local_only":
            eligible = [m for m in self.get_enabled_models().values() 
                       if m.model_type == "local" or m.provider == "ollama"]
        elif privacy_mode == "cloud_only":
            eligible = [m for m in self.get_enabled_models().values() 
                       if m.model_type == "cloud"]
        else:  # automatic
            eligible = list(self.get_enabled_models().values())
        
        if not eligible:
            self._logger.warning("No eligible models found for recommendation")
            return None
        
        # Score each model
        scored_models = []
        for model in eligible:
            score = self._calculate_model_score(model, task_type, prompt)
            scored_models.append((model, score))
        
        # Sort by score (highest first)
        scored_models.sort(key=lambda x: x[1], reverse=True)
        
        # Return best model
        if scored_models:
            best_model, best_score = scored_models[0]
            self._logger.info(f"Recommended model '{best_model.display_name}' for {task_type}: score={best_score:.2f}")
            return best_model
        
        return None
    
    def _calculate_model_score(self, model: ModelInfo, task_type: str, 
                               prompt: str) -> float:
        """Calculate a score for a model based on task requirements."""
        # Get rating for the task type
        rating = model.get_rating(task_type)
        
        # Base score from rating
        score = rating.rating * 10
        
        # Adjust for context window (if prompt is long)
        prompt_len = len(prompt)
        context_needed = prompt_len * 4  # Rough token estimate
        if context_needed > model.context_window:
            score -= 50  # Large penalty for insufficient context
        elif context_needed > model.context_window * 0.8:
            score -= 10  # Moderate penalty near limit
        
        # Adjust for cost (prefer free for non-critical tasks)
        if task_type not in ("coding", "reasoning") and model.cost_type == "paid":
            score -= 5
        
        # Adjust for availability (prefer reliable models)
        score += model.availability * 5
        
        # Adjust for response time (prefer faster for quick tasks)
        if task_type == "translation" or prompt_len < 100:
            score -= model.avg_response_time_ms / 100  # Penalize slow models
        
        # Priority boost for high-priority models
        score += model.priority * 0.1
        
        return score
    
    def get_fallback_model(self, primary_model_id: str) -> Optional[ModelInfo]:
        """Get a fallback model for when primary fails."""
        primary = self.get_model(primary_model_id)
        if not primary:
            return None
        
        # Get models from same provider first
        same_provider = [
            m for m in self._models.values() 
            if m.provider == primary.provider and m.model_id != primary.model_id
        ]
        
        if same_provider:
            # Sort by priority
            same_provider.sort(key=lambda m: m.priority, reverse=True)
            return same_provider[0]
        
        # Fall back to any available local model
        local_models = [
            m for m in self.get_enabled_models().values() 
            if m.model_type == "local"
        ]
        if local_models:
            local_models.sort(key=lambda m: m.priority, reverse=True)
            return local_models[0]
        
        return None
    
    def get_cost_estimate(self, model_id: str, prompt: str, 
                         include_output: bool = True) -> Dict[str, Any]:
        """Get cost estimate for a request."""
        model = self.get_model(model_id)
        if not model:
            return {"error": "Model not found"}
        
        if model.cost_type == "free":
            return {
                "cost_type": "free",
                "estimated_cost": "$0.00",
                "note": "Model is free to use",
            }
        
        # Rough cost estimation (this would be replaced with actual provider pricing)
        input_tokens = len(prompt) // 4  # Rough estimate
        output_tokens = input_tokens // 2  # Rough estimate
        
        # Generic pricing (per 1M tokens)
        pricing = {
            "gemini": {"input": 0.0005, "output": 0.0015},
            "openai": {"input": 0.0005, "output": 0.0015},
            "anthropic": {"input": 0.003, "output": 0.015},
            "groq": {"input": 0.0002, "output": 0.0002},
            "deepseek": {"input": 0.00014, "output": 0.00028},
        }
        
        provider_pricing = pricing.get(model.provider.lower(), {"input": 0.001, "output": 0.002})
        
        input_cost = (input_tokens / 1_000_000) * provider_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * provider_pricing["output"]
        total_cost = input_cost + output_cost
        
        return {
            "cost_type": "paid",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens if include_output else 0,
            "estimated_cost": f"${total_cost:.6f}",
            "provider_pricing": provider_pricing,
        }
    
    def get_response_time_estimate(self, model_id: str) -> Dict[str, Any]:
        """Get estimated response time for a model."""
        model = self.get_model(model_id)
        if not model:
            return {"error": "Model not found"}
        
        # Estimate based on model type and capabilities
        base_time = {
            "local": 1000,  # ms
            "cloud": 500,   # ms
        }
        
        # Adjust for capabilities
        adjustment = 1.0
        if model.capabilities.streaming:
            adjustment *= 0.8
        if model.capabilities.tool_use:
            adjustment *= 1.2
        if model.capabilities.multimodal:
            adjustment *= 1.3
        
        estimated_time = base_time.get(model.model_type, 1000) * adjustment
        
        return {
            "estimated_time_ms": estimated_time,
            "model_response_time_ms": model.avg_response_time_ms,
            "adjustment_factors": {
                "streaming": 0.8 if model.capabilities.streaming else 1.0,
                "tool_use": 1.2 if model.capabilities.tool_use else 1.0,
                "multimodal": 1.3 if model.capabilities.multimodal else 1.0,
            },
        }
    
    def get_task_type_from_prompt(self, prompt: str) -> str:
        """Determine task type from prompt content."""
        prompt_lower = prompt.lower()
        
        # Check for common task indicators
        if "debug" in prompt_lower or "error" in prompt_lower or "fix" in prompt_lower:
            return "debug"
        elif "test" in prompt_lower or "unit test" in prompt_lower or "test case" in prompt_lower:
            return "testing"
        elif "review" in prompt_lower or "feedback" in prompt_lower or "improve" in prompt_lower:
            return "review"
        elif "refactor" in prompt_lower or "optimize" in prompt_lower or "clean" in prompt_lower:
            return "refactoring"
        elif "translate" in prompt_lower or "convert" in prompt_lower:
            return "translation"
        elif "document" in prompt_lower or "doc" in prompt_lower or "comment" in prompt_lower:
            return "documentation"
        elif "explain" in prompt_lower or "summary" in prompt_lower or "overview" in prompt_lower:
            return "documentation"
        elif "large" in prompt_lower or "context" in prompt_lower or "file" in prompt_lower:
            return "large_context"
        elif "image" in prompt_lower or "visual" in prompt_lower or "picture" in prompt_lower:
            return "vision"
        else:
            return "coding"
    
    def get_provider_status(self, provider_name: str) -> Dict[str, Any]:
        """Get detailed status for a provider."""
        provider = self.provider_registry.get_provider(provider_name)
        if not provider:
            return {"error": "Provider not found"}
        
        health = self.provider_manager.get_health_status().get(provider_name, {})
        
        return {
            "provider_name": provider_name,
            "endpoint": provider.config.endpoint,
            "enabled": provider.config.enabled,
            "status": provider.get_status().value,
            "health": health,
            "models": [m.model_id for m in self.get_provider_models(provider_name)],
        }


# Global instance
_model_center = None


def get_model_center() -> ModelCenter:
    """Get the global model center instance."""
    global _model_center
    if _model_center is None:
        raise RuntimeError("ModelCenter not initialized")
    return _model_center


def initialize_model_center(provider_registry, provider_manager, model_registry) -> ModelCenter:
    """Initialize the global model center."""
    global _model_center
    _model_center = ModelCenter(provider_registry, provider_manager, model_registry)
    return _model_center


def reset_model_center():
    """Reset the global model center (for testing)."""
    global _model_center
    _model_center = None