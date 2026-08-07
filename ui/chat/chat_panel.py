"""
Chat Panel — v1.5

Real AI chat with streaming, model switching, and session management.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLineEdit, QPushButton,
    QLabel, QComboBox, QMenu, QMessageBox, QDialog, QPlainTextEdit,
    QTextEdit
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from core.logger import setup_logger

from ai.chat.ai_chat_engine import AIChatEngine, ChatMessage


logger = setup_logger(__name__)


class ChatBubble(QWidget):
    """A single chat message bubble."""
    
    def __init__(self, message: ChatMessage, is_user: bool):
        super().__init__()
        self.message = message
        self.is_user = is_user
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        # Role label
        role_label = QLabel("You" if self.is_user else "AI")
        role_label.setStyleSheet(f"""
            color: {'#3B82F6' if self.is_user else '#22C55E'};
            font-size: 10px;
            font-weight: 600;
            background-color: transparent;
        """)
        layout.addWidget(role_label)
        
        # Content
        self.content_label = QLabel(self.message.content)
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextBrowserInteraction
        )
        self.content_label.setStyleSheet(f"""
            color: {'#E2E2E6' if self.is_user else '#D1D5DB'};
            font-size: 11px;
            background-color: {'#313244' if self.is_user else '#1E1E2E'};
            padding: 10px;
            border-radius: 6px;
            border: 1px solid {'#3B82F6' if self.is_user else '#22C55E'};
        """)
        layout.addWidget(self.content_label)
        
        # Metadata
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(8)
        
        # Timestamp
        time_label = QLabel(self.message.timestamp.strftime("%H:%M:%S"))
        time_label.setStyleSheet("""
            color: #6B7280;
            font-size: 9px;
            background-color: transparent;
        """)
        meta_layout.addWidget(time_label)
        
        # Model name (only for AI)
        if not self.is_user and self.message.model_id:
            model_label = QLabel(self.message.model_id)
            model_label.setStyleSheet("""
                color: #9CA3AF;
                font-size: 9px;
                background-color: #374151;
                padding: 1px 4px;
                border-radius: 3px;
            """)
            meta_layout.addWidget(model_label)
        
        meta_layout.addStretch()
        layout.addLayout(meta_layout)


class ChatSessionSidebar(QWidget):
    """Sidebar for chat session management."""
    
    session_selected = Signal(str)
    session_deleted = Signal(str)
    session_renamed = Signal(str, str)
    session_pinned = Signal(str, bool)
    
    def __init__(self, chat_engine: AIChatEngine):
        super().__init__()
        self.chat_engine = chat_engine
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setStyleSheet("background-color: #111113;")
        header.setFixedHeight(36)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 0, 8, 0)
        header_layout.setSpacing(6)
        
        new_btn = QPushButton("+ New Chat")
        new_btn.setFixedHeight(24)
        new_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        new_btn.clicked.connect(lambda: self.session_selected.emit(""))
        header_layout.addWidget(new_btn)
        
        layout.addWidget(header)
        
        # Session list
        self.session_list = QWidget()
        self.session_list_layout = QVBoxLayout(self.session_list)
        self.session_list_layout.setContentsMargins(0, 0, 0, 0)
        self.session_list_layout.setSpacing(0)
        self.session_list_layout.addStretch()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.session_list)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #161618;
            }
        """)
        
        layout.addWidget(scroll, stretch=1)
        
        self._refresh_sessions()
    
    def _refresh_sessions(self):
        """Refresh session list."""
        while self.session_list_layout.count() > 1:
            item = self.session_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        sessions = self.chat_engine.get_all_sessions()
        
        if not sessions:
            empty_label = QLabel("No chat sessions yet")
            empty_label.setStyleSheet("color: #52525C; font-size: 10px; padding: 10px;")
            self.session_list_layout.insertWidget(0, empty_label)
            return
        
        for session in sessions:
            session_widget = self._create_session_widget(session)
            self.session_list_layout.insertWidget(
                self.session_list_layout.count() - 1,
                session_widget
            )
    
    def _create_session_widget(self, session):
        """Create a session widget."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #111113;
                border-bottom: 1px solid #252528;
            }
            QWidget:hover {
                background-color: #222226;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)
        
        # Title row
        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        
        title_label = QLabel(session.title)
        title_label.setStyleSheet("color: #E2E2E6; font-size: 11px; font-weight: 500;")
        
        # Pin button
        pin_btn = QPushButton("📌" if session.is_pinned else " ")
        pin_btn.setFixedWidth(20)
        pin_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3B82F6;
                border-radius: 2px;
            }
        """)
        pin_btn.clicked.connect(lambda: self.session_pinned.emit(session.session_id, not session.is_pinned))
        
        title_row.addWidget(title_label)
        title_row.addWidget(pin_btn)
        title_row.addStretch()
        
        # Model and time
        info_row = QHBoxLayout()
        info_row.setSpacing(8)
        
        model_label = QLabel(session.model_id)
        model_label.setStyleSheet("color: #8E8E98; font-size: 9px;")
        
        time_label = QLabel(session.messages[-1].timestamp.strftime("%H:%M") if session.messages else "—")
        time_label.setStyleSheet("color: #52525C; font-size: 9px;")
        
        info_row.addWidget(model_label)
        info_row.addStretch()
        info_row.addWidget(time_label)
        
        layout.addLayout(title_row)
        layout.addLayout(info_row)
        
        # Click to select
        widget.mousePressEvent = lambda e, s=session: self.session_selected.emit(s.session_id)
        
        return widget


