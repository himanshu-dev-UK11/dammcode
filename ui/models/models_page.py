"""
Models Page — v1.4

Professional model center UI with:
- Provider grouping (Local, Cloud, Custom, Experimental, Unavailable)
- Model cards with Normal/Advanced views
- Model rating display
- Smart recommendations
- Privacy mode selector
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel,
    QPushButton, QFrame, QTabWidget, QStackedWidget, QGroupBox,
    QComboBox, QLineEdit, QSlider, QCheckBox, QSplitter
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor
from core.logger import setup_logger

from ai.models.model_center import ModelCenter, ModelInfo, ModelRating
from ai.providers.provider_registry import ProviderRegistry
from ai.providers.provider_manager import ProviderManager
from ai.models.model_registry import ModelRegistry

logger = setup_logger(__name__)


class ModelRatingDisplay(QWidget):
    """Display model ratings as stars."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setMinimumHeight(30)
        
    def set_ratings(self, ratings: list):
        """Set ratings from list of ModelRating."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Common rating categories
        category_labels = {
            "coding": "Coding",
            "reasoning": "Reasoning",
            "speed": "Speed",
            "context": "Context",
            "tool_use": "Tool Use",
            "vision": "Vision",
            "function_calling": "Function Call",
            "code_editing": "Code Edit",
        }
        
        for rating in ratings:
            # Create rating badge
            badge = QFrame()
            badge.setFixedWidth(80)
            badge.setStyleSheet("""
                QFrame {
                    background-color: #1C1C1F;
                    border-radius: 3px;
                    padding: 2px 6px;
                }
            """)
            
            badge_layout = QVBoxLayout(badge)
            badge_layout.setContentsMargins(0, 0, 0, 0)
            badge_layout.setSpacing(1)
            
            # Category label
            cat_label = QLabel(category_labels.get(rating.use_case, rating.use_case))
            cat_label.setStyleSheet("""
                color: #52525C;
                font-size: 8px;
                font-weight: 600;
                letter-spacing: 0.5px;
            """)
            badge_layout.addWidget(cat_label, alignment=Qt.AlignCenter)
            
            # Star display
            stars = QLabel(rating.stars())
            stars.setStyleSheet("""
                color: #F59E0B;
                font-size: 10px;
                font-weight: 700;
            """)
            badge_layout.addWidget(stars, alignment=Qt.AlignCenter)
            
            layout.addWidget(badge)


class ModelCard(QWidget):
    """Model card displaying model information."""
    
    model_selected = Signal(str)
    model_rated = Signal(str, float)
    
    def __init__(self, model: ModelInfo, advanced_view: bool = False, parent=None):
        super().__init__(parent)
        self.model = model
        self.advanced_view = advanced_view
        self.setup_ui()
        
    def setup_ui(self):
        self.setObjectName("ModelCard")
        self.setStyleSheet("""
            #ModelCard {
                background-color: #111113;
                border: 1px solid #252528;
                border-radius: 6px;
                padding: 0;
            }
            #ModelCard:hover {
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
        """Create header with model name and provider."""
        header = QWidget()
        header.setStyleSheet("background-color: #161618;")
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        
        # Model name row
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        
        # Provider badge
        provider_badge = QLabel(self.model.provider.upper())
        provider_badge.setStyleSheet("""
            background-color: #3B82F6;
            color: #FFFFFF;
            font-size: 9px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 3px;
        """)
        provider_badge.setFixedHeight(20)
        name_row.addWidget(provider_badge)
        
        # Model name
        name_label = QLabel(self.model.display_name)
        name_label.setStyleSheet("""
            color: #E2E2E6;
            font-size: 14px;
            font-weight: 600;
        """)
        name_row.addWidget(name_label)
        
        layout.addLayout(name_row)
        
        # Status row
        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        
        # Status indicator
        status_badge = QLabel(self._get_status_text())
        status_badge.setStyleSheet(self._get_status_style())
        status_badge.setFixedHeight(18)
        status_row.addWidget(status_badge)
        
        # Context window
        context_label = QLabel(f"{self.model.context_window // 1000}K ctx")
        context_label.setStyleSheet("""
            color: #52525C;
            font-size: 10px;
        """)
        status_row.addWidget(context_label)
        
        # Cost badge
        cost_badge = QLabel(self.model.cost_type.upper())
        cost_badge.setStyleSheet("""
            background-color: #1C1C1F;
            color: #22C55E;
            font-size: 9px;
            font-weight: 600;
            padding: 1px 6px;
            border-radius: 2px;
        """)
        status_row.addWidget(cost_badge)
        
        layout.addLayout(status_row)
        
        return header
    
    def _create_content(self) -> QWidget:
        """Create content with model info."""
        content = QWidget()
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        
        if self.advanced_view:
            # Advanced view: detailed capabilities and ratings
            layout.addWidget(self._create_advanced_content())
        else:
            # Normal view: compact summary
            layout.addWidget(self._create_normal_content())
        
        return content
    
    def _create_normal_content(self) -> QWidget:
        """Create normal view content."""
        normal = QWidget()
        layout = QVBoxLayout(normal)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Brief description
        desc = QLabel(self.model.tags[0] if self.model.tags else "AI Model")
        desc.setStyleSheet("""
            color: #8E8E98;
            font-size: 11px;
        """)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Quick capabilities
        caps_row = QHBoxLayout()
        caps_row.setSpacing(4)
        
        if self.model.capabilities.streaming:
            streaming_badge = QLabel("⚡")
            streaming_badge.setToolTip("Streaming")
            streaming_badge.setStyleSheet("""
                background-color: #1C1C1F;
                color: #3B82F6;
                font-size: 10px;
                padding: 1px 4px;
                border-radius: 2px;
            """)
            caps_row.addWidget(streaming_badge)
        
        if self.model.capabilities.tool_use:
            tool_badge = QLabel("🔧")
            tool_badge.setToolTip("Tool Calling")
            tool_badge.setStyleSheet("""
                background-color: #1C1C1F;
                color: #22C55E;
                font-size: 10px;
                padding: 1px 4px;
                border-radius: 2px;
            """)
            caps_row.addWidget(tool_badge)
        
        if self.model.capabilities.vision:
            vision_badge = QLabel("👁")
            vision_badge.setToolTip("Vision")
            vision_badge.setStyleSheet("""
                background-color: #1C1C1F;
                color: #F59E0B;
                font-size: 10px;
                padding: 1px 4px;
                border-radius: 2px;
            """)
            caps_row.addWidget(vision_badge)
        
        layout.addLayout(caps_row)
        
        return normal
    
    def _create_advanced_content(self) -> QWidget:
        """Create advanced view content."""
        advanced = QWidget()
        layout = QVBoxLayout(advanced)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Detailed capabilities
        layout.addWidget(self._create_capabilities())
        
        # Ratings by use case
        layout.addWidget(self._create_ratings())
        
        # Health status
        layout.addWidget(self._create_health_status())
        
        return advanced
    
    def _create_capabilities(self) -> QWidget:
        """Create capabilities section."""
        group = QGroupBox("Capabilities")
        group.setStyleSheet("""
            QGroupBox {
                color: #E2E2E6;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid #252528;
                border-radius: 4px;
                margin-top: 6px;
                padding-top: 6px;
            }
            QGroupBox::title {
                subline-offset: -2px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Capability grid
        grid = QWidget()
        grid_layout = QVBoxLayout(grid)
        grid_layout.setSpacing(3)
        
        capabilities = [
            ("Coding", self.model.capabilities.coding, "#3B82F6"),
            ("Reasoning", self.model.capabilities.reasoning, "#8B5CF6"),
            ("Speed", self.model.capabilities.speed, "#22C55E"),
            ("Context", self.model.capabilities.context, "#F59E0B"),
            ("Tool Use", self.model.capabilities.tool_use, "#10B981"),
            ("Vision", self.model.capabilities.vision, "#F97316"),
            ("Function Call", self.model.capabilities.function_calling, "#EC4899"),
        ]
        
        for name, rating, color in capabilities:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            
            label = QLabel(name)
            label.setStyleSheet("color: #E2E2E6; font-size: 10px;")
            row_layout.addWidget(label)
            
            # Rating bar
            bar = QWidget()
            bar.setFixedHeight(4)
            bar.setStyleSheet(f"""
                background-color: #1C1C1F;
                border-radius: 2px;
            """)
            bar_layout = QVBoxLayout(bar)
            bar_layout.setContentsMargins(0, 0, 0, 0)
            bar_layout.setSpacing(0)
            
            fill = QWidget()
            fill.setFixedWidth(int(rating * 16))  # 16px per star
            fill.setStyleSheet(f"""
                background-color: {color};
                border-radius: 2px;
            """)
            bar_layout.addWidget(fill)
            
            row_layout.addWidget(bar)
            
            # Rating text
            rating_text = QLabel(f"{rating:.1f}/5.0")
            rating_text.setStyleSheet("color: #52525C; font-size: 10px;")
            row_layout.addWidget(rating_text)
            
            grid_layout.addWidget(row)
        
        layout.addWidget(grid)
        
        return group
    
    def _create_ratings(self) -> QWidget:
        """Create ratings by use case."""
        group = QGroupBox("Performance Ratings")
        group.setStyleSheet("""
            QGroupBox {
                color: #E2E2E6;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid #252528;
                border-radius: 4px;
                margin-top: 6px;
                padding-top: 6px;
            }
            QGroupBox::title {
                subline-offset: -2px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        ratings = [
            ("Programming", self.model.get_rating("coding")),
            ("Reasoning", self.model.get_rating("reasoning")),
            ("Translation", self.model.get_rating("translation")),
            ("Debugging", self.model.get_rating("debug")),
            ("Testing", self.model.get_rating("testing")),
            ("Documentation", self.model.get_rating("documentation")),
        ]
        
        for task, rating in ratings:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            
            label = QLabel(task)
            label.setStyleSheet("color: #E2E2E6; font-size: 10px;")
            row_layout.addWidget(label)
            
            stars = QLabel(rating.stars())
            stars.setStyleSheet("color: #F59E0B; font-size: 11px; font-weight: 700;")
            row_layout.addWidget(stars)
            
            rating_text = QLabel(f"{rating.rating:.1f}")
            rating_text.setStyleSheet("color: #52525C; font-size: 10px;")
            row_layout.addWidget(rating_text)
            
            layout.addWidget(row)
        
        return group
    
    def _create_health_status(self) -> QWidget:
        """Create health status section."""
        group = QGroupBox("Health Status")
        group.setStyleSheet("""
            QGroupBox {
                color: #E2E2E6;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid #252528;
                border-radius: 4px;
                margin-top: 6px;
                padding-top: 6px;
            }
            QGroupBox::title {
                subline-offset: -2px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Availability
        availability_row = QWidget()
        availability_layout = QHBoxLayout(availability_row)
        availability_layout.setContentsMargins(0, 0, 0, 0)
        availability_layout.setSpacing(8)
        
        availability_label = QLabel("Availability")
        availability_label.setStyleSheet("color: #E2E2E6; font-size: 10px;")
        availability_layout.addWidget(availability_label)
        
        availability_val = QLabel(f"{self.model.availability * 100:.0f}%")
        availability_val.setStyleSheet("color: #22C55E; font-size: 10px;")
        availability_layout.addWidget(availability_val)
        
        layout.addWidget(availability_row)
        
        # Response time
        response_row = QWidget()
        response_layout = QHBoxLayout(response_row)
        response_layout.setContentsMargins(0, 0, 0, 0)
        response_layout.setSpacing(8)
        
        response_label = QLabel("Response Time")
        response_label.setStyleSheet("color: #E2E2E6; font-size: 10px;")
        response_layout.addWidget(response_label)
        
        response_val = QLabel(f"{self.model.avg_response_time_ms:.0f}ms")
        response_val.setStyleSheet("color: #52525C; font-size: 10px;")
        response_layout.addWidget(response_val)
        
        layout.addWidget(response_row)
        
        return group
    
    def _create_footer(self) -> QWidget:
        """Create footer with action buttons."""
        footer = QWidget()
        footer.setStyleSheet("background-color: #111113;")
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        
        # Select button
        select_btn = QPushButton("Select")
        select_btn.setFixedHeight(28)
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        select_btn.clicked.connect(lambda: self.model_selected.emit(self.model.model_id))
        layout.addWidget(select_btn)
        
        layout.addStretch()
        
        # Cost estimate
        cost_label = QLabel(f"Free" if self.model.cost_type == "free" else "Paid")
        cost_label.setStyleSheet("color: #52525C; font-size: 10px;")
        layout.addWidget(cost_label)
        
        return footer
    
    def _get_status_text(self) -> str:
        """Get status text for badge."""
        if self.model.status == "connected":
            return "✓ Connected"
        elif self.model.status == "disconnected":
            return "✗ Disconnected"
        elif self.model.status == "error":
            return "⚠ Error"
        else:
            return "● Unknown"
    
    def _get_status_style(self) -> str:
        """Get status badge style."""
        if self.model.status == "connected":
            return """
                background-color: #14532D;
                color: #22C55E;
                font-size: 9px;
                font-weight: 600;
                padding: 1px 6px;
                border-radius: 2px;
            """
        elif self.model.status == "disconnected":
            return """
                background-color: #1C1C1F;
                color: #52525C;
                font-size: 9px;
                font-weight: 600;
                padding: 1px 6px;
                border-radius: 2px;
            """
        elif self.model.status == "error":
            return """
                background-color: #450A0A;
                color: #EF4444;
                font-size: 9px;
                font-weight: 600;
                padding: 1px 6px;
                border-radius: 2px;
            """
        else:
            return """
                background-color: #1C1C1F;
                color: #52525C;
                font-size: 9px;
                font-weight: 600;
                padding: 1px 6px;
                border-radius: 2px;
            """
    
    def toggle_advanced(self):
        """Toggle advanced view."""
        self.advanced_view = not self.advanced_view
        self.layout().takeAt(1).widget().deleteLater()
        content = self._create_content()
        self.layout().insertWidget(1, content)


class ModelsPage(QWidget):
    """Main models page with provider groups and model cards."""
    
    model_selected = Signal(str)
    
    def __init__(self, model_center: ModelCenter, parent=None):
        super().__init__(parent)
        self.model_center = model_center
        self.advanced_view = False
        self.selected_provider = None
        self.search_text = ""
        self.sort_by = "priority"
        self.setup_ui()
        self._refresh_models()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top bar
        top_bar = self._create_top_bar()
        layout.addWidget(top_bar)
        
        # Provider tabs
        provider_tabs = self._create_provider_tabs()
        layout.addWidget(provider_tabs)
        
        # Model cards container
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.cards_container)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        layout.addWidget(scroll)
        
    def _create_top_bar(self) -> QWidget:
        """Create top control bar."""
        bar = QWidget()
        bar.setStyleSheet("background-color: #111113; border-bottom: 1px solid #252528;")
        bar.setFixedHeight(50)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("Model Center")
        title.setStyleSheet("""
            color: #E2E2E6;
            font-size: 14px;
            font-weight: 600;
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Search
        search = QLineEdit()
        search.setPlaceholderText("Search models...")
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
        
        # Sort dropdown
        sort_combo = QComboBox()
        sort_combo.addItem("By Priority", "priority")
        sort_combo.addItem("By Name", "name")
        sort_combo.addItem("By Context", "context")
        sort_combo.setStyleSheet("""
            QComboBox {
                background-color: #1C1C1F;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 6px 10px;
                color: #E2E2E6;
                font-size: 11px;
                min-width: 100px;
            }
            QComboBox:hover {
                border-color: #3B82F6;
            }
        """)
        sort_combo.currentIndexChanged.connect(lambda: self._on_sort_changed(sort_combo.currentData()))
        layout.addWidget(sort_combo)
        
        # Advanced view toggle
        self.advanced_toggle = QPushButton("Normal View")
        self.advanced_toggle.setFixedHeight(28)
        self.advanced_toggle.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #8E8E98;
                border: 1px solid #252528;
                border-radius: 4px;
                font-size: 11px;
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
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.toggled.connect(self._on_advanced_toggled)
        layout.addWidget(self.advanced_toggle)
        
        return bar
    
    def _create_provider_tabs(self) -> QWidget:
        """Create provider category tabs."""
        tabs = QWidget()
        tabs.setStyleSheet("background-color: #161618;")
        
        layout = QVBoxLayout(tabs)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab container
        tab_container = QWidget()
        tab_container.setStyleSheet("background-color: #161618;")
        tab_layout = QHBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        categories = [
            ("All", None),
            ("Local", "local"),
            ("Cloud", "cloud"),
            ("Custom", "custom"),
            ("Experimental", "experimental"),
            ("Unavailable", "unavailable"),
        ]
        
        self.category_buttons = []
        for name, category in categories:
            btn = QPushButton(name)
            btn.setFixedHeight(36)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #8E8E98;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 0 16px;
                    border: none;
                    border-bottom: 2px solid transparent;
                }
                QPushButton:hover {
                    color: #E2E2E6;
                    background-color: #1C1C1F;
                }
                QPushButton:checked {
                    color: #3B82F6;
                    border-bottom: 2px solid #3B82F6;
                    background-color: transparent;
                }
            """)
            btn.setCheckable(True)
            if not self.selected_provider:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, c=category: self._on_category_selected(c, btn))
            self.category_buttons.append(btn)
            tab_layout.addWidget(btn)
        
        layout.addWidget(tab_container)
        
        return tabs
    
    def _refresh_models(self):
        """Refresh model cards based on current filters."""
        # Clear existing cards
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get models to display
        if self.selected_provider == "local":
            models = [
                m for m in self.model_center.get_enabled_models().values()
                if m.model_type == "local" or m.provider == "ollama"
            ]
        elif self.selected_provider == "cloud":
            models = [
                m for m in self.model_center.get_enabled_models().values()
                if m.model_type == "cloud"
            ]
        elif self.selected_provider == "custom":
            models = [
                m for m in self.model_center.get_enabled_models().values()
                if m.provider == "custom"
            ]
        elif self.selected_provider == "experimental":
            models = [
                m for m in self.model_center.get_enabled_models().values()
                if m.availability < 0.8 or m.success_rate < 0.9
            ]
        elif self.selected_provider == "unavailable":
            models = [
                m for m in self.model_center.get_models().values()
                if m.status in ("error", "disconnected")
            ]
        else:  # All
            models = list(self.model_center.get_enabled_models().values())
        
        # Apply search filter
        if self.search_text:
            search_lower = self.search_text.lower()
            models = [
                m for m in models
                if search_lower in m.display_name.lower() or
                   search_lower in m.provider.lower() or
                   any(search_lower in tag.lower() for tag in m.tags)
            ]
        
        # Sort models
        if self.sort_by == "name":
            models.sort(key=lambda m: m.display_name.lower())
        elif self.sort_by == "context":
            models.sort(key=lambda m: m.context_window, reverse=True)
        else:  # priority
            models.sort(key=lambda m: (m.priority, m.display_name.lower()))
        
        # Create cards
        for model in models:
            card = ModelCard(model, self.advanced_view)
            card.model_selected.connect(self.model_selected.emit)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        
        # Empty state
        if len(models) == 0:
            empty_label = QLabel("No models found")
            empty_label.setStyleSheet("""
                color: #52525C;
                font-size: 12px;
                padding: 20px;
            """)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, empty_label)
    
    def _on_search_changed(self, text: str):
        """Handle search text change."""
        self.search_text = text
        self._refresh_models()
    
    def _on_sort_changed(self, sort_key: str):
        """Handle sort key change."""
        self.sort_by = sort_key
        self._refresh_models()
    
    def _on_advanced_toggled(self, checked: bool):
        """Handle advanced view toggle."""
        self.advanced_view = checked
        self.advanced_toggle.setText("Advanced View" if checked else "Normal View")
        self._refresh_models()
    
    def _on_category_selected(self, category: str, btn):
        """Handle category button click."""
        # Update selected provider
        self.selected_provider = category
        
        # Update button states
        for b in self.category_buttons:
            b.setChecked(b.text().lower().replace(" ", "_") == category if category else b.text().lower() == "all")
        
        # Refresh models
        self._refresh_models()


# Global instance
_models_page = None


def get_models_page() -> ModelsPage:
    """Get the global models page instance."""
    global _models_page
    return _models_page


def initialize_models_page(model_center: ModelCenter) -> ModelsPage:
    """Initialize the global models page."""
    global _models_page
    _models_page = ModelsPage(model_center)
    return _models_page


def reset_models_page():
    """Reset the global models page."""
    global _models_page
    _models_page = None
