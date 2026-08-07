"""
Qwen3 Coding Assistant Panel.

Provides dedicated UI controls for Qwen3 8B local coding agent.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QComboBox, QFrame,
    QScrollArea, QLineEdit, QGroupBox
)
from PySide6.QtCore import Qt, Signal, QThread, Slot
from PySide6.QtGui import QFont
from typing import Optional
from core.logger import setup_logger

logger = setup_logger(__name__)


class QwenWorkerThread(QThread):
    """Background thread for Qwen API calls."""
    
    response_ready = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, qwen_model, operation: str, **kwargs):
        super().__init__()
        self.qwen_model = qwen_model
        self.operation = operation
        self.kwargs = kwargs
        
    def run(self):
        """Execute the Qwen operation in background."""
        try:
            if self.operation == "generate_code":
                result = self.qwen_model.generate_code(**self.kwargs)
            elif self.operation == "explain_code":
                result = self.qwen_model.explain_code(**self.kwargs)
            elif self.operation == "debug_code":
                result = self.qwen_model.debug_code(**self.kwargs)
            elif self.operation == "refactor_code":
                result = self.qwen_model.refactor_code(**self.kwargs)
            elif self.operation == "complete_code":
                result = self.qwen_model.complete_code(**self.kwargs)
            else:
                result = self.qwen_model.generate_response(**self.kwargs)
            
            self.response_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class QwenCodingPanel(QWidget):
    """
    UI panel for Qwen3 8B coding assistant.
    
    Features:
    - Code generation
    - Code explanation
    - Debugging assistance
    - Code refactoring
    - Code completion
    - Server connection management
    """
    
    code_generated = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._qwen_model = None
        self._provider = None
        self._current_thread = None
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Connection status section
        self._create_connection_section(main_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #252528;")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # Operation tabs
        self._create_operation_section(main_layout)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setStyleSheet("background-color: #252528;")
        separator2.setFixedHeight(1)
        main_layout.addWidget(separator2)
        
        # Input area
        self._create_input_section(main_layout)
        
        # Action buttons
        self._create_action_buttons(main_layout)
        
        # Output area
        self._create_output_section(main_layout)
        
    def _create_connection_section(self, parent_layout):
        """Create connection status and controls."""
        conn_group = QGroupBox("Qwen3 8B Server")
        conn_group.setStyleSheet("""
            QGroupBox {
                color: #ACACB8;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid #252528;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        conn_layout = QVBoxLayout(conn_group)
        
        # Status row
        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        
        status_label = QLabel("Status:")
        status_label.setStyleSheet("color: #6B6B78; font-size: 10px;")
        status_row.addWidget(status_label)
        
        self._status_indicator = QLabel("●")
        self._status_indicator.setStyleSheet("color: #DC2626; font-size: 14px;")
        status_row.addWidget(self._status_indicator)
        
        self._status_text = QLabel("Disconnected")
        self._status_text.setStyleSheet("color: #DC2626; font-size: 10px;")
        status_row.addWidget(self._status_text)
        
        status_row.addStretch()
        
        self._connect_btn = QPushButton("Connect")
        self._connect_btn.setFixedSize(80, 24)
        self._connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #ACACB8;
                border: 1px solid #252528;
                border-radius: 3px;
                font-size: 10px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #252528;
                border-color: #3C3C3F;
            }
            QPushButton:pressed {
                background-color: #161618;
            }
        """)
        self._connect_btn.clicked.connect(self._toggle_connection)
        status_row.addWidget(self._connect_btn)
        
        conn_layout.addLayout(status_row)
        
        # Endpoint row
        endpoint_row = QHBoxLayout()
        endpoint_row.setSpacing(8)
        
        endpoint_label = QLabel("Endpoint:")
        endpoint_label.setStyleSheet("color: #6B6B78; font-size: 10px;")
        endpoint_label.setFixedWidth(60)
        endpoint_row.addWidget(endpoint_label)
        
        self._endpoint_input = QLineEdit("http://localhost:11434")
        self._endpoint_input.setStyleSheet("""
            QLineEdit {
                background-color: #1C1C1F;
                color: #ACACB8;
                border: 1px solid #252528;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
            }
            QLineEdit:focus {
                border-color: #3C3C3F;
            }
        """)
        endpoint_row.addWidget(self._endpoint_input)
        
        conn_layout.addLayout(endpoint_row)
        
        parent_layout.addWidget(conn_group)
        
    def _create_operation_section(self, parent_layout):
        """Create operation mode selector."""
        op_layout = QHBoxLayout()
        op_layout.setSpacing(8)
        
        op_label = QLabel("Operation:")
        op_label.setStyleSheet("color: #6B6B78; font-size: 10px; font-weight: 600;")
        op_layout.addWidget(op_label)
        
        self._operation_combo = QComboBox()
        self._operation_combo.addItems([
            "Generate Code",
            "Explain Code",
            "Debug Code",
            "Refactor Code",
            "Complete Code",
            "Custom Prompt"
        ])
        self._operation_combo.setStyleSheet("""
            QComboBox {
                background-color: #1C1C1F;
                color: #ACACB8;
                border: 1px solid #252528;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
            }
            QComboBox:hover {
                border-color: #3C3C3F;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #ACACB8;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #1C1C1F;
                color: #ACACB8;
                selection-background-color: #252528;
                border: 1px solid #252528;
            }
        """)
        self._operation_combo.currentIndexChanged.connect(self._on_operation_changed)
        op_layout.addWidget(self._operation_combo, stretch=1)
        
        # Language selector
        lang_label = QLabel("Language:")
        lang_label.setStyleSheet("color: #6B6B78; font-size: 10px; font-weight: 600;")
        op_layout.addWidget(lang_label)
        
        self._language_combo = QComboBox()
        self._language_combo.addItems([
            "Python", "JavaScript", "TypeScript", "Java",
            "C++", "C#", "Go", "Rust", "Ruby", "PHP"
        ])
        self._language_combo.setStyleSheet(self._operation_combo.styleSheet())
        op_layout.addWidget(self._language_combo)
        
        parent_layout.addLayout(op_layout)
        
    def _create_input_section(self, parent_layout):
        """Create input text area."""
        input_label = QLabel("Input:")
        input_label.setStyleSheet("color: #6B6B78; font-size: 10px; font-weight: 600;")
        parent_layout.addWidget(input_label)
        
        self._input_text = QTextEdit()
        self._input_text.setPlaceholderText("Enter your code or prompt here...")
        self._input_text.setStyleSheet("""
            QTextEdit {
                background-color: #1C1C1F;
                color: #ACACB8;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border-color: #3C3C3F;
            }
        """)
        self._input_text.setMinimumHeight(150)
        parent_layout.addWidget(self._input_text)
        
        # Additional input (for error messages in debug mode, etc.)
        self._additional_label = QLabel("Additional Info:")
        self._additional_label.setStyleSheet("color: #6B6B78; font-size: 10px; font-weight: 600;")
        self._additional_label.setVisible(False)
        parent_layout.addWidget(self._additional_label)
        
        self._additional_text = QTextEdit()
        self._additional_text.setPlaceholderText("Enter error message, refactoring goal, etc...")
        self._additional_text.setStyleSheet(self._input_text.styleSheet())
        self._additional_text.setMaximumHeight(80)
        self._additional_text.setVisible(False)
        parent_layout.addWidget(self._additional_text)
        
    def _create_action_buttons(self, parent_layout):
        """Create action buttons."""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self._execute_btn = QPushButton("Execute")
        self._execute_btn.setFixedHeight(30)
        self._execute_btn.setEnabled(False)
        self._execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton:pressed {
                background-color: #1E40AF;
            }
            QPushButton:disabled {
                background-color: #252528;
                color: #52525C;
            }
        """)
        self._execute_btn.clicked.connect(self._execute_operation)
        btn_layout.addWidget(self._execute_btn)
        
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedHeight(30)
        self._clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #ACACB8;
                border: 1px solid #252528;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #252528;
                border-color: #3C3C3F;
            }
            QPushButton:pressed {
                background-color: #161618;
            }
        """)
        self._clear_btn.clicked.connect(self._clear_all)
        btn_layout.addWidget(self._clear_btn)
        
        btn_layout.addStretch()
        
        parent_layout.addLayout(btn_layout)
        
    def _create_output_section(self, parent_layout):
        """Create output display area."""
        output_label = QLabel("Output:")
        output_label.setStyleSheet("color: #6B6B78; font-size: 10px; font-weight: 600;")
        parent_layout.addWidget(output_label)
        
        self._output_text = QTextEdit()
        self._output_text.setReadOnly(True)
        self._output_text.setPlaceholderText("Results will appear here...")
        self._output_text.setStyleSheet("""
            QTextEdit {
                background-color: #111113;
                color: #ACACB8;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                line-height: 1.5;
            }
        """)
        self._output_text.setMinimumHeight(200)
        parent_layout.addWidget(self._output_text)
        
        # Copy to editor button
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.setFixedHeight(28)
        copy_btn.setStyleSheet(self._clear_btn.styleSheet())
        copy_btn.clicked.connect(self._copy_output)
        parent_layout.addWidget(copy_btn)
        
    def set_qwen_model(self, qwen_model):
        """Set the Qwen model instance."""
        self._qwen_model = qwen_model
        
    def set_provider(self, provider):
        """Set the Qwen provider instance."""
        self._provider = provider
        self._update_connection_status()
        
    @Slot()
    def _toggle_connection(self):
        """Toggle connection to Qwen server."""
        if not self._qwen_model:
            from ai.models.qwen import QwenModel
            endpoint = self._endpoint_input.text().strip()
            self._qwen_model = QwenModel(endpoint=endpoint)
        
        provider = self._qwen_model._get_provider()
        
        if provider and provider.is_connected():
            provider.disconnect()
            self._update_connection_status()
        else:
            if provider:
                success = provider.connect()
                self._update_connection_status()
                if success:
                    logger.info("Connected to Qwen3 successfully")
                else:
                    logger.error("Failed to connect to Qwen3")
            
    def _update_connection_status(self):
        """Update connection status UI."""
        if self._qwen_model:
            provider = self._qwen_model._get_provider()
            if provider and provider.is_connected():
                self._status_indicator.setStyleSheet("color: #22C55E; font-size: 14px;")
                self._status_text.setText("Connected")
                self._status_text.setStyleSheet("color: #22C55E; font-size: 10px;")
                self._connect_btn.setText("Disconnect")
                self._execute_btn.setEnabled(True)
                self._endpoint_input.setEnabled(False)
                return
        
        self._status_indicator.setStyleSheet("color: #DC2626; font-size: 14px;")
        self._status_text.setText("Disconnected")
        self._status_text.setStyleSheet("color: #DC2626; font-size: 10px;")
        self._connect_btn.setText("Connect")
        self._execute_btn.setEnabled(False)
        self._endpoint_input.setEnabled(True)
        
    @Slot()
    def _on_operation_changed(self):
        """Handle operation mode change."""
        operation = self._operation_combo.currentText()
        
        # Show/hide additional input based on operation
        if operation == "Debug Code":
            self._additional_label.setText("Error Message:")
            self._additional_label.setVisible(True)
            self._additional_text.setPlaceholderText("Enter error message or stack trace...")
            self._additional_text.setVisible(True)
        elif operation == "Refactor Code":
            self._additional_label.setText("Refactoring Goal:")
            self._additional_label.setVisible(True)
            self._additional_text.setPlaceholderText("e.g., 'improve performance', 'add error handling'...")
            self._additional_text.setVisible(True)
        else:
            self._additional_label.setVisible(False)
            self._additional_text.setVisible(False)
            
        # Update input placeholder
        if operation == "Generate Code":
            self._input_text.setPlaceholderText("Describe what code to generate...")
        elif operation == "Explain Code":
            self._input_text.setPlaceholderText("Paste code to explain...")
        elif operation == "Debug Code":
            self._input_text.setPlaceholderText("Paste code with error...")
        elif operation == "Refactor Code":
            self._input_text.setPlaceholderText("Paste code to refactor...")
        elif operation == "Complete Code":
            self._input_text.setPlaceholderText("Paste partial code to complete...")
        else:
            self._input_text.setPlaceholderText("Enter your prompt...")
            
    @Slot()
    def _execute_operation(self):
        """Execute the selected operation."""
        if not self._qwen_model:
            return
        
        operation = self._operation_combo.currentText()
        language = self._language_combo.currentText().lower()
        input_text = self._input_text.toPlainText().strip()
        additional = self._additional_text.toPlainText().strip()
        
        if not input_text:
            self._output_text.setPlainText("Error: Input is required")
            return
        
        # Disable button during execution
        self._execute_btn.setEnabled(False)
        self._execute_btn.setText("Processing...")
        self._output_text.setPlainText("Processing request...")
        
        # Prepare kwargs based on operation
        kwargs = {}
        
        if operation == "Generate Code":
            kwargs = {"task": input_text, "language": language}
            op_name = "generate_code"
        elif operation == "Explain Code":
            kwargs = {"code": input_text, "language": language}
            op_name = "explain_code"
        elif operation == "Debug Code":
            kwargs = {"code": input_text, "error": additional or "Unknown error", "language": language}
            op_name = "debug_code"
        elif operation == "Refactor Code":
            kwargs = {"code": input_text, "goal": additional or "improve code quality", "language": language}
            op_name = "refactor_code"
        elif operation == "Complete Code":
            kwargs = {"prefix": input_text, "language": language}
            op_name = "complete_code"
        else:  # Custom Prompt
            kwargs = {"prompt": input_text}
            op_name = "generate_response"
        
        # Execute in background thread
        self._current_thread = QwenWorkerThread(self._qwen_model, op_name, **kwargs)
        self._current_thread.response_ready.connect(self._on_response_ready)
        self._current_thread.error_occurred.connect(self._on_error)
        self._current_thread.finished.connect(self._on_thread_finished)
        self._current_thread.start()
        
    @Slot(str)
    def _on_response_ready(self, response: str):
        """Handle successful response."""
        self._output_text.setPlainText(response)
        self.code_generated.emit(response)
        
    @Slot(str)
    def _on_error(self, error: str):
        """Handle error."""
        self._output_text.setPlainText(f"Error: {error}")
        logger.error(f"Qwen operation failed: {error}")
        
    @Slot()
    def _on_thread_finished(self):
        """Handle thread completion."""
        self._execute_btn.setEnabled(True)
        self._execute_btn.setText("Execute")
        
    @Slot()
    def _clear_all(self):
        """Clear all input and output."""
        self._input_text.clear()
        self._additional_text.clear()
        self._output_text.clear()
        
    @Slot()
    def _copy_output(self):
        """Copy output to clipboard."""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self._output_text.toPlainText())
        logger.info("Output copied to clipboard")
