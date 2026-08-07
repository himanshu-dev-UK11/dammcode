"""
Provider Selection Section — v1.8

Provides UI for selecting and managing AI providers.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QLineEdit, QGroupBox, QFrame, QStackedWidget, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class ProviderSelectionSection(QWidget):
    """
    Section for selecting and configuring AI providers.
    """
    
    provider_changed = Signal(str)  # provider_name
    model_changed = Signal(str)  # model_id
    api_key_changed = Signal(str, str)  # provider_name, api_key
    
    def __init__(self, event_bus, provider_registry, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        self.provider_registry = provider_registry
        
        self._current_provider = None
        self._current_model = None
        
        self.setup_ui()
        self._refresh_providers()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Provider Selection Group
        provider_group = QGroupBox("AI Provider")
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
        
        # Provider combo
        provider_row = QHBoxLayout()
        
        provider_label = QLabel("Provider:")
        provider_label.setStyleSheet("""
            color: #E2E2E6;
            font-size: 10px;
            font-weight: 500;
            min-width: 70px;
        """)
        provider_row.addWidget(provider_label)
        
        self.provider_combo = QComboBox()
        self.provider_combo.setStyleSheet("""
            QComboBox {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 6px 10px;
                min-width: 150px;
                font-size: 10px;
            }
            QComboBox:hover {
                border-color: #3B82F6;
            }
            QComboBox::drop-down {
                background-color: transparent;
                border: none;
                padding: 2px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #8E8E98;
            }
        """)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_row.addWidget(self.provider_combo)
        
        provider_row.addStretch()
        provider_layout.addLayout(provider_row)
        
        # Model selection (shown when provider selected)
        model_row = QHBoxLayout()
        
        model_label = QLabel("Model:")
        model_label.setStyleSheet("""
            color: #E2E2E6;
            font-size: 10px;
            font-weight: 500;
            min-width: 70px;
        """)
        model_row.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 6px 10px;
                min-width: 200px;
                font-size: 10px;
            }
            QComboBox:hover {
                border-color: #3B82F6;
            }
            QComboBox::drop-down {
                background-color: transparent;
                border: none;
                padding: 2px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #8E8E98;
            }
        """)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        model_row.addWidget(self.model_combo)
        
        # Refresh models button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedHeight(24)
        refresh_btn.setFixedWidth(60)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #3B82F6;
                border: 1px solid #252528;
                border-radius: 4px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #252528;
            }
        """)
        refresh_btn.clicked.connect(self._on_refresh_models)
        model_row.addWidget(refresh_btn)
        
        model_row.addStretch()
        provider_layout.addLayout(model_row)
        
        # Provider Status Indicator
        status_layout = QHBoxLayout()
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #6B7280; font-size: 14px;")
        status_layout.addWidget(self.status_indicator)
        
        self.status_label = QLabel("No provider selected")
        self.status_label.setStyleSheet("""
            color: #8E8E98;
            font-size: 10px;
        """)
        status_layout.addWidget(self.status_label)
        
        provider_layout.addLayout(status_layout)
        
        layout.addWidget(provider_group)
        
        # Advanced Settings (collapsible)
        advanced_group = QGroupBox("Advanced Settings")
        advanced_group.setStyleSheet("""
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
        
        advanced_layout = QVBoxLayout(advanced_group)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.setSpacing(8)
        
        # API Key input (for cloud providers)
        api_key_row = QHBoxLayout()
        
        api_key_label = QLabel("API Key:")
        api_key_label.setStyleSheet("""
            color: #E2E2E6;
            font-size: 10px;
            font-weight: 500;
            min-width: 70px;
        """)
        api_key_row.addWidget(api_key_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setStyleSheet("""
            QLineEdit {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 6px 10px;
                min-width: 250px;
                font-size: 10px;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
            }
        """)
        self.api_key_input.textChanged.connect(self._on_api_key_changed)
        api_key_row.addWidget(self.api_key_input)
        
        # Test connection button
        test_btn = QPushButton("Test")
        test_btn.setFixedHeight(24)
        test_btn.setFixedWidth(50)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #10B981;
                border: 1px solid #252528;
                border-radius: 4px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #252528;
            }
        """)
        test_btn.clicked.connect(self._on_test_connection)
        api_key_row.addWidget(test_btn)
        
        api_key_row.addStretch()
        advanced_layout.addLayout(api_key_row)
        
        layout.addWidget(advanced_group)
        
        # Provider Actions Row
        actions_row = QHBoxLayout()
        
        # Remove provider button
        self.remove_btn = QPushButton("Remove Provider")
        self.remove_btn.setFixedHeight(24)
        self.remove_btn.setFixedWidth(130)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
            QPushButton:disabled {
                background-color: #252528;
                color: #52525C;
            }
        """)
        self.remove_btn.clicked.connect(self._on_remove_provider)
        actions_row.addWidget(self.remove_btn)
        
        actions_row.addStretch()
        layout.addLayout(actions_row)
        
    def _refresh_providers(self):
        """Refresh provider list."""
        self.provider_combo.clear()
        
        for provider_name, provider in self.provider_registry.get_all_providers().items():
            display_name = provider_name.upper()
            self.provider_combo.addItem(display_name, provider_name)
        
        # Select first provider if available
        if self.provider_combo.count() > 0:
            self.provider_combo.setCurrentIndex(0)
            self._on_provider_changed(0)
        
    def _on_provider_changed(self, index: int):
        """Handle provider selection change."""
        provider_name = self.provider_combo.currentData()
        
        if provider_name:
            self._current_provider = provider_name
            self._refresh_models(provider_name)
            self._update_status(provider_name)
            
            # Get API key from provider config if available
            provider = self.provider_registry.get_provider(provider_name)
            if provider and provider.config.api_key:
                self.api_key_input.setText(provider.config.api_key)
        else:
            self._current_provider = None
            self.model_combo.clear()
            self.status_label.setText("No provider selected")
        
        self.provider_changed.emit(provider_name or "")
        
    def _on_model_changed(self, index: int):
        """Handle model selection change."""
        model_id = self.model_combo.currentData()
        self._current_model = model_id
        self.model_changed.emit(model_id or "")
        
    def _refresh_models(self, provider_name: str):
        """Refresh models for selected provider."""
        self.model_combo.clear()
        
        provider = self.provider_registry.get_provider(provider_name)
        if not provider:
            return
        
        models = provider.get_models()
        
        for model_id, model_info in models.items():
            model_name = model_info.get("name", model_info.get("id", model_id))
            self.model_combo.addItem(model_name, model_id)
        
        # Select default model if available
        if self.model_combo.count() > 0:
            self.model_combo.setCurrentIndex(0)
            self._current_model = self.model_combo.currentData()
            self.model_changed.emit(self._current_model)
        
    def _update_status(self, provider_name: str):
        """Update provider status indicator."""
        provider = self.provider_registry.get_provider(provider_name)
        if not provider:
            return
        
        status = provider.get_status()
        
        if status.value == "connected":
            self.status_indicator.setText("●")
            self.status_indicator.setStyleSheet("color: #10B981; font-size: 14px;")
            self.status_label.setText(f"Connected: {provider.config.endpoint}")
        elif status.value == "disconnected":
            self.status_indicator.setText("●")
            self.status_indicator.setStyleSheet("color: #EF4444; font-size: 14px;")
            self.status_label.setText("Disconnected")
        elif status.value == "error":
            self.status_indicator.setText("●")
            self.status_indicator.setStyleSheet("color: #EF4444; font-size: 14px;")
            self.status_label.setText(f"Error: {provider.config.connection_status}")
        else:
            self.status_indicator.setText("●")
            self.status_indicator.setStyleSheet("color: #6B7280; font-size: 14px;")
            self.status_label.setText(f"Status: {status.value}")
        
    def _on_api_key_changed(self, text: str):
        """Handle API key change."""
        if self._current_provider:
            self.api_key_changed.emit(self._current_provider, text)
        
    def _on_refresh_models(self):
        """Refresh models for current provider."""
        if self._current_provider:
            self._refresh_models(self._current_provider)
        
    def _on_test_connection(self):
        """Test connection to current provider."""
        if self._current_provider:
            api_key = self.api_key_input.text().strip()
            
            # Test with provided API key if any
            if api_key:
                # Save API key
                provider = self.provider_registry.get_provider(self._current_provider)
                if provider:
                    provider.config.api_key = api_key
            
            result = self.event_bus.publish("ai_test_provider_connection", {
                "provider_name": self._current_provider,
            })
            
            # Show result
            self.status_label.setText(f"Connection test sent for {self._current_provider}")
    
    def _on_remove_provider(self):
        """Remove current provider."""
        if self._current_provider:
            reply = QMessageBox.question(
                self, "Remove Provider",
                f"Are you sure you want to remove provider '{self._current_provider}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Remove from provider registry
                self.provider_registry.unregister_provider(self._current_provider)
                
                # Clear the provider
                self._current_provider = None
                self.provider_combo.removeItem(self.provider_combo.currentIndex())
                self.model_combo.clear()
                self.api_key_input.clear()
                self.status_label.setText("Provider removed")
                self.status_label.setStyleSheet("color: #EF4444; font-size: 10px;")
