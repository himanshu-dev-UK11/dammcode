"""
AI Diagnostics Page — v1.7

Provides diagnostic information about AI providers and models.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidget,
    QTreeWidgetItem, QLineEdit, QTextEdit, QGroupBox, QTabWidget, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from pathlib import Path
import time


class AIProviderItem(QTreeWidgetItem):
    """Tree widget item for a provider."""
    
    def __init__(self, provider_name: str, endpoint: str, status: str):
        super().__init__([provider_name])
        self.provider_name = provider_name
        self.endpoint = endpoint
        self.status = status
        self.setToolTip(0, f"Endpoint: {endpoint}")
        
        # Status colors
        status_colors = {
            "connected": "#10B981",
            "disconnected": "#EF4444",
            "error": "#EF4444",
            "unknown": "#6B7280",
        }
        color = status_colors.get(status, "#6B7280")
        self.setForeground(0, self._make_color(color))
        
    def _make_color(self, hex_color: str):
        """Convert hex color to QBrush for QTreeWidgetItem."""
        from PySide6.QtGui import QColor
        return QColor(hex_color)


class AIModelItem(QTreeWidgetItem):
    """Tree widget item for a model."""
    
    def __init__(self, model_id: str, provider: str, context_window: int = 0):
        super().__init__([model_id, provider, str(context_window)])
        self.model_id = model_id
        self.provider = provider
        self.context_window = context_window


class AIProviderCard(QFrame):
    """Card displaying provider information."""
    
    def __init__(self, provider_name: str, endpoint: str, status: str,
                 models: list = None, parent=None):
        super().__init__(parent)
        self.provider_name = provider_name
        self.endpoint = endpoint
        self.status = status
        self.models = models or []
        
        self.setObjectName("ProviderCard")
        self.setStyleSheet("""
            #ProviderCard {
                background-color: #1C1C1F;
                border: 1px solid #252528;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Status indicator
        status_label = QLabel()
        if self.status == "connected":
            status_label.setText("●")
            status_label.setStyleSheet("color: #10B981; font-size: 12px;")
        elif self.status == "disconnected":
            status_label.setText("●")
            status_label.setStyleSheet("color: #EF4444; font-size: 12px;")
        else:
            status_label.setText("●")
            status_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        
        # Provider name
        name_label = QLabel(self.provider_name.upper())
        name_label.setStyleSheet("""
            color: #E2E2E6;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)
        
        header_layout.addWidget(status_label)
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        
        # Endpoint
        endpoint_label = QLabel(self.endpoint)
        endpoint_label.setStyleSheet("""
            color: #8E8E98;
            font-size: 9px;
            font-family: "JetBrains Mono", monospace;
        """)
        
        # Models count
        models_label = QLabel(f"{len(self.models)} models")
        models_label.setStyleSheet("""
            color: #3B82F6;
            font-size: 9px;
            font-weight: 500;
        """)
        
        layout.addLayout(header_layout)
        layout.addWidget(endpoint_label)
        layout.addWidget(models_label)


class AIDiagnosticsPage(QWidget):
    """
    AI Diagnostics page for testing and monitoring AI providers.
    """
    
    models_refreshed = Signal()
    
    def __init__(self, event_bus, provider_registry, provider_manager,
                 model_center, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        self.provider_registry = provider_registry
        self.provider_manager = provider_manager
        self.model_center = model_center
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("AI DIAGNOSTICS")
        title.setStyleSheet("""
            color: #E2E2E6;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.8px;
            margin-bottom: 8px;
        """)
        layout.addWidget(title)
        
        # Provider Status Section
        provider_group = QGroupBox("Provider Status")
        provider_group.setStyleSheet("""
            QGroupBox {
                background-color: #111113;
                border: 1px solid #252528;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subline-offset: -4px;
                color: #52525C;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.5px;
                padding: 0 8px;
            }
        """)
        
        provider_layout = QVBoxLayout(provider_group)
        provider_layout.setContentsMargins(0, 0, 0, 0)
        provider_layout.setSpacing(8)
        
        # Provider list
        self.provider_list = QTreeWidget()
        self.provider_list.setHeaderLabels(["Provider", "Endpoint", "Status"])
        self.provider_list.setColumnWidth(0, 150)
        self.provider_list.setColumnWidth(1, 250)
        self.provider_list.setColumnWidth(2, 80)
        self.provider_list.setStyleSheet("""
            QTreeWidget {
                background-color: #161618;
                border: 1px solid #252528;
                border-radius: 4px;
                font-size: 11px;
            }
            QTreeWidget::item {
                padding: 6px 8px;
            }
            QTreeWidget::item:selected {
                background-color: #1E3A5F;
            }
        """)
        provider_layout.addWidget(self.provider_list)
        
        # Provider actions
        provider_actions = QHBoxLayout()
        
        refresh_providers_btn = QPushButton("Refresh Providers")
        refresh_providers_btn.setFixedHeight(28)
        refresh_providers_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #252528;
            }
        """)
        refresh_providers_btn.clicked.connect(self.refresh_providers)
        provider_actions.addWidget(refresh_providers_btn)
        
        test_providers_btn = QPushButton("Test All Connections")
        test_providers_btn.setFixedHeight(28)
        test_providers_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #3B82F6;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #252528;
            }
        """)
        test_providers_btn.clicked.connect(self.test_all_connections)
        provider_actions.addWidget(test_providers_btn)
        
        provider_layout.addLayout(provider_actions)
        
        layout.addWidget(provider_group)
        
        # Model Status Section
        model_group = QGroupBox("Installed Models")
        model_group.setStyleSheet("""
            QGroupBox {
                background-color: #111113;
                border: 1px solid #252528;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subline-offset: -4px;
                color: #52525C;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.5px;
                padding: 0 8px;
            }
        """)
        
        model_layout = QVBoxLayout(model_group)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.setSpacing(8)
        
        # Model list
        self.model_list = QTreeWidget()
        self.model_list.setHeaderLabels(["Model", "Provider", "Context Window"])
        self.model_list.setColumnWidth(0, 200)
        self.model_list.setColumnWidth(1, 150)
        self.model_list.setColumnWidth(2, 120)
        self.model_list.setStyleSheet("""
            QTreeWidget {
                background-color: #161618;
                border: 1px solid #252528;
                border-radius: 4px;
                font-size: 11px;
            }
            QTreeWidget::item {
                padding: 6px 8px;
            }
            QTreeWidget::item:selected {
                background-color: #1E3A5F;
            }
        """)
        model_layout.addWidget(self.model_list)
        
        # Model actions
        model_actions = QHBoxLayout()
        
        refresh_models_btn = QPushButton("Refresh Models")
        refresh_models_btn.setFixedHeight(28)
        refresh_models_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #252528;
            }
        """)
        refresh_models_btn.clicked.connect(self.refresh_models)
        model_actions.addWidget(refresh_models_btn)
        
        model_layout.addLayout(model_actions)
        
        layout.addWidget(model_group)
        
        # Health Check Section
        health_group = QGroupBox("Provider Health")
        health_group.setStyleSheet("""
            QGroupBox {
                background-color: #111113;
                border: 1px solid #252528;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subline-offset: -4px;
                color: #52525C;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.5px;
                padding: 0 8px;
            }
        """)
        
        health_layout = QVBoxLayout(health_group)
        health_layout.setContentsMargins(0, 0, 0, 0)
        health_layout.setSpacing(8)
        
        # Health status display
        self.health_status = QTextEdit()
        self.health_status.setReadOnly(True)
        self.health_status.setFont(QFont("JetBrains Mono, monospace", 10))
        self.health_status.setFixedHeight(150)
        self.health_status.setStyleSheet("""
            QTextEdit {
                background-color: #0D0D0F;
                border: 1px solid #252528;
                border-radius: 4px;
                color: #8E8E98;
                padding: 8px;
            }
        """)
        self.health_status.setPlaceholderText("Health status will appear here...")
        health_layout.addWidget(self.health_status)
        
        health_actions = QHBoxLayout()
        
        check_health_btn = QPushButton("Check All Health")
        check_health_btn.setFixedHeight(28)
        check_health_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #252528;
            }
        """)
        check_health_btn.clicked.connect(self.check_all_health)
        health_actions.addWidget(check_health_btn)
        
        health_layout.addLayout(health_actions)
        
        layout.addWidget(health_group)
        
        # Auto-refresh every 30 seconds
        from PySide6.QtCore import QTimer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.auto_refresh)
        self._timer.start(30000)
        
        # Initial refresh
        self.refresh_providers()
        
    def refresh_providers(self):
        """Refresh provider list."""
        if self.provider_registry is None:
            return
            
        self.provider_list.clear()
        
        for provider_name, provider in self.provider_registry.get_all_providers().items():
            status = provider.get_status().value
            endpoint = provider.config.endpoint
            
            item = QTreeWidgetItem([provider_name, endpoint, status])
            item.setForeground(2, self._get_status_color(status))
            self.provider_list.addTopLevelItem(item)
        
        self.provider_list.expandAll()
        
    def test_all_connections(self):
        """Test all provider connections."""
        self.health_status.append("\n" + "="*50)
        self.health_status.append(f"Testing all connections at {time.strftime('%H:%M:%S')}")
        self.health_status.append("="*50)
        
        results = self.provider_registry.test_all_connections()
        
        for provider_name, success in results.items():
            status = "✓ Connected" if success else "✗ Disconnected"
            self.health_status.append(f"{provider_name}: {status}")
        
        self.health_status.append("")
        self.health_status.ensureCursorVisible()
        
    def refresh_models(self):
        """Refresh models for all providers."""
        if self.provider_registry is None:
            return
            
        self.model_list.clear()
        
        for provider_name, provider in self.provider_registry.get_all_providers().items():
            models = provider.get_models()
            
            for model_id, model_info in models.items():
                context = model_info.get("context_window", model_info.get("context", 4096))
                
                item = QTreeWidgetItem([model_id, provider_name, str(context)])
                self.model_list.addTopLevelItem(item)
        
        self.model_list.expandAll()
        self.models_refreshed.emit()
        
    def check_all_health(self):
        """Check health of all providers."""
        if self.provider_manager is None:
            self.health_status.append("Provider manager not initialized")
            return
            
        health_data = self.provider_manager.get_health_status()
        
        self.health_status.append("\n" + "="*50)
        self.health_status.append(f"Health check at {time.strftime('%H:%M:%S')}")
        self.health_status.append("="*50)
        
        for provider_name, health in health_data.items():
            status = health.get("status", "unknown")
            is_connected = health.get("is_connected", False)
            success_rate = health.get("success_rate", 0)
            
            self.health_status.append(
                f"{provider_name}: {status} "
                f"(connected={is_connected}, "
                f"success_rate={success_rate:.0%})"
            )
        
        self.health_status.append("")
        self.health_status.ensureCursorVisible()
        
    def auto_refresh(self):
        """Auto-refresh provider status."""
        self.refresh_providers()
        
    def _get_status_color(self, status: str):
        """Get QBrush for status color."""
        from PySide6.QtGui import QColor
        status_colors = {
            "connected": "#10B981",
            "disconnected": "#EF4444",
            "error": "#EF4444",
            "unknown": "#6B7280",
        }
        return QColor(status_colors.get(status, "#6B7280"))


# Initialize provider configurations
def initialize_provider_configs():
    """Initialize provider configuration files if they don't exist."""
    from PySide6.QtCore import QStandardPaths
    import json
    import os
    
    # Try user config directory first
    config_dir = Path("config/providers")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Default provider configs
    providers = {
        "ollama": {
            "provider_name": "ollama",
            "endpoint": "http://localhost:11434",
            "auth_type": "none",
            "enabled": True,
            "priority": 10,
            "default_model": "qwen2.5:latest",
            "timeout_seconds": 30,
            "retry_count": 3,
            "supports_streaming": True,
            "supports_tool_calling": False,
            "supports_vision": False,
            "supports_function_calling": False,
        },
        "gemini": {
            "provider_name": "gemini",
            "endpoint": "https://generativelanguage.googleapis.com/v1beta",
            "auth_type": "api_key",
            "enabled": False,
            "priority": 5,
            "default_model": "gemini-1.5-flash",
            "timeout_seconds": 30,
            "retry_count": 3,
            "supports_streaming": True,
            "supports_tool_calling": True,
            "supports_vision": True,
            "supports_function_calling": True,
        },
    }
    
    for name, config in providers.items():
        config_path = config_dir / f"{name}.json"
        if not config_path.exists():
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
