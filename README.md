# SpeechWave

A minimal, privacy-focused Speech-to-Text (STT) application for Windows that runs in the system tray. Press and hold a hotkey to record your voice, and SpeechWave will transcribe it locally using Whisper and type the text directly at your cursor position.

## 💾 Download & Run (Executable)

The easiest way to use SpeechWave is to download the pre-built executable:

1.  Go to the [**Releases Page**](https://github.com/spectralf/speechwave/releases).
2.  Find the latest release (e.g., `v0.1.0`).
3.  Under the **Assets** section, download the `SpeechWave.exe` file.
4.  Save the `.exe` file somewhere convenient on your computer.
5.  Double-click `SpeechWave.exe` to run the application. The icon will appear in your system tray.

*(See the [Usage](#-usage) section below for how to use the hotkey)*

## ✨ Key Features

*   **Hotkey Activation:** Press and hold a user-defined hotkey to start recording.
*   **Local Transcription:** Uses the efficient `faster-whisper` library (with CTranslate2) for fast, offline speech recognition. No audio data leaves your computer.
*   **Direct Text Insertion:** Transcribed text is automatically typed out where your cursor is focused.
*   **System Tray Integration:** Runs discreetly in the system tray with options to open settings or quit.
*   **Configurable:** Settings like the hotkey and Whisper model options can be adjusted.
*   **Cross-Platform (Potential):** Built with Python and PyQt6, aiming for compatibility (though currently focused on Windows features like text insertion).

## 🚀 Getting Started (from Source)

If you prefer to run or build the application from the source code:

### Prerequisites

*   Python 3.10 or later
*   Git (for cloning the repository)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/spectralf/speechwave.git
    cd SpeechWave
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    # On Windows
    .\.venv\Scripts\activate
    # On macOS/Linux
    # source .venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 💻 Usage

1.  **(If running from source)** Run the application:
    ```bash
    python src/app.py
    ```
2.  The SpeechWave icon will appear in your system tray.
3.  **Press and hold** the configured hotkey (default might need setting first via the systray menu if not pre-configured) while you speak.
4.  **Release** the hotkey when you are finished speaking.
5.  The application will transcribe the audio and type the text at your current cursor location.
6.  **Right-click** the system tray icon for options like opening Settings or Quitting the application.

## ⚙️ Configuration

*   Application settings, including the hotkey and Whisper model preferences, are stored in a configuration file (e.g., `settings.json`) located in `%APPDATA%\SpeechWave`.
*   Settings can be adjusted through the UI accessible from the system tray menu (if implemented).

## 📦 Building from Source

You can create a distributable executable using PyInstaller:

1.  Make sure you are in the activated virtual environment with development dependencies installed.
2.  Run PyInstaller with the provided spec file:
    ```bash
    pyinstaller SpeechWave.spec
    ```
3.  The executable will be located in the `dist/` directory (either `dist/SpeechWave` for one-dir or `dist/SpeechWave.exe` for one-file, depending on the spec configuration).

## 📚 Dependencies

Key libraries used:

*   PyQt6 (GUI and System Tray)
*   faster-whisper (Whisper Transcription)
*   ctranslate2 (Backend for faster-whisper)
*   keyboard (Global Hotkey Management - *or pynput*)
*   PyAudio (Audio Recording - *or sounddevice*)
*   PyAutoGUI (Text Insertion)
*   Loguru (Logging)

See `requirements.txt` for the full list.

## ❤️ Support the Project

If you find SpeechWave useful, please consider supporting its development!

![Donation QR Code](qrcode.png)



## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
