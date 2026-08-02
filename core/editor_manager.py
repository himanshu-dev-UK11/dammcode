"""
Editor Manager — v2.0

Manages all file I/O for the editor:
- Multi-encoding file loading (UTF-8, UTF-16, Latin-1 fallback)
- Read-only file detection
- Session persistence (open tabs)
- Save / Save-As
- External file-change detection with user notification
- EventBus integration
"""

import json
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer
from PySide6.QtWidgets import QMessageBox, QFileDialog

from core.logger import setup_logger

logger = setup_logger(__name__)

# Maximum file size we will load without a warning (10 MB)
_MAX_FILE_SIZE = 10 * 1024 * 1024


class EditorManager(QObject):
    """
    Central file I/O manager for the editor.
    Wired to EditorTabs (UI) through the EventBus.
    """

    def __init__(self, event_bus):
        super().__init__()
        self.event_bus   = event_bus
        self.session_file = Path("config/editor_session.json")

        # path_str → True/False (True = currently open)
        self.open_files: Dict[str, bool] = {}
        self.session_data: dict = {
            "open_tabs": [],
            "active_tab": None,
            "tabs": {},
            "splits": [],
            "search": None,
        }
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(150)
        self._save_timer.timeout.connect(self.save_session)

        self.watcher = QFileSystemWatcher()
        self.watcher.fileChanged.connect(self._on_file_changed_externally)

        self._subscribe()

    # ------------------------------------------------------------------ #
    #  EventBus wiring                                                     #
    # ------------------------------------------------------------------ #

    def _subscribe(self):
        logger.info("[EditorManager._subscribe] Subscribing to events")
        self.event_bus.subscribe("file_selected",        self._handle_file_selected)
        self.event_bus.subscribe("file_open_requested",  self._handle_file_open_requested)
        self.event_bus.subscribe("request_save_current", self._handle_save_current)
        self.event_bus.subscribe("request_save_file",    self._handle_save_file)
        self.event_bus.subscribe("request_close_file",   self._handle_close_file)
        self.event_bus.subscribe("editor_saved",         self._handle_editor_saved)
        self.event_bus.subscribe("editor_session_updated", self._handle_session_updated)
        self.event_bus.subscribe("app_closing",          self.save_session)

    # ------------------------------------------------------------------ #
    #  Session                                                             #
    # ------------------------------------------------------------------ #

    def load_session(self):
        """Reopen files from the last session."""
        try:
            if self.session_file.exists():
                with open(self.session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.session_data = data or self.session_data
                self.event_bus.publish("editor_session_loaded", self.session_data)
                for path_str in data.get("open_tabs", []):
                    self.open_file(path_str)
        except Exception as exc:
            logger.error(f"Failed to load editor session: {exc}")

    def save_session(self, _event_data=None):
        """Persist open files list."""
        try:
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.session_file, "w", encoding="utf-8") as f:
                if not self.session_data.get("open_tabs"):
                    self.session_data["open_tabs"] = list(self.open_files.keys())
                json.dump(self.session_data, f, indent=4)
        except Exception as exc:
            logger.error(f"Failed to save editor session: {exc}")

    def _schedule_session_save(self):
        self._save_timer.start()

    # ------------------------------------------------------------------ #
    #  EventBus handlers                                                   #
    # ------------------------------------------------------------------ #

    def _handle_file_selected(self, data: dict):
        """Explorer double-click → open file."""
        logger.info(f"[EditorManager._handle_file_selected] Received data: {data}")
        path_str = data.get("path", "")
        if path_str:
            logger.info(f"[EditorManager._handle_file_selected] Calling open_file with: {path_str}")
            self.open_file(path_str)
        else:
            logger.warning("[EditorManager._handle_file_selected] No path in event data")

    def _handle_file_open_requested(self, data: dict):
        """File → Open File menu → open file."""
        logger.info(f"[EditorManager._handle_file_open_requested] Received data: {data}")
        path_str = data.get("path", "")
        if path_str:
            logger.info(f"[EditorManager._handle_file_open_requested] Calling open_file with: {path_str}")
            self.open_file(path_str)
        else:
            logger.warning("[EditorManager._handle_file_open_requested] No path in event data")

    def _handle_save_current(self, data: dict):
        """Ctrl+S from menu / toolbar — forward to active editor via event."""
        logger.info("[EditorManager._handle_save_current] Publishing editor_save_current_requested")
        self.event_bus.publish("editor_save_current_requested", {})

    def _handle_save_file(self, data: dict):
        """
        Save a specific editor widget.
        Payload must include {'editor': <CodeEditor>, 'path': optional str}.
        """
        logger.info(f"[EditorManager._handle_save_file] Received data: {data}")
        editor = data.get("editor")
        if not editor:
            logger.warning("[EditorManager._handle_save_file] No editor in data")
            return
        path_str = getattr(editor, "file_path", None) or data.get("path")
        if not path_str:
            logger.warning("[EditorManager._handle_save_file] No path in data or editor")
            return
        logger.info(f"[EditorManager._handle_save_file] Calling _write_file for: {path_str}")
        self._write_file(editor, Path(path_str))

    def _handle_close_file(self, data: dict):
        """Remove file from tracked list and watcher."""
        logger.info(f"[EditorManager._handle_close_file] Received data: {data}")
        path_str = data.get("path", "")
        if path_str and path_str in self.open_files:
            del self.open_files[path_str]
            if path_str in self.watcher.files():
                self.watcher.removePath(path_str)
            self.save_session()
            self.event_bus.publish("file_closed", {"path": path_str})
        else:
            logger.warning(f"[EditorManager._handle_close_file] Path not open: {path_str}")

    def _handle_editor_saved(self, data: dict):
        """Re-add watcher path after a save (was removed to avoid feedback loop)."""
        logger.info(f"[EditorManager._handle_editor_saved] Received data: {data}")
        path_str = data.get("path", "")
        if path_str and path_str not in self.watcher.files():
            self.watcher.addPath(path_str)

    def _handle_session_updated(self, data: dict):
        """Store the latest editor session state and save it shortly after."""
        if isinstance(data, dict):
            self.session_data = data
            self._schedule_session_save()

    # ------------------------------------------------------------------ #
    #  Core: open                                                          #
    # ------------------------------------------------------------------ #

    def open_file(self, path_str: str):
        """
        Read file from disk and publish 'file_opened' event.

        Handles:
        - UTF-8, UTF-16, Latin-1 encoding fallback
        - Binary / undecodable files (skipped with log)
        - Read-only files (content loaded, read-only flag set)
        - Very large files (warned, then still loaded)
        - Symlinks (resolved before opening)
        - Missing files (error logged and published)
        """
        logger.info(f"[EditorManager.open_file] Starting with path_str: {path_str}")
        try:
            path = Path(path_str).resolve()
        except Exception as exc:
            logger.error(f"Invalid path: {path_str}: {exc}")
            return

        if not path.exists():
            self._err(f"File not found: {path}")
            return

        if not path.is_file():
            logger.info(f"[EditorManager.open_file] Path is not file, ignoring: {path}")
            return

        path_str_resolved = str(path)
        if path_str_resolved in self.open_files:
            logger.info(f"[EditorManager.open_file] Path already open, reusing existing tab: {path_str_resolved}")
            self.event_bus.publish("file_opened", {
                "path": path,
                "path_str": path_str_resolved,
                "content": "",
                "encoding": None,
                "read_only": False,
                "already_open": True,
            })
            return

        # Large file warning
        try:
            size = path.stat().st_size
            if size > _MAX_FILE_SIZE:
                logger.warning(f"Large file ({size // 1024} KB): {path}")
                self.event_bus.publish("log_message", {
                    "message": f"⚠ Large file ({size // 1024} KB): {path.name}"
                })
        except OSError:
            pass

        # Detect read-only
        is_read_only = not path.stat().st_mode & 0o200 if path.exists() else False

        # Read content — try multiple encodings
        logger.info(f"[EditorManager.open_file] Reading file: {path}")
        content, encoding = self._read_with_encoding(path)
        if content is None:
            self._err(f"Cannot decode file (binary?): {path.name}")
            return

        # Track & watch
        self.open_files[path_str_resolved] = True
        if path_str_resolved not in self.watcher.files():
            self.watcher.addPath(path_str_resolved)
        self._schedule_session_save()

        # Publish so EditorTabs can open the tab
        logger.info(f"[EditorManager.open_file] Publishing file_opened event for: {path_str_resolved}")
        self.event_bus.publish("file_opened", {
            "path":        path,          # Path object
            "path_str":    path_str_resolved,
            "content":     content,
            "encoding":    encoding,
            "read_only":   is_read_only,
            "already_open": False,
        })
        self.event_bus.publish("log_message", {"message": f"Opened: {path.name}"})

    @staticmethod
    def _read_with_encoding(path: Path):
        """Try UTF-8, then UTF-16, then Latin-1. Returns (content, encoding) or (None, None)."""
        logger.debug(f"[EditorManager._read_with_encoding] Reading: {path}")
        for enc in ("utf-8", "utf-16", "latin-1"):
            try:
                content = path.read_text(encoding=enc)
                logger.debug(f"[EditorManager._read_with_encoding] Success with encoding: {enc}")
                return content, enc
            except UnicodeDecodeError:
                logger.debug(f"[EditorManager._read_with_encoding] Decode error with {enc}, trying next")
                continue
            except OSError as exc:
                logger.error(f"OS error reading {path}: {exc}")
                return None, None
        logger.warning(f"[EditorManager._read_with_encoding] All encodings failed for {path}")
        return None, None

    # ------------------------------------------------------------------ #
    #  Core: write                                                         #
    # ------------------------------------------------------------------ #

    def _write_file(self, editor, path: Path):
        """Write editor content to disk using safe file operations."""
        logger.info(f"[EditorManager._write_file] Starting for path: {path}")
        from core.safe_file_ops import safe_write_text

        try:
            # Remove from watcher to avoid feedback loop
            path_str = str(path)
            if path_str in self.watcher.files():
                self.watcher.removePath(path_str)

            content = editor.toPlainText()
            logger.debug(f"[EditorManager._write_file] Writing {len(content)} chars")
            success = safe_write_text(path, content, encoding="utf-8")

            if success:
                editor.document().setModified(False)
                self.event_bus.publish("editor_saved", {"path": path_str})
                self.event_bus.publish("log_message", {"message": f"Saved: {path.name}"})
                logger.info(f"File saved: {path}")
            else:
                self._err(f"Failed to save file: {path.name}")

        except Exception as exc:
            self._err(f"Error saving {path.name}: {exc}")

    # ------------------------------------------------------------------ #
    #  External file change detection                                      #
    # ------------------------------------------------------------------ #

    def _on_file_changed_externally(self, path_str: str):
        """QFileSystemWatcher fires when a watched file changes on disk."""
        logger.info(f"[EditorManager._on_file_changed_externally] File changed: {path_str}")
        path = Path(path_str)

        # Re-add to watcher if it was removed (some editors replace the file)
        if path.exists() and path_str not in self.watcher.files():
            self.watcher.addPath(path_str)

        # Publish so EditorTabs can show a "reload?" prompt
        self.event_bus.publish("file_changed_externally", {
            "path":   path_str,
            "exists": path.exists(),
        })

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _err(self, msg: str):
        logger.error(msg)
        self.event_bus.publish("log_message",    {"message": f"⚠ {msg}"})
        self.event_bus.publish("editor_error",   {"error": msg})
