"""
Hotkey management for the SpeechWave application using keyboard.hook for more robust detection.
"""
import threading
import time
from typing import Callable, Dict, Optional, Set

# Potential hidden import issues with packaging tools:
# PyInstaller might need hooks or --hidden-import for the keyboard library,
# especially its low-level OS-specific components.
import keyboard

from src.utils import get_logger, settings

logger = get_logger("hotkey_manager")


class HotkeyManager:
    """
    Manages global hotkey registration and detection using keyboard.hook.
    
    This approach monitors all keyboard events to manage hotkey states internally,
    aiming for more reliability than separate press/release handlers.
    """
    
    def __init__(self):
        """Initialize the HotkeyManager."""
        self._callbacks: Dict[str, Dict[str, Optional[Callable]]] = {} # hotkey_str -> {'press': cb, 'release': cb}
        self._hotkey_parts: Dict[str, Set[str]] = {} # hotkey_str -> set of normalized key names
        self._hotkey_states: Dict[str, bool] = {} # hotkey_str -> is_active (all keys pressed)
        self._pressed_keys: Set[str] = set() # Set of currently pressed normalized key names
        self._hooked = False
        self._lock = threading.Lock()
        
        # Get hotkey from settings (will be registered in start)
        self._record_hotkey_str = settings.get("hotkey.record")

        logger.info("HotkeyManager initialized (hook-based)")

    def _normalize_key_name(self, name: str) -> str:
        """ Normalizes key names for consistent tracking (e.g., 'left alt' -> 'alt'). """
        return keyboard.normalize_name(name)

    def _keyboard_event_callback(self, event: keyboard.KeyboardEvent):
        """ Handles events from keyboard.hook. """
        try:
            normalized_name = self._normalize_key_name(event.name)
        except KeyError:
             # Ignore unknown keys
            # logger.debug(f"Ignoring unknown key: {event.name}")
            return

        with self._lock:
            if event.event_type == keyboard.KEY_DOWN:
                self._pressed_keys.add(normalized_name)
                # logger.debug(f"Key down: {normalized_name}, Pressed set: {self._pressed_keys}")
            elif event.event_type == keyboard.KEY_UP:
                self._pressed_keys.discard(normalized_name)
                # logger.debug(f"Key up: {normalized_name}, Pressed set: {self._pressed_keys}")
            else:
                return # Should not happen with keyboard.hook

            # Check status of all registered hotkeys
            for hotkey_str, parts in self._hotkey_parts.items():
                all_parts_pressed = parts.issubset(self._pressed_keys)
                current_state = self._hotkey_states.get(hotkey_str, False)

                if all_parts_pressed and not current_state:
                    # Hotkey activated (transition from False to True)
                    self._hotkey_states[hotkey_str] = True
                    press_callback = self._callbacks.get(hotkey_str, {}).get('press')
                    if press_callback:
                        logger.debug(f"Hotkey {hotkey_str} activated. Calling on_press.")
                        threading.Thread(target=press_callback, daemon=True).start()
                elif not all_parts_pressed and current_state:
                    # Hotkey deactivated (transition from True to False)
                    self._hotkey_states[hotkey_str] = False
                    release_callback = self._callbacks.get(hotkey_str, {}).get('release')
                    if release_callback:
                        logger.debug(f"Hotkey {hotkey_str} deactivated. Calling on_release.")
                        threading.Thread(target=release_callback, daemon=True).start()

    def start(self) -> bool:
        """
        Start the keyboard hook listener.
        """
        if self._hooked:
            logger.warning("Hotkey listener already started.")
            return True
        
        logger.info("Starting keyboard hook...")
        try:
            # Use a lambda to avoid issues with method binding if needed, though direct should work
            # keyboard.hook(lambda e: self._keyboard_event_callback(e))
            keyboard.hook(self._keyboard_event_callback)
            self._hooked = True
            logger.info(f"Keyboard hook started. Waiting for hotkey actions (e.g., {self._record_hotkey_str})")
            return True
        except Exception as e:
            # Log a more specific message suggesting permission issues
            logger.error(f"Failed to start keyboard hook: {e}. This might be a permissions issue.", exc_info=True)
            self._hooked = False
            return False

    def stop(self) -> bool:
        """
        Stop the keyboard hook listener.
        """
        if not self._hooked:
            logger.warning("Hotkey listener not running.")
            return True
        
        logger.info("Stopping keyboard hook...")
        try:
            keyboard.unhook_all()
            self._hooked = False
             # Clear state on stop
            with self._lock:
                self._pressed_keys.clear()
                self._hotkey_states.clear()
            logger.info("Keyboard hook stopped and state cleared.")
            return True
        except Exception as e:
            logger.error(f"Failed to stop keyboard hook: {e}", exc_info=True)
            return False

    def register_hotkey(self, hotkey_str: str, on_press: Optional[Callable], on_release: Optional[Callable]) -> bool:
        """
        Register a hotkey combination and its callbacks.
        Args:
            hotkey_str: The hotkey string (e.g., 'alt+v').
            on_press: Callback for press action.
            on_release: Callback for release action.
        Returns:
            bool: True if registered successfully.
        """
        logger.debug(f"Registering hotkey: {hotkey_str}")
        with self._lock:
            try:
                # Parse and normalize hotkey parts
                parts = set(self._normalize_key_name(part.strip()) for part in hotkey_str.split('+'))
                if not parts:
                     logger.error(f"Cannot register empty hotkey: '{hotkey_str}'")
                     return False
                     
                self._hotkey_parts[hotkey_str] = parts
                self._callbacks[hotkey_str] = {'press': on_press, 'release': on_release}
                self._hotkey_states[hotkey_str] = False # Initial state is inactive
                logger.info(f"Registered hotkey '{hotkey_str}' with parts: {parts}")
                return True
            except Exception as e:
                logger.error(f"Failed to parse or register hotkey '{hotkey_str}': {e}", exc_info=True)
                # Clean up partial registration if failed
                self._hotkey_parts.pop(hotkey_str, None)
                self._callbacks.pop(hotkey_str, None)
                self._hotkey_states.pop(hotkey_str, None)
                return False

    def unregister_hotkey(self, hotkey_str: str) -> bool:
        """
        Unregister a previously registered hotkey.
        Args:
            hotkey_str: The hotkey string to unregister.
        Returns:
            bool: True if unregistered successfully.
        """
        logger.debug(f"Unregistering hotkey: {hotkey_str}")
        with self._lock:
            if hotkey_str in self._hotkey_parts:
                self._hotkey_parts.pop(hotkey_str, None)
                self._callbacks.pop(hotkey_str, None)
                self._hotkey_states.pop(hotkey_str, None)
                logger.info(f"Unregistered hotkey: {hotkey_str}")
                return True
            else:
                logger.warning(f"Attempted to unregister non-existent hotkey: {hotkey_str}")
                return False

    def update_record_hotkey(self, new_hotkey_str: str) -> bool:
        """
        Updates the main recording hotkey, re-registering callbacks if they exist.
        Args:
            new_hotkey_str: The new hotkey string.
        Returns:
            bool: True if update succeeded.
        """
        logger.info(f"Attempting to update record hotkey to: {new_hotkey_str}")
        old_hotkey_str = self._record_hotkey_str
        callbacks = self._callbacks.get(old_hotkey_str) # Get callbacks associated with the old hotkey

        if old_hotkey_str == new_hotkey_str:
            logger.info("New hotkey is the same as the old one. No update needed.")
            return True

        # Unregister the old hotkey
        if old_hotkey_str in self._hotkey_parts:
            self.unregister_hotkey(old_hotkey_str)

        # Register the new hotkey with the old callbacks (if they existed)
        success = False
        if callbacks:
            success = self.register_hotkey(new_hotkey_str, callbacks.get('press'), callbacks.get('release'))
        else:
            # This case should ideally not happen if setup_callbacks ran, but handle defensively
            logger.warning("No callbacks found for the old hotkey during update. Registering new hotkey without callbacks.")
            success = self.register_hotkey(new_hotkey_str, None, None)
            
        if success:
            self._record_hotkey_str = new_hotkey_str
            settings.set("hotkey.record", new_hotkey_str)
            settings.save()
            logger.info(f"Successfully updated record hotkey from '{old_hotkey_str}' to '{new_hotkey_str}'")
            return True
        else:
            logger.error(f"Failed to register new hotkey '{new_hotkey_str}' during update. Attempting to restore old hotkey '{old_hotkey_str}'.")
            # Attempt to re-register the old hotkey if the new one failed
            if callbacks:
                 self.register_hotkey(old_hotkey_str, callbacks.get('press'), callbacks.get('release'))
            return False

    def __del__(self):
        """ Ensure the hook is removed when the object is deleted. """
        self.stop()