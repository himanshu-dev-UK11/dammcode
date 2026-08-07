"""
Provider Router.

Routes requests to the appropriate provider based on task requirements.
"""

from typing import Dict, List, Optional, Any
from core.logger import setup_logger

from ai.providers.base_provider import BaseProvider, ProviderStatus
from ai.providers.provider_registry import ProviderRegistry
from ai.engine.task import Task
from ai.memory.project_context import ProjectContext


logger = setup_logger(__name__)


class ProviderRouter:
    """
    Routes AI requests to the best available provider.
    
    Implements routing logic based on:
    - Provider priority
    - Task requirements (streaming, tool calling, vision, etc.)
    - Provider health and availability
    - Model capabilities
    """
    
    def __init__(self, registry: ProviderRegistry):
        self.registry = registry
        self.logger = logger

    # ─────────────────────────────────────────────────────────────────────────────
    # Request Routing
    # ─────────────────────────────────────────────────────────────────────────────

    def route_request(
        self,
        prompt: str,
        task: Optional[Task] = None,
        context: Optional[ProjectContext] = None,
        **kwargs
    ) -> str:
        """
        Route a request to the best available provider.
        
        Args:
            prompt: The user prompt
            task: Optional task for context
            context: Optional project context
            **kwargs: Additional routing options
            
        Returns:
            The generated response
            
        Raises:
            RuntimeError: If no suitable provider is available
        """
        provider = self.select_provider(task, **kwargs)
        
        if not provider:
            raise RuntimeError("No suitable provider available for this request")
        
        self.logger.info(f"Routed request to provider: {provider.config.provider_name}")
        
        try:
            model_id = kwargs.get("model_id")
            response = provider.generate_response(
                prompt=prompt,
                model_id=model_id,
                **kwargs
            )
            return response
            
        except Exception as e:
            self.logger.error(f"Provider {provider.config.provider_name} failed: {e}")
            raise

    def route_stream(
        self,
        prompt: str,
        task: Optional[Task] = None,
        context: Optional[ProjectContext] = None,
        on_chunk=None,
        **kwargs
    ) -> str:
        """
        Route a streaming request to the best available provider.
        
        Args:
            prompt: The user prompt
            task: Optional task for context
            context: Optional project context
            on_chunk: Callback for each response chunk
            **kwargs: Additional routing options
            
        Returns:
            The complete generated response
        """
        provider = self.select_provider(task, require_streaming=True, **kwargs)
        
        if not provider:
            raise RuntimeError("No suitable streaming provider available")
        
        if not provider.supports_streaming():
            self.logger.warning(
                f"Provider {provider.config.provider_name} does not support streaming, "
                "using regular response"
            )
            return self.route_request(prompt, task, context, **kwargs)
        
        self.logger.info(f"Routed streaming request to provider: {provider.config.provider_name}")
        
        try:
            model_id = kwargs.get("model_id")
            response = provider.stream_response(
                prompt=prompt,
                model_id=model_id,
                on_chunk=on_chunk,
                **kwargs
            )
            return response
            
        except Exception as e:
            self.logger.error(f"Streaming provider {provider.config.provider_name} failed: {e}")
            raise

    # ─────────────────────────────────────────────────────────────────────────────
    # Provider Selection
    # ─────────────────────────────────────────────────────────────────────────────

    def select_provider(
        self,
        task: Optional[Task] = None,
        require_streaming: bool = False,
        require_vision: bool = False,
        require_tool_calling: bool = False,
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> Optional[BaseProvider]:
        """
        Select the best provider for a request.
        
        Args:
            task: Optional task for context
            require_streaming: Require streaming support
            require_vision: Require vision support
            require_tool_calling: Require tool/function calling support
            preferred_provider: Preferred provider name
            **kwargs: Additional selection criteria
            
        Returns:
            Selected provider or None if no suitable provider available
        """
        providers = self._get_eligible_providers(
            require_streaming=require_streaming,
            require_vision=require_vision,
            require_tool_calling=require_tool_calling,
        )
        
        if not providers:
            return None
        
        # Sort by priority (highest first)
        providers.sort(key=lambda p: p.config.priority, reverse=True)
        
        # Use preferred provider if available and in the list
        if preferred_provider:
            for provider in providers:
                if provider.config.provider_name == preferred_provider:
                    return provider
        
        # Return highest priority provider
        return providers[0]

    def _get_eligible_providers(
        self,
        require_streaming: bool = False,
        require_vision: bool = False,
        require_tool_calling: bool = False,
    ) -> List[BaseProvider]:
        """Get providers that meet the specified requirements."""
        eligible = []
        
        for provider in self.registry.get_available_providers():
            # Check required capabilities
            if require_streaming and not provider.supports_streaming():
                continue
            
            if require_vision and not provider.supports_vision():
                continue
            
            if require_tool_calling and not provider.supports_tool_calling():
                continue
            
            eligible.append(provider)
        
        return eligible

    # ─────────────────────────────────────────────────────────────────────────────
    # Capability Queries
    # ────────────────────────────────────────────��────────────────────────────────

    def get_providers_supporting(self, capability: str) -> List[BaseProvider]:
        """
        Get all providers supporting a specific capability.
        
        Args:
            capability: Capability name (streaming, vision, tool_calling, etc.)
            
        Returns:
            List of providers supporting the capability
        """
        result = []
        
        for provider in self.registry.get_available_providers():
            if capability == "streaming" and provider.supports_streaming():
                result.append(provider)
            elif capability == "vision" and provider.supports_vision():
                result.append(provider)
            elif capability == "tool_calling" and provider.supports_tool_calling():
                result.append(provider)
            elif capability == "function_calling" and provider.supports_function_calling():
                result.append(provider)
        
        return result

    def get_capabilities_for_provider(self, provider_name: str) -> Dict[str, bool]:
        """
        Get capabilities for a specific provider.
        
        Args:
            provider_name: Provider name
            
        Returns:
            Dict mapping capability names to bool
        """
        provider = self.registry.get_provider(provider_name)
        if not provider:
            return {}
        
        return {
            "streaming": provider.supports_streaming(),
            "vision": provider.supports_vision(),
            "tool_calling": provider.supports_tool_calling(),
            "function_calling": provider.supports_function_calling(),
        }
