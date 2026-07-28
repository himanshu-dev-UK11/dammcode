"""
Embedded Connection Panel - Inside AI Workspace.

No popup windows - everything happens inline.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QTextEdit, QFrame, QScrollArea, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from core.logger import setup_logger
from ai.connection import get_connection_manager, ConnectionStatus

logger = setup_logger(__name__)


class EmbeddedConnectionPanel(QWidget):
    """Connection panel embedded in AI workspace - no popups."""
    
    connection_successful = Signal(str, str)  # provider_name, model
    connection_failed = Signal(str)  # error_message
    
    def __init__(self, provider_registry, provider_manager, event_bus, parent=None):
        super().__init__(parent)
        self.provider_registry = provider_registry
        self.provider_manager = provider_manager
        self.event_bus = event_bus
        self.connection_manager = get_connection_manager()
        self._current_provider = None
        
        self.setup_ui()
        self._load_connections()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setStyleSheet("background-color: #0D0D0F; border-bottom: 1px solid #252528;")
        header.setFixedHeight(36)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        
        title = QLabel("AI CONNECTION")
        title.setStyleSheet("""
            color: #52525C;
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 1px;
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Main content area
        content = QWidget()
        content.setStyleSheet("background-color: #111113;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(12)
        
        # Provider Type Selection
        type_label = QLabel("Provider Type:")
        type_label.setStyleSheet("color: #E2E2E6; font-size: 11px; font-weight: 600;")
        content_layout.addWidget(type_label)
        
        self.provider_type_combo = QComboBox()
        self.provider_type_combo.addItems([
            "Google Gemini (Free)",
            "OpenAI (GPT-4)",
            "Anthropic (Claude)",
            "Groq (Fast & Free)",
            "DeepSeek",
            "Ollama (Local)",
            "Custom/Other"
        ])
        self.provider_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
            }
            QComboBox:hover { border-color: #3B82F6; }
        """)
        self.provider_type_combo.currentTextChanged.connect(self._on_type_changed)
        content_layout.addWidget(self.provider_type_combo)
        
        # API Key Input
        key_label = QLabel("API Key:")
        key_label.setStyleSheet("color: #E2E2E6; font-size: 11px; font-weight: 600;")
        content_layout.addWidget(key_label)
        
        key_row = QHBoxLayout()
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your API key here...")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setStyleSheet("""
            QLineEdit {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
            }
            QLineEdit:focus { border-color: #3B82F6; }
        """)
        key_row.addWidget(self.api_key_input)
        
        show_btn = QPushButton("👁")
        show_btn.setFixedSize(32, 32)
        show_btn.setCheckable(True)
        show_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                border: 1px solid #252528;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #252528; }
            QPushButton:checked { background-color: #3B82F6; }
        """)
        show_btn.toggled.connect(
            lambda checked: self.api_key_input.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        key_row.addWidget(show_btn)
        
        content_layout.addLayout(key_row)
        
        # Help text
        self.help_text = QLabel("Get your free API key at: https://makersuite.google.com/app/apikey")
        self.help_text.setOpenExternalLinks(True)
        self.help_text.setWordWrap(True)
        self.help_text.setStyleSheet("""
            color: #3B82F6;
            font-size: 10px;
            padding: 8px;
            background-color: #1C1C1F;
            border-radius: 4px;
        """)
        content_layout.addWidget(self.help_text)
        
        # Endpoint (optional)
        self.endpoint_label = QLabel("Endpoint (optional):")
        self.endpoint_label.setStyleSheet("color: #8E8E98; font-size: 10px;")
        content_layout.addWidget(self.endpoint_label)
        
        self.endpoint_input = QLineEdit()
        self.endpoint_input.setPlaceholderText("Auto-detected")
        self.endpoint_input.setStyleSheet("""
            QLineEdit {
                background-color: #1C1C1F;
                color: #8E8E98;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
            }
        """)
        content_layout.addWidget(self.endpoint_input)
        
        # Status message
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            color: #8E8E98;
            font-size: 10px;
            padding: 8px;
            background-color: #1C1C1F;
            border-radius: 4px;
        """)
        content_layout.addWidget(self.status_label)
        
        # Action buttons
        btn_row = QHBoxLayout()
        
        self.connect_btn = QPushButton("🚀 Connect & Test")
        self.connect_btn.setFixedHeight(36)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #059669; }
            QPushButton:disabled {
                background-color: #252528;
                color: #52525C;
            }
        """)
        self.connect_btn.clicked.connect(self._on_connect)
        btn_row.addWidget(self.connect_btn)
        
        content_layout.addLayout(btn_row)
        
        # Connected providers list
        connected_label = QLabel("Connected Providers:")
        connected_label.setStyleSheet("color: #E2E2E6; font-size: 11px; font-weight: 600; margin-top: 8px;")
        content_layout.addWidget(connected_label)
        
        self.connected_list = QWidget()
        self.connected_layout = QVBoxLayout(self.connected_list)
        self.connected_layout.setContentsMargins(0, 0, 0, 0)
        self.connected_layout.setSpacing(4)
        content_layout.addWidget(self.connected_list)
        
        content_layout.addStretch()
        layout.addWidget(content)
    
    def _on_type_changed(self, type_text: str):
        """Update help text based on provider type."""
        help_urls = {
            "Google Gemini (Free)": "https://makersuite.google.com/app/apikey",
            "OpenAI (GPT-4)": "https://platform.openai.com/api-keys",
            "Anthropic (Claude)": "https://console.anthropic.com/",
            "Groq (Fast & Free)": "https://console.groq.com/keys",
            "DeepSeek": "https://platform.deepseek.com/api_keys",
            "Ollama (Local)": "http://localhost:11434 (no key needed)",
        }
        
        url = help_urls.get(type_text, "")
        if url:
            self.help_text.setText(f'Get your API key: <a href="{url}" style="color: #3B82F6;">{url}</a>')
        else:
            self.help_text.setText("Enter your custom provider endpoint and API key")
        
        # Show/hide endpoint for local
        is_local = "Local" in type_text
        self.endpoint_label.setVisible(not is_local)
        self.endpoint_input.setVisible(not is_local)
    
    def _on_connect(self):
        """Connect to the provider and test it."""
        provider_type = self.provider_type_combo.currentText()
        api_key = self.api_key_input.text().strip()
        
        # Map display name to internal name
        provider_map = {
            "Google Gemini (Free)": "gemini",
            "OpenAI (GPT-4)": "openai",
            "Anthropic (Claude)": "anthropic",
            "Groq (Fast & Free)": "groq",
            "DeepSeek": "deepseek",
            "Ollama (Local)": "ollama",
        }
        
        provider_name = provider_map.get(provider_type, "custom")
        
        # Validate
        if not api_key and provider_name != "ollama":
            self._show_status("⚠️ Please enter your API key", "error")
            return
        
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("Connecting...")
        self._show_status("🔄 Testing connection...", "info")
        
        # Connect using actual provider
        QTimer.singleShot(100, lambda: self._do_connect(provider_name, api_key, provider_type))
    
    def _do_connect(self, provider_name: str, api_key: str, display_name: str):
        """Actually connect to the provider."""
        try:
            from ai.providers.base_provider import ProviderConfig, AuthenticationType
            from ai.providers.provider_factory import ProviderFactory
            
            # Get endpoint
            endpoint = self.endpoint_input.text().strip()
            if not endpoint:
                endpoints = {
                    "gemini": "https://generativelanguage.googleapis.com/v1beta",
                    "openai": "https://api.openai.com/v1",
                    "anthropic": "https://api.anthropic.com/v1",
                    "groq": "https://api.groq.com/openai/v1",
                    "deepseek": "https://api.deepseek.com/v1",
                    "ollama": "http://localhost:11434",
                }
                endpoint = endpoints.get(provider_name, "")
            
            # Create provider config
            config = ProviderConfig(
                provider_name=provider_name,
                endpoint=endpoint,
                auth_type=AuthenticationType.API_KEY if api_key else AuthenticationType.NONE,
                api_key=api_key,
                enabled=True,
            )
            
            # Create provider instance
            provider = ProviderFactory.create_from_config_obj(config)
            
            # Test connection
            logger.info(f"Testing connection to {provider_name}...")
            success = provider.test_connection()
            
            if success:
                # Get models
                logger.info(f"Fetching models from {provider_name}...")
                models = provider.refresh_models()
                model_ids = [m.get("id", m.get("name", "")) for m in models]
                
                # Save connection
                self.connection_manager.add_connection(
                    provider_name=provider_name,
                    display_name=display_name,
                    api_key=api_key,
                    endpoint=endpoint,
                    models=model_ids
                )
                
                # Register with provider registry
                self.provider_registry.register_provider(provider)
                
                self._show_status(f"✅ Connected! Found {len(model_ids)} models", "success")
                self._load_connections()
                
                # Emit success
                if model_ids:
                    self.connection_successful.emit(provider_name, model_ids[0])
                
                # Clear inputs
                self.api_key_input.clear()
                
                logger.info(f"Successfully connected to {provider_name}")
            else:
                self._show_status("❌ Connection failed. Check your API key.", "error")
                logger.error(f"Connection test failed for {provider_name}")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Connection error: {error_msg}")
            
            # Smart error messages
            if "400" in error_msg or "Bad Request" in error_msg:
                self._show_status("❌ Invalid API key format. Please check and try again.", "error")
            elif "401" in error_msg or "Unauthorized" in error_msg:
                self._show_status("❌ Invalid API key. Please get a new key from the provider.", "error")
            elif "404" in error_msg:
                self._show_status("❌ Invalid endpoint. Please check the URL.", "error")
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                self._show_status("❌ Network error. Check your internet connection.", "error")
            else:
                self._show_status(f"❌ Error: {error_msg}", "error")
            
            self.connection_failed.emit(error_msg)
        
        finally:
            self.connect_btn.setEnabled(True)
            self.connect_btn.setText("🚀 Connect & Test")
    
    def _show_status(self, message: str, status_type: str):
        """Show status message."""
        colors = {
            "info": "#3B82F6",
            "success": "#10B981",
            "error": "#EF4444",
        }
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"""
            color: {colors.get(status_type, '#8E8E98')};
            font-size: 10px;
            padding: 8px;
            background-color: #1C1C1F;
            border-radius: 4px;
            border-left: 3px solid {colors.get(status_type, '#252528')};
        """)
    
    def _load_connections(self):
        """Load and display connected providers."""
        # Clear list
        while self.connected_layout.count():
            child = self.connected_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        connections = self.connection_manager.get_all_connections()
        
        if not connections:
            empty = QLabel("No providers connected yet")
            empty.setStyleSheet("color: #52525C; font-size: 10px; padding: 8px;")
            self.connected_layout.addWidget(empty)
            return
        
        for name, conn in connections.items():
            self._add_connection_item(name, conn.display_name, len(conn.models))
    
    def _add_connection_item(self, provider_name: str, display_name: str, model_count: int):
        """Add a connected provider item."""
        item = QWidget()
        item.setStyleSheet("""
            QWidget {
                background-color: #1C1C1F;
                border: 1px solid #252528;
                border-radius: 4px;
            }
            QWidget:hover {
                border-color: #3B82F6;
            }
        """)
        
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(8, 6, 8, 6)
        
        # Status dot
        dot = QLabel("●")
        dot.setStyleSheet("color: #10B981; font-size: 12px;")
        item_layout.addWidget(dot)
        
        # Name
        name_label = QLabel(display_name)
        name_label.setStyleSheet("color: #E2E2E6; font-size: 11px;")
        item_layout.addWidget(name_label)
        
        # Model count
        count_label = QLabel(f"{model_count} models")
        count_label.setStyleSheet("color: #52525C; font-size: 9px;")
        item_layout.addWidget(count_label)
        
        item_layout.addStretch()
        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(20, 20)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8E8E98;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #EF4444;
            }
        """)
        remove_btn.clicked.connect(lambda: self._remove_connection(provider_name))
        item_layout.addWidget(remove_btn)
        
        self.connected_layout.addWidget(item)
    
    def _remove_connection(self, provider_name: str):
        """Remove a connection."""
        self.connection_manager.remove_connection(provider_name)
        self.provider_registry.unregister_provider(provider_name)
        self._load_connections()
        self._show_status(f"Removed {provider_name}", "info")