class ChatPanel(QWidget):
    """
    Real AI chat panel with streaming support.
    
    Features:
    - Streaming responses (token by token)
    - Model switching
    - Session management
    - Markdown rendering
    - Code blocks
    - Message history
    """
    
    def __init__(self, event_bus, chat_engine: AIChatEngine):
        super().__init__()
        self.event_bus = event_bus
        self.chat_engine = chat_engine
        self._current_model = None
        self._typing_label = None
        self.setup_ui()
        self._subscribe_to_events()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top bar
        top_bar = self._create_top_bar()
        layout.addWidget(top_bar)
        
        # Main area (chat bubbles + sidebar)
        main_split = QWidget()
        main_layout = QHBoxLayout(main_split)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = ChatSessionSidebar(self.chat_engine)
        self.sidebar.session_selected.connect(self._on_session_selected)
        main_layout.addWidget(self.sidebar)
        
        # Chat area
        chat_area = QWidget()
        chat_area.setStyleSheet("background-color: #111113;")
        chat_layout = QVBoxLayout(chat_area)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Chat history
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(8)
        self.scroll_area.setWidget(self.chat_container)
        
        chat_layout.addWidget(self.scroll_area)
        
        # Input area
        input_row = QWidget()
        input_row.setStyleSheet("background-color: #111113; border-top: 1px solid #252528;")
        input_row.setFixedHeight(48)
        
        input_layout = QHBoxLayout(input_row)
        input_layout.setContentsMargins(12, 8, 12, 8)
        input_layout.setSpacing(8)
        
        # Model selector
        self.model_combo = QComboBox()
        self.model_combo.setFixedWidth(180)
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #1C1C1F;
                border: 1px solid #252528;
                border-radius: 3px;
                padding: 6px 10px;
                color: #E2E2E6;
                font-size: 11px;
            }
            QComboBox:hover {
                border-color: #3B82F6;
            }
        """)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        self._refresh_models()
        input_layout.addWidget(self.model_combo)
        
        # Message input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message... (Shift+Enter for new line)")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #1C1C1F;
                border: 1px solid #252528;
                border-radius: 3px;
                padding: 8px 12px;
                color: #E2E2E6;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
            }
        """)
        self.input_field.returnPressed.connect(self._on_send)
        self.input_field.setFixedHeight(32)
        input_layout.addWidget(self.input_field)
        
        # Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedWidth(80)
        self.send_btn.setFixedHeight(32)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:disabled {
                background-color: #374151;
            }
        """)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)
        
        # Cancel button
        self.cancel_btn = QPushButton("Stop")
        self.cancel_btn.setFixedWidth(60)
        self.cancel_btn.setFixedHeight(32)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
            QPushButton:disabled {
                background-color: #374151;
            }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.setEnabled(False)
        input_layout.addWidget(self.cancel_btn)
        
        chat_layout.addWidget(input_row)
        
        main_layout.addWidget(chat_area, stretch=1)
        
        layout.addWidget(main_split)
        
        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+Enter"), self.input_field).activated.connect(self._on_send)
        QShortcut(QKeySequence("Shift+Enter"), self.input_field).activated.connect(self._on_new_line)
    
    def _create_top_bar(self) -> QWidget:
        """Create top control bar."""
        bar = QWidget()
        bar.setStyleSheet("background-color: #161618; border-bottom: 1px solid #252528;")
        bar.setFixedHeight(40)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)
        
        # Status
        status_layout = QHBoxLayout()
        status_layout.setSpacing(6)
        
        self.provider_label = QLabel("Provider: —")
        self.provider_label.setStyleSheet("color: #52525C; font-size: 10px;")
        status_layout.addWidget(self.provider_label)
        
        self.model_label = QLabel("Model: —")
        self.model_label.setStyleSheet("color: #52525C; font-size: 10px;")
        status_layout.addWidget(self.model_label)
        
        self.streaming_label = QLabel("Offline")
        self.streaming_label.setStyleSheet("""
            color: #EF4444;
            font-size: 10px;
            font-weight: 600;
        """)
        status_layout.addWidget(self.streaming_label)
        
        layout.addLayout(status_layout)
        layout.addStretch()
        
        return bar
    
    def _subscribe_to_events(self):
        """Subscribe to EventBus events."""
        self.event_bus.subscribe("ai_chat_message_added", self._on_message_added)
        self.event_bus.subscribe("ai_chat_streaming_started", self._on_streaming_started)
        self.event_bus.subscribe("ai_chat_streaming_complete", self._on_streaming_complete)
        self.event_bus.subscribe("ai_chat_error", self._on_error)
        self.event_bus.subscribe("ai_chat_model_switched", self._on_model_switched)
    
    def _refresh_models(self):
        """Refresh model list."""
        models = self.chat_engine.get_available_models()
        
        self.model_combo.clear()
        for model_id, display_name in models.items():
            self.model_combo.addItem(f"{display_name} ({model_id})", model_id)
        
        # Set current model
        current_model = self.chat_engine.get_current_model()
        if current_model:
            idx = self.model_combo.findData(current_model)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
    
    def _add_bubble(self, message: ChatMessage, is_user: bool):
        """Add a message bubble to the chat."""
        bubble = ChatBubble(message, is_user)
        self.chat_layout.addWidget(bubble)
        self._scroll_to_bottom()
    
    def _scroll_to_bottom(self):
        """Scroll to bottom of chat."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _on_send(self):
        """Handle send button click."""
        text = self.input_field.text().strip()
        if not text:
            return
        
        # Get current model
        current_model = self.model_combo.currentData()
        
        # Disable input during streaming
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.streaming_label.setText("Streaming...")
        self.streaming_label.setStyleSheet("""
            color: #F59E0B;
            font-size: 10px;
            font-weight: 600;
        """)
        
        # Add user message
        user_msg = ChatMessage(
            role="user",
            content=text,
            model_id=current_model,
        )
        self._add_bubble(user_msg, is_user=True)
        self.input_field.clear()
        
        # Send to AI
        self.chat_engine.send_message(
            text,
            model_id=current_model,
            on_chunk=self._on_chunk,
            on_complete=self._on_stream_complete,
        )
    
    def _on_new_line(self):
        """Add new line without sending."""
        self.input_field.setText(self.input_field.text() + "\n")
        self.input_field.setFocus()
    
    def _on_cancel(self):
        """Cancel streaming."""
        self.chat_engine._on_cancel_stream({})
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.streaming_label.setText("Offline")
        self.streaming_label.setStyleSheet("color: #EF4444; font-size: 10px; font-weight: 600;")
    
    def _on_chunk(self, chunk: str):
        """Handle streaming chunk."""
        if self._typing_label:
            self._typing_label.setText(self._typing_label.text() + chunk)
    
    def _on_stream_complete(self, full_response: str):
        """Handle stream completion."""
        # Create assistant message
        current_model = self.model_combo.currentData()
        assistant_msg = ChatMessage(
            role="assistant",
            content=full_response,
            model_id=current_model,
        )
        self._add_bubble(assistant_msg, is_user=False)
        
        # Re-enable input
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.streaming_label.setText("Ready")
        self.streaming_label.setStyleSheet("color: #22C55E; font-size: 10px; font-weight: 600;")
    
    def _on_streaming_started(self, data: dict):
        """Handle streaming start event."""
        # Add typing indicator
        current_model = data.get("model_id", "AI")
        self._typing_label = QLabel(f"{current_model} is typing...")
        self._typing_label.setStyleSheet("color: #52525C; font-size: 10px; font-style: italic;")
        self.chat_layout.addWidget(self._typing_label)
        self._scroll_to_bottom()
    
    def _on_streaming_complete(self, data: dict):
        """Handle streaming complete event."""
        if self._typing_label:
            self._typing_label.deleteLater()
            self._typing_label = None
    
    def _on_error(self, data: dict):
        """Handle error event."""
        error_msg = data.get("error", "Unknown error")
        
        # Add error bubble
        error_message = ChatMessage(
            role="assistant",
            content=f"**Error:** {error_msg}",
            model_id=self.model_combo.currentData(),
        )
        self._add_bubble(error_message, is_user=False)
        
        # Re-enable input
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.streaming_label.setText("Error")
        self.streaming_label.setStyleSheet("color: #EF4444; font-size: 10px; font-weight: 600;")
    
    def _on_message_added(self, data: dict):
        """Handle message added event."""
        role = data.get("role", "user")
        content = data.get("content", "")
        session_id = data.get("session_id")
        
        if session_id != self.chat_engine._current_session_id:
            return
        
        is_user = role == "user"
        msg = ChatMessage(role=role, content=content)
        self._add_bubble(msg, is_user=is_user)
    
    def _on_model_changed(self, index: int):
        """Handle model selection change."""
        model_id = self.model_combo.currentData()
        if model_id:
            self.chat_engine._on_switch_model({
                "model_id": model_id,
                "session_id": self.chat_engine._current_session_id,
            })
    
    def _on_model_switched(self, data: dict):
        """Handle model switched event."""
        model_id = data.get("model_id")
        if model_id:
            self._refresh_models()
    
    def _on_session_selected(self, session_id: str):
        """Handle session selection."""
        if not session_id:
            # Create new session
            self.chat_engine.create_session(
                model_id=self.model_combo.currentData(),
                title=f"Chat {len(self.chat_engine.get_all_sessions()) + 1}"
            )
        else:
            # Switch to session
            self.chat_engine.switch_session(session_id)
        
        self.sidebar._refresh_sessions()
    
    def set_provider_info(self, provider: str, model: str):
        """Update provider info display."""
        self.provider_label.setText(f"Provider: {provider}")
        self.model_label.setText(f"Model: {model}")
    
    def update_status(self, status: str, is_streaming: bool = False):
        """Update streaming status."""
        if is_streaming:
            self.streaming_label.setText("Streaming...")
            self.streaming_label.setStyleSheet("color: #F59E0B; font-size: 10px; font-weight: 600;")
        else:
            self.streaming_label.setText(status)
            if status == "Ready":
                self.streaming_label.setStyleSheet("color: #22C55E; font-size: 10px; font-weight: 600;")
            elif status == "Error":
                self.streaming_label.setStyleSheet("color: #EF4444; font-size: 10px; font-weight: 600;")
            else:
                self.streaming_label.setStyleSheet("color: #52525C; font-size: 10px; font-weight: 600;")
