# Qwen3 8B Provider Integration

## Overview

The Qwen provider enables integration with Qwen3 8B, a state-of-the-art local coding model optimized for code generation, completion, and understanding.

## Architecture

```
┌─────────────────────┐
│   UI Layer          │
│  QwenCodingPanel    │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Model Layer       │
│    QwenModel        │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Provider Layer     │
│   QwenProvider      │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Local Server      │
│  LM Studio/Ollama   │
│   (Qwen3 8B Model)  │
└─────────────────────┘
```

## Components

### 1. QwenProvider (`ai/providers/qwen_provider.py`)

**Responsibilities**:
- Manage connection to local Qwen3 server
- Handle OpenAI-compatible API communication
- Support streaming and non-streaming responses
- Provide specialized coding methods

**Key Features**:
- OpenAI-compatible API support
- Streaming response support
- Model discovery and management
- Connection health monitoring
- Retry logic with exponential backoff

**API Methods**:
```python
# Basic generation
generate_response(prompt, model_id, system_prompt, **kwargs) -> str

# Streaming generation
stream_response(prompt, model_id, system_prompt, on_chunk, **kwargs) -> str

# Code-specific methods
generate_code(task, language, context, **kwargs) -> str
explain_code(code, language, **kwargs) -> str
debug_code(code, error, language, **kwargs) -> str
refactor_code(code, goal, language, **kwargs) -> str

# Model management
refresh_models() -> List[Dict[str, Any]]
connect() -> bool
disconnect() -> None
```

### 2. QwenModel (`ai/models/qwen.py`)

**Responsibilities**:
- High-level interface for Qwen operations
- Lazy loading of provider
- Error handling and logging
- Code completion support

**Key Features**:
- Simplified API for common tasks
- Automatic provider initialization
- Connection management
- Fallback handling

**API Methods**:
```python
# Core methods
generate_response(prompt, system_prompt, **kwargs) -> str
generate_code(task, language, context, **kwargs) -> str
explain_code(code, language, **kwargs) -> str
debug_code(code, error, language, **kwargs) -> str
refactor_code(code, goal, language, **kwargs) -> str
complete_code(prefix, suffix, language, **kwargs) -> str
```

### 3. QwenCodingPanel (`ui/ai_workspace/qwen_coding_panel.py`)

**Responsibilities**:
- User interface for Qwen operations
- Operation mode selection
- Connection management UI
- Background thread execution
- Result display

**Key Features**:
- 6 operation modes (Generate, Explain, Debug, Refactor, Complete, Custom)
- Real-time connection status
- Language selector
- Async execution with progress feedback
- Copy to clipboard support

## Configuration

### Provider Config (`config/providers/qwen.json`)

```json
{
  "provider_name": "qwen",
  "endpoint": "http://localhost:1234/v1",
  "auth_type": "none",
  "enabled": true,
  "priority": 15,
  "default_model": "qwen3-8b",
  "timeout_seconds": 120,
  "retry_count": 3,
  "supports_streaming": true,
  "supports_tool_calling": false,
  "supports_vision": false,
  "supports_function_calling": true
}
```

### Key Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `endpoint` | `http://localhost:1234/v1` | Local server API endpoint |
| `priority` | `15` | Provider priority (higher = preferred) |
| `timeout_seconds` | `120` | Request timeout |
| `default_model` | `qwen3-8b` | Default model to use |
| `supports_streaming` | `true` | Enable streaming responses |
| `supports_function_calling` | `true` | Enable function calling |

## Usage Examples

### Basic Code Generation

```python
from ai.models.qwen import QwenModel

qwen = QwenModel(endpoint="http://localhost:1234/v1")

# Generate a function
code = qwen.generate_code(
    task="Create a function to validate email addresses",
    language="python",
    context="This is for a user registration system"
)
print(code)
```

### Code Explanation

```python
code_snippet = """
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)
"""

explanation = qwen.explain_code(code_snippet, language="python")
print(explanation)
```

### Debugging

```python
buggy_code = """
def divide_numbers(a, b):
    return a / b
"""

error_msg = "ZeroDivisionError: division by zero"

solution = qwen.debug_code(
    code=buggy_code,
    error=error_msg,
    language="python"
)
print(solution)
```

### Code Refactoring

```python
old_code = """
def get_user(user_id):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ' + str(user_id))
    result = cursor.fetchone()
    conn.close()
    return result
"""

improved = qwen.refactor_code(
    code=old_code,
    goal="add error handling, use context manager, prevent SQL injection",
    language="python"
)
print(improved)
```

### Streaming Response

```python
from ai.providers.qwen_provider import QwenProvider
from ai.providers.base_provider import ProviderConfig, AuthenticationType

config = ProviderConfig(
    provider_name="qwen",
    endpoint="http://localhost:1234/v1",
    auth_type=AuthenticationType.NONE,
    enabled=True,
    supports_streaming=True
)

provider = QwenProvider(config)
provider.connect()

def on_chunk(text):
    print(text, end='', flush=True)

response = provider.stream_response(
    prompt="Explain async/await in Python",
    on_chunk=on_chunk
)
```

## Integration Points

### 1. Provider Registry

The Qwen provider is automatically registered in `provider_factory.py`:

```python
from ai.providers.qwen_provider import QwenProvider
ProviderFactory.register_provider("qwen", QwenProvider)
```

### 2. Model Registry

Qwen models are discovered and registered automatically:

```python
# Models are registered from provider discovery
model_registry.register_model_from_provider("qwen", model_info)
```

