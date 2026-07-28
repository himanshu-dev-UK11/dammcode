"""
Gemini Provider.

Google Gemini cloud API provider.
"""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from core.logger import setup_logger

from ai.providers.base_provider import BaseProvider, ProviderConfig, ProviderStatus, AuthenticationType


logger = setup_logger(__name__)


class GeminiProvider(BaseProvider):
    """
    Provider implementation for Google Gemini API.
    
    Supports:
    - Text generation
    - Streaming responses
    - Vision (multimodal)
    - Tool calling
    
    Requires:
    - API key from Google Cloud
    """
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        # Update config with defaults
        if not self.config.endpoint:
            self.config.endpoint = "https://generativelanguage.googleapis.com/v1beta"
        if not self.config.supports_streaming:
            self.config.supports_streaming = True
        if not self.config.supports_vision:
            self.config.supports_vision = True
        if not self.config.supports_tool_calling:
            self.config.supports_tool_calling = True
        if not self.config.supports_function_calling:
            self.config.supports_function_calling = True

    def connect(self) -> bool:
        """Connect to Gemini API (validates API key)."""
        try:
            self._update_status(ProviderStatus.CONNECTING)
            
            if not self.config.api_key:
                self._update_status(ProviderStatus.ERROR, "API key not configured")
                return False
            
            # Test connection by listing models
            models = self.refresh_models()
            
            if models:
                self._set_connected()
                self.logger.info("Connected to Gemini API")
                return True
            else:
                self._update_status(ProviderStatus.ERROR, "No models available")
                return False
                
        except urllib.error.HTTPError as e:
            if e.code == 403:
                self._update_status(ProviderStatus.ERROR, "Invalid API key or insufficient permissions")
            elif e.code == 429:
                self._update_status(ProviderStatus.ERROR, "API quota exceeded")
            else:
                self._update_status(ProviderStatus.ERROR, f"HTTP {e.code}")
            self.logger.error(f"Gemini connection failed: {e}")
            return False
        except Exception as e:
            self._update_status(ProviderStatus.ERROR, str(e))
            self.logger.error(f"Unexpected error connecting to Gemini: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Gemini API."""
        self._update_status(ProviderStatus.DISCONNECTED)
        self.logger.info("Disconnected from Gemini API")

    def generate_response(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response from Gemini."""
        model = self._get_model_id(model_id)
        
        url = f"{self.config.endpoint}/models/{model}:generateContent?key={self.config.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
        }
        
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }
        
        # Add any additional kwargs
        payload.update(kwargs)
        
        data = json.dumps(payload).encode('utf-8')
        
        request = urllib.request.Request(url, data=data)
        request.add_header("Content-Type", "application/json")
        request.add_header("User-Agent", "MyCodingMaster/0.4")
        
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                # Extract text from response
                candidates = result.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                
                return ""
                
        except Exception as e:
            self.logger.error(f"Gemini generation failed: {e}")
            raise

    def stream_response(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        on_chunk: Optional[callable] = None,
        **kwargs
    ) -> str:
        """Stream a response from Gemini."""
        model = self._get_model_id(model_id)
        
        url = f"{self.config.endpoint}/models/{model}:streamGenerateContent?key={self.config.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "stream": True,
        }
        
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }
        
        payload.update(kwargs)
        
        data = json.dumps(payload).encode('utf-8')
        
        request = urllib.request.Request(url, data=data)
        request.add_header("Content-Type", "application/json")
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
                                candidates = chunk.get("candidates", [])
                                if candidates:
                                    content = candidates[0].get("content", {})
                                    parts = content.get("parts", [])
                                    if parts:
                                        text = parts[0].get("text", "")
                                        full_response += text
                                        
                                        if on_chunk:
                                            on_chunk(text)
                                
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            self.logger.error(f"Gemini streaming failed: {e}")
            raise
        
        return full_response

    def refresh_models(self) -> List[Dict[str, Any]]:
        """Refresh available models from Gemini API."""
        url = f"{self.config.endpoint}/models?key={self.config.api_key}"
        request = urllib.request.Request(url)
        request.add_header("User-Agent", "MyCodingMaster/0.4")
        
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                models = result.get("models", [])
                parsed_models = []
                
                for model in models:
                    model_info = {
                        "id": model.get("name", "").replace("models/", ""),
                        "name": model.get("displayName", ""),
                        "context_window": self._parse_context_window(model),
                        "max_output_tokens": self._parse_max_output(model),
                        "supports_vision": self._supports_vision(model),
                        "supports_tool_calling": self._supports_tool_calling(model),
                        "capabilities": self._extract_capabilities(model),
                    }
                    parsed_models.append(model_info)
                
                return parsed_models
                
        except Exception as e:
            self.logger.error(f"Failed to refresh Gemini models: {e}")
            return []

    # ─────────────────────────────────────────────────────────────────────────────
    # Private Methods
    # ─────────────────────────────────────────────────────────────────────────────

    def _set_connected(self) -> None:
        """Set provider to connected status."""
        self._update_status(ProviderStatus.CONNECTED)

    def _parse_context_window(self, model: Dict[str, Any]) -> int:
        """Parse context window from model info."""
        params = model.get("supportedGenerationMethods", {})
        return int(params.get("promptTokenCount", 32000))

    def _parse_max_output(self, model: Dict[str, Any]) -> int:
        """Parse max output tokens from model info."""
        params = model.get("supportedGenerationMethods", {})
        return int(params.get("maxTokenCount", 8192))

    def _supports_vision(self, model: Dict[str, Any]) -> bool:
        """Check if model supports vision."""
        methods = model.get("supportedGenerationMethods", {})
        return "uploadContent" in methods or "multimodal" in str(model.get("metadata", {}))

    def _supports_tool_calling(self, model: Dict[str, Any]) -> bool:
        """Check if model supports tool calling."""
        methods = model.get("supportedGenerationMethods", {})
        return "executableCode" in methods or "generateContent" in str(model.get("metadata", {}))

    def _extract_capabilities(self, model: Dict[str, Any]) -> List[str]:
        """Extract model capabilities."""
        capabilities = []
        
        if self._supports_vision(model):
            capabilities.append("vision")
        if self._supports_tool_calling(model):
            capabilities.append("tool_calling")
        
        return capabilities
