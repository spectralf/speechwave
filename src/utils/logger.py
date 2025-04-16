"""
Logger configuration for the SpeechWave application.
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

# --- Path Determination --- 
# Determine base directory for logs
def get_log_directory() -> Path:
    """Determines the appropriate directory for storing log files."""
    app_data = os.getenv("APPDATA")
    if app_data:
        log_dir = Path(app_data) / "SpeechWave" / "logs"
    else:
        # Fallback for non-Windows or if APPDATA is not set
        log_dir = Path.home() / ".speechwave" / "logs"
    return log_dir

LOG_DIR = get_log_directory()

# --- Initial Logger Configuration (Minimal for Setup Errors) --- 
# Configure a basic stderr logger initially to catch early errors during setup
_initial_stderr_handler_id = None
if sys.stderr: # Check if stderr exists
    _initial_stderr_handler_id = logger.add(
        sys.stderr,
        level="INFO",
        format="<level>{level: <8}</level> | <cyan>LOGGER_SETUP</cyan> | <level>{message}</level>"
    )

# Attempt to create log directory early, logging errors
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if _initial_stderr_handler_id: # Only log debug if handler was added
        logger.debug(f"Ensured log directory exists: {LOG_DIR}")
except OSError as e:
    # Use print as fallback if initial logger failed
    print(f"CRITICAL: Error creating log directory {LOG_DIR}: {e}. File logging will likely fail.", file=sys.stderr if sys.stderr else sys.stdout)
    if _initial_stderr_handler_id:
        logger.critical(f"CRITICAL: Error creating log directory {LOG_DIR}: {e}. File logging will likely fail.", exc_info=True)

# --- Main Logger Setup Function --- 
def setup_logger(log_level: str = "INFO", log_to_file: bool = True):
    """
    Configure the main logger sinks for the application.
    Should be called once explicitly at application startup.
    
    Args:
        log_level: Minimum log level to record.
        log_to_file: Whether to save logs to file.
    """
    # Remove the initial stderr handler (if it was added) and any other previous handlers
    logger.remove()
    
    # Add stdout logger with standard format if stdout exists
    if sys.stdout: # Check if stdout exists
        try:
            logger.add(
                sys.stdout,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                level=log_level.upper(), # Ensure level is uppercase
                enqueue=True # Make logging from threads safe
            )
        except Exception as e:
            # If even stdout fails, print as last resort
            print(f"CRITICAL: Failed to add stdout logger: {e}", file=sys.stderr if sys.stderr else None) # Avoid printing if both fail
    else:
        # If stdout doesn't exist, log this fact to the file logger later if possible
        # (Can't log it now as file logger isn't set up yet)
        pass 

    # Add file logger if enabled
    if log_to_file:
        try:
            # Basic validation
            if not LOG_DIR or not isinstance(LOG_DIR, Path):
                 # Log critical error if possible, otherwise print
                 logger.critical(f"CRITICAL: LOG_DIR is invalid ({LOG_DIR}). Cannot configure file logging.")
                 print(f"CRITICAL: LOG_DIR is invalid ({LOG_DIR}). Cannot configure file logging.", file=sys.stderr)
            else:
                # Construct log file path
                log_file_path = LOG_DIR / f"speechwave_{datetime.now().strftime('%Y-%m-%d')}.log"
                
                logger.add(
                    log_file_path,
                    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                    rotation="10 MB",
                    retention="7 days",
                    level=log_level.upper(), # Ensure level is uppercase
                    encoding='utf-8',
                    enqueue=True # Make logging from threads safe
                )
                # Log success message using the now configured logger
                logger.info(f"File logging enabled to: {log_file_path}")

        except Exception as e:
             # Log critical error if possible, otherwise print
             log_path_str = str(LOG_DIR) if LOG_DIR else "Unknown"
             logger.critical(f"CRITICAL: Error adding file logger sink to {log_path_str}: {e}", exc_info=True)
             print(f"CRITICAL: Error adding file logger sink to {log_path_str}: {e}", file=sys.stderr)

    logger.info(f"Logger setup complete. Level: {log_level.upper()}, File logging: {log_to_file}")

# --- Logger Retrieval Function --- 
def get_logger(name: Optional[str] = None):
    """
    Get a configured logger instance, optionally binding a name.
    
    Args:
        name: Optional name for the logger module/component.
        
    Returns:
        Configured logger instance.
    """
    # Loguru's logger is global, just bind the name if provided for context
    if name:
        return logger.bind(name=name)
    else:
        return logger 