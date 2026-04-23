# Whisper App

A lightweight local Whisper voice toggle app for Windows.

## What It Does

- Press `Ctrl+Space` to start recording.
- Press `Ctrl+Space` again to stop and transcribe.
- The transcript pastes into the active window automatically.
- Your previous clipboard contents are restored right after the paste.

## Files

- `local_whisper_windows.py` - main app
- `whisper.bat` - simple Windows launcher
- `requirements.txt` - Python dependencies

## Setup

```bash
pip install -r requirements.txt
```

Then run:

```bat
whisper.bat
```

## Notes

- Uses `faster-whisper` with low-latency settings and prefers GPU automatically when available.
- Default hotkey is `Ctrl+Space`.
- Dictation is limited to English and French, with direct in-memory transcription to reduce delay.
