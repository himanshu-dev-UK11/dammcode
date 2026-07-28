# Changelog

All notable changes to this project will be documented in this file.

## [1.8.6] - 2026-06-30

### Added
- **Non-blocking Provider/Model Switching** (`ui/ai_workspace/ai_chat_panel.py`):
  - Background thread for provider connection/model refresh
  - New signals: `provider_refresh_started`, `provider_refresh_complete`, `models_updated`
  - Model dropdown now shows status icons (✅ Ready, 🔵 Connected, 🟡 API Required, etc.)

- **Enhanced Smart Model Router** (`ai/models/router.py`):
  - `_is_provider_healthy()` method to check provider availability
  - `_get_healthy_models()` to retrieve only available models
  - Local model prioritization in `select_best_model()` (10,000 point bonus)
  - Enhanced scoring with latency, provider health, cost, and capabilities
  - `get_recommendation()` for smart fallback recommendations
  - Detailed logging of model selection decisions

- **Model Capability Registry** (`ai/models/model_capabilities.py`):
  - Complete set of capability definitions (coding, vision, tool calling, etc.)
  - Icon mapping for each capability
  - `CapabilityInfo` dataclass

- **Provider Health Score System** (`ai/providers/provider_health.py`):
  - `calculate_health_score()` method returning 0-100 score
  - New metrics: `available_models_count`, `requests_today`, `failures_today`, `last_sync`, `recent_errors`
  - `get_health_info()` for UI display

- **Parallel Provider Initialization** (`ai/providers/provider_manager.py`):
  - `initialize_all_providers_parallel()` method that initializes all enabled providers in parallel
  - One background thread per provider, UI stays responsive during initialization

- **Automatic Background Recovery** (`ai/providers/provider_manager.py`):
  - Config change detection via SHA-256 hashing
  - Auto-reconnect/refresh in background thread when provider config (API key, endpoint, etc.) changes

- **Provider Event System** (`ai/providers/provider_manager.py`):
  - `ProviderEventTypes` class with event types (connected, disconnected, failed, recovering, api_changed, etc.)
  - EventBus integration for automatic UI updates

- **Model Quality Profiles** (`ai/models/model_profile.py`):
  - `ModelQualityProfile` dataclass (coding, reasoning, speed, creativity: 1-5)
  - `to_stars()` method for star display

- **Failover Enhancement** (`ai/chat/ai_chat_engine.py`, `ui/ai_workspace/ai_chat_panel.py`):
  - Tries up to two attempts
  - Uses ModelRouter to find best healthy fallback
  - `ai_chat_failover` event, UI displays status message and adds to chat log

- **Provider Routing Report** (`Provider_Routing_Report.md`):
  - Comprehensive report covering all changes

### Improved
- **Automatic Provider Logic**: Now selects only healthy, available models instead of hardcoded DeepSeek
- **Performance**: No more 4-6 second UI freezes when switching providers
- **Version Update**: Bumped to 1.8.6 in `main.py`

### Fixed
- Removed all hardcoded DeepSeek defaults
- UI no longer blocks on provider/model refresh operations

---

## [1.8.5] - 2026-06-30

### Added
- **Centralized Error Manager** (`core/error_manager.py`):
  - Global error handling and recovery
  - Error history tracking
  - Automatic error event emission
  - Recovery handler registration

- **Resource Manager** (`core/resource_manager.py`):
  - Tracks threads, processes, file handles, timers, widgets
  - Automatic resource cleanup on shutdown
  - Prevents resource leaks

- **Config Validator** (`core/config_validator.py`):
  - Validates and recovers configuration files
  - Automatic default config creation
  - Corrupted config backup

- **Performance Watchdog** (`core/performance_watchdog.py`):
  - Real-time memory, CPU, thread monitoring
  - Threshold-based warnings
  - Performance statistics

- **Enhanced Logger** (`core/logger.py`):
  - File logging with automatic rotation
  - Gzip compression for old logs
  - Uncaught exception handling
  - Clean old logs function

- **Diagnostics Panel** (`ui/diagnostics_panel.py`):
  - Real-time performance metrics
  - Error history viewer
  - Resource usage monitor
  - Added to BottomDock as "Diagnostics" tab

### Improved
- **Application Startup** (`main.py`):
  - Startup validation and environment check
  - Missing directory creation
  - Config file validation and recovery
  - Graceful error handling for all subsystems
  - Version updated to 1.8.5

- **Core Exports** (`core/__init__.py`):
  - Added exports for all new subsystems

### Fixed
- Added try/except blocks around all critical operations in main.py
- Prevented application crash from single component failures
