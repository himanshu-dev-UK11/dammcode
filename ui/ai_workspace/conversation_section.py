"""AI Conversation Section - v1.5.2

Full interactive conversation with:
- Message sending
- Provider/model selection
- Stop/Clear/New/Delete/Rename/Export/Import
- Placeholder chat logic until AI is configured
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QFrame,
    QComboBox, QDialog, QDialogButtonBox, QFileDialog, QMessageBox,
    QTextEdit
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor


class MessageBubble(QWidget):
    """A single message bubble in the conversation."""
    def __init__(self, text: str, is_user: bool):
        super().__init__()
        self.setup_ui(text, is_user)
        
    def setup_ui(self, text: str, is_user: bool):
        from ui.design_system import get_design_system
        p = get_design_system().palette

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        role = "You" if is_user else "AI"
        role_color = p.accent if is_user else p.success

        role_lbl = QLabel(role)
        role_lbl.setStyleSheet(f"""
            color: {role_color};
            font-size: 9px;
            font-weight: 600;
            background-color: transparent;
            letter-spacing: 0.5px;
            padding: 0 0 2px 0;
        """)
        layout.addWidget(role_lbl)

        text_lbl = QLabel(text)
        text_lbl.setObjectName("text_lbl")
        text_lbl.setWordWrap(True)
        text_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_lbl.setStyleSheet(f"""
            color: {p.text if is_user else p.text_secondary};
            font-size: 11px;
            background-color: {'transparent' if is_user else p.surface};
            padding: 8px;
            border-radius: 4px;
        """)
        layout.addWidget(text_lbl)
        
        if not is_user:
            # Add copy button for AI messages
            btn_row = QHBoxLayout()
            btn_row.setContentsMargins(0, 0, 0, 0)
            btn_row.addStretch()
            
            copy_btn = QPushButton("Copy")
            copy_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {p.text_tertiary};
                    border: 1px solid {p.border_subtle};
                    border-radius: 2px;
                    padding: 2px 6px;
                    font-size: 9px;
                }}
                QPushButton:hover {{
                    background-color: {p.surface};
                    color: {p.text};
                }}
            """)
            copy_btn.clicked.connect(lambda: self.copy_text(text))
            btn_row.addWidget(copy_btn)
            layout.addLayout(btn_row)
            
    def copy_text(self, text: str):
        """Copy text to clipboard."""
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(text)
        
        # Show temporary feedback
        from ui.design_system import get_design_system
        p = get_design_system().palette
        self._copy_feedback = QLabel("Copied!")
        self._copy_feedback.setStyleSheet(f"""
            color: {p.success};
            font-size: 9px;
            background-color: transparent;
            padding: 2px 4px;
        """)
        self.layout().addWidget(self._copy_feedback)
        QTimer.singleShot(1000, self._copy_feedback.deleteLater)


