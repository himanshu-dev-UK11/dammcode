"""
Local Qwen3 8B integration.

Provides high-level interface for Qwen3 coding agent.
Works in conjunction with QwenProvider for API communication.
"""

from typing import Optional, Dict, Any
from ai.models.base_model import BaseModel
from core.logger import setup_logger

logger = setup_logger(__name__)


class QwenModel(BaseModel):
    """
    High-level interface for Qwen3 8B coding agent.
    
    Provides specialized methods for code-related tasks:
    - Code generation
    - Code completion
    - Debugging assistance
    - Code explanation
    - Refactoring suggestions
    """
    
    def __init__(self, endpoint: str = "http://localhost:1234/v1", api_key: Optional[str] = None):
        """
        Initialize Qwen model.
        
        Args:
            endpoint: API endpoint (default: http://localhost:1234/v1)
            api_key: Optional API key for authenticated access
        """
        super().__init__("qwen")
        self.endpoint = endpoint
        self.api_key = api_key
        self._provider = None
        
    def _get_provider(self):
        """Lazy load provider to avoid circular imports."""
        if self._provider is None:
            from ai.providers.qwen_provider import QwenProvider
            from ai.providers.base_provider import ProviderConfig, AuthenticationType
            
            config = ProviderConfig(
                provider_name="qwen",
                endpoint=self.endpoint,
                auth_type=AuthenticationType.API_KEY if self.api_key else AuthenticationType.NONE,
                api_key=self.api_key,
                enabled=True,
                default_model="qwen3-8b",
                supports_streaming=True,
                supports_function_calling=True,
            )
            
            self._provider = QwenProvider(config)
            
            # Try to connect
            if not self._provider.connect():
                logger.warning("Failed to connect to Qwen3 server")
        
        return self._provider
        
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Generate a response from Qwen3.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            **kwargs: Additional parameters
            
        Returns:
            Generated response text
        """
        provider = self._get_provider()
        
        if not provider or not provider.is_connected():
            self.logger.error("Qwen3 provider not connected")
            return ""
        
        try:
            return provider.generate_response(prompt, system_prompt=system_prompt, **kwargs)
        except Exception as e:
            self.logger.error(f"Failed to generate response: {e}")
            return ""
    
    def generate_code(
        self, 
        task: str, 
        language: str = "python",
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate code for a specific task.
        
        Args:
            task: Description of what to code
            language: Target programming language
            context: Additional context or existing code
            **kwargs: Additional parameters
            
        Returns:
            Generated code
        """
        provider = self._get_provider()
        
        if not provider or not provider.is_connected():
            self.logger.error("Qwen3 provider not connected")
            return ""
        
        try:
            return provider.generate_code(task, language, context, **kwargs)
        except Exception as e:
            self.logger.error(f"Failed to generate code: {e}")
            return ""
    
    def explain_code(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Explain what code does.
        
        Args:
            code: Code to explain
            language: Programming language
            **kwargs: Additional parameters
            
        Returns:
            Code explanation
        """
        provider = self._get_provider()
        
        if not provider or not provider.is_connected():
            self.logger.error("Qwen3 provider not connected")
            return ""
        
        try:
            return provider.explain_code(code, language, **kwargs)
        except Exception as e:
            self.logger.error(f"Failed to explain code: {e}")
            return ""
    
    def debug_code(
        self,
        code: str,
        error: str,
        language: str = "python",
        **kwargs
    ) -> str:
        """
        Help debug code with an error.
        
        Args:
            code: Code with error
            error: Error message
            language: Programming language
            **kwargs: Additional parameters
            
        Returns:
            Debugging suggestions
        """
        provider = self._get_provider()
        
        if not provider or not provider.is_connected():
            self.logger.error("Qwen3 provider not connected")
            return ""
        
        try:
            return provider.debug_code(code, error, language, **kwargs)
        except Exception as e:
            self.logger.error(f"Failed to debug code: {e}")
            return ""
    
    def refactor_code(
        self,
        code: str,
        goal: str,
        language: str = "python",
        **kwargs
    ) -> str:
        """
        Refactor code for improvement.
        
        Args:
            code: Code to refactor
            goal: Refactoring goal
            language: Programming language
            **kwargs: Additional parameters
            
        Returns:
            Refactored code
        """
        provider = self._get_provider()
        
        if not provider or not provider.is_connected():
            self.logger.error("Qwen3 provider not connected")
            return ""
        
        try:
            return provider.refactor_code(code, goal, language, **kwargs)
        except Exception as e:
            self.logger.error(f"Failed to refactor code: {e}")
            return ""
    
    def complete_code(
        self,
        prefix: str,
        suffix: Optional[str] = None,
        language: str = "python",
        **kwargs
    ) -> str:
        """
        Complete code based on prefix and optional suffix.
        
        Args:
            prefix: Code before cursor
            suffix: Code after cursor (optional)
            language: Programming language
            **kwargs: Additional parameters
            
        Returns:
            Code completion
        """
        system_prompt = f"You are a code completion assistant for {language}. Complete the code naturally."
        
        if suffix:
            prompt = f"Complete the code between prefix and suffix:\n\nPrefix:\n{prefix}\n\nSuffix:\n{suffix}"
        else:
            prompt = f"Complete this code:\n\n{prefix}"
        
        return self.generate_response(prompt, system_prompt=system_prompt, **kwargs)
