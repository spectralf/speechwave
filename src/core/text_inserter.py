"""
Text insertion functionality for the SpeechWave application.
"""
import time
from typing import Optional

# Potential hidden import issues with packaging tools:
# PyInstaller might need hooks or --hidden-import for pyautogui and its platform-specific dependencies.
import pyautogui

from src.utils import get_logger, settings

logger = get_logger("text_inserter")


class TextInserter:
    """
    Handles text insertion at the current cursor position.
    
    This class provides functionality to insert transcribed text
    at the current cursor position via simulated keyboard input.
    """
    
    def __init__(self):
        """Initialize the TextInserter."""
        # Get insertion delay from settings
        self._insertion_delay = settings.get("advanced.insertion_delay", 0.0)
        
        logger.info("TextInserter initialized")
    
    def insert_text(self, text: str) -> bool:
        """
        Insert text at the current cursor position, followed by a space.
        
        Args:
            text: Text to insert
            
        Returns:
            bool: True if insertion was successful, False otherwise
        """
        if not text:
            logger.warning("No text to insert")
            return False
            
        try:
            # Add a space after the transcribed text if setting is enabled
            text_to_insert = text
            if settings.get("text_insertion.add_space_after", True):
                 text_to_insert += " "
            
            # Optional delay before insertion (can help with certain applications)
            if self._insertion_delay > 0:
                time.sleep(self._insertion_delay)
                
            # Type the text at cursor position 
            pyautogui.write(text_to_insert, interval=0.01)  # Small interval to prevent overwhelming the system
            
            logger.debug(f"Inserted text: {text_to_insert[:30]}{'...' if len(text_to_insert) > 30 else ''}")
            return True
        except Exception as e:
            # Log with traceback and suggest potential permission issues
            logger.error(f"Failed to insert text: {e}. This could be due to permissions or the target application.", exc_info=True)
            return False
    
    def insert_text_with_formatting(self, text: str, capitalize_sentences: bool = True) -> bool:
        """
        Insert text with basic formatting applied.
        
        Args:
            text: Text to insert
            capitalize_sentences: Whether to capitalize the first letter of each sentence
            
        Returns:
            bool: True if insertion was successful, False otherwise
        """
        if not text:
            logger.warning("No text to insert")
            return False
            
        try:
            # Apply formatting
            if capitalize_sentences:
                text = self._capitalize_sentences(text)
                
            # Insert the formatted text
            return self.insert_text(text)
        except Exception as e:
            logger.error(f"Failed to insert formatted text: {e}")
            return False
    
    def _capitalize_sentences(self, text: str) -> str:
        """
        Capitalize the first letter of each sentence in the text.
        
        Args:
            text: Text to format
            
        Returns:
            str: Formatted text
        """
        # Split text into sentences
        sentences = []
        current = []
        
        for char in text:
            current.append(char)
            if char in ['.', '!', '?'] and len(current) > 0:
                sentences.append(''.join(current))
                current = []
                
        if current:
            sentences.append(''.join(current))
            
        # Capitalize first letter of each sentence
        formatted_sentences = []
        for sentence in sentences:
            trimmed = sentence.lstrip()
            if trimmed:
                formatted_sentences.append(sentence[:len(sentence)-len(trimmed)] + trimmed[0].upper() + trimmed[1:])
            else:
                formatted_sentences.append(sentence)
                
        return ''.join(formatted_sentences)
    
    def update_settings(self) -> None:
        """Update settings from the application configuration."""
        self._insertion_delay = settings.get("advanced.insertion_delay", 0.0)
        logger.debug(f"Updated insertion delay to {self._insertion_delay}s") 