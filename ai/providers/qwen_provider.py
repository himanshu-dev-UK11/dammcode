"""
Qwen Provider.

Local Qwen3 8B coding agent integration using OpenAI-compatible API.
Optimized for code generation, completion, and debugging tasks.
"""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Callable
from core.logger import setup_logger

from ai.providers.base_provider import BaseProvider, ProviderConfig, ProviderStatus


logger = setup_logger(__name__)


class QwenProvider(BaseProvider):
    """
    Provider implementation for Qwen3 8B local coding agent.
    
    Supports:
    - Text generation
    - Streaming responses
    - Code completion
    - Code explanation
    - Debugging assistance
    
    Optimized for:
    - Python, JavaScript, TypeScript
    - Code generation and refactoring
    - API design
    - Documentation generation
    
    Does NOT support:
    - Vision (text-only model)
    - Tool calling (may be added in future)
    """
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        # Update config with defaults
        if not self.config.endpoint:
            # Default to localhost Ollama
            self.config.endpoint = "http://localhost:11434"
        if not self.config.supports_streaming:
            self.config.supports_streaming = True
        if not self.config.supports_tool_calling:
            self.config.supports_tool_calling = False
        if not self.config.supports_vision:
            self.config.supports_vision = False
        if not self.config.supports_function_calling:
            self.config.supports_function_calling = True  # Qwen3 supports function calling
        
        # Detect API type from endpoint
        self.is_ollama = "11434" in self.config.endpoint or "/api/" in self.config.endpoint.lower()
        
        # Qwen-specific optimizations
        self.default_temperature = 0.7
        self.default_top_p = 0.95
        self.default_max_tokens = 4096
        self.context_window = 32768  # Qwen3 8B supports 32K context

    def connect(self) -> bool:
        """Connect to Qwen3 local server (Ollama or OpenAI-compatible)."""
        try:
            self._update_status(ProviderStatus.CONNECTING)
            
            # Test connection based on API type
            if self.is_ollama:
                # Ollama API
                url = f"{self.config.endpoint}/api/tags"
            else:
                # OpenAI-compatible API
                url = f"{self.config.endpoint}/models"
            
            request = urllib.request.Request(url)
            request.add_header("Content-Type", "application/json")
            request.add_header("User-Agent", "MyCodingMaster/0.4-Qwen")
            
            # Add API key if provided (some local servers use auth)
            if self.config.api_key:
                request.add_header("Authorization", f"Bearer {self.config.api_key}")
            
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    
                    # Check for models
                    if self.is_ollama:
                        models = result.get("models", [])
                    else:
                        models = result.get("data", [])
                    
                    if models:
                        self._set_connected()
                        self.logger.info(f"Connected to Qwen3 at {self.config.endpoint} (Ollama: {self.is_ollama})")
                        
                        # Refresh models on successful connection
                        self.refresh_models()
                        return True
                    else:
                        self._update_status(ProviderStatus.ERROR, "No models available")
                        return False
                        
        except urllib.error.URLError as e:
            self._update_status(ProviderStatus.ERROR, f"Connection failed: {str(e)}")
            self.logger.warning(f"Failed to connect to Qwen3: {e}")
        except Exception as e:
            self._update_status(ProviderStatus.ERROR, str(e))
            self.logger.error(f"Unexpected error connecting to Qwen3: {e}")
        
        return False

    def disconnect(self) -> None:
        """Disconnect from Qwen3 server."""
        self._update_status(ProviderStatus.DISCONNECTED)
        self.logger.info(f"Disconnected from Qwen3 at {self.config.endpoint}")

    def generate_response(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate a response from Qwen3.
        
        Args:
            prompt: User prompt
            model_id: Model to use (defaults to qwen3:8b for Ollama or qwen3-8b for OpenAI)
            system_prompt: System prompt for context
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated response text
        """
        model = self._get_model_id(model_id)
        
        if self.is_ollama:
            # Ollama API format - use /api/generate
            url = f"{self.config.endpoint}/api/generate"
            
            # Build prompt with system message if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", self.default_temperature),
                    "top_p": kwargs.get("top_p", self.default_top_p),
                    "num_predict": kwargs.get("max_tokens", self.default_max_tokens),
                }
            }
        else:
            # OpenAI-compatible API format
            url = f"{self.config.endpoint}/chat/completions"
            
            # Build messages array
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "temperature": kwargs.get("temperature", self.default_temperature),
                "top_p": kwargs.get("top_p", self.default_top_p),
                "max_tokens": kwargs.get("max_tokens", self.default_max_tokens),
            }
        
        data = json.dumps(payload).encode('utf-8')
        
        request = urllib.request.Request(url, data=data)
        request.add_header("Content-Type", "application/json")
        request.add_header("User-Agent", "MyCodingMaster/0.4-Qwen")
        
        if self.config.api_key:
            request.add_header("Authorization", f"Bearer {self.config.api_key}")
        
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if self.is_ollama:
                    # Ollama generate format
                    return result.get("response", "")
                else:
                    # OpenAI format
                    choices = result.get("choices", [])
                    if choices:
                        message = choices[0].get("message", {})
                        content = message.get("content", "")
                        return content
                
                return ""
                
        except urllib.error.HTTPError as e:
            error_msg = f"Qwen3 API error: {e.code} - {e.reason}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            self.logger.error(f"Qwen3 generation failed: {e}")
            raise

    def stream_response(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> str:
        """
        Stream a response from Qwen3.
        
        Args:
            prompt: User prompt
            model_id: Model to use
            system_prompt: System prompt for context
            on_chunk: Callback for each chunk
            **kwargs: Additional parameters
            
        Returns:
            Complete generated response
        """
        model = self._get_model_id(model_id)
        full_response = ""
        
        if self.is_ollama:
            # Ollama API format - use generate endpoint
            url = f"{self.config.endpoint}/api/generate"
            
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": kwargs.get("temperature", self.default_temperature),
                    "top_p": kwargs.get("top_p", self.default_top_p),
                    "num_predict": kwargs.get("max_tokens", self.default_max_tokens),
                }
            }
        else:
            # OpenAI-compatible API format
            url = f"{self.config.endpoint}/chat/completions"
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": True,
                "temperature": kwargs.get("temperature", self.default_temperature),
                "top_p": kwargs.get("top_p", self.default_top_p),
                "max_tokens": kwargs.get("max_tokens", self.default_max_tokens),
            }
        
        data = json.dumps(payload).encode('utf-8')
        
        request = urllib.request.Request(url, data=data)
        request.add_header("Content-Type", "application/json")
        request.add_header("User-Agent", "MyCodingMaster/0.4-Qwen")
        
        if self.config.api_key:
            request.add_header("Authorization", f"Bearer {self.config.api_key}")
        
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                for line in response:
                    if line:
                        line_str = line.decode('utf-8').strip()
                        
                        if not line_str:
                            continue
                        
                        try:
                            if self.is_ollama:
                                # Ollama generate format - direct JSON per line
                                chunk = json.loads(line_str)
                                response_text = chunk.get("response", "")
                                
                                if response_text:
                                    full_response += response_text
                                    if on_chunk:
                                        on_chunk(response_text)
                                
                                if chunk.get("done", False):
                                    break
                            else:
                                # OpenAI format - SSE with "data: " prefix
                                if line_str.startswith(':'):
                                    continue
                                
                                if line_str.startswith('data: '):
                                    data_str = line_str[6:]
                                    
                                    if data_str == '[DONE]':
                                        break
                                    
                                    chunk = json.loads(data_str)
                                    choices = chunk.get("choices", [])
                                    
                                    if choices:
                                        delta = choices[0].get("delta", {})
                                        content = delta.get("content", "")
                                        
                                        if content:
                                            full_response += content
                                            if on_chunk:
                                                on_chunk(content)
                                        
                                        if choices[0].get("finish_reason"):
                                            break
                                            
                        except json.JSONDecodeError:
                            continue
                                
        except Exception as e:
            self.logger.error(f"Qwen3 streaming failed: {e}")
            raise
        
        return full_response

    def refresh_models(self) -> List[Dict[str, Any]]:
        """
        Refresh available models from Qwen3 server.
        
        Returns:
            List of model information dictionaries
        """
        if self.is_ollama:
            url = f"{self.config.endpoint}/api/tags"
        else:
            url = f"{self.config.endpoint}/models"
        
        request = urllib.request.Request(url)
        request.add_header("User-Agent", "MyCodingMaster/0.4-Qwen")
        
        if self.config.api_key:
            request.add_header("Authorization", f"Bearer {self.config.api_key}")
        
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if self.is_ollama:
                    # Ollama format
                    models = result.get("models", [])
                    parsed_models = []
                    
                    for model in models:
                        model_name = model.get("name", "")
                        
                        # Only include Qwen models
                        if "qwen" in model_name.lower():
                            is_coder = "coder" in model_name.lower()
                            
                            model_info = {
                                "id": model_name,
                                "name": model_name,
                                "size": model.get("size", 0),
                                "digest": model.get("digest", ""),
                                "context_window": self.context_window,
                                "max_output_tokens": self.default_max_tokens,
                                "type": "local",
                                "provider": "qwen",
                                "capabilities": ["code_generation", "code_completion", "chat"] if is_coder else ["chat"],
                                "supports_streaming": True,
                                "supports_function_calling": True,
                                "supports_vision": False,
                                "supported_languages": [
                                    "python", "javascript", "typescript", "java", 
                                    "c++", "c#", "go", "rust", "ruby", "php"
                                ] if is_coder else ["*"],
                                "strengths": [
                                    "code_generation",
                                    "code_completion", 
                                    "debugging",
                                    "refactoring"
                                ] if is_coder else ["general"],
                            }
                            parsed_models.append(model_info)
                else:
                    # OpenAI-compatible format
                    models = result.get("data", [])
                    parsed_models = []
                    
                    for model in models:
                        model_id = model.get("id", "")
                        
                        # Extract model capabilities
                        is_qwen = "qwen" in model_id.lower()
                        is_coder = any(x in model_id.lower() for x in ["coder", "code", "qwen3"])
                        
                        model_info = {
                            "id": model_id,
                            "name": model.get("name", model_id),
                            "context_window": self.context_window,
                            "max_output_tokens": self.default_max_tokens,
                            "type": "local",
                            "provider": "qwen",
                            "capabilities": self._extract_capabilities(model_id),
                            "supports_streaming": True,
                            "supports_function_calling": is_qwen,
                            "supports_vision": False,
                            "supported_languages": [
                                "python", "javascript", "typescript", "java", 
                                "c++", "c#", "go", "rust", "ruby", "php"
                            ] if is_coder else ["*"],
                            "strengths": [
                                "code_generation",
                                "code_completion", 
                                "debugging",
                                "refactoring"
                            ] if is_coder else ["general"],
                        }
                        parsed_models.append(model_info)
                
                # Store models
                self._set_models(parsed_models)
                self.logger.info(f"Refreshed {len(parsed_models)} Qwen models")
                
                return parsed_models
                
        except Exception as e:
            self.logger.error(f"Failed to refresh Qwen3 models: {e}")
            return []

    # ─────────────────────────────────────────────────────────────────────────────
    # Qwen-Specific Features
    # ─────────────────────────────────────────────────────────────────────────────

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
            task: Description of code to generate
            language: Programming language
            context: Additional context or existing code
            **kwargs: Additional parameters
            
        Returns:
            Generated code
        """
        system_prompt = f"""You are an expert {language} programmer. Generate clean, 
efficient, and well-documented code. Follow best practices and modern patterns."""
        
        prompt = f"Task: {task}"
        if context:
            prompt = f"Context:\n{context}\n\n{prompt}"
        
        return self.generate_response(prompt, system_prompt=system_prompt, **kwargs)

    def explain_code(
        self,
        code: str,
        language: str = "python",
        **kwargs
    ) -> str:
        """
        Explain what code does.
        
        Args:
            code: Code to explain
            language: Programming language
            **kwargs: Additional parameters
            
        Returns:
            Code explanation
        """
        system_prompt = "You are an expert code reviewer. Explain code clearly and concisely."
        
        prompt = f"Explain this {language} code:\n\n```{language}\n{code}\n```"
        
        return self.generate_response(prompt, system_prompt=system_prompt, **kwargs)

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
        system_prompt = "You are an expert debugger. Identify issues and provide solutions."
        
        prompt = f"""Debug this {language} code:

```{language}
{code}
```

Error:
{error}

Identify the issue and suggest a fix."""
        
        return self.generate_response(prompt, system_prompt=system_prompt, **kwargs)

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
            goal: Refactoring goal (e.g., "improve performance", "add error handling")
            language: Programming language
            **kwargs: Additional parameters
            
        Returns:
            Refactored code
        """
        system_prompt = f"You are an expert {language} developer. Refactor code to improve quality."
        
        prompt = f"""Refactor this code to {goal}:

```{language}
{code}
```"""
        
        return self.generate_response(prompt, system_prompt=system_prompt, **kwargs)

    # ─────────────────────────────────────────────────────────────────────────────
    # Private Methods
    # ─────────────────────────────────────────────────────────────────────────────

    def _set_connected(self) -> None:
        """Set provider to connected status."""
        self._update_status(ProviderStatus.CONNECTED)

    def _extract_capabilities(self, model_id: str) -> List[str]:
        """Extract model capabilities from model ID."""
        capabilities = []
        
        model_lower = model_id.lower()
        
        if "qwen" in model_lower:
            capabilities.append("chat")
        if any(x in model_lower for x in ["coder", "code", "qwen3"]):
            capabilities.extend(["code_generation", "code_completion"])
        if "instruct" in model_lower or "chat" in model_lower:
            capabilities.append("instruction_following")
        
        return capabilities if capabilities else ["general"]

