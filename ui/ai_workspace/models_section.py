"""Models Section - v1.4

Professional model management with:
- Provider grouping (Local, Cloud, Custom, Experimental, Unavailable)
- Model cards with Normal/Advanced views
- Model rating display
- Smart recommendations
- Privacy mode selector
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QScrollArea, QSpacerItem, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from core.logger import setup_logger
from ai.models.model_center import ModelCenter, ModelInfo
from ai.providers.provider_registry import ProviderRegistry
from ai.providers.provider_manager import ProviderManager
from ai.models.model_registry import ModelRegistry
from ui.ai_workspace.connect_provider_dialog import ConnectProviderDialog

logger = setup_logger(__name__)


class ModelsSection(QWidget):
    """Display current model and allow selection through Model Center."""
    model_selected = Signal(str)
    privacy_mode_changed = Signal(str)
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self.model_center = None
        self.provider_registry = None
        self.provider_manager = None
        self.model_registry = None
        self.privacy_mode = "automatic"
        self.current_model = None
        self._provider_combo = None  # Will be created in setup_ui
        self._refresh_models_timer = None  # For deferring model list refresh
        self.setup_ui()
    
    def set_providers(self, provider_registry, provider_manager):
        """Set provider registry and manager."""
        self.provider_registry = provider_registry
        self.provider_manager = provider_manager
        # Store for use in initialization
        self._provider_manager = provider_manager
        self._provider_registry = provider_registry
        # Populate providers after initialization
        self._populate_providers()
        # Defer model list refresh until model_center is set
        if self.model_center:
            self._refresh_models_list()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setStyleSheet("background-color: #111113; border-bottom: 1px solid #252528;")
        header.setFixedHeight(36)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(8)
        
        title = QLabel("MODELS")
        title.setStyleSheet("""
            color: #52525C;
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 1px;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Connect New Provider button
        self.connect_btn = QPushButton("+ Connect New Provider")
        self.connect_btn.setFixedHeight(24)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #3B82F6;
                border: 1px solid #252528;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 500;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: #1C1C1F;
                border-color: #3B82F6;
            }
        """)
        self.connect_btn.clicked.connect(self._on_connect_provider)
        header_layout.addWidget(self.connect_btn)
        
        layout.addWidget(header)
        
        # Provider selector row
        provider_row = QHBoxLayout()
        provider_row.setSpacing(6)
        
        provider_label = QLabel("Provider:")
        provider_label.setStyleSheet("color: #8E8E98; font-size: 10px;")
        provider_row.addWidget(provider_label)
        
        self._provider_combo = QComboBox()
        self._provider_combo.addItem("Automatic", "automatic")
        self._provider_combo.setStyleSheet("""
            QComboBox {
                background-color: #1C1C1F;
                border: 1px solid #252528;
                border-radius: 2px;
                padding: 2px 6px;
                color: #E2E2E6;
                font-size: 10px;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #3B82F6;
            }
        """)
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_row.addWidget(self._provider_combo)
        
        layout.addLayout(provider_row)
        
        # Privacy mode selector
        privacy_label = QLabel("Privacy:")
        privacy_label.setStyleSheet("color: #8E8E98; font-size: 10px;")
        header_layout.addWidget(privacy_label)
        
        self.privacy_combo = QComboBox()
        self.privacy_combo.addItem("Automatic", "automatic")
        self.privacy_combo.addItem("Local Only", "local_only")
        self.privacy_combo.addItem("Cloud Only", "cloud_only")
        self.privacy_combo.addItem("Ask Before Cloud", "ask_before_cloud")
        self.privacy_combo.setStyleSheet("""
            QComboBox {
                background-color: #1C1C1F;
                border: 1px solid #252528;
                border-radius: 2px;
                padding: 2px 6px;
                color: #E2E2E6;
                font-size: 9px;
                min-width: 100px;
            }
            QComboBox:hover {
                border-color: #3B82F6;
            }
        """)
        self.privacy_combo.currentIndexChanged.connect(self._on_privacy_changed)
        header_layout.addWidget(self.privacy_combo)
        
        # Select model button
        self.select_btn = QPushButton("Select Model")
        self.select_btn.setFixedHeight(24)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        self.select_btn.clicked.connect(self._on_select_model)
        header_layout.addWidget(self.select_btn)
        
        layout.addWidget(header)
        
        # Current model display
        current = QWidget()
        current.setStyleSheet("background-color: #161618;")
        
        current_layout = QVBoxLayout(current)
        current_layout.setContentsMargins(10, 8, 10, 8)
        current_layout.setSpacing(4)
        
        # Current model row
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        
        self._dot = QLabel("●")
        self._dot.setStyleSheet("color: #52525C; font-size: 8px; background-color: transparent;")
        self._name = QLabel("No model selected")
        self._name.setStyleSheet("color: #E2E2E6; font-size: 12px; font-weight: 500; background-color: transparent;")
        self._name.setAlignment(Qt.AlignVCenter)
        
        name_row.addWidget(self._dot)
        name_row.addWidget(self._name)
        current_layout.addLayout(name_row)
        
        # Model info row - with model selector
        info_row = QHBoxLayout()
        info_row.setSpacing(12)
        
        self._provider_label = QLabel("Provider:")
        self._provider_label.setStyleSheet("color: #8E8E98; font-size: 10px;")
        info_row.addWidget(self._provider_label)
        
        self._provider = QLabel("—")
        self._provider.setStyleSheet("color: #52525C; font-size: 10px; background-color: transparent;")
        
        self._context = QLabel("—")
        self._context.setStyleSheet("color: #52525C; font-size: 10px; background-color: transparent;")
        
        self._cost = QLabel("—")
        self._cost.setStyleSheet("color: #52525C; font-size: 10px; background-color: transparent;")
        
        info_row.addWidget(self._provider)
        info_row.addWidget(self._context)
        info_row.addWidget(self._cost)
        current_layout.addLayout(info_row)
        
        # Model selector row
        model_select_row = QHBoxLayout()
        model_select_row.setSpacing(8)
        
        model_label = QLabel("Model:")
        model_label.setStyleSheet("color: #8E8E98; font-size: 10px;")
        model_select_row.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #1C1C1F;
                border: 1px solid #252528;
                border-radius: 2px;
                padding: 2px 6px;
                color: #E2E2E6;
                font-size: 10px;
                min-width: 150px;
            }
            QComboBox:hover {
                border-color: #3B82F6;
            }
        """)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        model_select_row.addWidget(self.model_combo)
        current_layout.addLayout(model_select_row)
        
        layout.addWidget(current)
        
        # Models list (scrollable)
        self.models_scroll = QScrollArea()
        self.models_scroll.setWidgetResizable(True)
        self.models_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.models_container = QWidget()
        self.models_layout = QVBoxLayout(self.models_container)
        self.models_layout.setContentsMargins(0, 0, 0, 0)
        self.models_layout.setSpacing(6)
        self.models_layout.addStretch()
        
        self.models_scroll.setWidget(self.models_container)
        layout.addWidget(self.models_scroll, stretch=1)
        
        # Subscribe to events
        self.event_bus.subscribe("model_selected", self._on_model_selected_event)
        self.event_bus.subscribe("provider_status_changed", self._on_provider_status_changed)
        
        # Store references for provider/model management
        self._provider_manager = None
        self._model_center = None
        
    def set_provider_manager(self, provider_manager):
        """Set provider manager to populate provider list."""
        self._provider_manager = provider_manager
        self._populate_providers()
        
    def _populate_providers(self):
        """Populate provider dropdown from provider manager."""
        if not self._provider_combo:
            return
            
        self._provider_combo.clear()
        self._provider_combo.addItem("Automatic", "automatic")
        
        if self._provider_manager and self._provider_registry:
            # Get loaded providers from registry
            all_providers = self._provider_registry.get_all_providers()
            if all_providers:
                for provider_name, _ in all_providers.items():
                    self._provider_combo.addItem(provider_name, provider_name)
            else:
                self._provider_combo.addItem("No providers configured", "no_providers")
        else:
            self._provider_combo.addItem("No providers configured", "no_providers")
            
        # Set default to first provider if available
        if self._provider_combo.count() > 2:
            self._provider_combo.setCurrentIndex(1)
            
    def _on_provider_changed(self, index: int):
        """Handle provider selection change."""
        provider_id = self._provider_combo.currentData()
        self._refresh_models_list()
    
    def initialize(self, model_center=None):
        """Initialize with model center (optional for now)."""
        if model_center:
            self.model_center = model_center
            self._refresh_models_list()
        logger.info("ModelsSection initialized")
    
    def _refresh_models_list(self):
        """Refresh the models list display."""
        if not self._provider_combo:
            return
            
        # Clear existing items
        while self.models_layout.count() > 1:
            item = self.models_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get models for current provider
        provider_id = self._provider_combo.currentData()
        
        if provider_id == "no_providers" or provider_id is None:
            empty_label = QLabel("No providers configured")
            empty_label.setStyleSheet("color: #52525C; font-size: 11px; padding: 10px;")
            self.models_layout.insertWidget(0, empty_label)
            return
        
        if not self.model_center:
            empty_label = QLabel("Loading models...")
            empty_label.setStyleSheet("color: #52525C; font-size: 11px; padding: 10px;")
            self.models_layout.insertWidget(0, empty_label)
            return
        
        # Get enabled models
        models = self.model_center.get_enabled_models()
        
        if len(models) == 0:
            empty_label = QLabel("No models available")
            empty_label.setStyleSheet("color: #52525C; font-size: 11px; padding: 10px;")
            self.models_layout.insertWidget(0, empty_label)
            return
        
        # Filter by provider if not "automatic"
        if provider_id != "automatic":
            models = {k: v for k, v in models.items() if v.provider == provider_id}
        
        if len(models) == 0:
            empty_label = QLabel(f"No models for {provider_id}")
            empty_label.setStyleSheet("color: #52525C; font-size: 11px; padding: 10px;")
            self.models_layout.insertWidget(0, empty_label)
            return
        
        # Sort by priority
        sorted_models = sorted(models.values(), key=lambda m: m.priority, reverse=True)
        
        # Update model combo box
        self.model_combo.clear()
        for model in sorted_models:
            card = self._create_model_card(model)
            self.models_layout.insertWidget(self.models_layout.count() - 1, card)
            
            # Add to combo box
            self.model_combo.addItem(f"{model.display_name} ({model.model_id})", model.model_id)
        
        # Select first model if none selected
        if not self.current_model and sorted_models:
            self.select_model(sorted_models[0].model_id)
    
    def _create_model_card(self, model: ModelInfo) -> QWidget:
        """Create a model selection card."""
        card = QWidget()
        card.setObjectName("ModelCard")
        card.setStyleSheet("""
            #ModelCard {
                background-color: #1C1C1F;
                border: 1px solid #252528;
                border-radius: 4px;
            }
            #ModelCard:hover {
                border: 1px solid #3B82F6;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)
        
        # Model name
        name_label = QLabel(model.display_name)
        name_label.setStyleSheet("color: #E2E2E6; font-size: 11px; font-weight: 600;")
        layout.addWidget(name_label)
        
        # Provider and context
        info_layout = QHBoxLayout()
        info_layout.setSpacing(8)
        
        provider_label = QLabel(model.provider)
        provider_label.setStyleSheet("color: #8E8E98; font-size: 10px;")
        info_layout.addWidget(provider_label)
        
        context_label = QLabel(f"{model.context_window // 1000}K ctx")
        context_label.setStyleSheet("color: #52525C; font-size: 10px;")
        info_layout.addWidget(context_label)
        
        layout.addLayout(info_layout)
        
        return card
    
    def _on_privacy_changed(self, index: int):
        """Handle privacy mode change."""
        self.privacy_mode = self.privacy_combo.currentData()
        self.privacy_mode_changed.emit(self.privacy_mode)
        logger.info(f"Privacy mode changed to: {self.privacy_mode}")
        
        # Refresh model list based on privacy mode
        self._refresh_models_list()
    
    def _on_select_model(self):
        """Open model selector dialog."""
        # For now, just select the highest priority model
        models = self.model_center.get_enabled_models()
        if models:
            sorted_models = sorted(models.values(), key=lambda m: m.priority, reverse=True)
            self.select_model(sorted_models[0].model_id)
    
    def _on_model_selected_event(self, data: dict):
        """Handle model selected event."""
        model_id = data.get("model_id", "")
        self.select_model(model_id)
    
    def _on_provider_status_changed(self, data: dict):
        """Handle provider status change."""
        provider = data.get("provider", "")
        if provider:
            self._refresh_models_list()
    
    def set_model_center(self, model_center, provider_registry, provider_manager, model_registry):
        """Set the model center instance (called after initialization)."""
        self.model_center = model_center
        self.provider_registry = provider_registry
        self.provider_manager = provider_manager
        self.model_registry = model_registry
        self._populate_providers()
        self._refresh_models_list()
        
    def set_model(self, name: str, provider: str = "", context_k: int = 0, active: bool = True):
        """Set the current model display."""
        if name:
            self._name.setText(name)
            self._provider.setText(provider)
            self._context.setText(f"{context_k}K ctx" if context_k else "—")
            
            if active:
                self._dot.setStyleSheet("color: #22C55E; font-size: 8px; background-color: transparent;")
            else:
                self._dot.setStyleSheet("color: #52525C; font-size: 8px; background-color: transparent;")
                
        # Refresh the provider combo
        if provider and self._provider_combo:
            idx = self._provider_combo.findData(provider)
            if idx >= 0:
                self._provider_combo.setCurrentIndex(idx)
    
    def select_model(self, model_id: str):
        """Select a model by ID."""
        model = self.model_center.get_model(model_id)
        if not model:
            return
        
        self.current_model = model
        self._name.setText(model.display_name)
        self._provider.setText(model.provider)
        self._context.setText(f"{model.context_window // 1000}K ctx")
        self._cost.setText("Free" if model.cost_type == "free" else "Paid")
        
        dot_color = "#22C55E"
        self._dot.setStyleSheet(f"color: {dot_color}; font-size: 8px; background-color: transparent;")
        
        self.model_selected.emit(model_id)
        self.event_bus.publish("model_changed", {"model_id": model_id})
        
    def _on_model_changed(self, index: int):
        """Handle model selection change from dropdown."""
        model_id = self.model_combo.currentData()
        if model_id:
            self.select_model(model_id)
    
    def get_current_model(self) -> ModelInfo:
        """Get currently selected model."""
        return self.current_model
    
    def get_privacy_mode(self) -> str:
        """Get current privacy mode."""
        return self.privacy_mode
    
    def _on_connect_provider(self):
        """Open dialog to connect new provider."""
        from PySide6.QtWidgets import QDialog
        
        dialog = ConnectProviderDialog(self)
        
        if dialog.exec() == QDialog.Accepted:
            # The dialog will emit provider_connected signal
            # Get the provider info
            provider_info = dialog.get_provider_info()
            
            provider_name = provider_info["provider_name"]
            api_key = provider_info["api_key"]
            endpoint = provider_info["endpoint"]
            models = provider_info["models"]
            
            if self.event_bus:
                # Emit event for model manager to handle
                self.event_bus.publish("provider_connected", {
                    "provider_name": provider_name,
                    "api_key": api_key,
                    "endpoint": endpoint,
                    "models": models
                })
            
            # Show success notification
            from ui.notifications import NotificationManager, NotificationType
            self.event_bus.publish("notification_show", {
                "title": "Provider Connected",
                "message": f"Successfully connected {provider_name}",
                "type": "success",
                "auto_hide": True
            })
