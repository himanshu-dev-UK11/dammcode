"""
Provider Discovery.

Automatically detects available local and cloud providers.
"""

import os
import socket
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from core.logger import setup_logger

from ai.providers.base_provider import AuthenticationType


logger = setup_logger(__name__)


class ProviderDiscovery:
    """
    Discovers available AI providers on the local system and network.
    
    Detects:
    - Ollama (local)
    - LM Studio (local)
    - llama.cpp (local)
    - vLLM (local)
    - OpenAI-compatible servers
    - Cloud providers (via configuration)
    """
    
    def __init__(self):
        self.logger = logger
        self._detected_providers: Dict[str, Dict[str, Any]] = {}
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Discovery Methods
    # ─────────────────────────────────────────────────────────────────────────────

    def discover_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Run all discovery methods.
        
        Returns:
            Dict of discovered providers with their details
        """
        self._detected_providers = {}
        
        # Local providers
        self._discover_ollama()
        self._discover_lm_studio()
        self._discover_llama_cpp()
        self._discover_vllm()
        
        # Network services
        self._discover_openai_compatible_servers()
        
        self.logger.info(f"Discovered {len(self._detected_providers)} providers")
        return dict(self._detected_providers)
    
    def discover_ollama(self) -> Optional[Dict[str, Any]]:
        """Discover Ollama provider."""
        return self._discover_ollama()
    
    def discover_lm_studio(self) -> Optional[Dict[str, Any]]:
        """Discover LM Studio provider."""
        return self._discover_lm_studio()
    
    def discover_llama_cpp(self) -> Optional[Dict[str, Any]]:
        """Discover llama.cpp provider."""
        return self._discover_llama_cpp()
    
    def discover_vllm(self) -> Optional[Dict[str, Any]]:
        """Discover vLLM provider."""
        return self._discover_vllm()
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Local Provider Discovery
    # ─────────────────────────────────────────────────────────────────────────────

    def _discover_ollama(self) -> Optional[Dict[str, Any]]:
        """Discover Ollama running locally."""
        ollama = {
            "name": "ollama",
            "display_name": "Ollama",
            "endpoint": "http://localhost:11434",
            "auth_type": AuthenticationType.NONE.value,
            "priority": 10,
            "supports_streaming": True,
            "supports_tool_calling": False,
            "supports_vision": False,
            "supports_function_calling": False,
            "detected_at": datetime.utcnow().isoformat(),
            "detection_method": "http_check",
        }
        
        try:
            # Check if Ollama is running by testing the endpoint
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request("http://localhost:11434/api/tags")
            req.add_header("User-Agent", "MyCodingMaster/0.4")
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    models = data.get("models", [])
                    ollama["detected"] = True
                    ollama["models_count"] = len(models)
                    ollama["default_model"] = models[0].get("name", "") if models else ""
                    ollama["version"] = "unknown"
                    
                    # Try to get version
                    try:
                        req = urllib.request.Request("http://localhost:11434/api/version")
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            ver_data = json.loads(resp.read().decode())
                            ollama["version"] = ver_data.get("version", "unknown")
                    except Exception:
                        pass
                    
                    self._detected_providers["ollama"] = ollama
                    return ollama
                    
        except (urllib.error.URLError, socket.timeout, ConnectionRefusedError):
            pass
        except Exception as e:
            self.logger.debug(f"Ollama detection failed: {e}")
        
        ollama["detected"] = False
        self._detected_providers["ollama"] = ollama
        return ollama

    def _discover_lm_studio(self) -> Optional[Dict[str, Any]]:
        """Discover LM Studio running locally."""
        lm_studio = {
            "name": "lm_studio",
            "display_name": "LM Studio",
            "endpoint": "http://localhost:1234",
            "auth_type": AuthenticationType.NONE.value,
            "priority": 8,
            "supports_streaming": True,
            "supports_tool_calling": True,
            "supports_vision": False,
            "supports_function_calling": False,
            "detected_at": datetime.utcnow().isoformat(),
            "detection_method": "http_check",
        }
        
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request("http://localhost:1234/v1/models")
            req.add_header("User-Agent", "MyCodingMaster/0.4")
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    lm_studio["detected"] = True
                    data = json.loads(response.read().decode())
                    lm_studio["models_count"] = len(data.get("data", []))
                    
                    self._detected_providers["lm_studio"] = lm_studio
                    return lm_studio
                    
        except (urllib.error.URLError, socket.timeout, ConnectionRefusedError):
            pass
        except Exception as e:
            self.logger.debug(f"LM Studio detection failed: {e}")
        
        lm_studio["detected"] = False
        self._detected_providers["lm_studio"] = lm_studio
        return lm_studio

    def _discover_llama_cpp(self) -> Optional[Dict[str, Any]]:
        """Discover llama.cpp server running locally."""
        llama_cpp = {
            "name": "llama_cpp",
            "display_name": "llama.cpp",
            "endpoint": "http://localhost:8080",
            "auth_type": AuthenticationType.NONE.value,
            "priority": 7,
            "supports_streaming": True,
            "supports_tool_calling": True,
            "supports_vision": False,
            "supports_function_calling": False,
            "detected_at": datetime.utcnow().isoformat(),
            "detection_method": "http_check",
        }
        
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request("http://localhost:8080/v1/models")
            req.add_header("User-Agent", "MyCodingMaster/0.4")
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    llama_cpp["detected"] = True
                    self._detected_providers["llama_cpp"] = llama_cpp
                    return llama_cpp
                    
        except (urllib.error.URLError, socket.timeout, ConnectionRefusedError):
            pass
        except Exception as e:
            self.logger.debug(f"llama.cpp detection failed: {e}")
        
        llama_cpp["detected"] = False
        self._detected_providers["llama_cpp"] = llama_cpp
        return llama_cpp

    def _discover_vllm(self) -> Optional[Dict[str, Any]]:
        """Discover vLLM server running locally."""
        vllm = {
            "name": "vllm",
            "display_name": "vLLM",
            "endpoint": "http://localhost:8000",
            "auth_type": AuthenticationType.NONE.value,
            "priority": 9,
            "supports_streaming": True,
            "supports_tool_calling": True,
            "supports_vision": False,
            "supports_function_calling": True,
            "detected_at": datetime.utcnow().isoformat(),
            "detection_method": "http_check",
        }
        
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request("http://localhost:8000/v1/models")
            req.add_header("User-Agent", "MyCodingMaster/0.4")
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    vllm["detected"] = True
                    self._detected_providers["vllm"] = vllm
                    return vllm
                    
        except (urllib.error.URLError, socket.timeout, ConnectionRefusedError):
            pass
        except Exception as e:
            self.logger.debug(f"vLLM detection failed: {e}")
        
        vllm["detected"] = False
        self._detected_providers["vllm"] = vllm
        return vllm

    # ─────────────────────────────────────────────────────────────────────────────
    # Network Discovery
    # ─────────────────────────────────────────────────────────────────────────────

    def _discover_openai_compatible_servers(self) -> List[Dict[str, Any]]:
        """Discover OpenAI-compatible servers on the network."""
        results = []
        
        # Common OpenAI-compatible endpoints
        common_endpoints = [
            ("http://localhost:3000", "vLLM"),
            ("http://localhost:8080", "llama.cpp"),
            ("http://localhost:9000", "Text Generation WebUI"),
        ]
        
        for endpoint, name in common_endpoints:
            provider = {
                "name": name.lower().replace(" ", "_"),
                "display_name": name,
                "endpoint": endpoint,
                "auth_type": AuthenticationType.API_KEY.value,
                "priority": 5,
                "supports_streaming": True,
                "supports_tool_calling": True,
                "supports_vision": False,
                "supports_function_calling": False,
                "detected_at": datetime.utcnow().isoformat(),
                "detection_method": "http_check",
                "compatible_with": "openai",
            }
            
            try:
                import urllib.request
                import urllib.error
                
                req = urllib.request.Request(f"{endpoint}/v1/models")
                req.add_header("User-Agent", "MyCodingMaster/0.4")
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        provider["detected"] = True
                        provider["detected_at"] = datetime.utcnow().isoformat()
                        self._detected_providers[provider["name"]] = provider
                        results.append(provider)
                        
            except Exception:
                provider["detected"] = False
                self._detected_providers[provider["name"]] = provider
        
        return results

    # ─────────────────────────────────────────────────────────────────────────────
    # Utility Methods
    # ─────────────────────────────────────────────────────────────────────────────

    def get_discovered_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get all discovered providers."""
        return dict(self._detected_providers)

    def is_provider_detected(self, provider_name: str) -> bool:
        """Check if a provider has been detected."""
        return self._detected_providers.get(provider_name, {}).get("detected", False)

    def get_detection_details(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed detection info for a provider."""
        return self._detected_providers.get(provider_name)

    def clear_cache(self) -> None:
        """Clear the discovery cache."""
        self._detected_providers.clear()
        self.logger.info("Discovery cache cleared")
