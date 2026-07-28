"""
LSP Manager - Manages multiple language server clients.
"""

from typing import Dict, Optional
from pathlib import Path
from PySide6.QtCore import QObject, Signal
from core.logger import setup_logger
from core.lsp.lsp_client import LSPClient
from core.lsp.language_server_config import LanguageServerConfig, get_standard_language_servers


logger = setup_logger(__name__)


class LSPManager(QObject):
    """Manages multiple language server clients for different languages."""
    
    # Signals
    diagnostics_received = Signal(str, list)  # (file_path, diagnostics)
    server_started = Signal(str)              # (language_id)
    server_stopped = Signal(str)              # (language_id)
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self.clients: Dict[str, LSPClient] = {}
        self.configs = get_standard_language_servers()
        self.workspace_path: Optional[Path] = None
        
    def set_workspace(self, workspace_path: Path):
        """Set the workspace path and start appropriate servers."""
        self.workspace_path = workspace_path
        logger.info(f"Workspace set to: {workspace_path}")
        
    def get_client_for_language(self, language_id: str) -> Optional[LSPClient]:
        """Get or create a client for the specified language."""
        if language_id in self.clients:
            return self.clients[language_id]
            
        if language_id not in self.configs:
            logger.warning(f"No language server configured for: {language_id}")
            return None
            
        config = self.configs[language_id]
        client = LSPClient(config)
        
        # Connect signals
        client.message_received.connect(lambda msg: self._on_server_message(language_id, msg))
        client.error_occurred.connect(lambda err: self._on_server_error(language_id, err))
        client.connection_closed.connect(lambda: self._on_server_closed(language_id))
        
        # Start client with workspace URI
        if self.workspace_path:
            root_uri = f"file:///{str(self.workspace_path.as_posix())}"
            if client.start(root_uri):
                self.clients[language_id] = client
                self.server_started.emit(language_id)
                return client
                
        return None
        
    def get_client_for_file(self, file_path: Path) -> Optional[LSPClient]:
        """Get a client appropriate for the given file based on extension."""
        for lang_id, config in self.configs.items():
            if file_path.suffix in config.supported_extensions:
                return self.get_client_for_language(lang_id)
        return None
        
    def open_document(self, file_path: Path, language_id: str, content: str):
        """Notify language server of an open document."""
        client = self.get_client_for_language(language_id)
        if client:
            uri = f"file:///{str(file_path.as_posix())}"
            client.send_notification("textDocument/didOpen", {
                "textDocument": {
                    "uri": uri,
                    "languageId": language_id,
                    "version": 1,
                    "text": content,
                }
            })
            
    def change_document(self, file_path: Path, content: str, version: int):
        """Notify language server of document changes."""
        client = self.get_client_for_file(file_path)
        if client:
            uri = f"file:///{str(file_path.as_posix())}"
            client.send_notification("textDocument/didChange", {
                "textDocument": {
                    "uri": uri,
                    "version": version,
                },
                "contentChanges": [{"text": content}],
            })
            
    def close_document(self, file_path: Path):
        """Notify language server that a document has closed."""
        client = self.get_client_for_file(file_path)
        if client:
            uri = f"file:///{str(file_path.as_posix())}"
            client.send_notification("textDocument/didClose", {
                "textDocument": {"uri": uri},
            })
            
    def save_document(self, file_path: Path, content: str):
        """Notify language server that a document was saved."""
        client = self.get_client_for_file(file_path)
        if client:
            uri = f"file:///{str(file_path.as_posix())}"
            client.send_notification("textDocument/didSave", {
                "textDocument": {"uri": uri},
                "text": content,
            })
            
    def request_completion(self, file_path: Path, line: int, character: int, callback):
        """Request completions from language server."""
        client = self.get_client_for_file(file_path)
        if client:
            uri = f"file:///{str(file_path.as_posix())}"
            client.send_request("textDocument/completion", {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": character},
            }, callback)
            
    def request_hover(self, file_path: Path, line: int, character: int, callback):
        """Request hover information from language server."""
        client = self.get_client_for_file(file_path)
        if client:
            uri = f"file:///{str(file_path.as_posix())}"
            client.send_request("textDocument/hover", {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": character},
            }, callback)
            
    def request_definition(self, file_path: Path, line: int, character: int, callback):
        """Request definition from language server."""
        client = self.get_client_for_file(file_path)
        if client:
            uri = f"file:///{str(file_path.as_posix())}"
            client.send_request("textDocument/definition", {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": character},
            }, callback)
            
    def request_references(self, file_path: Path, line: int, character: int, callback):
        """Request references from language server."""
        client = self.get_client_for_file(file_path)
        if client:
            uri = f"file:///{str(file_path.as_posix())}"
            client.send_request("textDocument/references", {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": character},
                "context": {"includeDeclaration": True},
            }, callback)
            
    def request_formatting(self, file_path: Path, callback):
        """Request document formatting from language server."""
        client = self.get_client_for_file(file_path)
        if client:
            uri = f"file:///{str(file_path.as_posix())}"
            client.send_request("textDocument/formatting", {
                "textDocument": {"uri": uri},
                "options": {
                    "tabSize": 4,
                    "insertSpaces": True,
                },
            }, callback)
            
    def _on_server_message(self, language_id: str, message: dict):
        """Handle messages from the language server."""
        method = message.get("method")
        if method == "textDocument/publishDiagnostics":
            uri = message["params"]["uri"]
            diagnostics = message["params"]["diagnostics"]
            # Convert file URI to path
            if uri.startswith("file:///"):
                file_path = uri[8:]
                self.diagnostics_received.emit(file_path, diagnostics)
                
    def _on_server_error(self, language_id: str, error: str):
        logger.error(f"Language server ({language_id}) error: {error}")
        
    def _on_server_closed(self, language_id: str):
        logger.info(f"Language server ({language_id}) closed")
        if language_id in self.clients:
            del self.clients[language_id]
            self.server_stopped.emit(language_id)
            
    def shutdown_all(self):
        """Shutdown all language servers."""
        for language_id, client in list(self.clients.items()):
            client.stop()
        self.clients.clear()
