import pyaudio
import os
import numpy as np
import torch
import json
from vosk import Model, KaldiRecognizer
import sys
import threading
from logger import LogOverlay
from registry import COMMAND_REGISTRY
from commands import set_overlay

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "model")

overlay = None

def get_registered_commands():
    commands = list(COMMAND_REGISTRY.keys())
    commands.append("[unk]")
    return commands

def execute_command(cmd_text):
    handler = COMMAND_REGISTRY.get(cmd_text)
    if handler:
        overlay.log(f"COMMAND RECOGNIZED: {cmd_text}", "#00FF00")
        handler()
    else:
        print(f"No handler found for: '{cmd_text}'")

def process_vosk_result(result_string):
    """Parses the JSON returned by Vosk and routes valid commands."""
    result = json.loads(result_string)
    text = result.get('text', '')
    if text and text != "[unk]":
        print(f"COMMAND HEARD: {text}")
        overlay.log(f"COMMAND HEARD: {text}", "#FFFF00") 
        execute_command(text)

def command_listener():
    
    if not os.path.exists(MODEL_PATH):
        print("Please ensure your 'model' folder is present in the root directory.")
        return

    print("Loading Vosk model...")
    vosk_model = Model(MODEL_PATH)
    commands_list = get_registered_commands()
    grammar = json.dumps(commands_list)
    rec = KaldiRecognizer(vosk_model, 16000, grammar)

    print("Loading Silero VAD model...")
    torch.set_num_threads(1)
    vad_model, _ = torch.hub.load(
        repo_or_dir='snakers4/silero-vad',
        model='silero_vad',
        trust_repo=True
    )
    vad_model.eval()

    # Silero requires 512 samples per chunk at 16kHz
    CHUNK = 512
    RATE = 16000
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("\n--- Listener Active (Vosk + Silero VAD) ---")
    overlay.log("Listener active...", "#888888")

    VAD_THRESHOLD = 0.3
    SILENCE_LIMIT_CHUNKS = 20  # ~640ms of silence to trigger Vosk finalization

    is_speaking = False
    silence_chunks = 0
    long_silence_chunks = 0  # continuous silence
    pre_buffer = []
    pre_buffer_len = 15 
    
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_int16 = np.frombuffer(data, np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0

            with torch.no_grad():
                tensor_chunk = torch.from_numpy(audio_float32)
                confidence = vad_model(tensor_chunk, RATE).item()

            if confidence > VAD_THRESHOLD:
                long_silence_chunks = 0  # reset on speech
                if not is_speaking:
                    print("\nListening...", end="", flush=True)
                    overlay.log("listening...", "#FFFF00")
                    is_speaking = True
                    for b in pre_buffer:
                        rec.AcceptWaveform(b)
                    pre_buffer.clear()
                silence_chunks = 0

                if rec.AcceptWaveform(data):
                    process_vosk_result(rec.Result())
                    is_speaking = False
                    vad_model.reset_states()

            elif is_speaking:
                long_silence_chunks = 0  # silence tracker
                silence_chunks += 1
                if rec.AcceptWaveform(data):
                    process_vosk_result(rec.Result())
                    is_speaking = False
                    silence_chunks = 0
                    vad_model.reset_states()

                if silence_chunks >= SILENCE_LIMIT_CHUNKS:
                    is_speaking = False
                    print(" Processing...")
                    overlay.log("processing...", "#FFFF00")
                    process_vosk_result(rec.FinalResult())
                    vad_model.reset_states()
            else:
                # Silero states drift during long idle periods
                long_silence_chunks += 1
                if long_silence_chunks > 300:  # ~9.5 seconds of pure silence
                    vad_model.reset_states()
                    long_silence_chunks = 0
                
                # sliding pre-buffer window
                pre_buffer.append(data)
                if len(pre_buffer) > pre_buffer_len:
                    pre_buffer.pop(0)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    try:
        overlay = LogOverlay()
        set_overlay(overlay)
        
        # audio on background thread
        audio_thread = threading.Thread(target=command_listener, daemon=True)
        audio_thread.start()
        
        # GUI loop on main thread
        overlay.start()
    except KeyboardInterrupt:
        print("\nStopping...")