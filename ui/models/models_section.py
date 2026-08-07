"""
Models Section — v1.4

Integrates the Models Page into the AI Engineering Workspace.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel,
    QPushButton, QStackedWidget
)
from PySide6.QtCore import Qt
from core.logger import setup_logger

from ai.models.model_center import ModelCenter
from ai.providers.provider_registry import ProviderRegistry
from ai.providers.provider_manager import ProviderManager
from ai.models.model_registry import ModelRegistry

from ai.models import model_center
from ui.models.models_page import ModelsPage
from ui.models.marketplace_page import MarketplacePage

logger = setup_logger(__name__)


class ModelsSection(QWidget):
    """
    Models section in AI Engineering Workspace.
    
    Provides:
    - Provider model management
    - Model cards with Normal/Advanced views
    - Smart model recommendations
    - Privacy mode selector
    """
    
    model_selected = Signal(str)
    privacy_mode_changed = Signal(str)
    
    def __init__(self, event_bus, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        self.model_center = None
        self.provider_registry = None
        self.provider_manager = None
        self.model_registry = None
        self.privacy_mode = "automatic"
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Section header
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
        
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Content area
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: #161618;")
        
        # Models page
        self.models_page = ModelsPage(self.model_center)
        self.models_page.model_selected.connect(self.model_selected.emit)
        self.content_stack.addWidget(self.models_page)
        
        # Marketplace page
        self.marketplace_page = MarketplacePage(self.provider_registry)
        self.content_stack.addWidget(self.marketplace_page)
        
        layout.addWidget(self.content_stack)
        
        # Mode toggle
        self.mode_toggle = QPushButton("Models")
        self.mode_toggle.setFixedHeight(28)
        self.mode_toggle.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #8E8E98;
                border: 1px solid #252528;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 600;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #252528;
                color: #E2E2E6;
            }
            QPushButton:checked {
                background-color: #3B82F6;
                color: #FFFFFF;
            }
        """)
        self.mode_toggle.setCheckable(True)
        self.mode_toggle.setChecked(True)
        self.mode_toggle.toggled.connect(self._on_mode_toggled)
        
        mode_layout = QHBoxLayout()
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.addWidget(self.mode_toggle)
        layout.addLayout(mode_layout)
        
        # Subscribe to model-related events
        self.event_bus.subscribe("model_selected", self._on_model_selected_event)
    
    def initialize(self, model_center: ModelCenter, provider_registry: ProviderRegistry,
                   provider_manager: ProviderManager, model_registry: ModelRegistry):
        """Initialize with dependencies."""
        self.model_center = model_center
        self.provider_registry = provider_registry
        self.provider_manager = provider_manager
        self.model_registry = model_registry
        
        # Initialize pages
        self.models_page = ModelsPage(model_center)
        self.models_page.model_selected.connect(self.model_selected.emit)
        self.content_stack.widget(0).deleteLater()
        self.content_stack.insertWidget(0, self.models_page)
        
        self.marketplace_page = MarketplacePage(provider_registry)
        self.content_stack.widget(1).deleteLater()
        self.content_stack.insertWidget(1, self.marketplace_page)
        
        logger.info("ModelsSection initialized")
    
    def _on_privacy_changed(self, index: int):
        """Handle privacy mode change."""
        self.privacy_mode = self.privacy_combo.currentData()
        self.privacy_mode_changed.emit(self.privacy_mode)
        logger.info(f"Privacy mode changed to: {self.privacy_mode}")
    
    def _on_mode_toggled(self, checked: bool):
        """Handle mode toggle."""
        if checked:
            self.content_stack.setCurrentIndex(0)
            self.mode_toggle.setText("Models")
        else:
            self.content_stack.setCurrentIndex(1)
            self.mode_toggle.setText("Marketplace")
    
    def _on_model_selected_event(self, data: dict):
        """Handle model selected event."""
        model_id = data.get("model_id", "")
        self.model_selected.emit(model_id)
    
    def set_privacy_mode(self, mode: str):
        """Set privacy mode."""
        self.privacy_mode = mode
        idx = self.privacy_combo.findData(mode)
        if idx >= 0:
            self.privacy_combo.setCurrentIndex(idx)
    
    def select_model(self, model_id: str):
        """Programmatically select a model."""
        self.models_page.model_selected.emit(model_id)
