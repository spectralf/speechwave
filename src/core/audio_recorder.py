"""
Audio recording functionality for the SpeechWave application.
"""
# Remove queue import
# import queue 
import threading
import wave
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, Tuple

import numpy as np
# Potential hidden import issues with packaging tools:
# PyInstaller might need hooks or --hidden-import for PyAudio
# and its underlying PortAudio library dependency.
import pyaudio

from src.utils import get_logger, settings

logger = get_logger("audio_recorder")


class AudioRecorder:
    """
    Manages audio recording from the microphone.
    
    This class handles microphone access, audio recording, and provides
    functionality to start and stop recording with proper resource management.
    """
    
    def __init__(self):
        """Initialize the AudioRecorder."""
        self._pyaudio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._recording: bool = False
        self._frames: list[bytes] = []
        # self._audio_data_queue = queue.Queue() # Removed
        self._temp_file: Optional[NamedTemporaryFile] = None
        # self._recording_thread = None # Removed
        self._lock = threading.Lock()
        
        # Audio settings from config
        self._sample_rate = settings.get("audio.sample_rate", 16000)
        self._channels = settings.get("audio.channels", 1)
        self._chunk_size = settings.get("audio.chunk_size", 1024)
        self._format = pyaudio.paInt16  # 16-bit audio
        
        logger.info("AudioRecorder initialized")
    
    def start_recording(self) -> bool:
        """
        Start recording audio from the microphone.
        
        Returns:
            bool: True if recording started successfully, False otherwise
        """
        # Acquire lock early to prevent race conditions with stop/cleanup
        with self._lock:
            if self._recording:
                logger.warning("Recording already in progress")
                return False
            
            try:
                # Initialize PyAudio if needed
                if not self._pyaudio:
                    logger.debug("Initializing PyAudio instance...")
                    self._pyaudio = pyaudio.PyAudio()
                    logger.debug("PyAudio instance initialized.")
                
                # Clear any previous recording data
                self._frames = []
                
                logger.debug(f"Opening audio stream: Rate={self._sample_rate}, Channels={self._channels}, Chunk={self._chunk_size}")
                # Open audio stream using callback
                self._stream = self._pyaudio.open(
                    format=self._format,
                    channels=self._channels,
                    rate=self._sample_rate,
                    input=True,
                    frames_per_buffer=self._chunk_size,
                    stream_callback=self._audio_callback # Callback handles frame collection
                )
                
                self._recording = True
                # No separate thread needed anymore
                # self._recording_thread = threading.Thread(target=self._record_thread)
                # self._recording_thread.daemon = True
                # self._recording_thread.start()
                
                logger.info("Started audio recording stream.")
                return True
                
            except Exception as e:
                logger.error(f"Failed to start recording: {e}", exc_info=True)
                # Ensure cleanup happens within the lock if start fails
                self._cleanup_internal()
                return False
    
    def stop_recording(self) -> Tuple[Optional[str], Optional[np.ndarray]]:
        """
        Stop recording audio and return the recorded audio data.
        
        Returns:
            Tuple[Optional[str], Optional[np.ndarray]]: A tuple containing the temp file path 
            and audio data as numpy array, or (None, None) if recording failed
        """
        temp_path: Optional[str] = None
        audio_data: Optional[np.ndarray] = None
        frames_to_save: list[bytes] = []

        try:
            with self._lock:
                if not self._recording:
                    logger.warning("Stop requested but not recording.")
                    return None, None
                
                logger.debug("Setting recording flag to False.")
                self._recording = False # Signal callback to stop adding frames
                
                # Wait briefly for any final callbacks potentially in progress
                # This is a small heuristic delay, might not be strictly necessary
                # depending on PyAudio callback guarantees, but can prevent rare races.
                # time.sleep(0.05) 

                # Stop and close the stream *before* processing frames
                if self._stream:
                     logger.debug("Stopping and closing audio stream...")
                     if self._stream.is_active(): # Check if active before stopping
                         self._stream.stop_stream()
                     self._stream.close()
                     self._stream = None
                     logger.debug("Audio stream stopped and closed.")
                else:
                    logger.warning("Stop recording called but stream was already None.")

                # Make a copy of frames collected *while holding the lock*
                frames_to_save = self._frames.copy()
                self._frames = [] # Clear internal buffer immediately

            # --- Process frames outside the lock --- 
            if not frames_to_save:
                logger.warning("Recording stopped, but no audio frames were captured.")
                return None, None
                
            logger.debug(f"Processing {len(frames_to_save)} captured audio frames.")
            # Create a temporary file for the recorded audio
            # Ensure temp file handle is closed properly after writing
            with NamedTemporaryFile(delete=False, suffix=".wav") as temp_f:
                temp_path = temp_f.name
                # Save the recorded audio to the temporary file
                with wave.open(temp_f, 'wb') as wf:
                    wf.setnchannels(self._channels)
                    # Ensure PyAudio instance exists for get_sample_size
                    pa_instance = self._pyaudio if self._pyaudio else pyaudio.PyAudio()
                    sample_width = pa_instance.get_sample_size(self._format)
                    if not self._pyaudio: # Terminate temporary instance if created
                        pa_instance.terminate()
                        
                    wf.setsampwidth(sample_width)
                    wf.setframerate(self._sample_rate)
                    wf.writeframes(b''.join(frames_to_save))
                
            # Convert frames to numpy array for processing (optional, if needed by caller)
            audio_data = np.frombuffer(b''.join(frames_to_save), dtype=np.int16)
                
            logger.info(f"Stopped recording, saved to {temp_path}")
            return temp_path, audio_data
            
        except Exception as e:
            logger.error(f"Failed during stop_recording or save process: {e}", exc_info=True)
            # Attempt to clean up partially created temp file if path exists
            if temp_path and Path(temp_path).exists():
                try:
                     Path(temp_path).unlink()
                     logger.info(f"Cleaned up partially created temp file: {temp_path}")
                except OSError as unlink_e:
                     logger.error(f"Error cleaning up temp file {temp_path}: {unlink_e}")
            return None, None
        finally:
            # Ensure PyAudio is terminated *after* processing frames is complete or failed
            with self._lock:
                self._cleanup_internal()
    
    def is_recording(self) -> bool:
        """
        Check if recording is in progress.
        
        Returns:
            bool: True if recording, False otherwise
        """
        with self._lock:
            return self._recording
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        Callback function for PyAudio stream.
        Appends data directly to the frames list, protected by the lock.
        """
        # Use lock to safely append frames and check recording status
        with self._lock:
            if self._recording:
                self._frames.append(in_data)
                return (None, pyaudio.paContinue) # Indicate continue
            else:
                # If self._recording is False, tell PyAudio we're done
                return (None, pyaudio.paComplete) # Indicate complete
    
    # Removed _record_thread as it's no longer needed
    # def _record_thread(self):
    #     ...
    
    # Renamed to _cleanup_internal to avoid conflict with __del__ logic
    def _cleanup_internal(self):
        """Internal method to clean up PyAudio resources. Assumes lock MAY NOT be held."""
        logger.debug("Entering internal cleanup...")
        # Stream cleanup
        stream = self._stream
        if stream:
            logger.debug(f"Stream exists. Active: {stream.is_active()}")
            try:
                if stream.is_active():
                    stream.stop_stream()
                    logger.debug("Stopped active stream.")
                stream.close()
                logger.debug("Closed stream.")
            except Exception as e:
                 logger.error(f"Exception during stream cleanup: {e}", exc_info=True)
            finally:
                 self._stream = None
        else:
            logger.debug("Stream is None, skipping stream cleanup.")
            
        # PyAudio instance cleanup
        pa_instance = self._pyaudio
        if pa_instance:
            logger.debug("PyAudio instance exists. Terminating...")
            try:
                 pa_instance.terminate()
                 logger.debug("PyAudio terminated.")
            except Exception as e:
                 logger.error(f"Exception during PyAudio termination: {e}", exc_info=True)
            finally:
                 self._pyaudio = None
        else:
            logger.debug("PyAudio instance is None, skipping termination.")
            
        # Reset state flags (redundant if lock is held, but safe)
        self._recording = False
        self._frames = []
        logger.debug("Internal audio resource cleanup finished.")
    
    def update_settings(self):
        """Update audio settings from the application settings."""
        self._sample_rate = settings.get("audio.sample_rate", 16000)
        self._channels = settings.get("audio.channels", 1)
        self._chunk_size = settings.get("audio.chunk_size", 1024)
        logger.debug("Audio settings updated")
    
    def get_available_devices(self) -> list:
        """
        Get a list of available audio input devices.
        
        Returns:
            list: List of device information dictionaries
        """
        devices = []
        try:
            temp_pyaudio = pyaudio.PyAudio()
            for i in range(temp_pyaudio.get_device_count()):
                device_info = temp_pyaudio.get_device_info_by_index(i)
                if device_info.get('maxInputChannels') > 0:
                    devices.append({
                        'index': i,
                        'name': device_info.get('name'),
                        'channels': device_info.get('maxInputChannels')
                    })
            temp_pyaudio.terminate()
        except Exception as e:
            logger.error(f"Failed to get audio devices: {e}")
        
        return devices
    
    def __del__(self):
        """Ensure PyAudio resources are cleaned up when object is destroyed."""
        logger.debug("AudioRecorder __del__ called. Initiating cleanup.")
        # Call internal cleanup, acquiring lock if necessary
        with self._lock:
            self._cleanup_internal()
        
        # Remove temp file cleanup from here - responsibility moved to app.py
        # if self._temp_file:
        #     try:
        #         temp_path = Path(self._temp_file.name)
        #         if temp_path.exists():
        #             temp_path.unlink()
        #     except Exception as e:
        #         logger.error(f"Failed to remove temporary file in __del__: {e}") 