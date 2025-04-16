import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QMessageBox, QDialog,
    QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.utils import get_logger, settings
from src.utils.autostart import is_autostart_enabled, enable_autostart, disable_autostart

logger = get_logger("settings_window")

# Basic dark theme stylesheet (can be expanded)
DARK_STYLESHEET = """
QWidget {
    background-color: #2b2b2b;
    color: #f0f0f0;
    font-size: 10pt;
}
QPushButton {
    background-color: #3c3f41;
    border: 1px solid #555;
    padding: 5px 10px;
    border-radius: 3px;
}
QPushButton:hover {
    background-color: #4f5254;
}
QPushButton:pressed {
    background-color: #5a5e60;
}
QLineEdit {
    background-color: #3c3f41;
    border: 1px solid #555;
    padding: 5px;
    border-radius: 3px;
}
QLabel {
    padding-top: 5px;
}
"""

class SettingsWindow(QDialog):
    """
    Settings dialog for the SpeechWave application.
    """
    # Signal to request hotkey update in the main application
    hotkey_update_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SpeechWave Settings")
        self.setMinimumWidth(400)
        self.setStyleSheet(DARK_STYLESHEET)
        self.setModal(True) # Block interaction with other windows

        self._current_hotkey = settings.get("hotkey.record", "alt+v") # Default if not found
        self._new_hotkey = self._current_hotkey
        self._is_recording_hotkey = False

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Initialize the user interface elements."""
        layout = QVBoxLayout(self)

        # --- Hotkey Section ---
        hotkey_group_layout = QVBoxLayout() # Group related controls
        hotkey_layout = QHBoxLayout()
        hotkey_label = QLabel("Record Hotkey:")
        self.hotkey_input = QLineEdit(self._current_hotkey)
        self.hotkey_input.setReadOnly(True) # Display only, set via button
        self.set_hotkey_button = QPushButton("Set New Hotkey")

        hotkey_layout.addWidget(hotkey_label)
        hotkey_layout.addWidget(self.hotkey_input)
        hotkey_layout.addWidget(self.set_hotkey_button)
        hotkey_group_layout.addLayout(hotkey_layout)
        layout.addLayout(hotkey_group_layout)

        # --- Autostart Section ---
        autostart_layout = QHBoxLayout()
        self.autostart_checkbox = QCheckBox("Start SpeechWave automatically on login")
        autostart_layout.addWidget(self.autostart_checkbox)
        layout.addLayout(autostart_layout)
        # Set initial state from registry
        try:
             current_autostart_state = is_autostart_enabled()
             self.autostart_checkbox.setChecked(current_autostart_state)
             logger.debug(f"Initial autostart state: {current_autostart_state}")
        except Exception as e:
             logger.error(f"Failed to get initial autostart state: {e}", exc_info=True)
             self.autostart_checkbox.setEnabled(False) # Disable if state cannot be determined
             self.autostart_checkbox.setToolTip("Could not read autostart setting.")

        layout.addStretch() # Add space before buttons

        # --- Buttons Section ---
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        button_layout.addStretch() # Push buttons to the right
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connect UI element signals to slots."""
        self.save_button.clicked.connect(self._save_settings)
        self.cancel_button.clicked.connect(self.reject) # QDialog's reject slot closes it
        self.set_hotkey_button.clicked.connect(self._toggle_hotkey_recording)

    def _toggle_hotkey_recording(self):
        """Handle the 'Set New Hotkey' button click."""
        if not self._is_recording_hotkey:
            logger.debug("Starting hotkey recording...")
            self._is_recording_hotkey = True
            self.set_hotkey_button.setText("Recording... (Press combination)")
            self.hotkey_input.setReadOnly(False)
            self.hotkey_input.setText("Press new combination...")
            self.hotkey_input.selectAll()
             # Temporarily grab keyboard focus to capture input
            self.grabKeyboard() 
            # TODO: Implement actual keyboard hook here
            # For now, we just enable the line edit and wait for manual entry or next step
        else:
            self._stop_hotkey_recording() # Allow canceling if needed
            # For now, manually setting it back if user clicks again
            self.hotkey_input.setText(self._new_hotkey) 


    def _stop_hotkey_recording(self, recorded_hotkey: str | None = None):
        """Stop the hotkey recording state."""
        logger.debug(f"Stopping hotkey recording. Recorded: {recorded_hotkey}")
        self.releaseKeyboard() # Release keyboard focus
        self._is_recording_hotkey = False
        self.set_hotkey_button.setText("Set New Hotkey")
        self.hotkey_input.setReadOnly(True)
        if recorded_hotkey:
             self._new_hotkey = recorded_hotkey.lower() # Normalize
             self.hotkey_input.setText(self._new_hotkey)
        else:
             # If recording stopped without success, revert display
             self.hotkey_input.setText(self._new_hotkey)

    # Override keyPressEvent to capture hotkey while recording
    def keyPressEvent(self, event):
        if self._is_recording_hotkey:
            key = event.key()
            modifiers = event.modifiers()
            
            # Ignore modifier-only presses
            if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
                return

            mod_str = ""
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                mod_str += "ctrl+"
            if modifiers & Qt.KeyboardModifier.AltModifier:
                mod_str += "alt+"
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                mod_str += "shift+"
            if modifiers & Qt.KeyboardModifier.MetaModifier: # Windows/Command key
                mod_str += "win+" # Use 'win' for consistency with 'keyboard' library
                
            key_text = event.text()
            # Handle special keys that don't produce text
            if not key_text or key_text.isspace():
                 key_enum = Qt.Key(key)
                 key_text = key_enum.name.replace("Key_", "").lower() # e.g., "Key_F1" -> "f1"

            if key_text:
                new_combination = f"{mod_str}{key_text.lower()}"
                logger.info(f"Hotkey combination captured: {new_combination}")
                self._stop_hotkey_recording(recorded_hotkey=new_combination)
            
            event.accept() # Prevent further processing
        else:
            super().keyPressEvent(event) # Default handling if not recording

    def _save_settings(self):
        """Save the settings and close the dialog."""
        try:
            # --- Hotkey Saving --- 
            # Validate hotkey?
            if not self._new_hotkey or self._new_hotkey == "press new combination...":
                 QMessageBox.warning(self, "Invalid Hotkey", "Please set a valid hotkey combination.")
                 return

            hotkey_changed = self._new_hotkey != self._current_hotkey
            if hotkey_changed:
                 settings.set("hotkey.record", self._new_hotkey)
                 logger.info(f"Hotkey setting updated to: {self._new_hotkey}")
            
            # --- Autostart Saving --- 
            desired_autostart_state = self.autostart_checkbox.isChecked()
            current_autostart_state = is_autostart_enabled() # Re-check just before saving
            autostart_changed = desired_autostart_state != current_autostart_state

            if autostart_changed:
                success = False
                if desired_autostart_state:
                    logger.info("Attempting to enable autostart...")
                    success = enable_autostart()
                else:
                    logger.info("Attempting to disable autostart...")
                    success = disable_autostart()
                
                if not success:
                     # Show specific error message
                     QMessageBox.critical(self, "Autostart Error", 
                                          "Failed to update the autostart setting.\n"
                                          "This might require administrator privileges.")
                     # Optionally revert the checkbox state if saving failed?
                     # self.autostart_checkbox.setChecked(current_autostart_state)
                     # We don't exit here, allow user to save other settings if possible
                else:
                     logger.info(f"Autostart setting changed to: {desired_autostart_state}")
                     # Also save this preference to our own settings file
                     settings.set("autostart.enabled", desired_autostart_state)
                     #pass # For now, just manage registry

            # --- Final Steps --- 
            settings.save() # Save any changes made to the settings object (e.g., hotkey)
            logger.info("Settings saved.")

            # Emit signal only if hotkey actually changed and was saved
            if hotkey_changed:
                self.hotkey_update_requested.emit(self._new_hotkey)
                
            self.accept() # QDialog's accept slot closes it

        except Exception as e:
            logger.error(f"Failed to save settings: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

# Example usage (for testing)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Make settings accessible for standalone test
    from src.utils import settings
    settings.load() # Load existing or default

    window = SettingsWindow()
    
    # Example of connecting the signal for testing
    def handle_update(new_key):
        print(f"Main app received hotkey update request: {new_key}")
        
    window.hotkey_update_requested.connect(handle_update)
    
    window.show()
    sys.exit(app.exec()) 