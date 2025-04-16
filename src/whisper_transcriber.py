import threading
# Remove standard logging import
# import logging 
import os
from faster_whisper import WhisperModel
from typing import Optional, Callable

# Import the application's logger
from src.utils.logger import get_logger
# Import settings object
from src.utils import settings

# Configure logging using the application's logger
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = get_logger("whisper_transcriber") # Get logger instance

# Potential hidden import issues with packaging tools:
# PyInstaller might need hooks or --hidden-import for faster_whisper and its dependencies (like torch, transformers if used internally).

class WhisperTranscriber:
    """
    Handles audio transcription using the Faster Whisper model with deferred loading.
    """
    def __init__(self):
        """
        Initializes the WhisperTranscriber settings by reading from the settings file,
        but defers model loading.
        """
        # Read configuration from settings
        self.model_size = settings.get("transcription.model", "small")
        self.device = settings.get("transcription.device", "cpu")
        self.compute_type = settings.get("transcription.compute_type", "int8")
        self.beam_size = settings.get("transcription.beam_size", 5)
        self.language = settings.get("transcription.language", None) # None allows auto-detect
        
        self.model: Optional[WhisperModel] = None
        self._model_lock = threading.Lock()
        self._load_attempted = False
        logger.info(f"WhisperTranscriber initialized with settings: model={self.model_size}, device={self.device}, compute={self.compute_type}, beam={self.beam_size}, lang={self.language or 'auto'}")

    def unload_model(self):
        """Explicitly releases the Whisper model and associated resources."""
        with self._model_lock:
            if self.model is not None:
                logger.info(f"Unloading Whisper model: {self.model_size}...")
                # FasterWhisper might not have an explicit unload, 
                # relying on garbage collection. Setting to None removes 
                # our reference, allowing GC to potentially reclaim memory sooner.
                # If using GPU, check if specific cleanup (like torch.cuda.empty_cache()) 
                # would be beneficial, though it might not be needed here.
                self.model = None 
                self._load_attempted = False # Allow reloading later if needed
                logger.info("Whisper model unloaded.")
            else:
                logger.debug("Unload called, but model was not loaded.")

    def _ensure_model_loaded(self) -> bool:
        """Loads the Faster Whisper model if not already loaded. Returns True on success."""
        with self._model_lock:
            if self.model is not None:
                return True
            if self._load_attempted:
                 # Avoid repeated load attempts if the first one failed
                logger.error("Previous model load attempt failed. Cannot transcribe.")
                return False
            
            self._load_attempted = True # Mark that we are attempting to load
            try:
                logger.info(f"Loading Faster Whisper model: {self.model_size} ({self.compute_type} on {self.device}) ...")
                # faster-whisper handles download/caching internally
                self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
                logger.info(f"Faster Whisper model '{self.model_size}' loaded successfully.")
                return True
            except Exception as e:
                logger.error(f"Failed to load Whisper model '{self.model_size}': {e}", exc_info=True)
                self.model = None # Ensure model is None on failure
                return False

    def transcribe(self, audio_path: str, callback: Callable[[Optional[str]], None]):
        """
        Transcribes the audio file in a separate thread after ensuring the model is loaded.

        Args:
            audio_path (str): The path to the audio file to transcribe.
            callback (Callable[[Optional[str]], None]): Function to call with the transcription result
                                                       (string) or None if an error occurred.
        """
        # Ensure model is loaded before starting transcription thread
        logger.debug(f"Transcribe called for: {audio_path}")
        if not self._ensure_model_loaded():
            logger.error("Transcription cancelled: Model is not available.")
            callback(None)
            return
        
        # Check audio path validity after confirming model is ready
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}. Cannot transcribe.")
            callback(None)
            return

        # Model is loaded and audio exists, proceed with transcription in a thread
        logger.debug(f"Starting transcription thread for: {audio_path}")
        thread = threading.Thread(target=self._transcribe_thread, args=(audio_path, callback), daemon=True)
        thread.start()

    def _transcribe_thread(self, audio_path: str, callback: Callable[[Optional[str]], None]):
        """
        Internal method to run transcription in a thread.

        Args:
            audio_path (str): Path to the audio file.
            callback (Callable[[Optional[str]], None]): Callback function for the result.
        """
        logger.debug(f"Transcription thread ({threading.current_thread().name}) started for: {audio_path}")
        try:
            # Model is guaranteed to be loaded here by the transcribe method
            logger.info(f"Starting actual transcription process for: {audio_path}")
            # Pass language and beam_size from settings
            segments, info = self.model.transcribe(
                audio_path, 
                beam_size=self.beam_size, 
                language=self.language # Pass None for auto-detect, or specific lang code
            )

            detected_lang = info.language
            lang_prob = info.language_probability
            logger.info(f"Detected language '{detected_lang}' with probability {lang_prob:.2f}")

            # Consider filtering based on language probability if needed
            # if lang_prob < 0.5:
            #    logger.warning(f"Low language detection confidence ({lang_prob:.2f}). Transcription might be inaccurate.")

            full_text = "".join([segment.text for segment in segments]).strip()
            logger.info(f"Transcription complete for: {audio_path} (Length: {len(full_text)} chars)")
            logger.debug(f"Invoking callback for: {audio_path}")
            callback(full_text)

        except Exception as e:
            logger.error(f"Error during transcription for {audio_path}: {e}", exc_info=True)
            logger.debug(f"Invoking callback with None (error) for: {audio_path}")
            callback(None) # Signal error to the callback
        finally:
            # Clean up the temporary audio file? 
            # Decision: Let the caller (AudioRecorder/MainApp) handle cleanup 
            # as WhisperTranscriber shouldn't manage files it didn't create.
            logger.debug(f"Transcription thread ({threading.current_thread().name}) finished for: {audio_path}")
            pass 