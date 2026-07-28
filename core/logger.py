"""
Centralized structured logging system — v1.8.5

Enhanced with:
- File logging with automatic rotation
- Log compression for old files
- Log level configuration
- Structured log format
- Memory-efficient log management
"""

import logging
import logging.handlers
import sys
import gzip
import shutil
from pathlib import Path
from typing import Optional

# Global log level
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5  # Keep up to 5 rotated logs


def namer(name):
    """Custom namer for rotated log files."""
    return name + ".gz"


def rotator(source, dest):
    """Custom rotator that compresses rotated logs with gzip."""
    with open(source, "rb") as f_in:
        with gzip.open(dest, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    Path(source).unlink()


def setup_logger(
    name: str,
    log_level: int = DEFAULT_LOG_LEVEL,
    log_dir: str = "logs",
    max_bytes: int = DEFAULT_MAX_FILE_SIZE,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> logging.Logger:
    """
    Creates and configures a standard logger for a module.
    
    Args:
        name: Module name for logger
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        max_bytes: Max size per log file before rotation
        backup_count: Number of rotated log files to keep
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Log format
    formatter = logging.Formatter(
        "%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler (for development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation and compression
    log_file = log_path / "app.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Attach custom rotator and namer for compression
    file_handler.rotator = rotator
    file_handler.namer = namer
    
    logger.addHandler(file_handler)
    
    # Also log uncaught exceptions
    def _handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
    
    sys.excepthook = _handle_exception
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


def set_global_log_level(level: int):
    """
    Set the log level for all existing loggers.
    """
    for logger in logging.Logger.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            logger.setLevel(level)


def clean_old_logs(log_dir: str = "logs", keep_days: int = 30):
    """
    Clean up log files older than the specified number of days.
    """
    import time
    
    log_path = Path(log_dir)
    if not log_path.exists():
        return
    
    now = time.time()
    cutoff = now - (keep_days * 86400)
    
    for log_file in log_path.glob("*.log*"):
        if log_file.stat().st_mtime < cutoff:
            try:
                log_file.unlink()
            except Exception:
                pass
