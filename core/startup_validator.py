"""
Application Startup Validator — v1.8.5

Validates and repairs the application environment on startup:
- Required directories
- Configuration files
- Permissions
- Python environment
- Cache directories
- Log directories
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

from core.logger import setup_logger
from core.error_manager import get_error_manager, ErrorSeverity

logger = setup_logger(__name__)
error_manager = get_error_manager()


class ValidationStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    REPAIRED = "repaired"


@dataclass
class ValidationResult:
    component: str
    status: ValidationStatus
    message: str
    repaired: bool = False


@dataclass
class StartupReport:
    results: List[ValidationResult] = field(default_factory=list)
    success: bool = True
    warnings: int = 0
    errors: int = 0


class StartupValidator:
    """
    Validates application environment on startup.
    """

    def __init__(self):
        self.report = StartupReport()
        self.required_dirs = [
            "config",
            "config/providers",
            "logs",
            "cache",
            "cache/models",
            "temp",
        ]
        self.config_defaults = {
            "config/settings.json": {
                "theme": "dark",
                "font_size": 12,
                "auto_save": True,
            },
            "config/recent_projects.json": [],
            "config/pinned_projects.json": [],
        }

    def validate(self) -> StartupReport:
        """
        Run all startup validations.

        Returns:
            StartupReport with all validation results
        """
        logger.info("Starting application environment validation...")

        self._validate_directories()
        self._validate_config_files()
        self._validate_permissions()
        self._validate_python_environment()
        self._validate_cache()
        self._cleanup_temp()

        # Final summary
        self._finalize_report()

        logger.info("Startup validation complete")
        return self.report

    def _validate_directories(self):
        """Validate and create required directories."""
        for dir_path in self.required_dirs:
            path = Path(dir_path)
            try:
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                    self.report.results.append(
                        ValidationResult(
                            component=f"directory:{dir_path}",
                            status=ValidationStatus.REPAIRED,
                            message=f"Created missing directory: {dir_path}",
                            repaired=True,
                        )
                    )
                    logger.info(f"Created directory: {dir_path}")
                elif not path.is_dir():
                    self.report.results.append(
                        ValidationResult(
                            component=f"directory:{dir_path}",
                            status=ValidationStatus.ERROR,
                            message=f"Path exists but is not a directory: {dir_path}",
                        )
                    )
                    self.report.errors += 1
                else:
                    self.report.results.append(
                        ValidationResult(
                            component=f"directory:{dir_path}",
                            status=ValidationStatus.OK,
                            message=f"Directory OK: {dir_path}",
                        )
                    )
            except Exception as e:
                error_manager.handle_exception(
                    type(e),
                    e,
                    e.__traceback__,
                    component=f"startup:directory:{dir_path}",
                    recoverable=True,
                )
                self.report.results.append(
                    ValidationResult(
                        component=f"directory:{dir_path}",
                        status=ValidationStatus.ERROR,
                        message=f"Failed to create directory: {dir_path}: {e}",
                    )
                )
                self.report.errors += 1

    def _validate_config_files(self):
        """Validate and restore config files with defaults."""
        for file_path, default_data in self.config_defaults.items():
            path = Path(file_path)
            try:
                if not path.exists():
                    # Create with defaults
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(default_data, f, indent=4)
                    self.report.results.append(
                        ValidationResult(
                            component=f"config:{file_path}",
                            status=ValidationStatus.REPAIRED,
                            message=f"Created config with defaults: {file_path}",
                            repaired=True,
                        )
                    )
                    logger.info(f"Created default config: {file_path}")
                else:
                    # Validate JSON
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            json.load(f)
                        self.report.results.append(
                            ValidationResult(
                                component=f"config:{file_path}",
                                status=ValidationStatus.OK,
                                message=f"Config OK: {file_path}",
                            )
                        )
                    except json.JSONDecodeError:
                        # Restore from backup or defaults
                        backup_path = path.with_suffix(path.suffix + ".corrupted")
                        if path.exists():
                            path.rename(backup_path)
                        with open(path, "w", encoding="utf-8") as f:
                            json.dump(default_data, f, indent=4)
                        self.report.results.append(
                            ValidationResult(
                                component=f"config:{file_path}",
                                status=ValidationStatus.REPAIRED,
                                message=f"Restored corrupted config: {file_path}",
                                repaired=True,
                            )
                        )
                        self.report.warnings += 1
                        logger.warning(f"Restored corrupted config: {file_path}")
            except Exception as e:
                error_manager.handle_exception(
                    type(e),
                    e,
                    e.__traceback__,
                    component=f"startup:config:{file_path}",
                    recoverable=True,
                )
                self.report.results.append(
                    ValidationResult(
                        component=f"config:{file_path}",
                        status=ValidationStatus.ERROR,
                        message=f"Failed to validate config: {file_path}: {e}",
                    )
                )
                self.report.errors += 1

    def _validate_permissions(self):
        """Validate read/write permissions for key directories."""
        check_paths = ["config", "logs", "cache", "temp"]
        for dir_path in check_paths:
            path = Path(dir_path)
            try:
                if not path.exists():
                    continue
                # Test write permission
                test_file = path / ".write_test"
                test_file.touch()
                test_file.unlink()
                self.report.results.append(
                    ValidationResult(
                        component=f"permissions:{dir_path}",
                        status=ValidationStatus.OK,
                        message=f"Permissions OK: {dir_path}",
                    )
                )
            except Exception as e:
                self.report.results.append(
                    ValidationResult(
                        component=f"permissions:{dir_path}",
                        status=ValidationStatus.WARNING,
                        message=f"Permission issues for {dir_path}: {e}",
                    )
                )
                self.report.warnings += 1

    def _validate_python_environment(self):
        """Validate Python version and required modules."""
        try:
            # Check Python version
            version = sys.version_info
            if version < (3, 9):
                self.report.results.append(
                    ValidationResult(
                        component="python:version",
                        status=ValidationStatus.WARNING,
                        message=f"Python {version.major}.{version.minor} detected, 3.9+ recommended",
                    )
                )
                self.report.warnings += 1
            else:
                self.report.results.append(
                    ValidationResult(
                        component="python:version",
                        status=ValidationStatus.OK,
                        message=f"Python {version.major}.{version.minor}.{version.micro} OK",
                    )
                )

            # Check core modules
            required_modules = ["PySide6"]
            for module in required_modules:
                try:
                    __import__(module)
                    self.report.results.append(
                        ValidationResult(
                            component=f"python:module:{module}",
                            status=ValidationStatus.OK,
                            message=f"Module OK: {module}",
                        )
                    )
                except ImportError:
                    self.report.results.append(
                        ValidationResult(
                            component=f"python:module:{module}",
                            status=ValidationStatus.ERROR,
                            message=f"Required module missing: {module}",
                        )
                    )
                    self.report.errors += 1
        except Exception as e:
            error_manager.handle_exception(
                type(e),
                e,
                e.__traceback__,
                component="startup:python",
                recoverable=True,
            )

    def _validate_cache(self):
        """Validate cache directories and clean old files."""
        try:
            cache_dir = Path("cache")
            if cache_dir.exists():
                # Clean old files (>7 days)
                import time
                now = time.time()
                cutoff = now - (7 * 86400)
                cleaned = 0
                for item in cache_dir.rglob("*"):
                    if item.is_file() and item.stat().st_mtime < cutoff:
                        try:
                            item.unlink()
                            cleaned += 1
                        except OSError:
                            pass
                if cleaned > 0:
                    self.report.results.append(
                        ValidationResult(
                            component="cache:cleanup",
                            status=ValidationStatus.OK,
                            message=f"Cleaned {cleaned} old cache files",
                        )
                    )
        except Exception as e:
            error_manager.handle_exception(
                type(e),
                e,
                e.__traceback__,
                component="startup:cache",
                recoverable=True,
            )

    def _cleanup_temp(self):
        """Clean up temporary files from previous runs."""
        try:
            temp_dir = Path("temp")
            if temp_dir.exists():
                removed = 0
                for item in temp_dir.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                        removed += 1
                    except OSError:
                        pass
                if removed > 0:
                    self.report.results.append(
                        ValidationResult(
                            component="temp:cleanup",
                            status=ValidationStatus.OK,
                            message=f"Cleaned {removed} temp items",
                        )
                    )
        except Exception as e:
            error_manager.handle_exception(
                type(e),
                e,
                e.__traceback__,
                component="startup:temp",
                recoverable=True,
            )

    def _finalize_report(self):
        """Finalize the report summary."""
        self.report.success = self.report.errors == 0
        logger.info(
            f"Startup validation complete: {len(self.report.results)} checks, "
            f"{self.report.warnings} warnings, {self.report.errors} errors"
        )


def run_startup_validation() -> StartupReport:
    """
    Run the complete startup validation.

    Returns:
        StartupReport with all results
    """
    validator = StartupValidator()
    return validator.validate()


# Import shutil here to avoid circular imports
import shutil
