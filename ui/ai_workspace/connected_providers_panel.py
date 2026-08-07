"""
Connected Providers Panel.

Displays all connected providers with options to manage them.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QLineEdit, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class ConnectedProvidersPanel(QWidget):
    """
    Panel showing all connected AI providers.
    """
    
    provider_selected = Signal(str)  # provider_name
    provider_removed = Signal(str)  # provider_name
    provider_edited = Signal(str, str)  # provider_name, new_api_key
    
    def __init__(self, token_manager, parent=None):
        super().__init__(parent)
        self.token_manager = token_manager
        self._providers = {}
        
        self.setup_ui()
        self._load_providers()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header
        header = QWidget()
        header.setStyleSheet("background-color: #111113; border-bottom: 1px solid #252528;")
        header.setFixedHeight(36)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(8)
        
        title = QLabel("CONNECTED PROVIDERS")
        title.setStyleSheet("""
            color: #52525C;
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 1px;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedHeight(24)
        refresh_btn.setFixedWidth(60)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #3B82F6;
                border: 1px solid #252528;
                border-radius: 3px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #252528;
            }
        """)
        refresh_btn.clicked.connect(self._on_refresh)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header)
        
        # Providers table
        self.providers_table = QTableWidget()
        self.providers_table.setColumnCount(3)
        self.providers_table.setHorizontalHeaderLabels(["Provider", "Models", "Status"])
        self.providers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.providers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.providers_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.providers_table.setColumnWidth(2, 80)
        self.providers_table.verticalHeader().setVisible(False)
        self.providers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.providers_table.setStyleSheet("""
            QTableWidget {
                background-color: #161618;
                border: 1px solid #252528;
                border-radius: 4px;
                gridline-color: #252528;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #1C1C1F;
            }
            QHeaderView::section {
                background-color: #111113;
                color: #8E8E98;
                padding: 6px;
                border: none;
                font-size: 9px;
                font-weight: 600;
            }
        """)
        
        self.providers_table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.providers_table)
        
        # Provider details
        details_group = QWidget()
        details_group.setStyleSheet("background-color: #111113; border-radius: 4px;")
        details_layout = QVBoxLayout(details_group)
        details_layout.setContentsMargins(12, 12, 12, 12)
        details_layout.setSpacing(8)
        
        # Provider name
        name_layout = QHBoxLayout()
        name_layout.setSpacing(8)
        
        name_label = QLabel("Provider:")
        name_label.setStyleSheet("color: #8E8E98; font-size: 10px;")
        name_layout.addWidget(name_label)
        
        self.details_name = QLabel("—")
        self.details_name.setStyleSheet("color: #E2E2E6; font-size: 10px;")
        self.details_name.setFont(QFont("Segoe UI", 10, QFont.Bold))
        name_layout.addWidget(self.details_name)
        
        details_layout.addLayout(name_layout)
        
        # API Key preview
        key_layout = QHBoxLayout()
        key_layout.setSpacing(8)
        
        key_label = QLabel("API Key:")
        key_label.setStyleSheet("color: #8E8E98; font-size: 10px;")
        key_layout.addWidget(key_label)
        
        self.details_key = QLineEdit()
        self.details_key.setReadOnly(True)
        self.details_key.setEchoMode(QLineEdit.Password)
        self.details_key.setStyleSheet("""
            QLineEdit {
                background-color: #1C1C1F;
                color: #8E8E98;
                border: 1px solid #252528;
                border-radius: 3px;
                padding: 4px;
                font-size: 10px;
                font-family: Consolas, monospace;
            }
        """)
        key_layout.addWidget(self.details_key)
        
        details_layout.addLayout(key_layout)
        
        # Models preview
        models_layout = QHBoxLayout()
        models_layout.setSpacing(8)
        
        models_label = QLabel("Models:")
        models_label.setStyleSheet("color: #8E8E98; font-size: 10px;")
        models_layout.addWidget(models_label)
        
        self.details_models = QTextEdit()
        self.details_models.setReadOnly(True)
        self.details_models.setMaximumHeight(80)
        self.details_models.setStyleSheet("""
            QTextEdit {
                background-color: #1C1C1F;
                color: #8E8E98;
                border: 1px solid #252528;
                border-radius: 3px;
                padding: 4px;
                font-size: 10px;
                font-family: Consolas, monospace;
            }
        """)
        models_layout.addWidget(self.details_models)
        
        details_layout.addLayout(models_layout)
        
        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setFixedHeight(24)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                font-size: 10px;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:disabled {
                background-color: #252528;
                color: #52525C;
            }
        """)
        self.edit_btn.clicked.connect(self._on_edit_provider)
        actions_layout.addWidget(self.edit_btn)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setFixedHeight(24)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                font-size: 10px;
                padding: 0 12px;
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
        actions_layout.addWidget(self.remove_btn)
        
        actions_layout.addStretch()
        details_layout.addLayout(actions_layout)
        
        layout.addWidget(details_group)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            color: #8E8E98;
            font-size: 10px;
        """)
        layout.addWidget(self.status_label)
    
    def _load_providers(self):
        """Load providers from token manager."""
        self._providers = self.token_manager.get_all_providers()
        self._refresh_table()
    
    def _refresh_table(self):
        """Refresh providers table."""
        self.providers_table.setRowCount(len(self._providers))
        
        for row, (provider_name, token) in enumerate(self._providers.items()):
            # Provider name
            item_name = QTableWidgetItem(token.display_name or provider_name)
            item_name.setData(Qt.UserRole, provider_name)
            item_name.setFlags(item_name.flags() & ~Qt.ItemIsEditable)
            self.providers_table.setItem(row, 0, item_name)
            
            # Models count
            models_count = len(token.models) if token.models else 0
            item_models = QTableWidgetItem(f"{models_count} models")
            item_models.setFlags(item_models.flags() & ~Qt.ItemIsEditable)
            self.providers_table.setItem(row, 1, item_models)
            
            # Status
            item_status = QTableWidgetItem("✓" if token.models else "?")
            item_status.setTextAlignment(Qt.AlignCenter)
            item_status.setFlags(item_status.flags() & ~Qt.ItemIsEditable)
            self.providers_table.setItem(row, 2, item_status)
    
    def _on_selection_changed(self):
        """Handle row selection change."""
        selected = self.providers_table.selectedItems()
        
        if selected:
            row = selected[0].row()
            provider_name = self.providers_table.item(row, 0).data(Qt.UserRole)
            
            if provider_name and provider_name in self._providers:
                token = self._providers[provider_name]
                
                self.details_name.setText(token.display_name or provider_name)
                
                # Show first and last 4 chars of API key (masked)
                if token.token_hash:
                    key_preview = "••••" + "•" * 16 + "••••"
                    self.details_key.setText(key_preview)
                
                # Models preview
                if token.models:
                    models_text = "\n".join(token.models[:5])
                    if len(token.models) > 5:
                        models_text += f"\n... and {len(token.models) - 5} more"
                    self.details_models.setPlainText(models_text)
                else:
                    self.details_models.setPlainText("No models loaded")
                
                self.edit_btn.setEnabled(True)
                self.remove_btn.setEnabled(True)
            else:
                self._clear_details()
        else:
            self._clear_details()
    
    def _clear_details(self):
        """Clear provider details."""
        self.details_name.setText("—")
        self.details_key.setText("")
        self.details_models.setPlainText("")
        self.edit_btn.setEnabled(False)
        self.remove_btn.setEnabled(False)
    
    def _on_refresh(self):
        """Refresh provider list."""
        self._load_providers()
        self.status_label.setText("Providers refreshed")
    
    def _on_edit_provider(self):
        """Edit selected provider."""
        selected = self.providers_table.selectedItems()
        
        if selected:
            row = selected[0].row()
            provider_name = self.providers_table.item(row, 0).data(Qt.UserRole)
            
            if provider_name:
                QMessageBox.information(
                    self, "Edit Provider",
                    f"Edit provider: {provider_name}\n\nNote: To edit provider settings, "
                    "you need to disconnect and reconnect with updated credentials."
                )
    
    def _on_remove_provider(self):
        """Remove selected provider."""
        selected = self.providers_table.selectedItems()
        
        if selected:
            row = selected[0].row()
            provider_name = self.providers_table.item(row, 0).data(Qt.UserRole)
            
            if provider_name:
                reply = QMessageBox.question(
                    self, "Remove Provider",
                    f"Are you sure you want to disconnect '{provider_name}'?\n\n"
                    "This will remove all stored information for this provider.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    if self.token_manager.remove_token(provider_name):
                        self._load_providers()
                        self._clear_details()
                        self.status_label.setText(f"Removed provider: {provider_name}")
                    else:
                        QMessageBox.warning(
                            self, "Error",
                            f"Failed to remove provider: {provider_name}"
                        )
    
    def get_selected_provider(self) -> str:
        """Get currently selected provider name."""
        selected = self.providers_table.selectedItems()
        if selected:
            row = selected[0].row()
            return self.providers_table.item(row, 0).data(Qt.UserRole)
        return ""