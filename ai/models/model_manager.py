"""
Model Manager.

Unified interface for all model interactions through the provider platform.

Uses the provider architecture to route requests to appropriate providers
based on task requirements, provider capabilities, and health status.
"""

from typing import Any, Optional
from core.logger import setup_logger
from ai.models.model_registry import ModelRegistry
from ai.models.model_selector import ModelSelector
from ai.engine.task import Task
from ai.memory.project_context import ProjectContext
from ai.providers.provider_router import ProviderRouter
from ai.providers.provider_manager import ProviderManager
from ai.providers.provider_registry import ProviderRegistry

logger = setup_logger(__name__)

class ModelManager:
    """
    Coordinates model selection, routing, and execution through the provider platform.
    
    The ModelManager now uses the ProviderRouter and ProviderManager to:
    - Select the best provider based on task requirements
    - Route requests to appropriate providers
    - Handle provider health and reconnection
    - Support streaming, tool calling, and other capabilities
    """
    def __init__(
        self,
        provider_registry: ProviderRegistry,
        provider_manager: ProviderManager,
        model_registry: ModelRegistry,
        event_bus: Any
    ):
        self.provider_registry = provider_registry
        self.provider_manager = provider_manager
        self.model_registry = model_registry
        self.event_bus = event_bus
        self.selector = ModelSelector(model_registry)
        self.router = ProviderRouter(provider_registry)

    def execute_request(
        self,
        prompt: str,
        task: Task,
        context: ProjectContext,
        plan: Any = None,
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Selects the best provider and executes the request, handling fallbacks.
        
        Args:
            prompt: The user prompt
            task: The task being executed
            context: Project context
            plan: Optional execution plan
            preferred_provider: Preferred provider name (optional)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            The generated response
        """
        # Step 1: Select Provider based on task requirements
        provider = self.router.select_provider(
            task=task,
            require_streaming=kwargs.get("streaming", False),
            require_vision=kwargs.get("require_vision", False),
            require_tool_calling=kwargs.get("require_tool_calling", False),
            preferred_provider=preferred_provider,
        )
        
        if not provider:
            raise RuntimeError("No suitable provider available to execute the request.")

        provider_name = provider.config.provider_name
        logger.info(f"ModelManager: Selected provider {provider_name}")
        
        # Step 2: Execute with retries
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                # Generate response through the provider
                response = provider.generate_response(
                    prompt=prompt,
                    **kwargs
                )
                
                # Record health
                self.provider_manager._health.record_request(provider_name, success=True)
                logger.info(f"ModelManager: Successfully executed request with {provider_name}")
                
                return response
                
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed on attempt {attempt + 1}: {e}")
                self.provider_manager._health.record_request(provider_name, success=False)
                
                # If provider goes offline, re-select
                if not provider.is_connected():
                    logger.info("Provider went offline. Attempting to select a fallback provider.")
                    provider = self.router.select_provider(
                        task=task,
                        require_streaming=kwargs.get("streaming", False),
                        require_vision=kwargs.get("require_vision", False),
                        require_tool_calling=kwargs.get("require_tool_calling", False),
                        preferred_provider=preferred_provider,
                    )
                    if not provider:
                        raise RuntimeError("All providers exhausted.")

        raise RuntimeError(f"Failed to execute request after {max_retries} retries.")
