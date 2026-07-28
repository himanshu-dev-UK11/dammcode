"""
LSP Client - Handles JSON-RPC communication with language servers.
"""

import json
import subprocess
import threading
import queue
from typing import Dict, Any, Optional, Callable
from PySide6.QtCore import QObject, Signal
from core.logger import setup_logger

logger = setup_logger(__name__)


class LSPClient(QObject):
    """Client for communicating with a language server via JSON-RPC."""
    
    # Signals
    message_received = Signal(object)  # Emits (message)
    error_occurred = Signal(str)       # Emits error message
    connection_closed = Signal()       # Emits when connection closes
    
    def __init__(self, config: "LanguageServerConfig"):
        super().__init__()
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self.pending_requests: Dict[int, Callable] = {}
        self.message_queue = queue.Queue()
        self.running = False
        self.read_thread: Optional[threading.Thread] = None
        
    def start(self, root_uri: str, workspace_folders: Optional[list] = None) -> bool:
        """Start the language server process."""
        try:
            cmd = self.config.command + self.config.args
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
            )
            
            self.running = True
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            
            # Send initialize request
            initialize_params = {
                "processId": None,
                "rootUri": root_uri,
                "workspaceFolders": workspace_folders or [{"uri": root_uri, "name": "workspace"}],
                "capabilities": {
                    "textDocument": {
                        "completion": {"dynamicRegistration": False},
                        "hover": {"dynamicRegistration": False},
                        "definition": {"dynamicRegistration": False},
                        "references": {"dynamicRegistration": False},
                        "publishDiagnostics": {},
                    },
                    "workspace": {
                        "workspaceFolders": True,
                    },
                },
            }
            
            self.send_request("initialize", initialize_params, self._on_initialize_response)
            return True
            
        except Exception as e:
            logger.error(f"Failed to start language server: {e}")
            self.error_occurred.emit(str(e))
            return False
            
    def stop(self):
        """Stop the language server process."""
        self.running = False
        if self.process:
            try:
                self.send_notification("shutdown")
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error stopping language server: {e}")
                self.process.kill()
            finally:
                self.process = None
                self.connection_closed.emit()
                
    def _read_loop(self):
        """Read messages from the server."""
        buffer = b""
        try:
            while self.running and self.process and self.process.stdout:
                chunk = self.process.stdout.read(4096)
                if not chunk:
                    break
                buffer += chunk
                
                # Parse messages
                while b"\r\n\r\n" in buffer:
                    header_part, buffer = buffer.split(b"\r\n\r\n", 1)
                    headers = {}
                    for line in header_part.split(b"\r\n"):
                        if b":" in line:
                            key, value = line.split(b":", 1)
                            headers[key.decode().strip()] = value.decode().strip()
                            
                    content_length = int(headers.get("Content-Length", 0))
                    if len(buffer) >= content_length:
                        content = buffer[:content_length].decode("utf-8")
                        buffer = buffer[content_length:]
                        try:
                            message = json.loads(content)
                            self._handle_message(message)
                        except Exception as e:
                            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Read loop error: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.running = False
            self.connection_closed.emit()
            
    def _handle_message(self, message: Dict[str, Any]):
        """Handle an incoming message from the server."""
        if "id" in message:
            # Response
            if "error" in message:
                logger.error(f"Request error: {message['error']}")
                if message["id"] in self.pending_requests:
                    # TODO: Handle error in callback
                    del self.pending_requests[message["id"]]
            elif "result" in message and message["id"] in self.pending_requests:
                callback = self.pending_requests.pop(message["id"])
                callback(message["result"])
        else:
            # Notification
            self.message_received.emit(message)
            
    def send_request(self, method: str, params: Any, callback: Callable) -> int:
        """Send a request to the server."""
        self.request_id += 1
        req_id = self.request_id
        self.pending_requests[req_id] = callback
        
        message = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }
        
        self._send_message(message)
        return req_id
        
    def send_notification(self, method: str, params: Any = None):
        """Send a notification to the server."""
        message = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params is not None:
            message["params"] = params
            
        self._send_message(message)
        
    def _send_message(self, message: Dict[str, Any]):
        """Send a message to the server's stdin."""
        try:
            content = json.dumps(message, ensure_ascii=False)
            content_bytes = content.encode("utf-8")
            header = f"Content-Length: {len(content_bytes)}\r\n\r\n"
            header_bytes = header.encode("utf-8")
            
            if self.process and self.process.stdin:
                self.process.stdin.write(header_bytes)
                self.process.stdin.write(content_bytes)
                self.process.stdin.flush()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.error_occurred.emit(str(e))
            
    def _on_initialize_response(self, result):
        """Handle initialize response."""
        logger.info("Language server initialized")
        self.send_notification("initialized")
