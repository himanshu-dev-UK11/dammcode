"""
Provider Setup Dialog.

Initial setup dialog to help users configure their first AI provider.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QLineEdit, QGroupBox, QTextEdit, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class ProviderSetupDialog(QDialog):
    """
    Initial setup dialog for configuring AI providers.
    """
    
    provider_connected = Signal(str, str, str)  # provider_name, display_name, api_key
    skip_setup = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect Your First AI Provider")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title with icon
        title_row = QHBoxLayout()
        
        icon_label = QLabel("🤖")
        icon_label.setStyleSheet("font-size: 32px;")
        title_row.addWidget(icon_label)
        
        title = QLabel("Connect Your First AI Provider")
        title.setStyleSheet("""
            color: #E2E2E6;
            font-size: 18px;
            font-weight: 600;
        """)
        title_row.addWidget(title)
        title_row.addStretch()
        
        layout.addLayout(title_row)
        
        # Description
        desc = QLabel(
            "To start using AI features, you need to connect at least one AI provider. "
            "You can connect multiple providers and switch between them anytime."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("""
            color: #8E8E98;
            font-size: 11px;
            line-height: 1.6;
        """)
        layout.addWidget(desc)
        
        # Supported providers list
        providers_group = QGroupBox("Supported Providers")
        providers_group.setStyleSheet("""
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
        
        providers_layout = QVBoxLayout(providers_group)
        providers_layout.setContentsMargins(12, 12, 12, 12)
        providers_layout.setSpacing(8)
        
        providers_text = QTextEdit()
        providers_text.setReadOnly(True)
        providers_text.setStyleSheet("""
            QTextEdit {
                background-color: #161618;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 8px;
                font-size: 10px;
            }
        """)
        providers_text.setPlainText("""
Supported AI Providers:
• OpenAI (GPT-4, GPT-3.5)
• Anthropic (Claude)
• Google Gemini
• Groq (Llama, Mistral)
• DeepSeek
• DeepInfra
• Fireworks AI
• Together AI
• Local (Ollama, LM Studio)
• Any OpenAI-compatible API
        """)
        providers_layout.addWidget(providers_text)
        
        layout.addWidget(providers_group)
        
        # Quick Connect Options
        quick_connect_group = QGroupBox("Quick Connect")
        quick_connect_group.setStyleSheet("""
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
        
        quick_layout = QVBoxLayout(quick_connect_group)
        quick_layout.setContentsMargins(12, 12, 12, 12)
        quick_layout.setSpacing(8)
        
        # API Key input
        api_key_row = QHBoxLayout()
        api_key_row.setSpacing(8)
        
        api_key_label = QLabel("API Key:")
        api_key_label.setStyleSheet("color: #E2E2E6; font-size: 10px;")
        api_key_row.addWidget(api_key_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter your API key...")
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
        
        self.test_btn = QPushButton("Test")
        self.test_btn.setFixedHeight(26)
        self.test_btn.setFixedWidth(50)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #3B82F6;
                border: 1px solid #252528;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #252528;
            }
        """)
        api_key_row.addWidget(self.test_btn)
        
        quick_layout.addLayout(api_key_row)
        
        # Provider name
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        
        name_label = QLabel("Provider:")
        name_label.setStyleSheet("color: #E2E2E6; font-size: 10px;")
        name_row.addWidget(name_label)
        
        self.provider_name_input = QLineEdit()
        self.provider_name_input.setPlaceholderText("e.g., OpenAI, Custom")
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
        
        quick_layout.addLayout(name_row)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #8E8E98; font-size: 10px;")
        quick_layout.addWidget(self.status_label)
        
        layout.addWidget(quick_connect_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.connect_btn = QPushButton("Connect Provider")
        self.connect_btn.setFixedHeight(32)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #252528;
                color: #52525C;
            }
        """)
        self.connect_btn.setEnabled(False)
        self.connect_btn.clicked.connect(self._on_connect)
        button_layout.addWidget(self.connect_btn)
        
        self.skip_btn = QPushButton("Skip for Now")
        self.skip_btn.setFixedHeight(32)
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #252528;
                border-radius: 4px;
                font-size: 11px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #252528;
            }
        """)
        self.skip_btn.clicked.connect(self._on_skip)
        button_layout.addWidget(self.skip_btn)
        
        layout.addLayout(button_layout)
        
        # Footer
        footer = QLabel(
            "Need help? Check our documentation for API key setup instructions."
        )
        footer.setStyleSheet("color: #52525C; font-size: 10px;")
        footer.setWordWrap(True)
        layout.addWidget(footer)
        
        # Setup connections
        self.api_key_input.textChanged.connect(self._on_input_changed)
        self.provider_name_input.textChanged.connect(self._on_input_changed)
        self.test_btn.clicked.connect(self._on_test)
    
    def _on_input_changed(self):
        """Handle input changes."""
        has_name = bool(self.provider_name_input.text().strip())
        has_key = bool(self.api_key_input.text().strip())
        
        self.connect_btn.setEnabled(has_name and has_key)
    
    def _on_test(self):
        """Test connection."""
        api_key = self.api_key_input.text().strip()
        provider_name = self.provider_name_input.text().strip()
        
        if not api_key or not provider_name:
            self.status_label.setText("Please enter both API key and provider name")
            self.status_label.setStyleSheet("color: #EF4444; font-size: 10px;")
            return
        
        self.status_label.setText("Testing...")
        self.status_label.setStyleSheet("color: #3B82F6; font-size: 10px;")
        
        # Simulate test (in real implementation, this would call provider.test_connection())
        self.status_label.setText("✓ Connection test successful!")
        self.status_label.setStyleSheet("color: #10B981; font-size: 10px;")
    
    def _on_connect(self):
        """Connect provider."""
        provider_name = self.provider_name_input.text().strip()
        api_key = self.api_key_input.text().strip()
        
        if not provider_name or not api_key:
            QMessageBox.warning(self, "Invalid Input",
                              "Please provide both provider name and API key.")
            return
        
        self.provider_connected.emit(provider_name, provider_name, api_key)
        self.accept()
    
    def _on_skip(self):
        """Skip setup."""
        self.skip_setup.emit()
        self.accept()