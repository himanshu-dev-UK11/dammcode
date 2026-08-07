"""
DeepInfra Provider.

DeepInfra cloud API provider (using OpenAI-compatible interface).
"""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from core.logger import setup_logger

from ai.providers.base_provider import BaseProvider, ProviderConfig, ProviderStatus


logger = setup_logger(__name__)


class DeepInfraProvider(BaseProvider):
    """
    Provider implementation for DeepInfra API.
    
    DeepInfra provides fast inference for various open models.
    Supports OpenAI-compatible API format.
    
    Requires:
    - API key from DeepInfra
    """
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        # Update config with defaults
        if not self.config.endpoint:
            self.config.endpoint = "https://api.deepinfra.com/v1/openai"
        if not self.config.supports_streaming:
            self.config.supports_streaming = True
        if not self.config.supports_tool_calling:
            self.config.supports_tool_calling = False

    def connect(self) -> bool:
        """Connect to DeepInfra API (validates API key)."""
        try:
            self._update_status(ProviderStatus.CONNECTING)
            
            if not self.config.api_key:
                self._update_status(ProviderStatus.ERROR, "API key not configured")
                return False
            
            # Test connection by listing models
            models = self.refresh_models()
            
            if models:
                self._set_connected()
                self.logger.info("Connected to DeepInfra API")
                return True
            else:
                self._update_status(ProviderStatus.ERROR, "No models available")
                return False
                
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self._update_status(ProviderStatus.ERROR, "Invalid API key")
            elif e.code == 403:
                self._update_status(ProviderStatus.ERROR, "API key lacks required permissions")
            else:
                self._update_status(ProviderStatus.ERROR, f"HTTP {e.code}")
            self.logger.error(f"DeepInfra connection failed: {e}")
            return False
        except Exception as e:
            self._update_status(ProviderStatus.ERROR, str(e))
            self.logger.error(f"Unexpected error connecting to DeepInfra: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from DeepInfra API."""
        self._update_status(ProviderStatus.DISCONNECTED)
        self.logger.info("Disconnected from DeepInfra API")

    def generate_response(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response from DeepInfra."""
        model = self._get_model_id(model_id)
        
        url = f"{self.config.endpoint}/chat/completions"
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        
        if system_prompt:
            payload["messages"].insert(0, {"role": "system", "content": system_prompt})
        
        payload.update(kwargs)
        
        data = json.dumps(payload).encode('utf-8')
        
        request = urllib.request.Request(url, data=data)
        request.add_header("Content-Type", "application/json")
        request.add_header("Authorization", f"Bearer {self.config.api_key}")
        request.add_header("User-Agent", "MyCodingMaster/0.4")
        
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                choices = result.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    return message.get("content", "")
                
                return ""
                
        except Exception as e:
            self.logger.error(f"DeepInfra generation failed: {e}")
            raise

    def stream_response(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        on_chunk: Optional[callable] = None,
        **kwargs
    ) -> str:
        """Stream a response from DeepInfra."""
        model = self._get_model_id(model_id)
        
        url = f"{self.config.endpoint}/chat/completions"
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        
        if system_prompt:
            payload["messages"].insert(0, {"role": "system", "content": system_prompt})
        
        payload.update(kwargs)
        
        data = json.dumps(payload).encode('utf-8')
        
        request = urllib.request.Request(url, data=data)
        request.add_header("Content-Type", "application/json")
        request.add_header("Authorization", f"Bearer {self.config.api_key}")
        request.add_header("User-Agent", "MyCodingMaster/0.4")
        
        full_response = ""
        
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                for line in response:
                    if line:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith("data:"):
                            try:
                                chunk = json.loads(line_str[5:])
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    full_response += content
                                    
                                    if on_chunk:
                                        on_chunk(content)
                                
                                if chunk.get("choices", [{}])[0].get("finish_reason") == "stop":
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            self.logger.error(f"DeepInfra streaming failed: {e}")
            raise
        
        return full_response

    def refresh_models(self) -> List[Dict[str, Any]]:
        """Refresh available models from DeepInfra API."""
        url = f"{self.config.endpoint}/models"
        
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Bearer {self.config.api_key}")
        request.add_header("User-Agent", "MyCodingMaster/0.4")
        
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                models = result.get("data", [])
                parsed_models = []
                
                for model in models:
                    model_info = {
                        "id": model.get("id", ""),
                        "name": model.get("id", ""),
                        "context_window": self._get_context_window(model.get("id", "")),
                        "max_output_tokens": 4096,
                        "supports_streaming": True,
                        "supports_tool_calling": False,
                        "capabilities": [],
                    }
                    parsed_models.append(model_info)
                
                return parsed_models
                
        except Exception as e:
            self.logger.error(f"Failed to refresh DeepInfra models: {e}")
            return []

    # ─────────────────────────────────────────────────────────────────────────────
    # Private Methods
    # ─────────────────────────────────────────────────────────────────────────────

    def _set_connected(self) -> None:
        """Set provider to connected status."""
        self._update_status(ProviderStatus.CONNECTED)

    def _get_context_window(self, model_id: str) -> int:
        """Get context window for a model."""
        if "llama-3" in model_id:
            return 8192
        elif "mistral" in model_id:
            return 32768
        elif "mixtral" in model_id:
            return 32768
        elif "gemma" in model_id:
            return 8192
        return 4096
