# AI Provider Platform

## Overview

The AI Provider Platform is a provider-based architecture that allows unlimited local or cloud providers to be added without modifying the IDE core. The platform follows SOLID principles and provides a clean separation between the IDE and AI provider implementations.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI Workspace (IDE)                              │
│                         ↓                                               │
│                    Provider Router                                      │
│                         ↓                                               │
│                    Provider Manager                                     │
│                         ↓                                               │
│                    Provider Registry                                    │
│                         ↓                                               │
│           ┌─────────────┬─────────────┬─────────────┐                   │
│           │ Provider    │ Provider    │ Provider    │                   │
│           │ Ollama      │ Gemini      │ OpenAI      │                   │
│           └─────────────┴─────────────┴─────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### BaseProvider (`ai/providers/base_provider.py`)

Abstract base class for all AI providers. Defines the contract that all providers must implement:

```python
class BaseProvider(ABC):
    @abstractmethod
    def connect(self) -> bool: ...
    
    @abstractmethod
    def disconnect(self) -> None: ...
    
    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        **kwargs
    ) -> str: ...
    
    @abstractmethod
    def stream_response(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        on_chunk: Optional[callable] = None,
        **kwargs
    ) -> str: ...
    
    @abstractmethod
    def refresh_models(self) -> List[Dict[str, Any]]: ...
```

### ProviderConfig

Configuration for a provider instance:

```python
@dataclass
class ProviderConfig:
    provider_name: str
    endpoint: str
    auth_type: AuthenticationType  # none, api_key, bearer_token, oauth, custom
    api_key: Optional[str]
    enabled: bool
    priority: int  # Higher = preferred
    default_model: str
    timeout_seconds: int
    retry_count: int
    supports_streaming: bool
    supports_tool_calling: bool
    supports_vision: bool
    supports_function_calling: bool
```

### ProviderRegistry (`ai/providers/provider_registry.py`)

Central registry for managing all providers:

```python
class ProviderRegistry:
    def register_provider(self, provider: BaseProvider) -> None
    def load_all_providers(self) -> List[str]
    def get_provider(self, provider_name: str) -> Optional[BaseProvider]
    def enable_provider(self, provider_name: str) -> bool
    def disable_provider(self, provider_name: str) -> bool
    def refresh_all_models(self) -> Dict[str, List[str]]
    def test_all_connections(self) -> Dict[str, bool]
```

### ProviderManager (`ai/providers/provider_manager.py`)

Unified management interface for all provider operations:

```python
class ProviderManager:
    def enable_provider(self, provider_name: str) -> bool
    def disable_provider(self, provider_name: str) -> bool
    def validate_api_key(self, provider_name: str, api_key: str) -> bool
    def test_connection(self, provider_name: str) -> bool
    def refresh_models(self, provider_name: Optional[str] = None)
    def get_health_status(self) -> Dict[str, Dict[str, Any]]
    def monitor_health(self) -> None  # Background monitoring
```

### ProviderRouter (`ai/providers/provider_router.py`)

Routes requests to the appropriate provider:

```python
class ProviderRouter:
    def route_request(self, prompt: str, **kwargs) -> str
    def route_stream(
        self,
        prompt: str,
        on_chunk: callable,
        **kwargs
    ) -> str
    def select_provider(
        self,
        task: Optional[Task] = None,
        require_streaming: bool = False,
        require_vision: bool = False,
        require_tool_calling: bool = False,
        **kwargs
    ) -> Optional[BaseProvider]
```

### ProviderHealth (`ai/providers/provider_health.py`)

Tracks operational status and reliability of providers:

```python
class ProviderHealth:
    def record_request(
        self,
        provider_name: str,
        success: bool,
        latency_ms: float = 0.0,
        is_timeout: bool = False
    ) -> None
    
    def get_all_health(self) -> Dict[str, Dict[str, Any]]
    def get_unavailable_providers(self) -> List[str]
    def get_recommended_provider(self) -> Optional[str]
```

### ProviderDiscovery (`ai/providers/provider_discovery.py`)

Automatically detects available local providers:

```python
class ProviderDiscovery:
    def discover_all(self) -> Dict[str, Dict[str, Any]]
    def discover_ollama(self) -> Optional[Dict[str, Any]]
    def discover_lm_studio(self) -> Optional[Dict[str, Any]]
    def discover_llama_cpp(self) -> Optional[Dict[str, Any]]
    def discover_vllm(self) -> Optional[Dict[str, Any]]
```

## Provider Implementations

### Local Providers

