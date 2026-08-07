"""
Ollama Provider.

Local LLM provider using Ollama API.
"""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from core.logger import setup_logger

from ai.providers.base_provider import BaseProvider, ProviderConfig, ProviderStatus


logger = setup_logger(__name__)


class OllamaProvider(BaseProvider):
    """
    Provider implementation for Ollama local LLM server.
    
    Supports:
    - Text generation
    - Streaming responses
    - Model listing
    
    Does NOT support:
    - Vision
    - Tool calling (currently)
    """
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        # Update config with defaults if not set
        if not self.config.endpoint:
            self.config.endpoint = "http://localhost:11434"
        if not self.config.supports_streaming:
            self.config.supports_streaming = True
        if not self.config.supports_tool_calling:
            self.config.supports_tool_calling = False
        if not self.config.supports_vision:
            self.config.supports_vision = False

    def connect(self) -> bool:
        """Connect to Ollama server."""
        try:
            self._update_status(ProviderStatus.CONNECTING)
            
            # Test connection
            url = f"{self.config.endpoint}/api/tags"
            request = urllib.request.Request(url)
            request.add_header("User-Agent", "MyCodingMaster/0.4")
            
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                if response.status == 200:
                    self._set_connected()
                    self.logger.info(f"Connected to Ollama at {self.config.endpoint}")
                    return True
                    
        except urllib.error.URLError as e:
            self._update_status(ProviderStatus.ERROR, str(e))
            self.logger.warning(f"Failed to connect to Ollama: {e}")
        except Exception as e:
            self._update_status(ProviderStatus.ERROR, str(e))
            self.logger.error(f"Unexpected error connecting to Ollama: {e}")
        
        return False

    def disconnect(self) -> None:
        """Disconnect from Ollama server."""
        self._update_status(ProviderStatus.DISCONNECTED)
        self.logger.info(f"Disconnected from Ollama at {self.config.endpoint}")

    def generate_response(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response from Ollama."""
        model = self._get_model_id(model_id)
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        # Add any additional kwargs
        payload.update(kwargs)
        
        url = f"{self.config.endpoint}/api/generate"
        data = json.dumps(payload).encode('utf-8')
        
        request = urllib.request.Request(url, data=data)
        request.add_header("Content-Type", "application/json")
        request.add_header("User-Agent", "MyCodingMaster/0.4")
        
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "")
                
        except Exception as e:
            self.logger.error(f"Ollama generation failed: {e}")
            raise

    def stream_response(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        on_chunk: Optional[callable] = None,
        **kwargs
    ) -> str:
        """Stream a response from Ollama."""
        model = self._get_model_id(model_id)
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        payload.update(kwargs)
        
        url = f"{self.config.endpoint}/api/generate"
        data = json.dumps(payload).encode('utf-8')
        
        request = urllib.request.Request(url, data=data)
        request.add_header("Content-Type", "application/json")
        request.add_header("User-Agent", "MyCodingMaster/0.4")
        
        full_response = ""
        
        # Use a long timeout for streaming — Ollama needs time to load model on cold start
        stream_timeout = max(self.config.timeout_seconds, 300)
        
        try:
            with urllib.request.urlopen(request, timeout=stream_timeout) as response:
                for line in response:
                    if line:
                        line_str = line.decode('utf-8').strip()
                        if line_str:
                            try:
                                chunk = json.loads(line_str)
                                response_text = chunk.get("response", "")
                                full_response += response_text
                                
                                if on_chunk and response_text:
                                    on_chunk(response_text)
                                
                                if chunk.get("done", False):
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                                
        except urllib.error.URLError as e:
            self.logger.error(f"Ollama streaming failed (URLError): {e}")
            # Try to reconnect for next call
            self._update_status(ProviderStatus.ERROR, str(e))
            raise
        except Exception as e:
            self.logger.error(f"Ollama streaming failed: {e}")
            raise
        
        return full_response

    def refresh_models(self) -> List[Dict[str, Any]]:
        """Refresh available models from Ollama."""
        url = f"{self.config.endpoint}/api/tags"
        request = urllib.request.Request(url)
        request.add_header("User-Agent", "MyCodingMaster/0.4")
        
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode('utf-8'))
                models = result.get("models", [])
                
                # Parse model info
                parsed_models = []
                for model in models:
                    parsed_models.append({
                        "id": model.get("name", ""),
                        "name": model.get("name", ""),
                        "size": model.get("size", 0),
                        "digest": model.get("digest", ""),
                        "details": model.get("details", {}),
                    })
                
                return parsed_models
                
        except Exception as e:
            self.logger.error(f"Failed to refresh Ollama models: {e}")
            return []

    # ─────────────────────────────────────────────────────────────────────────────
    # Private Methods
    # ─────────────────────────────────────────────────────────────────────────────

    def _set_connected(self) -> None:
        """Set provider to connected status."""
        self._update_status(ProviderStatus.CONNECTED)
