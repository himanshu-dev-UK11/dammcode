"""
Marketplace Page — v1.4

Model marketplace UI for enabling providers.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel,
    QPushButton, QFrame, QGroupBox, QCheckBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from core.logger import setup_logger

from ai.providers.provider_registry import ProviderRegistry

logger = setup_logger(__name__)


class ProviderCard(QWidget):
    """Card displaying provider information and enabling it."""
    
    provider_enabled = Signal(str, bool)
    provider_tested = Signal(str)
    
    def __init__(self, provider_name: str, provider_info: dict, parent=None):
        super().__init__(parent)
        self.provider_name = provider_name
        self.provider_info = provider_info
        self.enabled = provider_info.get("enabled", False)
        self.setup_ui()
        
    def setup_ui(self):
        self.setObjectName("ProviderCard")
        self.setStyleSheet("""
            #ProviderCard {
                background-color: #111113;
                border: 1px solid #252528;
                border-radius: 6px;
                padding: 0;
            }
            #ProviderCard:hover {
                border: 1px solid #3B82F6;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Content
        content = self._create_content()
        layout.addWidget(content)
        
        # Footer
        footer = self._create_footer()
        layout.addWidget(footer)
    
    def _create_header(self) -> QWidget:
        """Create header with provider name."""
        header = QWidget()
        header.setStyleSheet("background-color: #161618;")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Provider name
        name = QLabel(self.provider_info.get("display_name", self.provider_name.upper()))
        name.setStyleSheet("""
            color: #E2E2E6;
            font-size: 14px;
            font-weight: 600;
        """)
        layout.addWidget(name)
        
        layout.addStretch()
        
        # Status indicator
        status = QLabel("●" if self.enabled else "○")
        status.setStyleSheet(f"""
            color: {'#22C55E' if self.enabled else '#52525C'};
            font-size: 10px;
        """)
        layout.addWidget(status)
        
        return header
    
    def _create_content(self) -> QWidget:
        """Create content with provider details."""
        content = QWidget()
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        
        # Endpoint
        endpoint = QLabel(f"Endpoint: {self.provider_info.get('endpoint', 'N/A')}")
        endpoint.setStyleSheet("""
            color: #8E8E98;
            font-size: 10px;
            font-family: "JetBrains Mono", monospace;
        """)
        layout.addWidget(endpoint)
        
        # Authentication
        auth = QLabel(f"Auth: {self.provider_info.get('auth_type', 'none').upper()}")
        auth.setStyleSheet("color: #52525C; font-size: 10px;")
        layout.addWidget(auth)
        
        # Capabilities
        caps = self.provider_info.get("capabilities", {})
        if caps:
            caps_row = QHBoxLayout()
            caps_row.setSpacing(4)
            
            for cap, supported in caps.items():
                if supported:
                    badge = QLabel(f"✓ {cap}")
                    badge.setStyleSheet("""
                        background-color: #1C1C1F;
                        color: #22C55E;
                        font-size: 9px;
                        padding: 1px 4px;
                        border-radius: 2px;
                    """)
                    caps_row.addWidget(badge)
            
            if caps_row.count() > 0:
                layout.addLayout(caps_row)
        
        return content
    
    def _create_footer(self) -> QWidget:
        """Create footer with action buttons."""
        footer = QWidget()
        footer.setStyleSheet("background-color: #111113;")
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        
        # Test connection button
        test_btn = QPushButton("Test")
        test_btn.setFixedHeight(28)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #252528;
                border-radius: 4px;
                font-size: 11px;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #252528;
            }
            QPushButton:pressed {
                background-color: #3B82F6;
            }
        """)
        test_btn.clicked.connect(lambda: self.provider_tested.emit(self.provider_name))
        layout.addWidget(test_btn)
        
        # Enable toggle
        self.enable_btn = QPushButton("Enable" if not self.enabled else "Disable")
        self.enable_btn.setFixedHeight(28)
        self.enable_btn.setStyleSheet(self._get_enable_style())
        self.enable_btn.clicked.connect(self._on_enable_toggled)
        layout.addWidget(self.enable_btn)
        
        layout.addStretch()
        
        return footer
    
    def _get_enable_style(self) -> str:
        """Get style for enable button."""
        if self.enabled:
            return """
                QPushButton {
                    background-color: #EF4444;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 0 12px;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                }
                QPushButton:pressed {
                    background-color: #B91C1C;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #22C55E;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 0 12px;
                }
                QPushButton:hover {
                    background-color: #16A34A;
                }
                QPushButton:pressed {
                    background-color: #15803D;
                }
            """
    
    def _on_enable_toggled(self):
        """Handle enable toggle."""
        self.enabled = not self.enabled
        self.provider_enabled.emit(self.provider_name, self.enabled)
        self.enable_btn.setText("Enable" if not self.enabled else "Disable")
        self.enable_btn.setStyleSheet(self._get_enable_style())


class MarketplacePage(QWidget):
    """Main marketplace page for managing providers."""
    
    provider_enabled = Signal(str, bool)
    
    def __init__(self, provider_registry: ProviderRegistry, parent=None):
        super().__init__(parent)
        self.provider_registry = provider_registry
        self.provider_cards = {}
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top bar
        top_bar = self._create_top_bar()
        layout.addWidget(top_bar)
        
        # Provider list
        self.providers_container = QWidget()
        self.providers_layout = QVBoxLayout(self.providers_container)
        self.providers_layout.setContentsMargins(0, 0, 0, 0)
        self.providers_layout.setSpacing(8)
        self.providers_layout.addStretch()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.providers_container)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        layout.addWidget(scroll)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Providers")
        refresh_btn.setFixedHeight(36)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_providers)
        layout.addWidget(refresh_btn, alignment=Qt.AlignCenter)
        
        # Initial load
        self._refresh_providers()
    
    def _create_top_bar(self) -> QWidget:
        """Create top control bar."""
        bar = QWidget()
        bar.setStyleSheet("background-color: #111113; border-bottom: 1px solid #252528;")
        bar.setFixedHeight(50)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("Provider Marketplace")
        title.setStyleSheet("""
            color: #E2E2E6;
            font-size: 14px;
            font-weight: 600;
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Search
        search = QLineEdit()
        search.setPlaceholderText("Search providers...")
        search.setFixedWidth(200)
        search.setStyleSheet("""
            QLineEdit {
                background-color: #1C1C1F;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 6px 10px;
                color: #E2E2E6;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
            }
        """)
        search.textChanged.connect(self._on_search_changed)
        layout.addWidget(search)
        
        return bar
    
    def _refresh_providers(self):
        """Refresh provider cards."""
        # Clear existing cards
        while self.providers_layout.count() > 1:
            item = self.providers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get all registered providers
        providers = self.provider_registry.get_all_providers()
        
        if len(providers) == 0:
            empty_label = QLabel("No providers registered")
            empty_label.setStyleSheet("""
                color: #52525C;
                font-size: 12px;
                padding: 20px;
            """)
            self.providers_layout.insertWidget(self.providers_layout.count() - 1, empty_label)
            return
        
        # Create cards for each provider
        for provider_name, provider in providers.items():
            provider_info = {
                "provider_name": provider_name,
                "display_name": provider.config.provider_name,
                "endpoint": provider.config.endpoint,
                "auth_type": provider.config.auth_type.value,
                "enabled": provider.config.enabled,
                "capabilities": {
                    "streaming": provider.supports_streaming(),
                    "tool_calling": provider.supports_tool_calling(),
                    "vision": provider.supports_vision(),
                    "function_calling": provider.supports_function_calling(),
                },
            }
            
            card = ProviderCard(provider_name, provider_info)
            card.provider_enabled.connect(self.provider_enabled.emit)
            card.provider_tested.connect(lambda name: self._test_provider(name))
            self.providers_layout.insertWidget(self.providers_layout.count() - 1, card)
            self.provider_cards[provider_name] = card
    
    def _on_search_changed(self, text: str):
        """Handle search text change."""
        for card in self.provider_cards.values():
            provider_name = card.provider_name.lower()
            provider_info = card.provider_info
            display_name = provider_info.get("display_name", "").lower()
            endpoint = provider_info.get("endpoint", "").lower()
            
            if text.lower() in provider_name or text.lower() in display_name or text.lower() in endpoint:
                card.setVisible(True)
            else:
                card.setVisible(False)
    
    def _test_provider(self, provider_name: str):
        """Test provider connection."""
        provider = self.provider_registry.get_provider(provider_name)
        if provider:
            success = provider.test_connection()
            if success:
                provider._update_status(None)
                self.provider_registry._health[provider_name] = {
                    "last_tested": "just now",
                    "success_rate": 1.0,
                }
            else:
                provider._update_status(None)
    
    def get_enabled_providers(self) -> list[str]:
        """Get list of enabled provider names."""
        return [name for name, card in self.provider_cards.items() if card.enabled]


# Global instance
_marketplace_page = None


def get_marketplace_page() -> MarketplacePage:
    """Get the global marketplace page instance."""
    global _marketplace_page
    return _marketplace_page


def initialize_marketplace_page(provider_registry: ProviderRegistry) -> MarketplacePage:
    """Initialize the global marketplace page."""
    global _marketplace_page
    _marketplace_page = MarketplacePage(provider_registry)
    return _marketplace_page


def reset_marketplace_page():
    """Reset the global marketplace page."""
    global _marketplace_page
    _marketplace_page = None