- **Ollama** (`ollama_provider.py`) - Local LLM server
- **Custom** (`custom_provider.py`) - Generic OpenAI-compatible server

### Cloud Providers

- **Gemini** (`gemini_provider.py`) - Google Gemini API
- **OpenAI** (`openai_provider.py`) - OpenAI API
- **Anthropic** (`anthropic_provider.py`) - Claude API
- **Groq** (`groq_provider.py`) - Groq cloud API
- **Cerebras** (`cerebras_provider.py`) - Cerebras GPT API
- **Fireworks** (`fireworks_provider.py`) - Fireworks AI API
- **DeepInfra** (`deepinfra_provider.py`) - DeepInfra API
- **Together** (`together_provider.py`) - Together AI API

## Configuration

### Provider Configuration

Each provider has its own configuration file in `config/providers/`:

```json
{
    "provider_name": "ollama",
    "endpoint": "http://localhost:11434",
    "auth_type": "none",
    "enabled": true,
    "priority": 10,
    "default_model": "llama3:8b",
    "timeout_seconds": 30,
    "retry_count": 3,
    "supports_streaming": true,
    "supports_tool_calling": false,
    "supports_vision": false,
    "supports_function_calling": false
}
```

### Model Configuration

Each model has its own configuration file in `config/models/`:

```json
{
    "display_name": "Qwen 3 Coder",
    "provider": "qwen",
    "model_id": "qwen3-coder",
    "context_window": 32768,
    "max_output_tokens": 8192,
    "type": "local",
    "supports_streaming": true,
    "supports_tool_calling": true,
    "supports_vision": false,
    "supports_function_calling": true,
    "license": "Apache 2.0",
    "cost_type": "free",
    "priority": 10,
    "version": "3.0",
    "tags": ["coding", "local", "fast"]
}
```

## Adding a New Provider

1. Create a new provider class extending `BaseProvider`:
```python
from ai.providers.base_provider import BaseProvider, ProviderConfig

class MyProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
    
    def connect(self) -> bool:
        # Implement connection logic
        pass
    
    def disconnect(self) -> None:
        # Implement disconnection logic
        pass
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        # Implement response generation
        pass
    
    def stream_response(self, prompt: str, on_chunk: callable, **kwargs) -> str:
        # Implement streaming
        pass
    
    def refresh_models(self) -> List[Dict[str, Any]]:
        # Implement model listing
        pass
```

2. Register the provider in `provider_factory.py`:
```python
from ai.providers.my_provider import MyProvider
ProviderFactory.register_provider("my_provider", MyProvider)
```

3. Create a configuration file `config/providers/my_provider.json`

4. Restart the application

## Request Flow

```
User Prompt
    ↓
ModelManager.execute_request()
    ↓
ProviderRouter.select_provider()
    ↓
ProviderRouter.route_request()
    ↓
Provider.generate_response()
    ↓
Provider Health Recording
    ↓
Response
```

## Health Monitoring

The provider manager runs background health monitoring:
- Checks provider availability every 60 seconds
- Automatically attempts reconnection
- Tracks success/failure rates
- Calculates availability scores

## Event System

Providers fire events for state changes:
- `provider_enabled` - Provider enabled
- `provider_disabled` - Provider disabled
- `provider_connected` - Provider connected
- `provider_disconnected` - Provider disconnected
- `provider_status_changed` - Status changed

## Best Practices

1. **Never hardcode provider details** - Always use the provider platform
2. **Use background threads** for network operations
3. **Implement proper error handling** in provider implementations
4. **Track health metrics** for reliable provider selection
5. **Support streaming** when possible
6. **Implement model refresh** for dynamic model discovery
7. **Use configuration files** for all provider settings
8. **Test connection before use** to provide early feedback

## Migration from Old Model System

The old model system (`ai/models/`) has been replaced by the provider platform. Key changes:

- `ModelManager` now uses `ProviderManager` and `ProviderRouter`
- `ModelRouter` replaced by `ProviderRouter`
- `ModelRegistry` works with `ProviderRegistry`
- Models are now loaded from providers dynamically

## References

- Base Provider Interface: `ai/providers/base_provider.py`
- Provider Factory: `ai/providers/provider_factory.py`
- Provider Registry: `ai/providers/provider_registry.py`
- Provider Manager: `ai/providers/provider_manager.py`
- Provider Router: `ai/providers/provider_router.py`
- Provider Health: `ai/providers/provider_health.py`
- Provider Discovery: `ai/providers/provider_discovery.py`
