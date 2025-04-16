"""
Main application module for SpeechWave.
"""
import sys
import threading
import signal
import os # Added for file deletion
import time # Added for latency logging
from typing import Optional

from PyQt6.QtWidgets import QApplication

# Explicitly import setup_logger
from src.utils.logger import setup_logger 

from src.core import HotkeyManager, AudioRecorder, TextInserter
from src.whisper_transcriber import WhisperTranscriber
from src.ui import SystemTrayManager
from src.utils import get_logger, settings

# Don't get logger at module level here if setup hasn't run
# logger = get_logger("app")


class SpeechWaveApp:
    """
    Main application class for SpeechWave.
    
    This class coordinates all components of the application and manages
    the application lifecycle.
    """
    
    def __init__(self):
        """Initialize the SpeechWave application."""
        # --- Crucial: Set up logger FIRST --- 
        # Read log level from settings, defaulting if necessary
        # This assumes settings can be loaded before logging is fully set up
        # If settings load fails, it might use default log level
        log_level = settings.get("advanced.debug", False) and "DEBUG" or "INFO"
        log_to_file = True # Or read from settings if you add a setting for this
        setup_logger(log_level=log_level, log_to_file=log_to_file)
        # --- Logger setup complete --- 
        
        # Now it's safe to get the logger instance
        self.logger = get_logger("app") # Use self.logger or a local variable

        self._qt_app = QApplication(sys.argv)
        self._qt_app.setQuitOnLastWindowClosed(False)  # Don't quit when windows are closed
        
        # Initialize components
        self._hotkey_manager = HotkeyManager()
        self._audio_recorder = AudioRecorder()
        self._text_inserter = TextInserter()
        self._transcriber = WhisperTranscriber()
        self._system_tray = SystemTrayManager(self._qt_app)
        
        # Set up callbacks
        self._setup_callbacks()
        
        # State management
        self._recording = False # Tracks intent based on hotkey state
        self._state_lock = threading.Lock() # Lock for state changes
        
        self.logger.info("SpeechWave application initialized")
    
    def _setup_callbacks(self) -> None:
        """Set up callback functions between components."""
        # Set up system tray callbacks
        self._system_tray.set_callback('exit', self.shutdown)
        self._system_tray.set_callback('settings', self._handle_settings_update) # Pass method to handle update
        
        # Register initial hotkey
        self._register_current_hotkey()
    
    def _register_current_hotkey(self) -> None:
        """ Reads hotkey from settings and registers it with the manager. """
        # Unregister previous if exists (needed for updates)
        # TODO: Improve HotkeyManager to handle this more gracefully if needed
        # For now, assume only one hotkey registered via this mechanism
        current_hotkey = settings.get("hotkey.record")
        self.logger.debug(f"Attempting to register hotkey: {current_hotkey}")
        success = self._hotkey_manager.register_hotkey(
            current_hotkey,
            on_press=self._on_record_hotkey_press,
            on_release=self._on_record_hotkey_release
        )
        if not success:
             self.logger.error(f"Failed to register hotkey '{current_hotkey}' on startup/update.")
             # Optionally show error message via tray?
             # self._system_tray.show_message("Error", f"Failed to register hotkey: {current_hotkey}")

    def _handle_settings_update(self, new_hotkey: str):
        """ Callback received from SettingsWindow via SystemTrayManager when hotkey changes. """
        self.logger.info(f"Received request to update hotkey to: {new_hotkey}")
        # Use the HotkeyManager's update method
        success = self._hotkey_manager.update_record_hotkey(new_hotkey)
        if success:
            # Show confirmation (optional)
             self._system_tray.show_message("Settings Updated", f"Recording hotkey changed to {new_hotkey}")
             # Re-register with the new hotkey string (update_record_hotkey handles saving)
             # NOTE: update_record_hotkey internally calls unregister/register now.
             pass # No longer need to call _register_current_hotkey here
        else:
            self.logger.error(f"Failed to update hotkey in manager to {new_hotkey}")
            self._system_tray.show_message("Error", f"Failed to update hotkey to {new_hotkey}")
            # Optionally revert UI or settings?

    def _on_record_hotkey_press(self) -> None:
        """Handle record hotkey press event."""
        self.logger.debug("_on_record_hotkey_press invoked") # Log entry
        with self._state_lock:
            # Check both intent flag and actual recorder state
            if not self._recording and not self._audio_recorder.is_recording():
                self.logger.debug("Record hotkey pressed - initiating recording")
                self._recording = True # Set intent flag
                # Start recording in a separate thread
                threading.Thread(target=self._start_recording, daemon=True).start()
            else:
                self.logger.debug("Record hotkey pressed - already recording or starting, ignoring.")
    
    def _on_record_hotkey_release(self) -> None:
        """Handle record hotkey release event."""
        self.logger.debug("_on_record_hotkey_release invoked") # Log entry
        with self._state_lock:
             # Check both intent flag and actual recorder state
            if self._recording and self._audio_recorder.is_recording():
                self.logger.debug("Record hotkey released - initiating stop sequence")
                self._recording = False # Reset intent flag
                # Stop recording and process in a separate thread
                # Pass the release time to the processing thread
                release_time = time.monotonic()
                threading.Thread(target=self._stop_and_process_recording, args=(release_time,), daemon=True).start()
            else:
                 self.logger.debug("Record hotkey released - not recording or already stopping, ignoring.")
    
    def _start_recording(self) -> None:
        """Start audio recording. Should only be called when lock is held or state is certain."""
        success = self._audio_recorder.start_recording()
        if not success:
            self.logger.error("Failed to start recording in worker thread")
            # Reset the intent flag if starting failed
            with self._state_lock:
                self._recording = False 
        else:
            self.logger.info("Audio recording successfully started.")
    
    def _stop_and_process_recording(self, release_time: float) -> None:
        """Stop recording, transcribe audio, and insert text. Assumes recorder is active."""
        temp_audio_file: Optional[str] = None
        try:
            start_stop_time = time.monotonic()
            self.logger.debug("Stopping audio recording in worker thread...")
            temp_audio_file, _ = self._audio_recorder.stop_recording()
            stop_record_time = time.monotonic()
            self.logger.debug(f"Audio stopping took: {stop_record_time - start_stop_time:.3f}s")
            
            if not temp_audio_file:
                self.logger.error("No audio file produced by recorder.")
                return
            
            self.logger.info(f"Audio recorded to temporary file: {temp_audio_file}")
            
            # Trigger transcription, passing audio path via lambda
            # Pass the release time along to the final callback
            audio_path_for_callback = temp_audio_file 
            self.logger.debug(f"Requesting transcription for {audio_path_for_callback}...")
            self._transcriber.transcribe(
                audio_path_for_callback, 
                lambda result: self._handle_transcription_result(result, audio_path_for_callback, release_time)
            )
            self.logger.debug(f"Transcription request sent for {audio_path_for_callback}.")
            
        except Exception as e:
            self.logger.error(f"Error in _stop_and_process_recording: {e}", exc_info=True)
            if isinstance(e, TypeError):
                 if temp_audio_file:
                    self._cleanup_temp_file(temp_audio_file)
    
    def _handle_transcription_result(self, transcription: Optional[str], audio_file_path: str, release_time: float) -> None:
        """
        Callback function for handling transcription results.
        
        Args:
            transcription (Optional[str]): The transcribed text, or None if failed.
            audio_file_path (str): The path to the audio file that was transcribed.
            release_time (float): The time the hotkey was released (monotonic).
        """
        transcription_complete_time = time.monotonic()
        self.logger.debug(f"_handle_transcription_result invoked for {audio_file_path} (Result type: {type(transcription)})")
        
        insert_success = False
        try:
            if transcription is not None:
                if transcription: # Check if transcription is not empty
                    self.logger.info(f"Transcription successful: '{transcription[:50]}...'")
                    # Insert transcribed text
                    self.logger.debug("Inserting transcribed text...")
                    start_insert_time = time.monotonic()
                    insert_success = self._text_inserter.insert_text(transcription)
                    end_insert_time = time.monotonic()
                    if not insert_success:
                        self.logger.warning("Failed to insert text.")
                    else:
                         self.logger.debug(f"Text insertion took: {end_insert_time - start_insert_time:.3f}s")
                else:
                    self.logger.info("Transcription resulted in empty text.")
            else:
                self.logger.error("Transcription failed.")
        except Exception as e:
            self.logger.error(f"Error handling transcription result: {e}", exc_info=True)
        finally:
            # Always clean up the temporary audio file after handling the result
            self._cleanup_temp_file(audio_file_path)
            
            # Log total time from release to end of processing
            end_process_time = time.monotonic()
            total_time = end_process_time - release_time
            self.logger.info(f"Total processing time (release to end): {total_time:.3f}s")
    
    def _cleanup_temp_file(self, file_path: str) -> None:
        """ Safely delete the temporary audio file. """
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                self.logger.debug(f"Cleaned up temporary audio file: {file_path}")
        except OSError as e:
            self.logger.error(f"Error deleting temporary file {file_path}: {e}", exc_info=True)
    
    def start(self) -> int:
        """
        Start the application and enter the main event loop.
        
        Returns:
            int: Application exit code
        """
        try:
            # Start the hotkey manager
            if not self._hotkey_manager.start():
                self.logger.error("Failed to start hotkey manager")
                return 1
                
            # Set up signal handling for clean shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            
            # Show notification
            self._system_tray.show_message(
                "SpeechWave", 
                f"SpeechWave is running. Use {settings.get('hotkey.record')} to record."
            )
            
            self.logger.info("SpeechWave application started")
            
            # Enter Qt event loop
            return self._qt_app.exec()
        except Exception as e:
            self.logger.error(f"Error starting application: {e}")
            return 1
    
    def shutdown(self) -> None:
        """Perform a clean shutdown of the application."""
        self.logger.info("Shutting down SpeechWave")
        
        # Stop hotkey manager
        self._hotkey_manager.stop()
        
        # Unload the transcription model to free resources
        if self._transcriber:
            self._transcriber.unload_model()
        
        # Stop audio recorder if recording and cleanup resources
        if self._recording:
            self.logger.warning("Shutdown called while recording, stopping recording.")
            audio_file, _ = self._audio_recorder.stop_recording() # This calls _cleanup internally in recorder
            if audio_file:
                 # Ensure temp file gets deleted even on abrupt shutdown during recording
                 self._cleanup_temp_file(audio_file)
        else:
            # Explicitly clean up PyAudio resources if not actively recording
            self._audio_recorder._cleanup() 
        
        # Clean up system tray
        self._system_tray.shutdown()
        
        # Quit application
        self._qt_app.quit()
        
        self.logger.info("SpeechWave shutdown complete")
        # Force exit the process
        sys.exit(0)
    
    def _signal_handler(self, sig, frame) -> None:
        """Handle system signals for clean shutdown."""
        self.logger.info(f"Received signal {sig}, initiating shutdown...")
        self.shutdown()


def main() -> int:
    # No logger needed here usually, maybe just a print for entry
    print("Starting SpeechWave main...")
    try:
        app = SpeechWaveApp()
        exit_code = app.start()
    except Exception as e:
        # Minimal logging/printing if app fails very early
        print(f"CRITICAL ERROR during app initialization or start: {e}", file=sys.stderr)
        # Potentially try a very basic log attempt if possible
        try:
            from src.utils import get_logger
            logger = get_logger("main_critical")
            logger.critical(f"CRITICAL ERROR during app initialization or start: {e}", exc_info=True)
        except:
            pass # Avoid errors during critical error logging
        exit_code = 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main() 