### 3. AI Workspace Panel

The Qwen coding panel is integrated into the AI Workspace:

```python
from ui.ai_workspace.qwen_coding_panel import QwenCodingPanel

# In AI Workspace initialization
qwen_panel = QwenCodingPanel()
qwen_section = Section("Qwen3 Coding Assistant", qwen_panel)
workspace_layout.addWidget(qwen_section)
```

## Performance Optimization

### 1. Request Parameters

Adjust generation parameters for better performance:

```python
# Faster, more deterministic (good for code)
qwen.generate_code(
    task=task,
    language=language,
    temperature=0.3,      # Lower temperature
    max_tokens=2048,      # Limit output length
    top_p=0.9
)

# More creative (good for explanations)
qwen.explain_code(
    code=code,
    language=language,
    temperature=0.7,      # Higher temperature
    max_tokens=4096
)
```

### 2. Model Quantization

Use appropriate quantization level:
- **Q4_K_M**: Fast, good quality (recommended)
- **Q5_K_M**: Better quality, slightly slower
- **Q8_0**: Best quality, slowest

### 3. Context Management

Optimize context window usage:

```python
# For long files, provide relevant excerpt only
context = extract_relevant_context(full_file, max_tokens=2000)
code = qwen.generate_code(task, language, context=context)
```

## Error Handling

### Connection Errors

```python
from ai.models.qwen import QwenModel

try:
    qwen = QwenModel(endpoint="http://localhost:1234/v1")
    response = qwen.generate_response("Hello")
except ConnectionError as e:
    print(f"Failed to connect to Qwen server: {e}")
    # Fallback to another provider or show error to user
```

### Timeout Handling

```python
# Increase timeout for complex requests
qwen.generate_code(
    task=complex_task,
    language="python",
    timeout_seconds=180  # 3 minutes
)
```

### Graceful Degradation

```python
def generate_with_fallback(task, language):
    try:
        # Try Qwen first
        return qwen.generate_code(task, language)
    except Exception as e:
        logger.warning(f"Qwen failed, trying fallback: {e}")
        # Fallback to another provider
        return openai.generate_code(task, language)
```

## Testing

### Unit Tests

```python
import unittest
from ai.providers.qwen_provider import QwenProvider
from ai.providers.base_provider import ProviderConfig, AuthenticationType

class TestQwenProvider(unittest.TestCase):
    def setUp(self):
        config = ProviderConfig(
            provider_name="qwen",
            endpoint="http://localhost:1234/v1",
            auth_type=AuthenticationType.NONE
        )
        self.provider = QwenProvider(config)
    
    def test_connection(self):
        success = self.provider.connect()
        self.assertTrue(success)
    
    def test_generate_code(self):
        code = self.provider.generate_code(
            task="Create a hello world function",
            language="python"
        )
        self.assertIn("def", code)
        self.assertIn("hello", code.lower())
```

### Integration Tests

```python
def test_end_to_end_code_generation():
    # Initialize
    qwen = QwenModel()
    
    # Generate code
    code = qwen.generate_code(
        task="Create a function to calculate factorial",
        language="python"
    )
    
    # Verify code is executable
    exec_globals = {}
    exec(code, exec_globals)
    
    # Test generated function
    assert 'factorial' in exec_globals
    assert exec_globals['factorial'](5) == 120
```

## Monitoring and Logging

### Connection Health

```python
from ai.providers.provider_manager import ProviderManager

manager = ProviderManager(registry, event_bus)
health = manager.get_health_status()

qwen_health = health.get('qwen', {})
print(f"Status: {qwen_health.get('status')}")
print(f"Last tested: {qwen_health.get('last_tested')}")
print(f"Success rate: {qwen_health.get('success_rate')}")
```

### Request Logging

```python
# Enable debug logging
import logging
logging.getLogger('provider.qwen').setLevel(logging.DEBUG)

# Logs will include:
# - Connection attempts
# - Request/response data
# - Error details
# - Performance metrics
```

## Security Considerations

1. **Local Execution**: All processing happens locally
2. **No Data Leaks**: Code never leaves your machine
3. **Authentication**: Optional API key support for secured local servers
4. **Code Review**: Always review AI-generated code before use

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Connection refused" | Ensure local server (LM Studio/Ollama) is running |
| Slow responses | Reduce max_tokens, use lower quantization |
| Out of memory | Use Q4_K_M quantization, close other apps |
| Poor code quality | Lower temperature (0.3-0.5), provide more context |
| Timeout errors | Increase timeout_seconds in config |

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will log:
# - All API requests/responses
# - Connection status changes
# - Error stack traces
```

## Future Enhancements

- [ ] Function calling support
- [ ] Code execution sandbox
- [ ] Multi-file context support
- [ ] Code diff generation
- [ ] Test generation
- [ ] Documentation generation
- [ ] Code review suggestions
- [ ] Performance profiling
- [ ] Security vulnerability scanning

## Contributing

When contributing to the Qwen integration:

1. Follow existing code style
2. Add unit tests for new features
3. Update documentation
4. Test with multiple quantization levels
5. Consider backward compatibility

## License

This integration follows the same license as the main MyCodingMaster IDE project.

## References

- [Qwen2.5-Coder Official Repo](https://github.com/QwenLM/Qwen2.5-Coder)
- [LM Studio Documentation](https://lmstudio.ai/docs)
- [Ollama Documentation](https://ollama.com/docs)
- [OpenAI API Compatibility](https://platform.openai.com/docs/api-reference)
