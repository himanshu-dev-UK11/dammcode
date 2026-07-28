"""
Workspace Manager — v3.0 (QFileSystemModel First Architecture)
Complete rewrite to prioritize explorer visibility before scanning!
Instrumented with detailed step-by-step logging for debugging.
"""
import json
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QObject, QThread, Signal

from core.logger import setup_logger
from ai.tools.project_scanner import ProjectScanner

logger = setup_logger(__name__)


class _MetadataScanWorker(QObject):
    """Runs ProjectScanner.scan() in a background QThread to build metadata only."""
    scan_complete = Signal(object)  # emits ProjectContext
    scan_failed = Signal(str)       # emits error message

    def __init__(self, path: Path):
        super().__init__()
        self._path = path
        logger.info(f"[_MetadataScanWorker.__init__] Initialized for path: {path}")

    def run(self):
        logger.info(f"[_MetadataScanWorker.run] Starting metadata scan for path: {self._path}")
        try:
            logger.debug(f"[_MetadataScanWorker.run] Creating ProjectScanner instance...")
            scanner = ProjectScanner(self._path)
            logger.debug(f"[_MetadataScanWorker.run] ProjectScanner created, calling scan()...")
            context = scanner.scan()
            logger.info(f"[_MetadataScanWorker.run] Metadata scan complete, emitting scan_complete...")
            self.scan_complete.emit(context)
        except Exception as exc:
            logger.exception(f"[_MetadataScanWorker.run] Metadata scan failed with exception: {exc}")
            self.scan_failed.emit(str(exc))
        logger.info(f"[_MetadataScanWorker.run] Exiting run() method")


class Workspace:
    """Represents a single open workspace/project."""
    def __init__(self, path: Path, context=None, pinned: bool = False):
        self.path = path
        self.context = context
        self.pinned = pinned
        self.is_active = False
        self.scanning = False
        logger.debug(f"[Workspace.__init__] Created workspace for path: {path}")


