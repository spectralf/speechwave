"""
Handles enabling/disabling application autostart on Windows using the registry.
"""

import sys
import os
import winreg
# Replace standard logging with application logger
# import logging 
from pathlib import Path
from src.utils.logger import get_logger # Import application logger

# Use application logger instance
logger = get_logger("autostart")

# Registry path for user startup programs
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
# Name of the registry key for this application
APP_NAME = "SpeechWave"

def get_executable_path() -> str:
    """Gets the path to the currently running executable."""
    # sys.executable is the reliable way to get the path, even when packaged
    return sys.executable

def is_autostart_enabled() -> bool:
    """Check if the application is configured to start automatically."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        # Use logger instead of print
        logger.error(f"Error checking autostart: {e}", exc_info=True) 
        return False

def enable_autostart() -> bool:
    """Enable autostart for the application."""
    try:
        executable_path = get_executable_path()
        if not executable_path:
            # Use logger instead of print
            logger.error("Error: Could not determine executable path for autostart.")
            return False

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE)
        # Ensure the path is quoted in case it contains spaces
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{executable_path}"')
        winreg.CloseKey(key)
        # Use logger instead of print
        logger.info(f"Autostart enabled for: {executable_path}")
        return True
    except PermissionError:
         # Use logger instead of print
         logger.error(f"Error enabling autostart: Permission denied. Try running as administrator?")
         return False
    except Exception as e:
        # Use logger instead of print
        logger.error(f"Error enabling autostart: {e}", exc_info=True)
        return False

def disable_autostart() -> bool:
    """Disable autostart for the application."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        # Use logger instead of print
        logger.info("Autostart disabled.")
        return True
    except FileNotFoundError:
        # Use logger instead of print
        logger.info("Autostart was not enabled, nothing to disable.")
        return True  # Not enabled is success in disabling
    except PermissionError:
         # Use logger instead of print
         logger.error(f"Error disabling autostart: Permission denied. Try running as administrator?")
         return False
    except Exception as e:
        # Use logger instead of print
        logger.error(f"Error disabling autostart: {e}", exc_info=True)
        return False

# Example usage (for testing)
# Use logger if running standalone for testing
# if __name__ == '__main__':
#     # Setup basic logging for standalone test
#     from src.utils.logger import setup_logger
#     setup_logger(log_level="DEBUG", log_to_file=False)
#     logger.info(f"Executable path: {get_executable_path()}")
#     if is_autostart_enabled():
#         logger.info("Autostart is currently enabled.")
#         # disable_autostart()
#     else:
#         logger.info("Autostart is currently disabled.")
#         # enable_autostart()

    # Example toggle
    # if not is_autostart_enabled():
    #     print("Enabling autostart...")
    #     enable_autostart()
    # else:
    #     print("Disabling autostart...")
    #     disable_autostart()
    # print(f"Autostart now enabled: {is_autostart_enabled()}") 