class ConversationSection(QWidget):
    """AI conversation history panel with full interactivity."""
    message_sent = Signal(str)
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._is_streaming = False
        self._current_ai_message = None
        self.setup_ui()
        
        # Subscribe to events
        self.event_bus.subscribe("ai_chat_streaming_started", self._on_streaming_started)
        self.event_bus.subscribe("ai_chat_streaming_complete", self._on_streaming_complete)
        self.event_bus.subscribe("ai_chat_chunk", self._on_chunk)
        self.event_bus.subscribe("ai_chat_error", self._on_error)
        
    def setup_ui(self):
        from ui.design_system import get_design_system
        p = get_design_system().palette

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Provider and Model selectors
        controls = QWidget()
        controls.setStyleSheet(f"background-color: transparent; border-bottom: 1px solid {p.border_subtle};")
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(6, 4, 6, 4)
        controls_layout.setSpacing(4)
        
        # Provider selector row
        provider_row = QHBoxLayout()
        provider_row.setSpacing(4)
        
        provider_lbl = QLabel("Provider:")
        provider_lbl.setStyleSheet(f"color: {p.text_tertiary}; font-size: 10px; background-color: transparent;")
        provider_row.addWidget(provider_lbl)
        
        self._provider_combo = QComboBox()
        self._provider_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {p.surface};
                border: 1px solid {p.border_subtle};
                border-radius: 2px;
                padding: 2px 6px;
                color: {p.text};
                font-size: 10px;
            }}
            QComboBox:hover {{ border-color: {p.accent}; }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
        """)
        self._provider_combo.addItems(["Automatic", "Ollama", "Gemini", "Groq", "Together AI", 
                                       "DeepInfra", "OpenAI Compatible", "Custom Provider"])
        self._provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_row.addWidget(self._provider_combo)
        
        controls_layout.addLayout(provider_row)
        
        # Model selector row
        model_row = QHBoxLayout()
        model_row.setSpacing(4)
        
        model_lbl = QLabel("Model:")
        model_lbl.setStyleSheet(f"color: {p.text_tertiary}; font-size: 10px; background-color: transparent;")
        model_row.addWidget(model_lbl)
        
        self._model_combo = QComboBox()
        self._model_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {p.surface};
                border: 1px solid {p.border_subtle};
                border-radius: 2px;
                padding: 2px 6px;
                color: {p.text};
                font-size: 10px;
            }}
            QComboBox:hover {{ border-color: {p.accent}; }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
        """)
        self._model_combo.addItem("No models available")
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        model_row.addWidget(self._model_combo)
        
        controls_layout.addLayout(model_row)
        
        # Status row
        status_row = QHBoxLayout()
        status_row.setSpacing(4)
        
        self._status_lbl = QLabel("● Provider not configured")
        self._status_lbl.setStyleSheet(f"color: {p.error}; font-size: 9px; background-color: transparent;")
        status_row.addWidget(self._status_lbl)
        status_row.addStretch()
        
        self._response_time = QLabel("")
        self._response_time.setStyleSheet(f"color: {p.text_tertiary}; font-size: 9px; background-color: transparent;")
        status_row.addWidget(self._response_time)
        
        controls_layout.addLayout(status_row)
        
        layout.addWidget(controls)

        # Message area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("background-color: transparent; border: none;")

        self._msg_widget = QWidget()
        self._msg_widget.setStyleSheet("background-color: transparent;")
        self._msg_layout = QVBoxLayout(self._msg_widget)
        self._msg_layout.setContentsMargins(0, 4, 0, 4)
        self._msg_layout.setSpacing(8)
        self._msg_layout.setAlignment(Qt.AlignTop)
        self._msg_layout.addStretch()

        self._scroll.setWidget(self._msg_widget)
        layout.addWidget(self._scroll)

        # Action buttons
        actions = QWidget()
        actions.setStyleSheet(f"background-color: transparent; border-top: 1px solid {p.border_subtle};")
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(6, 4, 6, 4)
        actions_layout.setSpacing(4)
        
        self._btn_new = QPushButton("New Chat")
        self._btn_new.setToolTip("Start a new chat session")
        self._btn_new.clicked.connect(self._on_new_chat)
        
        self._btn_clear = QPushButton("Clear")
        self._btn_clear.setToolTip("Clear current conversation")
        self._btn_clear.clicked.connect(self._on_clear_chat)
        
        self._btn_rename = QPushButton("Rename")
        self._btn_rename.setToolTip("Rename current chat")
        self._btn_rename.clicked.connect(self._on_rename_chat)
        
        self._btn_delete = QPushButton("Delete")
        self._btn_delete.setToolTip("Delete current chat")
        self._btn_delete.clicked.connect(self._on_delete_chat)
        
        self._btn_export = QPushButton("Export")
        self._btn_export.setToolTip("Export conversation to file")
        self._btn_export.clicked.connect(self._on_export_chat)
        
        self._btn_import = QPushButton("Import")
        self._btn_import.setToolTip("Import conversation from file")
        self._btn_import.clicked.connect(self._on_import_chat)
        
        # Style all buttons
        button_style = f"""
            QPushButton {{
                background-color: {p.surface};
                color: {p.text};
                border: 1px solid {p.border_subtle};
                border-radius: 2px;
                padding: 3px 8px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {p.surface_hover};
                border-color: {p.accent};
            }}
            QPushButton:pressed {{
                background-color: {p.bg};
            }}
        """
        
        for btn in [self._btn_new, self._btn_clear, self._btn_rename, 
                    self._btn_delete, self._btn_export, self._btn_import]:
            btn.setStyleSheet(button_style)
            actions_layout.addWidget(btn)
        
        actions_layout.addStretch()
        layout.addWidget(actions)

        # Input row
        input_frame = QWidget()
        input_frame.setStyleSheet(f"background-color: transparent; border-top: 1px solid {p.border_subtle};")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(6, 4, 6, 4)
        input_layout.setSpacing(4)

        self._input = QTextEdit()
        self._input.setPlaceholderText("Ask AI… (Shift+Enter for new line, Enter to send)")
        self._input.setMaximumHeight(80)
        self._input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {p.surface};
                border: 1px solid {p.border_subtle};
                border-radius: 2px;
                padding: 4px 8px;
                color: {p.text};
                font-size: 11px;
            }}
            QTextEdit:focus {{ border-color: {p.accent}; }}
        """)
        
        # Custom key handling for multi-line support
        self._input.installEventFilter(self)

        self._btn_send = QPushButton("Send")
        self._btn_send.setFixedHeight(28)
        self._btn_send.setToolTip("Send  [Enter]")
        self._btn_send.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.accent};
                color: {p.primary_text};
                border: none;
                border-radius: 2px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{ background-color: {p.accent_hover}; }}
            QPushButton:pressed {{ background-color: {p.accent_active}; }}
            QPushButton:disabled {{
                background-color: {p.border_subtle};
                color: {p.text_tertiary};
            }}
        """)
        self._btn_send.clicked.connect(self._send)
        
        self._btn_stop = QPushButton("Stop")
        self._btn_stop.setFixedHeight(28)
        self._btn_stop.setToolTip("Stop current response")
        self._btn_stop.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.error};
                color: {p.primary_text};
                border: none;
                border-radius: 2px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{ background-color: {p.error}; }}
            QPushButton:pressed {{ background-color: {p.error_bg}; }}
        """)
        self._btn_stop.clicked.connect(self._on_stop)
        self._btn_stop.hide()  # Hidden by default

        input_layout.addWidget(self._input)
        input_layout.addWidget(self._btn_send)
        input_layout.addWidget(self._btn_stop)
        layout.addWidget(input_frame)
        
        # Load available providers and models
        self._refresh_providers()
        
    def eventFilter(self, obj, event):
        """Handle key events for multi-line input."""
        if obj == self._input and event.type() == event.Type.KeyPress:
            # Shift+Enter or Ctrl+Enter = new line (default behavior)
            # Enter alone = send message
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                if event.modifiers() == Qt.ShiftModifier or event.modifiers() == Qt.ControlModifier:
                    # Allow default behavior (new line)
                    return False
                else:
                    # Send message
                    self._send()
                    return True
        return super().eventFilter(obj, event)
        
    def _refresh_providers(self):
        """Refresh available providers from Model Center."""
        # This will be enhanced when Model Center is properly wired
        self._update_status("Provider not configured", "error")
        
    def _on_provider_changed(self, provider: str):
        """Handle provider selection change."""
        # Refresh models for selected provider
        self._model_combo.clear()
        
        # Placeholder - will be replaced with real provider query
        if provider == "Automatic":
            self._model_combo.addItem("Best available model")
        elif provider == "Ollama":
            self._model_combo.addItems(["llama3:8b", "codellama:7b", "mistral:7b"])
        elif provider == "Gemini":
            self._model_combo.addItems(["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"])
        else:
            self._model_combo.addItem("Configure provider in Settings")
        
        self._update_status(f"Provider: {provider}", "info")
        
    def _on_model_changed(self, model: str):
        """Handle model selection change."""
        if model and model != "No models available":
            self._update_status(f"Model: {model}", "success")
            self.event_bus.publish("ai_chat_switch_model", {"model_id": model})
        
    def _update_status(self, message: str, status_type: str = "info"):
        """Update status indicator."""
        from ui.design_system import get_design_system
        p = get_design_system().palette
        colors = {
            "error": p.error,
            "warning": p.warning,
            "success": p.success,
            "info": p.accent,
        }
        color = colors.get(status_type, p.text_tertiary)
        self._status_lbl.setText(f"● {message}")
        self._status_lbl.setStyleSheet(f"color: {color}; font-size: 9px; background-color: transparent;")
        
    def _send(self):
        """Send message."""
        text = self._input.toPlainText().strip()
        if not text:
            return
        
        self._add_message(text, is_user=True)
        self._input.clear()
        
        # Show stop button, hide send
        self._btn_send.hide()
        self._btn_stop.show()
        self._is_streaming = True
        
        self.message_sent.emit(text)
        self.event_bus.publish("user_message", {"message": text})
        
        # Placeholder response until real AI is configured
        QTimer.singleShot(500, lambda: self._show_placeholder_response())
        
    def _on_stop(self):
        """Stop current AI response."""
        self._is_streaming = False
        self._btn_stop.hide()
        self._btn_send.show()
        self.event_bus.publish("ai_chat_cancel", {})
        self._update_status("Stopped", "warning")
        
    def _on_new_chat(self):
        """Create a new chat session."""
        reply = QMessageBox.question(
            self, "New Chat",
            "Start a new chat? Current conversation will be saved.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.event_bus.publish("ai_chat_new_session", {"title": f"Chat {self._get_chat_count() + 1}"})
            self.clear_conversation()
            self._update_status("New chat started", "success")
            
    def _on_clear_chat(self):
        """Clear current conversation."""
        reply = QMessageBox.question(
            self, "Clear Chat",
            "Clear all messages in this conversation? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.clear_conversation()
            self._update_status("Conversation cleared", "info")
            
    def _on_rename_chat(self):
        """Rename current chat."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Rename Chat")
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Enter new chat name:")
        layout.addWidget(label)
        
        input_field = QLineEdit()
        input_field.setText(f"Chat {self._get_chat_count()}")
        layout.addWidget(input_field)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            new_name = input_field.text().strip()
            if new_name:
                self.event_bus.publish("ai_chat_rename_session", {
                    "session_id": self._get_current_session_id(),
                    "title": new_name
                })
                self._update_status(f"Renamed to: {new_name}", "success")
                
    def _on_delete_chat(self):
        """Delete current chat."""
        reply = QMessageBox.question(
            self, "Delete Chat",
            "Delete this chat permanently? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.event_bus.publish("ai_chat_delete_session", {
                "session_id": self._get_current_session_id()
            })
            self.clear_conversation()
            self._update_status("Chat deleted", "warning")
            
    def _on_export_chat(self):
        """Export conversation to file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Chat", "", "JSON Files (*.json);;Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            try:
                # Request export from AI chat engine
                import json
                from pathlib import Path
                
                # Collect messages
                messages = []
                for i in range(self._msg_layout.count() - 1):  # Skip stretch
                    item = self._msg_layout.itemAt(i)
                    if item and item.widget():
                        # Extract message text (simplified)
                        messages.append({"content": "Message content"})
                
                export_data = {
                    "title": f"Chat {self._get_chat_count()}",
                    "messages": messages,
                    "exported_at": str(QTimer().isActive()),  # Placeholder timestamp
                }
                
                Path(filepath).write_text(json.dumps(export_data, indent=2))
                self._update_status(f"Exported to {Path(filepath).name}", "success")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export chat:\n{str(e)}")
                
    def _on_import_chat(self):
        """Import conversation from file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Chat", "", "JSON Files (*.json);;Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            try:
                from pathlib import Path
                import json
                
                content = Path(filepath).read_text()
                data = json.loads(content)
                
                # Show success message
                QMessageBox.information(
                    self, "Import Successful",
                    f"Chat imported: {data.get('title', 'Unnamed')}"
                )
                
                self.event_bus.publish("ai_chat_import", {"content": content})
                self._update_status("Chat imported", "success")
                
            except Exception as e:
                QMessageBox.critical(self, "Import Failed", f"Failed to import chat:\n{str(e)}")
        
    def _get_chat_count(self) -> int:
        """Get current chat count (placeholder)."""
        return 1
        
    def _get_current_session_id(self) -> str:
        """Get current session ID (placeholder)."""
        return "default-session"
        
    def _on_streaming_started(self, data: dict):
        """Handle streaming started event."""
        self._is_streaming = True
        self._btn_send.hide()
        self._btn_stop.show()
        self._update_status("Generating response...", "info")
        
        # Create placeholder message for AI response
        self._current_ai_message = MessageBubble("", is_user=False)
        count = self._msg_layout.count()
        self._msg_layout.insertWidget(count - 1, self._current_ai_message)
        
    def _on_streaming_complete(self, data: dict):
        """Handle streaming complete event."""
        self._is_streaming = False
        self._btn_stop.hide()
        self._btn_send.show()
        self._current_ai_message = None
        
        # Update response time if available
        content_len = data.get("content_length", 0)
        self._response_time.setText(f"{content_len} chars")
        self._update_status("Response complete", "success")
        
    def _on_chunk(self, data: dict):
        """Handle streaming chunk event."""
        chunk = data.get("chunk", "")
        if self._current_ai_message:
            # Append chunk to current message
            current_text = self._current_ai_message.findChild(QLabel, "text_lbl")
            if current_text:
                current_text.setText(current_text.text() + chunk)
        self._scroll_to_bottom()
        
    def _on_error(self, data: dict):
        """Handle AI error event."""
        error = data.get("error", "Unknown error")
        self._is_streaming = False
        self._btn_stop.hide()
        self._btn_send.show()
        self._update_status(f"Error: {error}", "error")
        
        # Show error message
        if not self._current_ai_message:
            self._add_message(f"**Error:** {error}", is_user=False)
        else:
            self._current_ai_message = None
        
    def _send(self):
        """Send message."""
        text = self._input.toPlainText().strip()
        if not text:
            return
        
        self._add_message(text, is_user=True)
        self._input.clear()
        
        # Show stop button, hide send
        self._btn_send.hide()
        self._btn_stop.show()
        self._is_streaming = True
        
        self.message_sent.emit(text)
        self.event_bus.publish("user_message", {"message": text})
        
        # Placeholder response until real AI is configured
        QTimer.singleShot(500, lambda: self._show_placeholder_response())
        
    def _on_send(self):
        """Handle send button click."""
        self._send()
        
    def _add_message(self, text: str, is_user: bool):
        """Add message to conversation."""
        msg_widget = MessageBubble(text, is_user)
        count = self._msg_layout.count()
        self._msg_layout.insertWidget(count - 1, msg_widget)
        self._scroll_to_bottom()
        
    def _scroll_to_bottom(self):
        """Scroll to bottom of conversation."""
        QTimer.singleShot(50, lambda: self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        ))
        
    def add_ai_response(self, text: str):
        """Add AI response to conversation."""
        self._add_message(text, is_user=False)
        self._btn_stop.hide()
        self._btn_send.show()
        self._is_streaming = False
        
    def show_placeholder_response(self, message: str = None):
        """Show placeholder response when AI is not connected."""
        if message is None:
            provider = self._provider_combo.currentText()
            model = self._model_combo.currentText()
            
            if provider == "Automatic":
                message = ("**No AI provider is currently connected.**\n\n"
                          "To use AI features:\n"
                          "1. Configure a provider in Settings > AI Providers\n"
                          "2. Or select a specific provider from the dropdown above\n"
                          "3. Ensure the provider service is running (e.g., Ollama)\n\n"
                          "This is a placeholder response demonstrating the chat interface.")
            else:
                message = (f"**Provider '{provider}' is not configured.**\n\n"
                          f"Selected model: {model}\n\n"
                          f"To configure:\n"
                          f"1. Go to Settings > AI Providers\n"
                          f"2. Enable and configure {provider}\n"
                          f"3. Test the connection\n\n"
                          f"This placeholder confirms the chat pipeline is working.")
        
        self._add_message(message, is_user=False)
        self._btn_stop.hide()
        self._btn_send.show()
        self._is_streaming = False
        
    def _show_placeholder_response(self):
        """Internal method to show placeholder."""
        self.show_placeholder_response()
        
    def clear_conversation(self):
        """Clear all messages from conversation."""
        # Remove all message widgets, keep only stretch
        while self._msg_layout.count() > 1:
            item = self._msg_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._current_ai_message = None
        self._is_streaming = False
        self._btn_stop.hide()
        self._btn_send.show()
