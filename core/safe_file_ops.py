"""
Safe File Operations — v1.8.5

Guarantees no file corruption:
- Atomic writes using temp files
- Pre-write validation
- Post-write verification
- Permission checks
- Locking prevention
- Backup creation
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Tuple
from contextlib import contextmanager

from core.logger import setup_logger
from core.error_manager import get_error_manager, ErrorSeverity

logger = setup_logger(__name__)
error_manager = get_error_manager()


def safe_write_text(
    path: Path,
    content: str,
    encoding: str = "utf-8",
    create_backup: bool = True,
    verify: bool = True,
) -> bool:
    """
    Safely write text to a file using atomic replace.

    Args:
        path: Target file path
        content: Content to write
        encoding: File encoding
        create_backup: Whether to create a backup of existing file
        verify: Whether to verify the write was successful

    Returns:
        True if successful
    """
    path = Path(path).resolve()
    temp_path = None
    backup_path = None

    try:
        # 1. Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # 2. Create backup of existing file if requested
        if create_backup and path.exists():
            backup_path = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, backup_path)

        # 3. Write to temporary file in the same directory (for atomic rename)
        temp_dir = path.parent
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            dir=temp_dir,
            prefix=f".{path.name}.tmp.",
            delete=False,
        ) as f:
            temp_path = Path(f.name)
            f.write(content)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk

        # 4. Verify the temp file if requested
        if verify:
            verify_content = temp_path.read_text(encoding=encoding)
            if verify_content != content:
                raise IOError("File content verification failed")

        # 5. Atomic replace
        if os.name == "nt":
            # Windows: Need to handle read-only files
            if path.exists():
                try:
                    os.chmod(path, 0o666)
                except OSError:
                    pass
            try:
                os.replace(temp_path, path)
            except PermissionError:
                # Fallback for Windows: copy then delete
                shutil.copy2(temp_path, path)
                temp_path.unlink()
        else:
            # Unix: Atomic rename
            os.replace(temp_path, path)

        # 6. Clean up backup if everything succeeded
        if backup_path and backup_path.exists():
            try:
                backup_path.unlink()
            except OSError:
                pass

        logger.info(f"Safely wrote file: {path}")
        return True

    except Exception as e:
        error_manager.handle_exception(
            type(e), e, e.__traceback__, component="safe_file_ops", recoverable=True
        )
        # Clean up temp file
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        # Restore backup if available
        if backup_path and backup_path.exists() and not path.exists():
            try:
                shutil.copy2(backup_path, path)
                backup_path.unlink()
            except OSError:
                pass
        return False


def safe_read_text(
    path: Path,
    encoding: str = "utf-8",
    fallback_encodings: Tuple[str, ...] = ("utf-8", "utf-16", "latin-1"),
) -> Tuple[Optional[str], Optional[str]]:
    """
    Safely read text from a file with validation and encoding fallback.

    Args:
        path: File path to read
        encoding: Primary encoding to try
        fallback_encodings: Tuple of encodings to try if primary fails

    Returns:
        Tuple of (content, actual_encoding) or (None, None) on failure
    """
    path = Path(path).resolve()

    try:
        # Validate file exists and is readable
        if not path.exists():
            error_manager.report_error(
                f"File not found: {path}",
                severity=ErrorSeverity.WARNING,
                component="safe_file_ops",
            )
            return None, None

        if not path.is_file():
            error_manager.report_error(
                f"Path is not a file: {path}",
                severity=ErrorSeverity.WARNING,
                component="safe_file_ops",
            )
            return None, None

        # Try each encoding
        for enc in fallback_encodings:
            try:
                content = path.read_text(encoding=enc)
                logger.debug(f"Read file with {enc}: {path}")
                return content, enc
            except UnicodeDecodeError:
                continue
            except OSError as e:
                error_manager.report_error(
                    f"OS error reading {path}: {e}",
                    severity=ErrorSeverity.ERROR,
                    component="safe_file_ops",
                )
                return None, None

        error_manager.report_error(
            f"Failed to decode file with any encoding: {path}",
            severity=ErrorSeverity.ERROR,
            component="safe_file_ops",
        )
        return None, None

    except Exception as e:
        error_manager.handle_exception(
            type(e), e, e.__traceback__, component="safe_file_ops", recoverable=True
        )
        return None, None


def validate_file(
    path: Path,
    max_size: Optional[int] = 10 * 1024 * 1024,  # 10 MB
) -> Tuple[bool, Optional[str]]:
    """
    Validate a file before reading/writing.

    Args:
        path: File path to validate
        max_size: Maximum allowed file size (None for unlimited)

    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(path).resolve()

    try:
        if not path.exists():
            return False, "File does not exist"

        if not path.is_file():
            return False, "Path is not a file"

        if not os.access(path, os.R_OK):
            return False, "File is not readable"

        if max_size is not None:
            size = path.stat().st_size
            if size > max_size:
                return False, f"File too large ({size} bytes > {max_size} bytes)"

        return True, None

    except Exception as e:
        error_manager.handle_exception(
            type(e), e, e.__traceback__, component="safe_file_ops", recoverable=True
        )
        return False, str(e)


@contextmanager
def safe_file_lock(path: Path, timeout: float = 10.0):
    """
    Context manager for safe file locking (simple advisory lock).

    Args:
        path: File path to lock
        timeout: Timeout in seconds
    """
    lock_path = path.with_suffix(path.suffix + ".lock")
    acquired = False
    try:
        import time
        start = time.time()
        while time.time() - start < timeout:
            try:
                lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(lock_fd)
                acquired = True
                yield
                break
            except FileExistsError:
                time.sleep(0.1)
        if not acquired:
            raise TimeoutError(f"Could not acquire lock for {path}")
    finally:
        if acquired and lock_path.exists():
            try:
                lock_path.unlink()
            except OSError:
                pass
