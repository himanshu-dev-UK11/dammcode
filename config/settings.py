"""
Configuration management.
"""

from core.logger import setup_logger

logger = setup_logger(__name__)

class SettingsManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.settings = {}
        logger.info(f"SettingsManager initialized with config at {config_path}")
