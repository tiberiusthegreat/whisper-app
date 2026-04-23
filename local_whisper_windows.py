import time

import keyboard
import numpy as np
import pyperclip
import sounddevice as sd
import win32clipboard
from faster_whisper import WhisperModel

# --- CONFIGURATION ---
MODEL_SIZE = "tiny"
HOTKEY = "ctrl+space"
SAMPLE_RATE = 16000
ALLOWED_LANGUAGES = {"en", "fr"}
DEFAULT_LANGUAGE = "en"
BEAM_SIZE = 1
BEST_OF = 1

print("--- SuperWhisper Local Port (Low Latency) ---")


def build_model():
    preferred_configs = [
        ("cuda", "float16"),
        ("cuda", "int8_float16"),
        ("cpu", "int8"),
    ]
    last_error = None

    for device, compute_type in preferred_configs:
        try:
            print(f"Loading model: {MODEL_SIZE} on {device} ({compute_type})...")
            model_obj = WhisperModel(MODEL_SIZE, device=device, compute_type=compute_type)
            return model_obj, device, compute_type
        except Exception as exc:
            last_error = exc

    raise RuntimeError(f"Unable to initialize Whisper model: {last_error}")


model, DEVICE, COMPUTE_TYPE = build_model()

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


def detect_language(audio_array):
    segments, info = model.transcribe(
        audio_array,
        language=None,
        beam_size=1,
        best_of=1,
        condition_on_previous_text=False,
        vad_filter=True,
        without_timestamps=True,
    )
    detected_language = getattr(info, "language", None) or DEFAULT_LANGUAGE
    preview_text = "".join([segment.text for segment in segments]).strip()

    if detected_language not in ALLOWED_LANGUAGES:
        detected_language = DEFAULT_LANGUAGE

    return detected_language, preview_text


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
        audio_np = np.concatenate(audio_data, axis=0).astype(np.float32).flatten()
        language, preview_text = detect_language(audio_np)

        segments, info = model.transcribe(
            audio_np,
            language=language,
            beam_size=BEAM_SIZE,
            best_of=BEST_OF,
            condition_on_previous_text=False,
            vad_filter=True,
            without_timestamps=True,
        )
        text = "".join([segment.text for segment in segments]).strip()
        if not text:
            text = preview_text
        elapsed = time.perf_counter() - started_at

        if text:
            previous_clipboard = capture_clipboard()
            pyperclip.copy(text)
            print(f"DONE [{language}] ({elapsed:.2f}s): {text}")

            time.sleep(0.08)
            keyboard.press_and_release("ctrl+v")
            time.sleep(0.08)
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
