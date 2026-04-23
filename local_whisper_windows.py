import os
import time
import sounddevice as sd
import numpy as np
import wave
import keyboard
import pyperclip
import win32clipboard
from faster_whisper import WhisperModel

# --- CONFIGURATION ---
MODEL_SIZE = "tiny"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"
HOTKEY = "ctrl+space"
TEMP_FILE = "temp_recording.wav"
SAMPLE_RATE = 16000
LANGUAGE = "en"
BEAM_SIZE = 1
BEST_OF = 1

print("--- SuperWhisper Local Port (CPU Optimized) ---")
print(f"Loading model: {MODEL_SIZE} on {DEVICE}...")

model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)

print("\nSUCCESS: Model loaded.")
print("Press CTRL + SPACE to start/stop recording.")

recording = False
audio_data = []

CLIPBOARD_FORMATS_TO_PRESERVE = [
    win32clipboard.CF_DIB,
    win32clipboard.CF_UNICODETEXT,
    win32clipboard.CF_TEXT,
]


def capture_clipboard():
    snapshot = []
    try:
        win32clipboard.OpenClipboard()
        for clipboard_format in CLIPBOARD_FORMATS_TO_PRESERVE:
            if win32clipboard.IsClipboardFormatAvailable(clipboard_format):
                try:
                    data = win32clipboard.GetClipboardData(clipboard_format)
                    snapshot.append((clipboard_format, data))
                except TypeError:
                    pass
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass
    return snapshot


def restore_clipboard(snapshot):
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        for clipboard_format, data in snapshot:
            win32clipboard.SetClipboardData(clipboard_format, data)
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


def callback(indata, frames, time_info, status):
    if recording:
        audio_data.append(indata.copy())


def start_recording():
    global recording, audio_data
    recording = True
    audio_data = []
    print(">> Recording...")


def stop_recording():
    global recording
    recording = False
    print(">> Transcribing...")

    if not audio_data:
        print("!! No audio captured.")
        return

    try:
        started_at = time.perf_counter()
        audio_np = np.concatenate(audio_data, axis=0)
        with wave.open(TEMP_FILE, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes((audio_np * 32767).astype(np.int16).tobytes())

        segments, info = model.transcribe(
            TEMP_FILE,
            language=LANGUAGE,
            beam_size=BEAM_SIZE,
            best_of=BEST_OF,
            condition_on_previous_text=False,
            vad_filter=True,
            without_timestamps=True,
        )
        text = "".join([segment.text for segment in segments]).strip()
        elapsed = time.perf_counter() - started_at

        if text:
            previous_clipboard = capture_clipboard()
            pyperclip.copy(text)
            print(f"DONE ({elapsed:.2f}s): {text}")

            time.sleep(0.1)
            keyboard.press_and_release("ctrl+v")
            time.sleep(0.1)
            restore_clipboard(previous_clipboard)
            print(">> Auto-pasted!")
        else:
            print(f"!! No speech detected. ({elapsed:.2f}s)")
    except Exception as e:
        print(f"!! Error during processing: {e}")


def toggle_recording():
    if not recording:
        start_recording()
    else:
        stop_recording()


keyboard.add_hotkey(HOTKEY, toggle_recording)

try:
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=callback):
        while True:
            time.sleep(0.1)
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)
