"""
Anthropic Provider.

Anthropic (Claude) cloud API provider.
"""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from core.logger import setup_logger

from ai.providers.base_provider import BaseProvider, ProviderConfig, ProviderStatus


logger = setup_logger(__name__)


class AnthropicProvider(BaseProvider):
    """
    Provider implementation for Anthropic API (Claude).
    
    Supports:
    - Text generation
    - Streaming responses
    - Vision (Claude 3+)
    - Tool calling (Claude 3.5+)
    
    Requires:
    - API key from Anthropic
    """
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        # Update config with defaults
        if not self.config.endpoint:
            self.config.endpoint = "https://api.anthropic.com/v1"
        if not self.config.supports_streaming:
            self.config.supports_streaming = True
        if not self.config.supports_vision:
            self.config.supports_vision = True
        if not self.config.supports_tool_calling:
            self.config.supports_tool_calling = True

    def connect(self) -> bool:
        """Connect to Anthropic API (validates API key)."""
        try:
            self._update_status(ProviderStatus.CONNECTING)
            
            if not self.config.api_key:
                self._update_status(ProviderStatus.ERROR, "API key not configured")
                return False
            
            # Test connection by listing models
            models = self.refresh_models()
            
            if models:
                self._set_connected()
                self.logger.info("Connected to Anthropic API")
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
            self.logger.error(f"Anthropic connection failed: {e}")
            return False
        except Exception as e:
            self._update_status(ProviderStatus.ERROR, str(e))
            self.logger.error(f"Unexpected error connecting to Anthropic: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Anthropic API."""
        self._update_status(ProviderStatus.DISCONNECTED)
        self.logger.info("Disconnected from Anthropic API")

    def generate_response(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response from Anthropic."""
        model = self._get_model_id(model_id)
        
        url = f"{self.config.endpoint}/messages"
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        # Add any additional kwargs
        payload.update(kwargs)
        
        data = json.dumps(payload).encode('utf-8')
        
        request = urllib.request.Request(url, data=data)
        request.add_header("Content-Type", "application/json")
        request.add_header("x-api-key", self.config.api_key)
        request.add_header("anthropic-version", "2023-06-01")
        request.add_header("User-Agent", "MyCodingMaster/0.4")
        
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                # Extract text from response
                content = result.get("content", [])
                if content:
                    for item in content:
                        if item.get("type") == "text":
                            return item.get("text", "")
                
                return ""
                
        except Exception as e:
            self.logger.error(f"Anthropic generation failed: {e}")
            raise

    def stream_response(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        on_chunk: Optional[callable] = None,
        **kwargs
    ) -> str:
        """Stream a response from Anthropic."""
        model = self._get_model_id(model_id)
        
        url = f"{self.config.endpoint}/messages"
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        payload.update(kwargs)
        
        data = json.dumps(payload).encode('utf-8')
        
        request = urllib.request.Request(url, data=data)
        request.add_header("Content-Type", "application/json")
        request.add_header("x-api-key", self.config.api_key)
        request.add_header("anthropic-version", "2023-06-01")
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
                                event = chunk.get("type", "")
                                
                                if event == "content_block_delta":
                                    delta = chunk.get("delta", {})
                                    text = delta.get("text", "")
                                    full_response += text
                                    
                                    if on_chunk:
                                        on_chunk(text)
                                
                                if event == "message_stop":
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            self.logger.error(f"Anthropic streaming failed: {e}")
            raise
        
        return full_response

    def refresh_models(self) -> List[Dict[str, Any]]:
        """Refresh available models from Anthropic API."""
        url = f"{self.config.endpoint}/models"
        
        request = urllib.request.Request(url)
        request.add_header("x-api-key", self.config.api_key)
        request.add_header("anthropic-version", "2023-06-01")
        request.add_header("User-Agent", "MyCodingMaster/0.4")
        
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                models = result.get("data", [])
                parsed_models = []
                
                for model in models:
                    model_info = {
                        "id": model.get("id", ""),
                        "name": model.get("displayName", ""),
                        "context_window": self._get_context_window(model.get("id", "")),
                        "max_output_tokens": 8192,
                        "supports_vision": self._supports_vision(model.get("id", "")),
                        "supports_tool_calling": self._supports_tool_calling(model.get("id", "")),
                        "capabilities": self._extract_capabilities(model.get("id", "")),
                    }
                    parsed_models.append(model_info)
                
                return parsed_models
                
        except Exception as e:
            self.logger.error(f"Failed to refresh Anthropic models: {e}")
            return []

    # ─────────────────────────────────────────────────────────────────────────────
    # Private Methods
    # ─────────────────────────────────────────────────────────────────────────────

    def _set_connected(self) -> None:
        """Set provider to connected status."""
        self._update_status(ProviderStatus.CONNECTED)

    def _get_context_window(self, model_id: str) -> int:
        """Get context window for a model."""
        if "claude-3.5-sonnet" in model_id or "claude-3-opus" in model_id:
            return 200000
        elif "claude-3-sonnet" in model_id or "claude-3-haiku" in model_id:
            return 200000
        return 100000

    def _supports_vision(self, model_id: str) -> bool:
        """Check if model supports vision."""
        return "claude-3" in model_id.lower()

    def _supports_tool_calling(self, model_id: str) -> bool:
        """Check if model supports tool calling."""
        return "claude-3.5" in model_id.lower() or "claude-3-opus" in model_id.lower()

    def _extract_capabilities(self, model_id: str) -> List[str]:
        """Extract model capabilities."""
        capabilities = []
        
        if self._supports_vision(model_id):
            capabilities.append("vision")
        if self._supports_tool_calling(model_id):
            capabilities.append("tool_calling")
        
        return capabilities
