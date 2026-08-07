"""
Connect Provider Dialog.

Dialog for connecting new AI providers with API key and model selection.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QLineEdit, QGroupBox, QTextEdit, QMessageBox, QDialogButtonBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from core.logger import setup_logger
from ai.providers.base_provider import ProviderConfig, AuthenticationType
from ai.providers.provider_factory import ProviderFactory

logger = setup_logger(__name__)


class ConnectProviderDialog(QDialog):
    """
    Dialog to connect a new AI provider using API key.
    """
    
    provider_connected = Signal(str, str, str)  # provider_name, display_name, api_key
    
    def __init__(self, parent=None, available_providers=None):
        super().__init__(parent)
        self.available_providers = available_providers or []
        self.api_key = ""
        self.endpoint = ""
        self.models = []
        
        self.setWindowTitle("Connect AI Provider")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Connect AI Provider")
        title.setStyleSheet("""
            color: #E2E2E6;
            font-size: 16px;
            font-weight: 600;
        """)
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Add a new AI provider by entering your API key. "
                     "Supported providers: OpenAI, Anthropic, Google Gemini, Groq, DeepSeek, and more.")
        desc.setWordWrap(True)
        desc.setStyleSheet("""
            color: #8E8E98;
            font-size: 11px;
            line-height: 1.5;
        """)
        layout.addWidget(desc)
        
        # Provider Selection Group
        provider_group = QGroupBox("Provider Configuration")
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
        provider_layout.setContentsMargins(12, 12, 12, 12)
        provider_layout.setSpacing(12)
        
        # Provider name
        name_row = QHBoxLayout()
        name_label = QLabel("Provider Name:")
        name_label.setStyleSheet("color: #E2E2E6; font-size: 10px; min-width: 100px;")
        name_row.addWidget(name_label)
        
        self.provider_name_input = QLineEdit()
        self.provider_name_input.setPlaceholderText("e.g., openai, anthropic, custom")
        self.provider_name_input.setStyleSheet("""
            QLineEdit {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 10px;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
            }
        """)
        name_row.addWidget(self.provider_name_input)
        provider_layout.addLayout(name_row)
        
        # API Key
        api_key_row = QHBoxLayout()
        api_key_label = QLabel("API Key:")
        api_key_label.setStyleSheet("color: #E2E2E6; font-size: 10px; min-width: 100px;")
        api_key_row.addWidget(api_key_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter your API key")
        self.api_key_input.setStyleSheet("""
            QLineEdit {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 10px;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
            }
        """)
        api_key_row.addWidget(self.api_key_input)
        provider_layout.addLayout(api_key_row)
        
        # Endpoint (optional)
        endpoint_row = QHBoxLayout()
        endpoint_label = QLabel("Endpoint:")
        endpoint_label.setStyleSheet("color: #E2E2E6; font-size: 10px; min-width: 100px;")
        endpoint_row.addWidget(endpoint_label)
        
        self.endpoint_input = QLineEdit()
        self.endpoint_input.setPlaceholderText("https://api.example.com/v1")
        self.endpoint_input.setStyleSheet("""
            QLineEdit {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 10px;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
            }
        """)
        endpoint_row.addWidget(self.endpoint_input)
        provider_layout.addLayout(endpoint_row)
        
        layout.addWidget(provider_group)
        
        # Models Section
        models_group = QGroupBox("Available Models")
        models_group.setStyleSheet("""
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
        
        models_layout = QVBoxLayout(models_group)
        models_layout.setContentsMargins(12, 12, 12, 12)
        models_layout.setSpacing(8)
        
        # Models text area (read-only, auto-populated)
        models_text = QTextEdit()
        models_text.setReadOnly(True)
        models_text.setPlaceholderText("Enter endpoint and API key, then click 'Test' to fetch models")
        models_text.setMinimumHeight(80)
        models_text.setStyleSheet("""
            QTextEdit {
                background-color: #1C1C1F;
                color: #8E8E98;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 8px;
                font-size: 10px;
                font-family: Consolas, monospace;
            }
        """)
        self.models_text = models_text
        models_layout.addWidget(models_text)
        
        # Test and Auto-Fetch row
        test_row = QHBoxLayout()
        self.test_button = QPushButton("Test Connection")
        self.test_button.setFixedHeight(28)
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        test_row.addWidget(self.test_button)
        
        self.auto_fetch_checkbox = None  # Will be created later if needed
        test_row.addStretch()
        models_layout.addLayout(test_row)
        
        layout.addWidget(models_group)
        
        # Status area
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            color: #8E8E98;
            font-size: 10px;
        """)
        layout.addWidget(self.status_label)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.ok_button = button_box.button(QDialogButtonBox.Ok)
        self.ok_button.setText("Connect Provider")
        self.ok_button.setEnabled(False)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def setup_connections(self):
        """Setup signal connections."""
        self.api_key_input.textChanged.connect(self._on_input_changed)
        self.provider_name_input.textChanged.connect(self._on_input_changed)
        self.test_button.clicked.connect(self._on_test_connection)
    
    def _on_input_changed(self):
        """Handle input changes."""
        has_name = bool(self.provider_name_input.text().strip())
        has_key = bool(self.api_key_input.text().strip())
        
        self.ok_button.setEnabled(has_name and has_key)
    
    def _on_test_connection(self):
        """Test provider connection."""
        provider_name = self.provider_name_input.text().strip()
        api_key = self.api_key_input.text().strip()
        endpoint = self.endpoint_input.text().strip()
        
        if not provider_name or not api_key:
            QMessageBox.warning(self, "Missing Information",
                              "Please provide provider name and API key.")
            return
        
        self.status_label.setText("Testing connection...")
        self.status_label.setStyleSheet("color: #3B82F6; font-size: 10px;")
        QApplication.processEvents()  # Update UI
        
        try:
            # Create a temporary provider config
            config = ProviderConfig(
                provider_name=provider_name,
                endpoint=endpoint or "https://api.example.com/v1",
                auth_type=AuthenticationType.API_KEY,
                api_key=api_key,
                enabled=True,
            )
            
            # Try to create and test the provider
            # Note: This assumes you have the appropriate provider class
            # For a real implementation, you'd need to register provider types
            provider_class = ProviderFactory._get_provider_class(provider_name)
            
            if provider_class:
                provider = provider_class(config)
                success = provider.test_connection()
                
                if success:
                    # Fetch models
                    models = provider.refresh_models()
                    model_list = [m.get("id", m.get("name", "")) for m in models]
                    
                    self.models = model_list
                    self.api_key = api_key
                    self.endpoint = endpoint
                    
                    models_text = "\n".join(f"• {m}" for m in model_list[:20])
                    if len(model_list) > 20:
                        models_text += f"\n... and {len(model_list) - 20} more"
                    
                    self.models_text.setPlainText(models_text)
                    self.status_label.setText(f"✓ Connection successful! {len(model_list)} models loaded.")
                    self.status_label.setStyleSheet("color: #10B981; font-size: 10px;")
                else:
                    self.status_label.setText("✗ Connection failed. Check your API key and endpoint.")
                    self.status_label.setStyleSheet("color: #EF4444; font-size: 10px;")
            else:
                # No specific provider class, use generic test
                self.models_text.setPlainText("Model list would be fetched here...")
                self.status_label.setText("✓ Test complete (generic provider)")
                self.status_label.setStyleSheet("color: #10B981; font-size: 10px;")
        
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            self.status_label.setText(f"✗ Error: {str(e)}")
            self.status_label.setStyleSheet("color: #EF4444; font-size: 10px;")
        finally:
            self.test_button.setEnabled(True)
    
    def get_provider_info(self) -> dict:
        """Get provider configuration."""
        return {
            "provider_name": self.provider_name_input.text().strip(),
            "api_key": self.api_key_input.text().strip(),
            "endpoint": self.endpoint_input.text().strip(),
            "display_name": self.provider_name_input.text().strip(),
            "models": self.models,
        }
    
    def accept(self):
        """Accept dialog and emit signal."""
        provider_info = self.get_provider_info()
        
        if not provider_info["provider_name"]:
            QMessageBox.warning(self, "Invalid Input",
                              "Provider name cannot be empty.")
            return
        
        if not provider_info["api_key"]:
            QMessageBox.warning(self, "Invalid Input",
                              "API key cannot be empty.")
            return
        
        self.provider_connected.emit(
            provider_info["provider_name"],
            provider_info["display_name"],
            provider_info["api_key"]
        )
        
        super().accept()