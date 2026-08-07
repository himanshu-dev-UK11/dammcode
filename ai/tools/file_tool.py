"""
File operations tool.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from ai.tools.tool_base import BaseTool, ToolPermission, ToolCategory, ToolResult


class FileTool(BaseTool):
    def __init__(self, workspace_root: str):
        super().__init__(
            name="file",
            description="File operations (read, write, create, delete, rename)",
            category=ToolCategory.FILE,
            permission_level=ToolPermission.SAFE,
            supported_models=["all"]
        )
        self.workspace_root = workspace_root

    def _resolve_path(self, path: str) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute() and self.workspace_root:
            candidate = Path(self.workspace_root) / candidate
        candidate = candidate.resolve()

        if self.workspace_root:
            workspace_root = Path(self.workspace_root).resolve()
            try:
                candidate.relative_to(workspace_root)
            except ValueError as exc:
                raise PermissionError(f"Path is outside the workspace: {path}") from exc

        return candidate

    def _write_text(self, path: Path, content: str) -> ToolResult:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content or "", encoding="utf-8")
        return ToolResult.success_result(self.name, output=f"Written: {path}")

    def read(self, path: str) -> ToolResult:
        try:
            full_path = self._resolve_path(path)
            return ToolResult.success_result(self.name, output=full_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return ToolResult.error_result(self.name, str(exc))

    def write(self, path: str, content: str = "") -> ToolResult:
        try:
            full_path = self._resolve_path(path)
            return self._write_text(full_path, content)
        except Exception as exc:
            return ToolResult.error_result(self.name, str(exc))

    def create(self, path: str, content: str = "") -> ToolResult:
        try:
            full_path = self._resolve_path(path)
            if full_path.exists():
                return ToolResult.error_result(self.name, f"File already exists: {path}")
            return self._write_text(full_path, content)
        except Exception as exc:
            return ToolResult.error_result(self.name, str(exc))

    def delete(self, path: str, confirm: bool = False) -> ToolResult:
        try:
            if not confirm:
                return ToolResult.error_result(
                    self.name,
                    f"Delete requires confirm=True for: {path}",
                    metadata={"requires_confirmation": True, "action": "delete", "path": path},
                )

            full_path = self._resolve_path(path)
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()
            return ToolResult.success_result(self.name, output=f"Deleted: {path}")
        except Exception as exc:
            return ToolResult.error_result(self.name, str(exc))

    def rename(self, path: str, new_path: str) -> ToolResult:
        try:
            source = self._resolve_path(path)
            destination = self._resolve_path(new_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.rename(destination)
            return ToolResult.success_result(self.name, output=f"Renamed: {path} -> {new_path}")
        except Exception as exc:
            return ToolResult.error_result(self.name, str(exc))

    def move(self, path: str, new_path: str) -> ToolResult:
        try:
            source = self._resolve_path(path)
            destination = self._resolve_path(new_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            return ToolResult.success_result(self.name, output=f"Moved: {path} -> {new_path}")
        except Exception as exc:
            return ToolResult.error_result(self.name, str(exc))

    async def execute_async(self, action: str, path: str, content: str = None, new_path: str = None, confirm: bool = False) -> ToolResult:
        """Execute a file action."""
        try:
            if action in ("read", "read_file"):
                return self.read(path)
            if action in ("write", "write_file"):
                return self.write(path, content or "")
            if action in ("create", "create_file"):
                return self.create(path, content or "")
            if action in ("delete", "delete_file"):
                return self.delete(path, confirm=confirm)
            if action in ("rename", "rename_file"):
                if not new_path:
                    return ToolResult.error_result(self.name, "rename requires new_path")
                return self.rename(path, new_path)
            if action in ("move", "move_file"):
                if not new_path:
                    return ToolResult.error_result(self.name, "move requires new_path")
                return self.move(path, new_path)

            return ToolResult.error_result(self.name, f"Unknown action: {action}")
        except Exception as e:
            return ToolResult.error_result(self.name, str(e))

    def read_file(self, path: str) -> ToolResult:
        return self.read(path)

    def write_file(self, path: str, content: str) -> ToolResult:
        return self.write(path, content)

    def create_file(self, path: str, content: str = "") -> ToolResult:
        return self.create(path, content)

    def delete_file(self, path: str, confirm: bool = False) -> ToolResult:
        return self.delete(path, confirm=confirm)

    def rename_file(self, path: str, new_path: str) -> ToolResult:
        return self.rename(path, new_path)

    def move_file(self, path: str, new_path: str) -> ToolResult:
        return self.move(path, new_path)
