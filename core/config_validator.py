"""
Configuration Validator — v1.8.5

Validates and repairs configuration files:
- JSON validation
- Schema validation
- Default values restoration
- Backup creation
- Corruption recovery
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass

from core.logger import setup_logger
from core.error_manager import get_error_manager, ErrorSeverity

logger = setup_logger(__name__)
error_manager = get_error_manager()


@dataclass
class SchemaRule:
    key: str
    type: type
    default: Any
    required: bool = False


class ConfigValidator:
    """
    Validates and repairs JSON configuration files.
    """

    _instance: Optional["ConfigValidator"] = None
    _initialized = False

    def __init__(self):
        if ConfigValidator._initialized:
            return
        super().__init__()
        self._config_dir = Path("config")
        self._defaults: Dict[str, Dict[str, Any]] = {
            "settings.json": {
                "theme": "dark",
                "font_size": 12,
                "auto_save": True,
                "show_line_numbers": True,
                "word_wrap": False,
                "tab_size": 4,
                "insert_spaces": True,
            },
            "recent_projects.json": [],
            "pinned_projects.json": [],
            "workspace_session.json": {},
            "editor_session.json": {"open_tabs": []},
            "chat_sessions.json": [],
            "recent_commands.json": [],
        }
        ConfigValidator._initialized = True

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def validate_and_load(self, filename: str) -> Dict[str, Any]:
        """
        Validate a config file, repair if needed, and return the data.

        Args:
            filename: Config filename (in config/ directory)

        Returns:
            Validated config data
        """
        file_path = self._config_dir / filename
        defaults = self._defaults.get(filename, {})

        try:
            if not file_path.exists():
                logger.info(f"Creating missing config: {filename}")
                return self._save_config(file_path, defaults)

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate and merge with defaults
            validated = self._merge_with_defaults(data, defaults)

            if validated != data:
                logger.info(f"Repaired config: {filename}")
                self._save_config(file_path, validated)

            return validated

        except json.JSONDecodeError as e:
            error_manager.report_error(
                f"Corrupted config: {filename}: {e}",
                severity=ErrorSeverity.WARNING,
                component="config_validator",
            )
            return self._recover_config(file_path, defaults)

        except Exception as e:
            error_manager.handle_exception(
                type(e),
                e,
                e.__traceback__,
                component=f"config_validator:{filename}",
                recoverable=True,
            )
            return self._recover_config(file_path, defaults)

    def _merge_with_defaults(
        self, data: Any, defaults: Any
    ) -> Any:
        """Recursively merge data with defaults."""
        if isinstance(defaults, dict):
            if not isinstance(data, dict):
                return defaults
            result = defaults.copy()
            for key, value in data.items():
                if key in defaults:
                    result[key] = self._merge_with_defaults(value, defaults[key])
                else:
                    result[key] = value
            return result
        elif isinstance(defaults, list):
            if not isinstance(data, list):
                return defaults
            return data
        else:
            # Primitive type - use data if type matches, else default
            if isinstance(data, type(defaults)):
                return data
            return defaults

    def _save_config(self, file_path: Path, data: Any) -> Any:
        """Save config data to file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return data
        except Exception as e:
            error_manager.handle_exception(
                type(e),
                e,
                e.__traceback__,
                component=f"config_validator:save:{file_path.name}",
                recoverable=True,
            )
            return data

    def _recover_config(self, file_path: Path, defaults: Any) -> Any:
        """Recover a corrupted config file."""
        try:
            if file_path.exists():
                backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                shutil.copy2(file_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
        except Exception as e:
            logger.debug(f"Could not create backup: {e}")

        return self._save_config(file_path, defaults)

    def save(self, filename: str, data: Any):
        """Save data to a config file."""
        file_path = self._config_dir / filename
        self._save_config(file_path, data)


def get_config_validator() -> ConfigValidator:
    """Get the global ConfigValidator singleton."""
    return ConfigValidator()
