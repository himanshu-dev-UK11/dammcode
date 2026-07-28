"""
Application entry point for MyCodingMaster — v1.9.0

Initializes core systems with optimized startup for fast UI interactivity.
Heavy systems initialize in background after window is shown.

Configuration:
- Set OPTIMIZED_STARTUP=False to use legacy sequential initialization
- Set OPTIMIZED_STARTUP=True for fast background initialization (default)
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from core.logger import setup_logger
from core.event_bus import EventBus
from core.error_manager import get_error_manager
from core.resource_manager import get_resource_manager
from core.config_validator import get_config_validator
from core.performance_watchdog import get_performance_watchdog
from core.startup_profiler import get_startup_profiler, ProfilePhase
from ui.main_window import MainWindow
from ui.theme import ThemeManager
from ui.settings_manager import get_settings_manager

logger = setup_logger(__name__)
profiler = get_startup_profiler()

# Configuration: Enable optimized startup by default
OPTIMIZED_STARTUP = os.environ.get('OPTIMIZED_STARTUP', 'true').lower() != 'false'


def validate_startup() -> bool:
    """Validate startup environment and create missing directories/files."""
    with ProfilePhase("validate_startup"):
        logger.info("Validating startup environment...")
        
        # Create required directories
        with ProfilePhase("create_directories"):
            required_dirs = ["config", "config/providers", "config/models", "logs", "temp"]
            for dir_name in required_dirs:
                try:
                    Path(dir_name).mkdir(parents=True, exist_ok=True)
                    logger.debug(f"Ensured directory: {dir_name}")
                except Exception as e:
                    logger.error(f"Failed to create directory {dir_name}: {e}")
                    return False
        
        # Validate config files
        with ProfilePhase("validate_configs"):
            config_validator = get_config_validator()
            try:
                # Load and validate all configs
                config_validator.validate_and_load("settings.json")
                config_validator.validate_and_load("recent_projects.json")
                config_validator.validate_and_load("pinned_projects.json")
                config_validator.validate_and_load("workspace_session.json")
                config_validator.validate_and_load("editor_session.json")
                config_validator.validate_and_load("chat_sessions.json")
                config_validator.validate_and_load("recent_commands.json")
            except Exception as e:
                logger.error(f"Config validation failed: {e}")
                # Continue anyway - config validator recovers
        
        logger.info("Startup validation complete")
        return True


def initialize_background_systems(event_bus, window, error_manager):
    """
    Initialize heavy systems in background after UI is shown.
    This is only called when OPTIMIZED_STARTUP is True.
    """
    if not OPTIMIZED_STARTUP:
        return None
    
    from core.background_initializer import BackgroundInitializer
    
    initializer = BackgroundInitializer()
    
    def init_managers_and_heavy_systems():
        """Initialize all heavy systems in one background task."""
        try:
            # Watchdog
            watchdog = get_performance_watchdog()
            watchdog.set_event_bus(event_bus)
            watchdog.start()
            
            # Managers
            from core.workspace_manager import WorkspaceManager
            from core.editor_manager import EditorManager
            from core.lsp.lsp_manager import LSPManager
            from ai.intelligence.project_analyzer import ProjectAnalyzer
            
            workspace_manager = WorkspaceManager(event_bus)
            editor_manager = EditorManager(event_bus)
            lsp_manager = LSPManager(event_bus)
            project_analyzer = ProjectAnalyzer(event_bus)
            
            # Connect Project Analyzer events
            def _on_workspace_loaded_for_analyzer(data):
                path = data.get("path")
                if path:
                    project_analyzer.analyze(path)
            
            def _on_file_close(data):
                path = data.get("path", "")
                if path:
                    try:
                        window.center.editor_tabs.force_close_tab(path)
                    except Exception as e:
                        import traceback
                        exc_type = type(e)
                        exc_value = e
                        exc_traceback = e.__traceback__
                        error_manager.handle_exception(exc_type, exc_value, exc_traceback, "editor")
            
            event_bus.subscribe("workspace_loaded", _on_workspace_loaded_for_analyzer)
            event_bus.subscribe("file_force_closed", _on_file_close)
            
            # Connect LSP manager event
            def _on_workspace_opened(data):
                path = data.get("path", "")
                if path:
                    try:
                        lsp_manager.set_workspace(Path(path))
                    except Exception as e:
                        import traceback
                        exc_type = type(e)
                        exc_value = e
                        exc_traceback = e.__traceback__
                        error_manager.handle_exception(exc_type, exc_value, exc_traceback, "lsp")
            
            event_bus.subscribe("workspace_opened", _on_workspace_opened)
            
            # Wire managers to window on main thread
            QTimer.singleShot(0, lambda: window.set_lsp_manager(lsp_manager))
            QTimer.singleShot(0, lambda: window.set_project_analyzer(project_analyzer))
            QTimer.singleShot(0, lambda: window.set_workspace_manager(workspace_manager))
            
            # Provider Platform
            from ai.providers.provider_registry import ProviderRegistry
            from ai.providers.provider_manager import ProviderManager
            from ai.providers.provider_factory import register_standard_providers
            from ai.providers.provider_discovery import ProviderDiscovery
            
            register_standard_providers()
            provider_registry = ProviderRegistry(config_dir="config/providers")
            loaded_providers = provider_registry.load_all_providers()
            logger.info(f"Loaded {len(loaded_providers)} providers from config")
            try:
                discovery = ProviderDiscovery()
                discovered = discovery.discover_all()
                logger.info(f"Discovered {len(discovered)} providers")
            except Exception as e:
                logger.error(f"Error in provider discovery: {e}")
            
            provider_manager = ProviderManager(provider_registry, event_bus)
            provider_manager.monitor_health()
            
            # Connect providers
            for provider_name in loaded_providers:
                try:
                    provider = provider_registry.get_provider(provider_name)
                    if provider and provider.config.enabled:
                        if provider.connect():
                            logger.info(f"[OK] Connected to {provider_name}")
                            fetched_models = provider.refresh_models()
                            if fetched_models:
                                provider._set_models(fetched_models)
                except Exception as e:
                    logger.error(f"Provider {provider_name} connection failed: {e}")
            
            # Model Systems
            from ai.models.model_registry import ModelRegistry
            from ai.models.model_catalog import ModelState
            from ai.models.router import ModelRouter
            from ai.connection import initialize_connection_manager
            from ai.models.model_center import initialize_model_center
            
            model_registry = ModelRegistry(provider_registry)
            
            # Update model states
            for provider_name in loaded_providers:
                provider = provider_registry.get_provider(provider_name)
                if provider:
                    catalog_entries = model_registry.catalog.get_entries_by_provider(provider_name)
                    for entry in catalog_entries:
                        model_name = entry.profile.name
                        if provider.is_connected():
                            model_registry.update_model_state(model_name, ModelState.READY)
                        else:
                            model_registry.update_model_state(model_name, ModelState.API_REQUIRED)
            
            # Register models from providers
            for provider_name in loaded_providers:
                provider = provider_registry.get_provider(provider_name)
                if provider and provider.is_connected():
                    models = provider.get_models()
                    for model_id, model_info in models.items():
                        model_registry.register_model_from_provider(provider_name, model_info)
            
            model_router = ModelRouter(model_registry, provider_manager)
            connection_manager = initialize_connection_manager()
            model_center = initialize_model_center(provider_registry, provider_manager, model_registry)
            
            # Register models in model center
            for provider_name in loaded_providers:
                provider = provider_registry.get_provider(provider_name)
                if provider and provider.is_connected():
                    models = provider.get_models()
                    for model_id, model_info in models.items():
                        full_model_id = f"{provider_name}:{model_id}"
                        try:
                            from ai.models.model_center import ModelInfo, ModelCapabilities
                            model_center_info = ModelInfo(
                                model_id=full_model_id,
                                provider=provider_name,
                                display_name=model_info.get("name", model_id),
                                context_window=model_info.get("context_window", 4096),
                                max_output_tokens=model_info.get("max_output_tokens", 4096),
                                model_type=model_info.get("type", "local"),
                                capabilities=ModelCapabilities.from_config({
                                    "provider": provider_name,
                                    "type": model_info.get("type", "local"),
                                    "context_window": model_info.get("context_window", 4096),
                                    "supports_streaming": model_info.get("supports_streaming", True),
                                    "supports_vision": model_info.get("supports_vision", False),
                                    "supports_tool_calling": model_info.get("supports_tool_calling", False),
                                    "supports_function_calling": model_info.get("supports_function_calling", False),
                                }),
                                status="connected",
                                availability=1.0,
                                tags=model_info.get("strengths", []),
                            )
                            model_center._models[full_model_id] = model_center_info
                        except Exception as e:
                            logger.error(f"Failed to add {full_model_id} to Model Center: {e}")
            
            # AI Chat Engine
            from ai.chat.ai_chat_engine import initialize_ai_chat_engine
            chat_engine = initialize_ai_chat_engine(event_bus, provider_registry, provider_manager, 
                                                    model_center, model_registry)
            
            # Wire chat engine to window on main thread
            QTimer.singleShot(0, lambda: window.set_chat_engine(chat_engine))
            QTimer.singleShot(0, lambda: window.set_provider_manager(provider_manager))
            QTimer.singleShot(0, lambda: window.ai_workspace.set_providers(provider_registry, provider_manager))
            
            # Workflow Coordinator
            from ai.engine.engineering_workflow_coordinator import EngineeringWorkflowCoordinator
            from ai.execution.execution_engine import ExecutionEngine, ExecutionEngineConfig
            from ai.execution.task_executor import TaskExecutor
            from ai.editing.change_applier import ChangeApplier
            from ai.verification.verification_engine import VerificationEngine
            
            execution_engine = ExecutionEngine(event_bus, ExecutionEngineConfig(config_dir="config"))
            project_root_str = str(Path(".").resolve())
            change_applier = ChangeApplier(event_bus, project_root_str)
            verification_engine = VerificationEngine(event_bus, project_root_str)
            execution_engine.attach_change_applier(change_applier)
            execution_engine.attach_verification_engine(verification_engine)
            TaskExecutor.set_chat_engine(chat_engine)
            
            context_engine = None
            try:
                from ai.context.context_engine import ContextEngine
                context_engine = ContextEngine(event_bus, project_root_str)
                execution_engine.attach_context_engine(context_engine)
            except Exception as e:
                logger.warning(f"ContextEngine init failed: {e}")
                context_engine = None
            
            def _on_workspace_loaded_for_context(data):
                path = data.get("path", "")
                if path:
                    try:
                        from ai.context.context_engine import ContextEngine
                        new_ctx = ContextEngine(event_bus, path)
                        execution_engine.attach_context_engine(new_ctx)
                        if hasattr(window, 'workflow_coordinator'):
                            window.workflow_coordinator.context_engine = new_ctx
                    except Exception as e:
                        logger.warning(f"Failed to create ContextEngine for {path}: {e}")
            
            event_bus.subscribe("workspace_loaded", _on_workspace_loaded_for_context)
            
            workflow_coordinator = EngineeringWorkflowCoordinator(
                event_bus=event_bus,
                project_analyzer=project_analyzer,
                context_engine=context_engine,
                model_router=model_router,
                chat_engine=chat_engine,
                patch_engine=change_applier,
                verification_engine=verification_engine,
                execution_engine=execution_engine,
            )
            
            def _on_file_saved(data):
                path = data.get("path", "")
                if hasattr(window, 'workflow_coordinator') and window.workflow_coordinator.context_engine:
                    try:
                        window.workflow_coordinator.context_engine.notify_file_changed(path)
                    except Exception:
                        pass
            
            event_bus.subscribe("editor_saved", _on_file_saved)
            event_bus.subscribe("file_saved", _on_file_saved)
            
            # Wire agents on main thread
            def wire_agents():
                try:
                    from ai.agents.coder import CoderAgent
                    from ai.agents.debugger import DebuggerAgent
                    window.coder_agent = CoderAgent(event_bus, chat_engine)
                    window.debugger_agent = DebuggerAgent(event_bus, chat_engine)
                except Exception as ae:
                    logger.warning(f"Agent init failed: {ae}")
            
            QTimer.singleShot(0, wire_agents)
            
            # Wire memory
            def wire_memory():
                try:
                    def _on_workspace_loaded_for_memory(data):
                        path = data.get("path", "")
                        name = Path(path).name if path else "unknown"
                        if path and hasattr(window, 'workflow_coordinator'):
                            window.workflow_coordinator.project_memory.set_project(name, path)
                    event_bus.subscribe("workspace_loaded", _on_workspace_loaded_for_memory)
                except Exception as me:
                    logger.warning(f"Memory wiring failed: {me}")
            
            QTimer.singleShot(0, wire_memory)
            
            # Store on window
            QTimer.singleShot(0, lambda: setattr(window, 'workflow_coordinator', workflow_coordinator))
            QTimer.singleShot(0, lambda: setattr(window, 'connection_manager', connection_manager))
            
            # Load sessions
            try:
                editor_manager.load_session()
                workspace_manager.load_session()
            except Exception as e:
                logger.error(f"Session loading failed: {e}")
            
            # End profiling
            profiler.end("total_startup")
            profiler.print_summary_table()
            profiler.print_report()
            profiler.save_report(f"logs/startup_timing_optimized.json")
            
            logger.info("=" * 60)
            logger.info("MyCodingMaster v1.9.0 ready!")
            logger.info("=" * 60)
            
            logger.info("Background initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Background initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Add single background task
    initializer.add_task("heavy_systems", init_managers_and_heavy_systems, priority=100)
    
    # Progress feedback
    def on_progress(completed, total):
        try:
            if completed < total:
                window.status_bar.showMessage(f"Initializing systems...")
            else:
                window.status_bar.showMessage("Ready", 2000)
        except:
            pass
    
    initializer.progress_updated.connect(on_progress)
    
    return initializer


def main():
    """Main execution function — optimized for fast startup using BackgroundInitializer."""
    profiler.start("total_startup")
    
    logger.info("=" * 60)
    logger.info("Initializing MyCodingMaster v1.9.0 (Fast Startup)...")
    logger.info("=" * 60)

    # ── Minimal Startup Validation ────────────────────────
    if not validate_startup():
        logger.error("Startup validation failed, attempting to continue...")

    # ── Minimal Core Systems (only what's needed to show window) ─────────
    with ProfilePhase("minimal_core_init"):
        event_bus = EventBus()
        error_manager = get_error_manager()
        error_manager.set_event_bus(event_bus)
        resource_manager = get_resource_manager()
        resource_manager.set_event_bus(event_bus)

    # ── PySide6 Application (show window as soon as possible) ─────────
    with ProfilePhase("qapplication_init"):
        app = QApplication(sys.argv)
        app.setApplicationName("MyCodingMaster")
        app.setApplicationVersion("1.9.0")
        app.setOrganizationName("MyCodingMaster")

    # ── Design System & Theme (minimal to show UI) ─────────
    with ProfilePhase("design_system_init"):
        from ui.design_system import get_design_system
        design_system = get_design_system()
        app.setStyleSheet(design_system.get_stylesheet("global"))
        theme_manager = ThemeManager(app)
        theme_manager.apply_dark()

    # ── Create & Show Main Window FIRST! ─────────────────────────────
    with ProfilePhase("mainwindow_creation"):
        window = MainWindow(event_bus)
        window.set_theme_manager(theme_manager)
    
    # Show window NOW!
    with ProfilePhase("window_show"):
        window.show()
        window.showMaximized()

    # ── Use BackgroundInitializer for heavy systems ──────────────────────
    background_initializer = initialize_background_systems(event_bus, window, error_manager)
    if background_initializer:
        QTimer.singleShot(100, background_initializer.start)
    
    # ── Shutdown handler ────────────────────────────────────────────────
    def on_shutdown():
        logger.info("Shutting down...")
        try:
            watchdog = get_performance_watchdog()
            watchdog.stop()
        except:
            pass
        try:
            resource_manager.cleanup_all()
        except:
            pass
        try:
            error_manager.save_history()
        except:
            pass
        event_bus.publish("app_closing", {})
        logger.info("Shutdown complete")
    
    app.aboutToQuit.connect(on_shutdown)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
