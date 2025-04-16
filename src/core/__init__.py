"""
Core modules for the SpeechWave application.
"""
from .hotkey_manager import HotkeyManager
from .audio_recorder import AudioRecorder
from .text_inserter import TextInserter

__all__ = ['HotkeyManager', 'AudioRecorder', 'TextInserter']