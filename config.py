"""
Configuration management with JSON persistence.
"""

import json
import os
from pathlib import Path
from typing import Any


class Config:
    """Manages application configuration with JSON persistence."""
    
    DEFAULT_CONFIG = {
        "popup_duration": 1000,  # milliseconds
        "popup_opacity": 0.95,
        "popup_max_width": 400,
        "popup_max_height": 300,
        "cursor_offset_x": 20,
        "cursor_offset_y": 20,
        "show_text_popup": True,
        "show_image_popup": True,
        "text_preview_length": 500,
        "fade_duration": 150,  # milliseconds
        "run_on_startup": False,
        "theme": "dark",
        # Appearance
        "popup_bg_color": "#1e1e2e",
        "popup_border_color": "#7c3aed",
        "popup_text_color": "#e0e0e0",
        "popup_border_width": 1,
    }
    
    def __init__(self):
        self.config_dir = Path(os.environ.get("APPDATA", "")) / "ClipboardFlash"
        self.config_file = self.config_dir / "config.json"
        self._config = self.DEFAULT_CONFIG.copy()
        self._load()
        
    def _load(self):
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    saved_config = json.load(f)
                    # Merge with defaults to handle new settings
                    self._config.update(saved_config)
        except Exception as e:
            print(f"Error loading config: {e}")
            
    def save(self):
        """Save configuration to file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set a configuration value."""
        self._config[key] = value
        
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self._config = self.DEFAULT_CONFIG.copy()
        self.save()
        
    def get_all(self) -> dict:
        """Get all configuration values."""
        return self._config.copy()
