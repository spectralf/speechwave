# SpeechWave: Voice Transcription Application

## Project Overview

SpeechWave is a minimal speech-to-text (STT) application inspired by Wispr Flow, designed to allow users to transcribe their voice in real-time and have it typed at their cursor position. Users can hold a configurable hotkey to record their speech, and upon release, the transcribed text will be inserted wherever their cursor is currently positioned across any application.

## Core Requirements

### Functionality
- **Hotkey Recording**: Users can press and hold a configurable hotkey to record audio
- **Instant Transcription**: Upon release of the hotkey, audio is transcribed using Whisper small model
- **Text Insertion**: Transcribed text is automatically typed at the current cursor position
- **System-Wide Operation**: Works across all applications where text input is accepted
- **System Tray Integration**: Application runs in the background with system tray presence

### User Experience
- **Minimal Interface**: Clean, unobtrusive design that doesn't interfere with workflow
- **No Visual Recording Indicator**: As specified, no visual indication of recording is needed
- **Dark Mode**: Interface follows a dark mode, post-modern sleek design aesthetic
- **Settings Access**: Easy access to application settings via system tray icon

## Technical Specifications

### Technology Stack
- **Programming Language**: Python 3.10+
- **GUI Framework**: PyQt6
- **Speech Recognition**: Whisper small model
- **Audio Processing**: PyAudio/sounddevice for audio capture
- **Global Hotkey**: keyboard/pynput for hotkey detection across applications
- **Text Insertion**: pyautogui/keyboard for simulating keystrokes

### Architecture

The application will follow a modular architecture with clear separation of concerns:

1. **Hotkey Manager**: Responsible for registering and detecting global hotkeys
2. **Audio Recorder**: Handles microphone access and recording functionality
3. **Transcription Engine**: Integrates with Whisper model to convert speech to text
4. **Text Inserter**: Simulates keyboard input to insert text at the current cursor position
5. **Settings Manager**: Manages user configuration and preferences
6. **System Tray Interface**: Provides user access to the application while running in background

### Data Flow
1. User presses and holds the configured hotkey
2. Application begins recording audio from default microphone
3. Upon hotkey release, recording stops
4. Recorded audio is sent to Whisper model for transcription
5. Transcribed text is processed (formatting, etc. if configured)
6. Text is inserted at the current cursor position via simulated keyboard input

## Constraints and Limitations

- **Platform Compatibility**: Initially targeting Windows 10/11
- **Performance Considerations**: 
  - Minimize delay between hotkey release and text insertion
  - Optimize Whisper model loading to reduce memory footprint
  - Ensure minimal CPU usage when idle
- **Security and Privacy**:
  - Audio processing performed locally (no data sent to external services)
  - No logging of transcribed content
  - Transparently communicate microphone access requirements

## Future Expansion Possibilities

While not part of the initial implementation, the following features could be considered for future development:

- Customizable text formatting options
- Support for additional platforms (macOS, Linux)
- Transcription history and management
- Multiple language support
- Custom Whisper model options (tiny, base, large)

## Success Criteria

The application will be considered successful if it:

1. Accurately transcribes speech with minimal delay
2. Reliably inserts text at the cursor position
3. Functions across common applications (text editors, browsers, messaging apps)
4. Maintains minimal resource usage when idle
5. Provides an intuitive, user-friendly experience 