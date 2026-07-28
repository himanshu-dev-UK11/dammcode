"""
Smart Model Router.

Selects the best model for the task from available ones,
never selects an unusable model, falls back gracefully.
"""

from typing import Optional, List
from enum import Enum
from core.logger import setup_logger
from ai.models.model_registry import ModelRegistry
from ai.models.model_catalog import ModelState, CatalogEntry
from ai.providers.provider_registry import ProviderRegistry
from ai.providers.provider_manager import ProviderManager

logger = setup_logger(__name__)


class TaskType(Enum):
    """Types of tasks the router can optimize for."""
    SIMPLE_CHAT = "simple_chat"
    CODING = "coding"
    HEAVY_REASONING = "heavy_reasoning"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    LARGE_CONTEXT = "large_context"


class ModelRouter:
    """
    Smart model router that selects the appropriate model for the task.
    """
    def __init__(self, model_registry: ModelRegistry, provider_manager: ProviderManager):
        self.model_registry = model_registry
        self.provider_manager = provider_manager
        logger.info("ModelRouter (Smart) initialized.")
        
    def _is_provider_healthy(self, provider_name: str) -> bool:
        """Check if a provider is healthy, available, and connected"""
        provider = self.provider_manager.registry.get_provider(provider_name)
        if not provider:
            return False
        if not provider.config.enabled:
            return False
        return provider.is_available()
        
    def _get_healthy_models(self) -> List[CatalogEntry]:
        """Get all models from healthy, available providers"""
        all_entries = self.model_registry.catalog.get_all_entries()
        healthy = []
        
        for entry in all_entries:
            if not entry:
                continue
            if self._is_provider_healthy(entry.profile.provider):
                healthy.append(entry)
        
        return healthy

    def select_best_model(self, task_type: TaskType = TaskType.SIMPLE_CHAT) -> Optional[str]:
        """
        Select the best available model for the given task type.
        Never returns an unusable model.
        Prioritizes local models first, then highest quality available.
        EXCLUDES deepseek per user request.
        ONLY selects models that can reply (are connected and healthy).
        """
        healthy_entries = self._get_healthy_models()
        if not healthy_entries:
            logger.warning("No healthy models available")
            return None
            
        # Score models based on task type and preferences (Part 8)
        scored = []
        for entry in healthy_entries:
            profile = entry.profile
            score = 0
            
            # 0. User requested to ban deepseek from auto-selection
            if "deepseek" in profile.name.lower():
                logger.info(f"Skipping deepseek model {profile.name} per user request")
                continue

            # 0.5 Check if model can actually reply - get provider and verify connection
            provider = self.provider_manager.registry.get_provider(profile.provider)
            if not provider:
                logger.info(f"Skipping {profile.name} - provider {profile.provider} not found")
                continue
            if not provider.is_connected():
                logger.info(f"Skipping {profile.name} - provider {profile.provider} not connected")
                continue
            if not provider.is_available():
                logger.info(f"Skipping {profile.name} - provider {profile.provider} not available")
                continue
            
            # 1. Highest priority: local models (Part 5)
            if profile.is_local:
                score += 10000
                
            # 1.5 Model specific health check
            model_health = self.model_registry._health.get(profile.name)
            if model_health:
                if not model_health.is_online:
                    logger.info(f"Skipping {profile.name} - model health shows offline")
                    continue  # Skip models that are known to fail/not reply
                score += model_health.current_availability * 500
                
            # 2. Availability and provider health
            health_metrics = self.provider_manager._health.get_metrics(profile.provider)
            if health_metrics:
                score += health_metrics.current_availability * 100
                # Lower latency is better
                if health_metrics.average_latency_ms > 0:
                    score += 500 - min(health_metrics.average_latency_ms / 10, 400)
                
            # 3. Context window
            score += profile.context_window // 1000
                
            # 4. Task-specific optimization
            if task_type == TaskType.SIMPLE_CHAT:
                score += 50
                if "fast" in profile.strengths:
                    score += 150
                if profile.supports_streaming:
                    score += 50
            elif task_type == TaskType.CODING:
                score += profile.coding_ability * 100
                if "coding" in profile.strengths:
                    score += 300
                if profile.supports_tool_calling:
                    score += 100
                if profile.supports_function_calling:
                    score += 100
            elif task_type == TaskType.HEAVY_REASONING:
                score += profile.reasoning_ability * 100
                if "reasoning" in profile.strengths:
                    score += 300
            elif task_type == TaskType.LARGE_CONTEXT:
                score += profile.context_window // 500
                
            # 5. Cost preference (cheaper is better)
            score += (1.0 - min(profile.cost_per_1k_tokens / 3.0, 1.0)) * 100
                
            scored.append((score, profile.name))
            
        if not scored:
            logger.warning("No models passed health and availability checks")
            return None
            
        # Sort by score, descending
        scored.sort(reverse=True, key=lambda x: x[0])
        best_model = scored[0][1]
        logger.info(
            f"Automatic Router: Selected {best_model} "
            f"(Score: {scored[0][0]:.0f}, "
            f"Task: {task_type.value}, "
            f"Can reply: Yes, "
            f"Active: Yes)"
        )
        
        # Log reasoning
        if scored:
            logger.debug("Top 5 candidates:")
            for i, (score, name) in enumerate(scored[:5]):
                logger.debug(f"  {i+1}. {name} - score: {score}")
                
        return best_model
        
    def dispatch(self, model_name: Optional[str], prompt: str, task_type: TaskType = TaskType.SIMPLE_CHAT) -> Optional[str]:
        """
        Dispatch request: if model_name is provided, use it (if available).
        Otherwise, select the best model automatically.
        """
        if model_name:
            # Verify model is available
            entry = self.model_registry.catalog.get_entry(model_name)
            if entry and self._is_provider_healthy(entry.profile.provider):
                logger.info(f"Using explicitly requested model: {model_name}")
                return model_name
            else:
                logger.warning(f"Model {model_name} not available, selecting best alternative")
        
        # Select best available model automatically
        model_name = self.select_best_model(task_type)
        
        if not model_name:
            logger.error("No healthy models available")
            return None
            
        logger.info(f"Dispatching request to model: {model_name}")
        return model_name
        
    def get_recommendation(self, unavailable_model: Optional[str] = None, task_type: TaskType = TaskType.SIMPLE_CHAT) -> Optional[dict]:
        """
        Get a smart recommendation for the best available model (Part20),
        explaining why the original was unavailable and recommending the alternative.
        """
        from ai.models.model_catalog import ModelState
        
        recommendation = {
            "original_model": unavailable_model,
            "available": False,
            "reason": "",
            "recommended_model": None,
            "recommended_display_name": None,
            "score": 0
        }
        
        if unavailable_model:
            entry = self.model_registry.catalog.get_entry(unavailable_model)
            if not entry:
                recommendation["reason"] = f"Model '{unavailable_model}' not found in catalog"
            elif not self._is_provider_healthy(entry.profile.provider):
                provider = self.provider_manager.registry.get_provider(entry.profile.provider)
                if not provider:
                    recommendation["reason"] = f"Provider '{entry.profile.provider}' not found"
                elif not provider.config.enabled:
                    recommendation["reason"] = f"Provider '{entry.profile.provider}' is disabled"
                elif not provider.is_connected():
                    recommendation["reason"] = f"Provider '{entry.profile.provider}' not connected"
                else:
                    recommendation["reason"] = f"Provider '{entry.profile.provider}' unavailable"
        
        # Get best available model
        best_name = self.select_best_model(task_type)
        if best_name:
            entry = self.model_registry.catalog.get_entry(best_name)
            if entry:
                recommendation["available"] = True
                recommendation["recommended_model"] = best_name
                recommendation["recommended_display_name"] = entry.profile.name
        
        return recommendation
