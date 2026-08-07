"""
File Operations Manager — v1.6

Safe file and folder operations with validation and error handling.
Supports: create, rename, delete, move, copy, duplicate
"""
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple
from PySide6.QtWidgets import QMessageBox, QInputDialog, QWidget
from core.logger import setup_logger

logger = setup_logger(__name__)


class FileOperations:
    """
    Safe file and folder operations with user confirmation.
    """
    def __init__(self, event_bus, parent: Optional[QWidget] = None):
        self.event_bus = event_bus
        self.parent = parent
        
    def create_file(self, parent_dir: Path, filename: str = None) -> Optional[Path]:
        """Create a new file."""
        if filename is None:
            filename, ok = QInputDialog.getText(
                self.parent, "New File", "Enter file name:"
            )
            if not ok or not filename:
                return None
                
        file_path = parent_dir / filename
        
        if file_path.exists():
            QMessageBox.warning(
                self.parent, "File Exists", 
                f"File '{filename}' already exists."
            )
            return None
            
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
            logger.info(f"Created file: {file_path}")
            self.event_bus.publish("file_created", {"path": str(file_path)})
            return file_path
        except Exception as e:
            logger.error(f"Failed to create file: {e}")
            QMessageBox.critical(
                self.parent, "Error", 
                f"Failed to create file: {e}"
            )
            return None
            
    def create_folder(self, parent_dir: Path, folder_name: str = None) -> Optional[Path]:
        """Create a new folder."""
        if folder_name is None:
            folder_name, ok = QInputDialog.getText(
                self.parent, "New Folder", "Enter folder name:"
            )
            if not ok or not folder_name:
                return None
                
        folder_path = parent_dir / folder_name
        
        if folder_path.exists():
            QMessageBox.warning(
                self.parent, "Folder Exists",
                f"Folder '{folder_name}' already exists."
            )
            return None

            
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created folder: {folder_path}")
            self.event_bus.publish("folder_created", {"path": str(folder_path)})
            return folder_path
        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            QMessageBox.critical(
                self.parent, "Error",
                f"Failed to create folder: {e}"
            )
            return None
            
    def rename(self, old_path: Path, new_name: str = None) -> Optional[Path]:
        """Rename a file or folder."""
        if new_name is None:
            new_name, ok = QInputDialog.getText(
                self.parent, "Rename", 
                f"Rename '{old_path.name}' to:",
                text=old_path.name
            )
            if not ok or not new_name:
                return None
                
        new_path = old_path.parent / new_name
        
        if new_path.exists():
            QMessageBox.warning(
                self.parent, "Already Exists",
                f"'{new_name}' already exists."
            )
            return None
            
        try:
            old_path.rename(new_path)
            logger.info(f"Renamed: {old_path} -> {new_path}")
            self.event_bus.publish("file_renamed", {
                "old_path": str(old_path),
                "new_path": str(new_path)
            })
            return new_path
        except Exception as e:
            logger.error(f"Failed to rename: {e}")
            QMessageBox.critical(
                self.parent, "Error",
                f"Failed to rename: {e}"
            )
            return None

            
    def delete(self, path: Path, confirm: bool = True) -> bool:
        """Delete a file or folder with confirmation."""
        if confirm:
            is_dir = path.is_dir()
            item_type = "folder" if is_dir else "file"
            
            reply = QMessageBox.question(
                self.parent, "Confirm Delete",
                f"Are you sure you want to delete this {item_type}?\n\n{path.name}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return False
                
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            logger.info(f"Deleted: {path}")
            self.event_bus.publish("file_deleted", {"path": str(path)})
            return True
        except Exception as e:
            logger.error(f"Failed to delete: {e}")
            QMessageBox.critical(
                self.parent, "Error",
                f"Failed to delete: {e}"
            )
            return False
            
    def move(self, source: Path, destination: Path) -> Optional[Path]:
        """Move a file or folder."""
        if destination.exists():
            QMessageBox.warning(
                self.parent, "Already Exists",
                f"Destination already exists: {destination}"
            )
            return None
            
        try:
            shutil.move(str(source), str(destination))
            logger.info(f"Moved: {source} -> {destination}")
            self.event_bus.publish("file_moved", {
                "source": str(source),
                "destination": str(destination)
            })
            return destination
        except Exception as e:
            logger.error(f"Failed to move: {e}")
            QMessageBox.critical(
                self.parent, "Error",
                f"Failed to move: {e}"
            )
            return None

            
    def copy(self, source: Path, destination: Path) -> Optional[Path]:
        """Copy a file or folder."""
        if destination.exists():
            QMessageBox.warning(
                self.parent, "Already Exists",
                f"Destination already exists: {destination}"
            )
            return None
            
        try:
            if source.is_dir():
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
            logger.info(f"Copied: {source} -> {destination}")
            self.event_bus.publish("file_copied", {
                "source": str(source),
                "destination": str(destination)
            })
            return destination
        except Exception as e:
            logger.error(f"Failed to copy: {e}")
            QMessageBox.critical(
                self.parent, "Error",
                f"Failed to copy: {e}"
            )
            return None
            
    def duplicate(self, path: Path) -> Optional[Path]:
        """Duplicate a file or folder."""
        # Generate new name
        if path.is_dir():
            new_name = f"{path.name}_copy"
        else:
            stem = path.stem
            suffix = path.suffix
            new_name = f"{stem}_copy{suffix}"
            
        new_path = path.parent / new_name
        
        # If copy exists, add number
        counter = 2
        while new_path.exists():
            if path.is_dir():
                new_name = f"{path.name}_copy{counter}"
            else:
                new_name = f"{stem}_copy{counter}{suffix}"
            new_path = path.parent / new_name
            counter += 1
            
        return self.copy(path, new_path)
        
    def reveal_in_explorer(self, path: Path):
        """Open file location in system file explorer."""
        try:
            if path.is_file():
                path = path.parent
            os.startfile(str(path))
        except Exception as e:
            logger.error(f"Failed to reveal in explorer: {e}")
            QMessageBox.critical(
                self.parent, "Error",
                f"Failed to open location: {e}"
            )
