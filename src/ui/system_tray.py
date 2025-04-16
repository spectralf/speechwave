"""
System tray integration for the SpeechWave application.
"""
import sys
from typing import Optional, Callable

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction, QPixmap
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication

from src.utils import get_logger, settings, get_resource_path
from src.ui.settings_window import SettingsWindow

logger = get_logger("system_tray")

# Define icon path relative to project root
DEFAULT_ICON_PATH = "assets/icon.png"

class SystemTrayManager:
    """
    Manages the system tray icon and menu for the application.
    
    This class handles the creation and management of the system tray icon,
    providing the user with access to application features and settings.
    """
    
    def __init__(self, app: QApplication):
        """
        Initialize the SystemTrayManager.
        
        Args:
            app: QApplication instance
        """
        self._app = app
        self._tray_icon: Optional[QSystemTrayIcon] = None
        self._menu: Optional[QMenu] = None
        self._settings_window: Optional[SettingsWindow] = None
        self._callbacks = {
            'settings': None,
            'exit': None
        }
        
        # Load icon using resource path
        try:
             self._default_icon = QIcon(str(get_resource_path(DEFAULT_ICON_PATH)))
        except FileNotFoundError as e:
             logger.error(f"Failed to load default icon: {e}. Using fallback.")
             self._default_icon = self._create_fallback_icon()
        except Exception as e:
            logger.error(f"Unexpected error loading icon: {e}. Using fallback.", exc_info=True)
            self._default_icon = self._create_fallback_icon()
        
        # Initialize tray
        self._init_tray()
        
        logger.info("SystemTrayManager initialized")
    
    def _init_tray(self) -> None:
        """Initialize the system tray icon and menu."""
        # Create the menu
        self._menu = QMenu()
        self._menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3D3D3D;
            }
            QMenu::item {
                padding: 5px 20px 5px 20px;
                border: 1px solid transparent;
            }
            QMenu::item:selected {
                background-color: #3D3D3D;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3D3D3D;
                margin: 5px 0px 5px 0px;
            }
        """)
        
        # Create actions
        settings_action = QAction("Settings", self._menu)
        settings_action.triggered.connect(self._on_settings)
        
        exit_action = QAction("Exit", self._menu)
        exit_action.triggered.connect(self._on_exit)
        
        # Add actions to menu
        self._menu.addAction(settings_action)
        self._menu.addSeparator()
        self._menu.addAction(exit_action)
        
        # Create and setup tray icon
        self._tray_icon = QSystemTrayIcon(self._default_icon)
        self._tray_icon.setToolTip("SpeechWave")
        self._tray_icon.setContextMenu(self._menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        
        # Show the tray icon
        self._tray_icon.show()
    
    def _create_fallback_icon(self) -> QIcon:
        """
        Create a fallback icon if the main icon cannot be loaded.
        
        Returns:
            QIcon: Fallback icon
        """
        # Create a simple dark-themed icon (64x64 pixels)
        pixmap = QPixmap(QSize(64, 64))
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # Return an icon from the pixmap
        return QIcon(pixmap)
    
    def set_callback(self, action: str, callback: Callable) -> None:
        """
        Set a callback function for a specific action.
        
        Args:
            action: Action name ('settings', 'exit')
            callback: Callback function
        """
        if action in self._callbacks:
            self._callbacks[action] = callback
        else:
            logger.warning(f"Attempted to set callback for unknown action: {action}")
    
    def show_message(self, title: str, message: str, icon_type: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information) -> None:
        """
        Show a notification message from the system tray.
        
        Args:
            title: Notification title
            message: Notification message
            icon_type: Notification icon type
        """
        if self._tray_icon and settings.get("ui.notifications", True):
            self._tray_icon.showMessage(title, message, icon_type)
    
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """
        Handle tray icon activation.
        
        Args:
            reason: Activation reason
        """
        # Open settings on left click (Trigger)
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            logger.debug("Tray icon clicked, opening settings")
            self._on_settings()
    
    def _on_settings(self) -> None:
        """Handle settings action: Show the settings window."""
        logger.debug("Settings menu item clicked or tray icon activated")
        # Create window if it doesn't exist or reuse if already open (can be configured)
        if self._settings_window is None or not self._settings_window.isVisible():
            self._settings_window = SettingsWindow()
            # Connect the window's signal to the callback provided by the main app
            if self._callbacks.get('settings'):
                 self._settings_window.hotkey_update_requested.connect(self._callbacks['settings'])
            else:
                 logger.warning("No 'settings' callback provided by main app to connect to SettingsWindow.")
            self._settings_window.show()
            self._settings_window.activateWindow() # Bring to front
            self._settings_window.raise_() # Ensure it's on top
        else:
            # If already visible, just bring it to the front
            self._settings_window.activateWindow()
            self._settings_window.raise_()
    
    def _on_exit(self) -> None:
        """Handle exit action."""
        logger.info("Exit menu item clicked")
        if self._callbacks['exit']:
            self._callbacks['exit']()
        else:
            # Default exit behavior
            QApplication.quit()
    
    def shutdown(self) -> None:
        """Clean up resources when the application exits."""
        if self._tray_icon:
            self._tray_icon.hide()
        logger.info("SystemTrayManager shutdown") 