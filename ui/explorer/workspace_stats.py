"""
Workspace Statistics Manager — v2.3

Displays workspace statistics in the Explorer.
Shows: Files count, Folders count, Project size, Detected languages, Git branch, Workspace health
"""
from pathlib import Path
from typing import Dict, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from core.logger import setup_logger
from ai.tools.project_scanner import ProjectScanner

logger = setup_logger(__name__)


class WorkspaceStats:
    """Represents workspace statistics."""
    
    def __init__(self):
        self.files_count = 0
        self.folders_count = 0
        self.project_size = 0
        self.languages: Dict[str, float] = {}
        self.git_branch = "main"
        self.git_status = "clean"
        self.health_score = 100
        self.last_updated = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "files_count": self.files_count,
            "folders_count": self.folders_count,
            "project_size": self.project_size,
            "languages": self.languages,
            "git_branch": self.git_branch,
            "git_status": self.git_status,
            "health_score": self.health_score,
            "last_updated": str(self.last_updated) if self.last_updated else None,
        }


class WorkspaceStatsWorker(QThread):
    """Worker thread for calculating workspace statistics."""
    finished = Signal(dict)  # stats dict
    
    def __init__(self, root_path: Path):
        super().__init__()
        self.root_path = root_path
    
    def run(self):
        """Calculate workspace statistics."""
        try:
            stats = {
                "files_count": 0,
                "folders_count": 0,
                "project_size": 0,
                "languages": {},
                "git_branch": "main",
                "git_status": "clean",
            }
            
            if self.root_path.exists():
                # Count files and folders
                for item in self.root_path.rglob("*"):
                    if not item.exists():
                        continue
                    
                    if item.is_dir():
                        stats["folders_count"] += 1
                    else:
                        stats["files_count"] += 1
                        try:
                            stats["project_size"] += item.stat().st_size
                        except:
                            pass
                
                # Subtract 1 for root folder
                stats["folders_count"] = max(0, stats["folders_count"] - 1)
                
                # Calculate languages (simple approach)
                ext_counts = {}
                for item in self.root_path.rglob("*"):
                    if item.is_file():
                        ext = item.suffix.lower()
                        ext_counts[ext] = ext_counts.get(ext, 0) + 1
                
                total_files = stats["files_count"]
                if total_files > 0:
                    for ext, count in ext_counts.items():
                        stats["languages"][ext] = round(count / total_files * 100, 1)
                
                # Get git info
                git_path = self.root_path / ".git"
                if git_path.exists():
                    # Get current branch
                    head_path = git_path / "HEAD"
                    if head_path.exists():
                        try:
                            with open(head_path, "r") as f:
                                content = f.read().strip()
                                if content.startswith("ref: refs/heads/"):
                                    stats["git_branch"] = content.replace("ref: refs/heads/", "")
                        except:
                            pass
                    
                    # Check git status
                    import subprocess
                    try:
                        result = subprocess.run(
                            ["git", "status", "--porcelain"],
                            cwd=str(self.root_path),
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            if result.stdout.strip():
                                stats["git_status"] = "modified"
                            else:
                                stats["git_status"] = "clean"
                    except:
                        pass
            
            self.finished.emit(stats)
        except Exception as e:
            logger.error(f"Failed to calculate stats: {e}")
            self.finished.emit({})


class WorkspaceStatsWidget(QWidget):
    """Widget for displaying workspace statistics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._stats: Optional[WorkspaceStats] = None
        self._worker: Optional[WorkspaceStatsWorker] = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Files
        self.files_label = QLabel("Files: 0")
        self.files_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.files_label)
        
        # Folders
        self.folders_label = QLabel("Folders: 0")
        self.folders_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.folders_label)
        
        # Project size
        self.size_label = QLabel("Size: 0 B")
        self.size_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.size_label)
        
        # Languages
        self.lang_label = QLabel("Languages: -")
        self.lang_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.lang_label)
        
        # Git branch
        self.git_label = QLabel("Git: main")
        self.git_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.git_label)
        
        # Health score
        health_layout = QHBoxLayout()
        
        health_label = QLabel("Health:")
        health_label.setStyleSheet("font-size: 11px;")
        health_layout.addWidget(health_label)
        
        self.health_bar = QProgressBar()
        self.health_bar.setRange(0, 100)
        self.health_bar.setValue(100)
        self.health_bar.setTextVisible(False)
        self.health_bar.setMaximumWidth(100)
        health_layout.addWidget(self.health_bar)
        
        self.health_text = QLabel("100%")
        self.health_text.setStyleSheet("font-size: 11px;")
        health_layout.addWidget(self.health_text)
        
        health_layout.addStretch()
        layout.addLayout(health_layout)
        
        layout.addStretch()
    
    def calculate_stats(self, root_path: Path):
        """Calculate workspace statistics."""
        if self._worker:
            self._worker.quit()
        
        self._worker = WorkspaceStatsWorker(root_path)
        self._worker.finished.connect(self._on_stats_calculated)
        self._worker.start()
    
    def _on_stats_calculated(self, stats: dict):
        """Handle stats calculation completion."""
        self._stats = WorkspaceStats()
        
        self._stats.files_count = stats.get("files_count", 0)
        self._stats.folders_count = stats.get("folders_count", 0)
        self._stats.project_size = stats.get("project_size", 0)
        self._stats.languages = stats.get("languages", {})
        self._stats.git_branch = stats.get("git_branch", "main")
        self._stats.git_status = stats.get("git_status", "clean")
        
        # Update UI
        self.files_label.setText(f"Files: {self._stats.files_count}")
        self.folders_label.setText(f"Folders: {self._stats.folders_count}")
        self.size_label.setText(f"Size: {self._format_size(self._stats.project_size)}")
        
        # Format languages
        if self._stats.languages:
            top_langs = sorted(self._stats.languages.items(), key=lambda x: x[1], reverse=True)[:3]
            lang_text = ", ".join(f"{k} ({v}%)" for k, v in top_langs)
            self.lang_label.setText(f"Languages: {lang_text}")
        else:
            self.lang_label.setText("Languages: -")
        
        # Git info
        status_icon = "✓" if self._stats.git_status == "clean" else "⚠️"
        self.git_label.setText(f"{status_icon} Git: {self._stats.git_branch}")
        
        # Health score
        health = 100
        if self._stats.git_status != "clean":
            health = 90
        if self._stats.files_count == 0:
            health = 50
        self.health_bar.setValue(health)
        self.health_text.setText(f"{health}%")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"