class WorkspaceManager(QObject):
    """
    Manages workspaces and projects using QFileSystemModel first for instant UI!
    """

    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus

        self.recent_file = Path("config/recent_projects.json")
        self.pinned_file = Path("config/pinned_projects.json")
        self.session_file = Path("config/workspace_session.json")

        self.workspaces: List[Workspace] = []
        self.active_workspace: Optional[Workspace] = None
        self.recent_projects: List[str] = []
        self.pinned_projects: List[str] = []

        # Keep references so GC doesn't destroy running threads
        self._scan_threads: List[QThread] = []

        logger.info("[WorkspaceManager.__init__] Loading settings...")
        self._load_settings()
        logger.info("[WorkspaceManager.__init__] Subscribing to events...")
        self._subscribe_events()
        logger.info("[WorkspaceManager.__init__] Initialization complete!")

    def _subscribe_events(self):
        logger.debug("[WorkspaceManager._subscribe_events] Subscribing to request_open_workspace...")
        self.event_bus.subscribe("request_open_workspace", self._handle_open_request)
        self.event_bus.subscribe("request_close_workspace", self._handle_close_request)
        self.event_bus.subscribe("request_refresh_workspace", self._handle_refresh_request)
        self.event_bus.subscribe("request_reopen_last_workspace", self._handle_reopen_last)
        self.event_bus.subscribe("request_pin_project", self._handle_pin_project)
        self.event_bus.subscribe("request_unpin_project", self._handle_unpin_project)
        self.event_bus.subscribe("app_closing", self.save_session)
        logger.debug("[WorkspaceManager._subscribe_events] Event subscriptions complete!")

    def _load_settings(self):
        for attr, path in [("recent_projects", self.recent_file),
                           ("pinned_projects", self.pinned_file)]:
            try:
                if path.exists():
                    logger.debug(f"[WorkspaceManager._load_settings] Loading {attr} from {path}...")
                    with open(path, "r", encoding="utf-8") as f:
                        setattr(self, attr, json.load(f))
                    logger.debug(f"[WorkspaceManager._load_settings] Loaded {len(getattr(self, attr))} entries for {attr}")
                else:
                    logger.debug(f"[WorkspaceManager._load_settings] Settings file {path} does not exist, using defaults")
            except Exception as exc:
                logger.exception(f"[WorkspaceManager._load_settings] Failed to load {attr}: {exc}")
                setattr(self, attr, [])

    def _save_settings(self):
        for attr, path in [("recent_projects", self.recent_file),
                           ("pinned_projects", self.pinned_file)]:
            try:
                logger.debug(f"[WorkspaceManager._save_settings] Saving {attr} to {path}...")
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(getattr(self, attr), f, indent=4)
                logger.debug(f"[WorkspaceManager._save_settings] Saved {len(getattr(self, attr))} entries for {attr}")
            except Exception as exc:
                logger.exception(f"[WorkspaceManager._save_settings] Failed to save {attr}: {exc}")

    def save_session(self, _event_data=None):
        logger.info("[WorkspaceManager.save_session] Saving session...")
        try:
            data = {
                "last_workspace": str(self.active_workspace.path) if self.active_workspace else None,
                "open_workspaces": [str(ws.path) for ws in self.workspaces],
            }
            logger.debug(f"[WorkspaceManager.save_session] Session data: {data}")
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            logger.info("[WorkspaceManager.save_session] Session saved successfully!")
        except Exception as exc:
            logger.exception(f"[WorkspaceManager.save_session] Failed to save session: {exc}")

    def load_session(self):
        logger.info("[WorkspaceManager.load_session] Loading session...")
        try:
            if self.session_file.exists():
                logger.debug(f"[WorkspaceManager.load_session] Session file found at {self.session_file}")
                with open(self.session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.debug(f"[WorkspaceManager.load_session] Session data: {data}")
                last = data.get("last_workspace")
                if last and Path(last).exists():
                    logger.info(f"[WorkspaceManager.load_session] Restoring last workspace: {last}")
                    self.open_workspace(last)
                else:
                    logger.info("[WorkspaceManager.load_session] No valid last workspace found")
        except Exception as exc:
            logger.exception(f"[WorkspaceManager.load_session] Failed to load session: {exc}")

    def _add_recent(self, path: str):
        logger.debug(f"[WorkspaceManager._add_recent] Adding to recent: {path}")
        if path in self.recent_projects:
            self.recent_projects.remove(path)
        self.recent_projects.insert(0, path)
        self.recent_projects = self.recent_projects[:20]
        logger.debug(f"[WorkspaceManager._add_recent] Recent projects list now: {self.recent_projects}")
        self._save_settings()
        logger.info(f"[WorkspaceManager._add_recent] Emitting recent_projects_changed...")
        self.event_bus.publish("recent_projects_changed", {"projects": self.recent_projects})

    def pin_project(self, path: str):
        logger.info(f"[WorkspaceManager.pin_project] Pinning project: {path}")
        if path not in self.pinned_projects:
            self.pinned_projects.append(path)
            self._save_settings()
            logger.info("[WorkspaceManager.pin_project] Emitting pinned_projects_changed...")
            self.event_bus.publish("pinned_projects_changed", {"projects": self.pinned_projects})
        else:
            logger.debug(f"[WorkspaceManager.pin_project] Project already pinned: {path}")

    def unpin_project(self, path: str):
        logger.info(f"[WorkspaceManager.unpin_project] Unpinning project: {path}")
        if path in self.pinned_projects:
            self.pinned_projects.remove(path)
            self._save_settings()
            logger.info("[WorkspaceManager.unpin_project] Emitting pinned_projects_changed...")
            self.event_bus.publish("pinned_projects_changed", {"projects": self.pinned_projects})
        else:
            logger.debug(f"[WorkspaceManager.unpin_project] Project not pinned: {path}")

    def _handle_open_request(self, data):
        logger.info(f"[WorkspaceManager._handle_open_request] Received data: {data}")
        path = data.get("path")
        if path:
            logger.info(f"[WorkspaceManager._handle_open_request] Calling open_workspace with path: {path}")
            self.open_workspace(path)
        else:
            logger.warning("[WorkspaceManager._handle_open_request] No path in event data!")

    def _handle_close_request(self, data):
        logger.info(f"[WorkspaceManager._handle_close_request] Received data: {data}")
        path = data.get("path")
        if path:
            self.close_workspace(path)
        elif self.active_workspace:
            logger.info(f"[WorkspaceManager._handle_close_request] Closing active workspace: {self.active_workspace.path}")
            self.close_workspace(str(self.active_workspace.path))
        else:
            logger.debug("[WorkspaceManager._handle_close_request] No active workspace to close")

    def _handle_refresh_request(self, _data):
        logger.info("[WorkspaceManager._handle_refresh_request] Received refresh request...")
        if self.active_workspace:
            self.refresh_workspace(self.active_workspace)
        else:
            logger.debug("[WorkspaceManager._handle_refresh_request] No active workspace to refresh")

    def _handle_reopen_last(self, _data):
        logger.info("[WorkspaceManager._handle_reopen_last] Received reopen last request...")
        if self.recent_projects:
            logger.info(f"[WorkspaceManager._handle_reopen_last] Reopening: {self.recent_projects[0]}")
            self.open_workspace(self.recent_projects[0])
        else:
            logger.debug("[WorkspaceManager._handle_reopen_last] No recent projects to reopen")

    def _handle_pin_project(self, data):
        logger.info(f"[WorkspaceManager._handle_pin_project] Received data: {data}")
        path = data.get("path")
        if path:
            self.pin_project(path)

    def _handle_unpin_project(self, data):
        logger.info(f"[WorkspaceManager._handle_unpin_project] Received data: {data}")
        path = data.get("path")
        if path:
            self.unpin_project(path)

    def open_workspace(self, path_str: str):
        """
        Step-by-step:
        1. Validate path
        2. If already open, activate it and return immediately
        3. Else emit workspace_loaded IMMEDIATELY to show explorer!
        4. Then start background metadata scan!
        """
        logger.info("=" * 80)
        logger.info("[WorkspaceManager.open_workspace] STARTING WORKSPACE OPENING")
        logger.info(f"[WorkspaceManager.open_workspace] Step 1: Validating path_str = {path_str}")
        try:
            path = Path(path_str).resolve()
            logger.debug(f"[WorkspaceManager.open_workspace] Resolved path = {path}")
        except Exception as exc:
            logger.exception(f"[WorkspaceManager.open_workspace] Step 1 FAILED: Invalid path: {exc}")
            return

        if not path.exists():
            logger.error(f"[WorkspaceManager.open_workspace] Step 1 FAILED: Path does not exist: {path}")
            return
        if not path.is_dir():
            logger.error(f"[WorkspaceManager.open_workspace] Step 1 FAILED: Path is not a directory: {path}")
            return
        logger.info("[WorkspaceManager.open_workspace] Step 1 COMPLETE: Path is valid!")

        logger.info("[WorkspaceManager.open_workspace] Step 2: Checking if already open...")
        for ws in self.workspaces:
            if ws.path == path:
                logger.info(f"[WorkspaceManager.open_workspace] Step 2: Workspace already open! Activating: {ws.path}")
                self._activate(ws)
                return
        logger.info("[WorkspaceManager.open_workspace] Step 2 COMPLETE: Workspace not already open")

        logger.info("[WorkspaceManager.open_workspace] Step 3: Creating Workspace instance...")
        ws = Workspace(path, pinned=path_str in self.pinned_projects)
        ws.is_active = True

        if self.active_workspace:
            logger.debug(f"[WorkspaceManager.open_workspace] Step 3: Deactivating previous active workspace: {self.active_workspace.path}")
            self.active_workspace.is_active = False

        logger.info("[WorkspaceManager.open_workspace] Step 3: Adding to workspaces list...")
        self.workspaces.append(ws)
        self.active_workspace = ws
        logger.info(f"[WorkspaceManager.open_workspace] Step 3 COMPLETE: Active workspace is now: {ws.path}")

        logger.info("[WorkspaceManager.open_workspace] Step 4: Adding to recent projects...")
        self._add_recent(str(path))
        logger.info("[WorkspaceManager.open_workspace] Step 4 COMPLETE!")

        logger.info("[WorkspaceManager.open_workspace] Step 5: EMITTING workspace_loaded NOW!")
        self.event_bus.publish("workspace_loaded", {"path": str(path)})
        self.event_bus.publish("log_message", {"message": f"✓ Workspace open: {path.name}"})
        logger.info("[WorkspaceManager.open_workspace] Step 5 COMPLETE: workspace_loaded emitted!")

        logger.info("[WorkspaceManager.open_workspace] Step 6: Starting background metadata scan...")
        self._start_metadata_scan(ws)
        logger.info("[WorkspaceManager.open_workspace] Step 6 COMPLETE!")
        logger.info("=" * 80)

    def _start_metadata_scan(self, workspace: Workspace):
        logger.info(f"[WorkspaceManager._start_metadata_scan] Starting for workspace: {workspace.path}")
        if workspace.scanning:
            logger.info(f"[WorkspaceManager._start_metadata_scan] Already scanning, skipping duplicate scan!")
            return

        logger.debug("[WorkspaceManager._start_metadata_scan] Setting scanning = True...")
        workspace.scanning = True

        logger.debug("[WorkspaceManager._start_metadata_scan] Creating QThread instance...")
        thread = QThread()
        logger.debug("[WorkspaceManager._start_metadata_scan] Creating _MetadataScanWorker instance...")
        worker = _MetadataScanWorker(workspace.path)
        logger.debug("[WorkspaceManager._start_metadata_scan] Moving worker to thread...")
        worker.moveToThread(thread)

        logger.debug("[WorkspaceManager._start_metadata_scan] Connecting signals...")
        thread.started.connect(worker.run)
        worker.scan_complete.connect(lambda ctx: self._on_scan_complete(ctx, workspace))
        worker.scan_failed.connect(lambda msg: self._on_scan_failed(msg, workspace))
        worker.scan_complete.connect(thread.quit)
        worker.scan_failed.connect(thread.quit)
        # Connect cleanup before starting thread
        thread.finished.connect(lambda: self._on_thread_finished(thread))
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(worker.deleteLater)

        logger.debug("[WorkspaceManager._start_metadata_scan] Adding thread to _scan_threads list...")
        self._scan_threads.append(thread)
        logger.debug(f"[WorkspaceManager._start_metadata_scan] _scan_threads now has {len(self._scan_threads)} thread(s)")

        logger.info(f"[WorkspaceManager._start_metadata_scan] STARTING THREAD!")
        thread.start()
        logger.info(f"[WorkspaceManager._start_metadata_scan] COMPLETE!")

    def _on_thread_finished(self, thread: QThread):
        logger.debug(f"[WorkspaceManager._on_thread_finished] Thread finished, removing from _scan_threads...")
        if thread in self._scan_threads:
            self._scan_threads.remove(thread)
        logger.debug(f"[WorkspaceManager._on_thread_finished] _scan_threads now has {len(self._scan_threads)} thread(s)")
        # Ensure worker is also cleaned up
        # Note: worker.deleteLater() is called automatically when thread finishes

    def _on_scan_complete(self, context, workspace: Workspace):
        logger.info("=" * 80)
        logger.info(f"[WorkspaceManager._on_scan_complete] Metadata scan complete for: {workspace.path}")
        workspace.scanning = False
        workspace.context = context

        logger.info("[WorkspaceManager._on_scan_complete] Emitting workspace_metadata_updated...")
        self.event_bus.publish("workspace_metadata_updated", {
            "path": str(workspace.path),
            "project_name": getattr(context, "project_name", workspace.path.name),
            "total_files": getattr(context, "total_files", 0),
            "total_folders": getattr(context, "total_folders", 0),
            "primary_language": getattr(context, "primary_language", "Unknown"),
            "framework": getattr(context, "framework_name", "Unknown"),
            "scan_duration_ms": getattr(context, "scan_duration_ms", 0),
        })

        self.event_bus.publish("log_message", {"message": f"✓ Metadata scan complete: {workspace.path.name}"})
        logger.info(f"[WorkspaceManager._on_scan_complete] COMPLETE!")
        logger.info("=" * 80)

    def _on_scan_failed(self, msg: str, workspace: Workspace):
        logger.error("=" * 80)
        logger.error(f"[WorkspaceManager._on_scan_failed] Metadata scan FAILED for {workspace.path}: {msg}")
        workspace.scanning = False
        self.event_bus.publish("log_message", {"message": f"⚠ Metadata scan failed: {msg}"})
        logger.error("=" * 80)

    def close_workspace(self, path_str: str):
        logger.info("=" * 80)
        logger.info(f"[WorkspaceManager.close_workspace] Closing workspace: {path_str}")
        path = Path(path_str).resolve()
        for idx, ws in enumerate(self.workspaces):
            if ws.path == path:
                logger.debug(f"[WorkspaceManager.close_workspace] Found workspace at index {idx}, removing...")
                self.workspaces.pop(idx)
                if ws == self.active_workspace:
                    if self.workspaces:
                        logger.debug(f"[WorkspaceManager.close_workspace] Activating next workspace: {self.workspaces[0].path}")
                        self._activate(self.workspaces[0])
                    else:
                        logger.info("[WorkspaceManager.close_workspace] No workspaces left, setting active to None")
                        self.active_workspace = None
                        self.event_bus.publish("workspace_closed", {})
                logger.info("[WorkspaceManager.close_workspace] Emitting log_message...")
                self.event_bus.publish("log_message", {"message": f"Workspace closed: {path.name}"})
                logger.info("[WorkspaceManager.close_workspace] COMPLETE!")
                logger.info("=" * 80)
                return
        logger.warning(f"[WorkspaceManager.close_workspace] Workspace not found: {path}")

    def refresh_workspace(self, workspace: Workspace):
        logger.info(f"[WorkspaceManager.refresh_workspace] Refreshing metadata for: {workspace.path}")
        self.event_bus.publish("log_message", {"message": f"Refreshing metadata: {workspace.path.name}…"})
        self._start_metadata_scan(workspace)

    def _activate(self, ws: Workspace):
        logger.info(f"[WorkspaceManager._activate] Activating workspace: {ws.path}")
        if self.active_workspace and self.active_workspace != ws:
            logger.debug(f"[WorkspaceManager._activate] Deactivating: {self.active_workspace.path}")
            self.active_workspace.is_active = False
        ws.is_active = True
        self.active_workspace = ws

        logger.info("[WorkspaceManager._activate] Emitting workspace_loaded...")
        self.event_bus.publish("workspace_loaded", {"path": str(ws.path)})

        self.event_bus.publish("workspace_activated", {"path": str(ws.path)})
        logger.info(f"[WorkspaceManager._activate] COMPLETE: Active workspace is {ws.path}")
