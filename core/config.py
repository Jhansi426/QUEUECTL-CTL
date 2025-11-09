import json
import os
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

DEFAULT_CONFIG = {
    "max_retries": 3,
    "backoff_base": 2,
    "worker_count": 1,
    "job_timeout": 30
}


class ConfigManager:
    """Handles QueueCTL configuration persistence."""

    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config_path = config_path
        self._ensure_config_exists()

    # ------------------------------------------------------------------
    # Core Utilities
    # ------------------------------------------------------------------
    def _ensure_config_exists(self):
        """Create default config if missing."""
        if not os.path.exists(self.config_path):
            self.save(DEFAULT_CONFIG)

    def load(self) -> dict:
        """Load all configuration values."""
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: dict):
        """Write configuration dictionary to file."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_value(self, key: str, value):
        """Set a single configuration key."""
        config = self.load()
        config[key] = value
        self.save(config)

    def get_value(self, key: str):
        """Retrieve a single configuration key."""
        config = self.load()
        return config.get(key)

    def reset_config(self):
        """Reset to default configuration."""
        self.save(DEFAULT_CONFIG)

    # ------------------------------------------------------------------
    # Short Aliases (for CLI use)
    # ------------------------------------------------------------------
    def set(self, key: str, value):
        return self.set_value(key, value)

    def get(self, key: str):
        return self.get_value(key)

    def reset(self, full: bool = True):
        return self.reset_config()
