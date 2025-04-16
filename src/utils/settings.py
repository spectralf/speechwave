"""
Settings management for SpeechWave application.
"""
import os
import json
import threading # Import threading
from pathlib import Path
from typing import Any, Dict, Optional

from .logger import get_logger

logger = get_logger("settings")

# Default settings
DEFAULT_SETTINGS = {
    "hotkey": {
        "record": "alt+v",  # Default record hotkey
        "enabled": True,         # Whether hotkey is enabled
    },
    "audio": {
        "sample_rate": 16000,    # Sample rate for recording in Hz
        "channels": 1,           # Mono audio
        "chunk_size": 1024,      # Audio buffer size
    },
    "transcription": {
        "model": "small",        # Whisper model size
        "language": "en",        # Default language
        "beam_size": 5,          # Beam search parameter
        "device": "cpu",         # Default device
        "compute_type": "int8",  # Default compute type
    },
    "ui": {
        "start_minimized": True, # Start app minimized to tray
        "dark_mode": True,       # Use dark mode theme
        "notifications": True,   # Show notifications
    },
    "advanced": {
        "insertion_delay": 0.1,  # Delay before inserting text (seconds)
        "debug": False,          # Enable debug logging
    },
    "text_insertion": {
        "add_space_after": True # Automatically add a space after inserting text
    },
    # Add new section for autostart preference
    "autostart": {
        "enabled": False # Default to not enabled in settings file
    }
}

# Get the user's AppData folder (Windows)
APP_DATA = os.getenv("APPDATA")
if APP_DATA:
    CONFIG_DIR = Path(APP_DATA) / "SpeechWave"
else:
    CONFIG_DIR = Path.home() / ".speechwave"

# Create config directory if it doesn't exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Settings file path
SETTINGS_FILE = CONFIG_DIR / "settings.json"


class Settings:
    """
    Manages application settings and configuration.
    
    This class handles loading, saving, and accessing user settings.
    It ensures settings persistence across application restarts.
    """
    
    def __init__(self):
        """Initialize settings with defaults and load user settings if available."""
        self._settings = DEFAULT_SETTINGS.copy()
        self._lock = threading.Lock() # Initialize lock
        self.load()
        
    def load(self) -> bool:
        """
        Load settings from the settings file.
        
        Returns:
            bool: True if settings were loaded successfully, False otherwise
        """
        if not SETTINGS_FILE.exists():
            logger.info("Settings file not found, using defaults")
            # Attempt to save defaults, no need to acquire lock yet as instance isn't shared
            self.save() # This save call will acquire the lock internally
            return False
            
        try:
            # Read requires the lock if another thread could be saving
            with self._lock:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f: # Add encoding
                    loaded_settings = json.load(f)
            
            # Update internal settings dict (lock not strictly needed here if update is atomic)
            # but locking ensures consistency if load/set happens concurrently
            with self._lock:
                 self._update_nested_dict(self._settings, loaded_settings)
                 logger.info("Settings loaded successfully")
                 return True
        except json.JSONDecodeError as e:
             logger.error(f"Error decoding settings file {SETTINGS_FILE}: {e}", exc_info=True)
             # Optionally: Backup corrupted file?
             return False
        except OSError as e:
             logger.error(f"Error reading settings file {SETTINGS_FILE}: {e}", exc_info=True)
             return False
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"Unexpected error loading settings from {SETTINGS_FILE}: {e}", exc_info=True)
            return False
    
    def save(self) -> bool:
        """
        Save current settings to the settings file.
        
        Returns:
            bool: True if settings were saved successfully, False otherwise
        """
        try:
            # Ensure save is atomic and thread-safe
            with self._lock:
                with open(SETTINGS_FILE, 'w', encoding='utf-8') as f: # Add encoding
                    json.dump(self._settings, f, indent=4)
                logger.info("Settings saved successfully")
                return True
        except TypeError as e:
             logger.error(f"Error saving settings: Data is not JSON serializable. {e}", exc_info=True)
             return False
        except OSError as e:
             logger.error(f"Error writing settings file {SETTINGS_FILE}: {e}", exc_info=True)
             return False
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"Unexpected error saving settings to {SETTINGS_FILE}: {e}", exc_info=True)
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value by key.
        
        Args:
            key: Setting key, can be nested with dots (e.g., 'audio.sample_rate')
            default: Default value if key not found
            
        Returns:
            The setting value or default if not found
        """
        # Reading might not strictly need a lock if writes are guaranteed atomic
        # but acquiring it ensures we read a consistent state during save/set operations.
        with self._lock:
            keys = key.split('.')
            value = self._settings
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
                    
            return value # Return a copy? Depends if mutable settings are expected
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value by key.
        
        Args:
            key: Setting key, can be nested with dots (e.g., 'audio.sample_rate')
            value: Value to set
        """
        with self._lock: # Protect modification
            keys = key.split('.')
            target = self._settings
            
            # Navigate to the innermost dict
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            
            # Set the value
            target[keys[-1]] = value
            logger.debug(f"Setting updated: {key} = {value}")
            # Consider deferring save() call to avoid disk I/O on every set
            # self.save() # Optionally save immediately
    
    def reset(self) -> None:
        """Reset all settings to default values."""
        with self._lock: # Protect reset and subsequent save
            self._settings = DEFAULT_SETTINGS.copy()
            logger.info("Settings reset to defaults, attempting save...")
            # save() call will acquire lock again internally, which is fine.
            self.save()
    
    def _update_nested_dict(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Update nested dictionary with values from another dictionary.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with new values
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._update_nested_dict(target[key], value)
            else:
                target[key] = value


# Create global settings instance
settings = Settings() 