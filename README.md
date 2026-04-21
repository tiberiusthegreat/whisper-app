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

- Uses `faster-whisper` locally on CPU.
- Default hotkey is `Ctrl+Space`.
- Temporary audio is written to `temp_recording.wav` during transcription and cleaned up on exit.
