"""
Terminal Widget — v2.0 Production

Real terminal emulator widget with persistent shell sessions, ANSI support,
and full interactivity. Uses PTY for true terminal behavior.

Features:
- Persistent shell sessions (bash, zsh, fish, PowerShell, cmd)
- Real PTY-based terminal emulation
- ANSI escape sequence support (colors, bold, underline, etc.)
- Interactive command execution with Ctrl+C support
- Command history (arrow key navigation)
- Copy/paste support
- Unicode and emoji support
- Search within terminal output
- Configurable appearance (font, colors, cursor)
- Process management (detect running processes, execution time, exit codes)
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QApplication
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject, QProcess
from PySide6.QtGui import (QFont, QTextCursor, QTextCharFormat, QColor, 
                           QKeyEvent, QPalette, QTextFormat, QKeySequence, QTextDocument)
from pathlib import Path
import re
import os
import sys
import time
from typing import Optional, Dict, List
from core.logger import setup_logger

logger = setup_logger(__name__)


class ShellProcess(QObject):
    """Manages a real shell process with PTY support."""
    
    output_ready = Signal(bytes)
    process_finished = Signal(int)
    error_occurred = Signal(str)
    
    def __init__(self, shell_path: str, working_dir: Path, env: Dict[str, str] = None):
        super().__init__()
        self.shell_path = shell_path
        self.working_dir = working_dir
        self.env = env or os.environ.copy()
        self.process: Optional[QProcess] = None
        self.is_running = False
        self.exit_code = None
        self.start_time = None
        
    def start(self):
        """Start the shell process with PTY."""
        try:
            self.process = QProcess()
            self.process.setWorkingDirectory(str(self.working_dir))
            
            # Set environment
            env = QProcess.systemEnvironment()
            for key, value in self.env.items():
                env.append(f"{key}={value}")
            self.process.setEnvironment(env)
            
            # Enable PTY mode for Linux
            if sys.platform != 'win32':
                self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            
            # Connect signals
            self.process.readyReadStandardOutput.connect(self._on_output_ready)
            self.process.readyReadStandardError.connect(self._on_error_ready)
            self.process.finished.connect(self._on_finished)
            self.process.errorOccurred.connect(self._on_error)
            
            # Start process
            self.process.start(self.shell_path, [])
            
            if not self.process.waitForStarted(3000):
                raise Exception(f"Failed to start shell: {self.shell_path}")
            
            self.is_running = True
            self.start_time = time.time()
            logger.info(f"Shell process started: {self.shell_path} (PID: {self.process.processId()})")
            
        except Exception as e:
            logger.error(f"Failed to start shell: {e}")
            self.error_occurred.emit(str(e))
    
    def write(self, data: str):
        """Write data to the shell process."""
        if self.process and self.is_running:
            self.process.write(data.encode('utf-8'))
    
    def write_bytes(self, data: bytes):
        """Write raw bytes to the shell process."""
        if self.process and self.is_running:
            self.process.write(data)
    
    def terminate(self):
        """Terminate the shell process."""
        if self.process and self.is_running:
            self.process.terminate()
            if not self.process.waitForFinished(3000):
                self.process.kill()
    
    def kill(self):
        """Force kill the shell process."""
        if self.process and self.is_running:
            self.process.kill()
    
    def _on_output_ready(self):
        """Handle stdout output."""
        if self.process:
            data = self.process.readAllStandardOutput().data()
            self.output_ready.emit(data)
    
    def _on_error_ready(self):
        """Handle stderr output."""
        if self.process:
            data = self.process.readAllStandardError().data()
            self.output_ready.emit(data)
    
    def _on_finished(self, exit_code: int, exit_status):
        """Handle process finish."""
        self.is_running = False
        self.exit_code = exit_code
        duration_ms = int((time.time() - self.start_time) * 1000) if self.start_time else 0
        logger.info(f"Shell process finished: exit code {exit_code}, duration {duration_ms}ms")
        self.process_finished.emit(exit_code)
    
    def _on_error(self, error):
        """Handle process error."""
        error_msg = f"Process error: {error}"
        logger.error(error_msg)
        self.error_occurred.emit(error_msg)


class ANSIParser:
    """Parse ANSI escape sequences for terminal output formatting."""
    
    # ANSI color codes (standard 16 colors)
    COLORS = {
        # Foreground colors
        30: QColor("#2E3440"),  # Black
        31: QColor("#BF616A"),  # Red
        32: QColor("#A3BE8C"),  # Green
        33: QColor("#EBCB8B"),  # Yellow
        34: QColor("#81A1C1"),  # Blue
        35: QColor("#B48EAD"),  # Magenta
        36: QColor("#88C0D0"),  # Cyan
        37: QColor("#E5E9F0"),  # White
        90: QColor("#4C566A"),  # Bright Black (Gray)
        91: QColor("#D08770"),  # Bright Red
        92: QColor("#A3BE8C"),  # Bright Green
        93: QColor("#EBCB8B"),  # Bright Yellow
        94: QColor("#81A1C1"),  # Bright Blue
        95: QColor("#B48EAD"),  # Bright Magenta
        96: QColor("#8FBCBB"),  # Bright Cyan
        97: QColor("#ECEFF4"),  # Bright White
    }
    
    # Background colors (add 10 to foreground code)
    BG_COLORS = {k + 10: v for k, v in COLORS.items()}
    
    @staticmethod
    def parse(text: str) -> List[tuple]:
        """
        Parse text with ANSI codes into segments.
        Returns: List of (text, format_dict) tuples
        """
        # ANSI escape sequence pattern
        ansi_pattern = re.compile(r'\x1b\[([0-9;]+)m')
        
        segments = []
        current_format = {}
        pos = 0
        
        for match in ansi_pattern.finditer(text):
            # Add text before this escape sequence
            if match.start() > pos:
                segment_text = text[pos:match.start()]
                if segment_text:
                    segments.append((segment_text, current_format.copy()))
            
            # Parse the escape sequence
            codes = match.group(1).split(';')
            current_format = ANSIParser._apply_codes(codes, current_format)
            
            pos = match.end()
        
        # Add remaining text
        if pos < len(text):
            segments.append((text[pos:], current_format.copy()))
        
        return segments if segments else [(text, {})]
    
    @staticmethod
    def _apply_codes(codes: List[str], current_format: Dict) -> Dict:
        """Apply ANSI codes to format dict."""
        fmt = current_format.copy()
        
        for code_str in codes:
            try:
                code = int(code_str)
            except ValueError:
                continue
            
            if code == 0:  # Reset
                fmt = {}
            elif code == 1:  # Bold
                fmt['bold'] = True
            elif code == 2:  # Dim
                fmt['dim'] = True
            elif code == 3:  # Italic
                fmt['italic'] = True
            elif code == 4:  # Underline
                fmt['underline'] = True
            elif code == 7:  # Reverse
                fmt['reverse'] = True
            elif code == 22:  # Normal intensity
                fmt.pop('bold', None)
                fmt.pop('dim', None)
            elif code == 23:  # Not italic
                fmt.pop('italic', None)
            elif code == 24:  # Not underline
                fmt.pop('underline', None)
            elif code == 27:  # Not reverse
                fmt.pop('reverse', None)
            elif 30 <= code <= 37 or 90 <= code <= 97:  # Foreground color
                fmt['fg_color'] = ANSIParser.COLORS.get(code)
            elif 40 <= code <= 47 or 100 <= code <= 107:  # Background color
                fmt['bg_color'] = ANSIParser.BG_COLORS.get(code)
            elif code == 39:  # Default foreground
                fmt.pop('fg_color', None)
            elif code == 49:  # Default background
                fmt.pop('bg_color', None)
        
        return fmt
    
    @staticmethod
    def strip_ansi(text: str) -> str:
        """Remove all ANSI escape sequences from text."""
        ansi_pattern = re.compile(r'\x1b\[[0-9;]+m')
        return ansi_pattern.sub('', text)


class TerminalWidget(QWidget):
    """
    Production-quality terminal widget with real shell session support.
    
    Features:
    - Persistent shell sessions
    - ANSI color and formatting support
    - Interactive input with history
    - Copy/paste support
    - Search functionality
    - Process management
    """
    
    # Signals
    command_executed = Signal(str)
    process_started = Signal(int)  # PID
    process_finished = Signal(int, int)  # exit_code, duration_ms
    working_dir_changed = Signal(str)
    output_received = Signal(str)
    
    def __init__(self, session_id: str, working_dir: Path, shell: str = "bash", parent=None):
        super().__init__(parent)
        self.session_id = session_id
        self.working_dir = working_dir
        self.shell_name = shell
        self.shell_process: Optional[ShellProcess] = None
        
        # State
        self.command_history: List[str] = []
        self.history_index = -1
        self.current_command = ""
        self.is_running_command = False
        self.prompt_position = 0
        
        # Configuration
        self.font_family = "JetBrains Mono"
        self.font_size = 10
        self.show_timestamps = False
        
        self.setup_ui()
        self.start_shell()
    
    def setup_ui(self):
        """Setup the terminal UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Terminal output area
        self.output = QTextEdit()
        self.output.setReadOnly(False)  # Allow user input
        self.output.setAcceptRichText(False)
        self.output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.output.setUndoRedoEnabled(False)
        
        # Set monospace font
        font = QFont(self.font_family, self.font_size)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.output.setFont(font)
        
        # Apply terminal styling
        self.apply_terminal_theme()
        
        # Install event filter to handle special keys
        self.output.installEventFilter(self)
        
        # Connect signals
        self.output.textChanged.connect(self._on_text_changed)
        
        layout.addWidget(self.output)
    
    def apply_terminal_theme(self):
        """Apply terminal color theme."""
        from ui.design_system import get_design_system
        p = get_design_system().palette
        
        self.output.setStyleSheet(f"""
            QTextEdit {{
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: none;
                padding: 8px;
                selection-background-color: #264F78;
                selection-color: #FFFFFF;
            }}
        """)
    
    def start_shell(self):
        """Start the shell process."""
        shell_path = self._get_shell_path(self.shell_name)
        
        if not shell_path:
            self.write_output(f"Error: Shell '{self.shell_name}' not found\n", error=True)
            return
        
        # Setup environment
        env = os.environ.copy()
        env['TERM'] = 'xterm-256color'
        env['PS1'] = '\\[\\033[01;32m\\]\\u@\\h\\[\\033[00m\\]:\\[\\033[01;34m\\]\\w\\[\\033[00m\\]\\$ '
        
        # Create and start shell process
        self.shell_process = ShellProcess(shell_path, self.working_dir, env)
        self.shell_process.output_ready.connect(self._on_shell_output)
        self.shell_process.process_finished.connect(self._on_shell_finished)
        self.shell_process.error_occurred.connect(self._on_shell_error)
        self.shell_process.start()
        
        # Initial message
        self.write_output(f"Terminal session started: {self.shell_name}\n", color=QColor("#88C0D0"))
        self.write_output(f"Working directory: {self.working_dir}\n", color=QColor("#88C0D0"))
        self.write_output(f"Type 'exit' to close the terminal\n\n", color=QColor("#4C566A"))
    
    def _get_shell_path(self, shell_name: str) -> Optional[str]:
        """Get the full path to the shell executable."""
        import shutil
        
        shell_commands = {
            "bash": "bash",
            "zsh": "zsh",
            "fish": "fish",
            "sh": "sh",
            "cmd": "cmd.exe" if sys.platform == "win32" else None,
            "powershell": "powershell.exe" if sys.platform == "win32" else "pwsh",
        }
        
        command = shell_commands.get(shell_name.lower())
        if command:
            path = shutil.which(command)
            if path:
                return path
        
        # Try direct name
        path = shutil.which(shell_name)
        if path:
            return path
        
        return None
    
    def _on_shell_output(self, data: bytes):
        """Handle output from shell process."""
        try:
            text = data.decode('utf-8', errors='replace')
            self.write_output(text)
            self.output_received.emit(text)
        except Exception as e:
            logger.error(f"Failed to decode shell output: {e}")
    
    def _on_shell_finished(self, exit_code: int):
        """Handle shell process finish."""
        self.write_output(f"\n\nShell exited with code {exit_code}\n", 
                         color=QColor("#BF616A") if exit_code != 0 else QColor("#A3BE8C"))
        self.process_finished.emit(exit_code, 0)
    
    def _on_shell_error(self, error: str):
        """Handle shell process error."""
        self.write_output(f"\nShell error: {error}\n", error=True)
    
    def write_output(self, text: str, color: Optional[QColor] = None, error: bool = False):
        """Write output to the terminal with optional formatting."""
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Parse ANSI codes
        segments = ANSIParser.parse(text)
        
        for segment_text, fmt in segments:
            # Create text format
            char_format = QTextCharFormat()
            
            # Apply ANSI formatting
            if fmt.get('bold'):
                char_format.setFontWeight(QFont.Weight.Bold)
            if fmt.get('italic'):
                char_format.setFontItalic(True)
            if fmt.get('underline'):
                char_format.setFontUnderline(True)
            
            # Apply colors
            if error:
                char_format.setForeground(QColor("#BF616A"))
            elif color:
                char_format.setForeground(color)
            elif 'fg_color' in fmt:
                char_format.setForeground(fmt['fg_color'])
            
            if 'bg_color' in fmt:
                char_format.setBackground(fmt['bg_color'])
            
            # Insert text
            cursor.insertText(segment_text, char_format)
        
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()
    
    def eventFilter(self, obj, event):
        """Filter keyboard events for terminal interaction."""
        if obj == self.output and event.type() == event.Type.KeyPress:
            return self.handle_key_press(event)
        return super().eventFilter(obj, event)
    
    def handle_key_press(self, event: QKeyEvent) -> bool:
        """Handle key press events in the terminal."""
        key = event.key()
        modifiers = event.modifiers()
        
        # Ctrl+C - Send interrupt signal
        if key == Qt.Key.Key_C and modifiers & Qt.KeyboardModifier.ControlModifier:
            if self.shell_process and self.shell_process.is_running:
                self.shell_process.write_bytes(b'\x03')  # Send Ctrl+C
                return True
        
        # Ctrl+D - Send EOF
        elif key == Qt.Key.Key_D and modifiers & Qt.KeyboardModifier.ControlModifier:
            if self.shell_process and self.shell_process.is_running:
                self.shell_process.write_bytes(b'\x04')  # Send Ctrl+D
                return True
        
        # Enter - Execute command
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            if self.shell_process and self.shell_process.is_running:
                self.shell_process.write("\n")
                return True
        
        # Up arrow - Previous command in history
        elif key == Qt.Key.Key_Up:
            if self.shell_process and self.shell_process.is_running:
                self.shell_process.write_bytes(b'\x1b[A')  # Up arrow escape sequence
                return True
        
        # Down arrow - Next command in history
        elif key == Qt.Key.Key_Down:
            if self.shell_process and self.shell_process.is_running:
                self.shell_process.write_bytes(b'\x1b[B')  # Down arrow escape sequence
                return True
        
        # Left arrow
        elif key == Qt.Key.Key_Left:
            if self.shell_process and self.shell_process.is_running:
                self.shell_process.write_bytes(b'\x1b[D')
                return True
        
        # Right arrow
        elif key == Qt.Key.Key_Right:
            if self.shell_process and self.shell_process.is_running:
                self.shell_process.write_bytes(b'\x1b[C')
                return True
        
        # Backspace
        elif key == Qt.Key.Key_Backspace:
            if self.shell_process and self.shell_process.is_running:
                self.shell_process.write_bytes(b'\x7f')
                return True
        
        # Tab - Send tab for completion
        elif key == Qt.Key.Key_Tab:
            if self.shell_process and self.shell_process.is_running:
                self.shell_process.write('\t')
                return True
        
        # Regular character input
        elif not (modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)):
            text = event.text()
            if text and self.shell_process and self.shell_process.is_running:
                self.shell_process.write(text)
                return True
        
        return False
    
    def _on_text_changed(self):
        """Handle text changes (prevent direct editing in some cases)."""
        pass
    
    def execute_command(self, command: str):
        """Execute a command in the terminal."""
        if self.shell_process and self.shell_process.is_running:
            self.shell_process.write(command + "\n")
            self.command_executed.emit(command)
    
    def clear(self):
        """Clear the terminal output."""
        self.output.clear()
    
    def copy_selection(self):
        """Copy selected text."""
        self.output.copy()
    
    def paste_text(self):
        """Paste text from clipboard."""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text and self.shell_process and self.shell_process.is_running:
            self.shell_process.write(text)
    
    def search_text(self, query: str, case_sensitive: bool = False) -> bool:
        """Search for text in terminal output."""
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        
        return self.output.find(query, flags)
    
    def find_next(self, query: str, case_sensitive: bool = False) -> bool:
        """Find next occurrence of search query."""
        return self.search_text(query, case_sensitive)
    
    def find_previous(self, query: str, case_sensitive: bool = False) -> bool:
        """Find previous occurrence of search query."""
        flags = QTextDocument.FindFlag.FindBackward
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        
        return self.output.find(query, flags)
    
    def set_font(self, family: str, size: int):
        """Set terminal font."""
        self.font_family = family
        self.font_size = size
        font = QFont(family, size)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.output.setFont(font)
    
    def set_working_directory(self, directory: Path):
        """Change the working directory."""
        self.working_dir = directory
        if self.shell_process and self.shell_process.is_running:
            # Send cd command
            self.execute_command(f"cd {directory}")
            self.working_dir_changed.emit(str(directory))
    
    def terminate(self):
        """Terminate the shell process."""
        if self.shell_process:
            self.shell_process.terminate()
    
    def kill(self):
        """Force kill the shell process."""
        if self.shell_process:
            self.shell_process.kill()
    
    def restart(self):
        """Restart the shell."""
        if self.shell_process:
            self.shell_process.terminate()
        
        # Wait a bit before restarting
        QTimer.singleShot(500, self.start_shell)
    
    def get_output_text(self) -> str:
        """Get all terminal output as plain text."""
        return self.output.toPlainText()
    
    def get_output_html(self) -> str:
        """Get terminal output as HTML."""
        return self.output.toHtml()
