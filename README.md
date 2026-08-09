# Customizable Low Memory Voice Assistant

A Python-based, fully offline desktop voice assistant built for Windows. It listens for specific voice commands to control applications, manage media, and run custom background scripts, while providing real-time visual feedback through a transparent, non-blocking on-screen display (HUD).

## Features

* **Offline Speech Recognition**: Utilizes a local Vosk model combined with a PyTorch-based Silero Voice Activity Detector (VAD) to process audio streams efficiently without cloud processing.
* **Transparent GUI Overlay**: Features a custom `tkinter` overlay that automatically positions itself at the bottom right of the usable screen area. The HUD is borderless, click-through, and features fading text animations.
* **Window Management**: Uses raw Windows API (`ctypes`) calls to reliably open, close, and force specific applications (like Discord, VS Code, Opera, and Spotify) into the foreground.
* **Media & System Controls**: Supports hotkeys for media playback, window minimization, opening the calculator, and flushing the system DNS cache.
* **External Script Integration**: Integrates with external Python scripts.

## Project Structure

* **`main.py`** (Audio & Entry Point): Initializes the `pyaudio` microphone stream, the Silero VAD model, and the Vosk recognizer. It handles the background audio processing thread and triggers the GUI main loop.
* **`commands.py`**: Contains the execution logic for every registered voice command, from simple `pyautogui` hotkeys to launching sub-processes and text-to-speech workers.
* **`logger.py`**: Contains the `LogOverlay` class, handling the `tkinter` canvas, DPI awareness, transparency masking, and color interpolation for the fading log text.
* **`helper.py`**: Houses the `focus_process` function, which iterates through visible Windows OS windows to match and restore a specific executable (e.g., `spotify.exe`), as well as RGB/Hex conversion utilities.
* **`registry.py`**: A lightweight module providing the `COMMAND_REGISTRY` dictionary and the `@command` decorator used to map spoken phrases to functions.

## Architecture
```
Microphone
    ↓
Silero VAD
    ↓
Pre-buffer
    ↓
Vosk + constrained grammar
    ↓
Command Registry
    ↓
Command Function
    ├── Windows / media control
    ├── TTS
    └── External Python process
    ↓
HUD feedback
```

## Requirements and Memory Usage

### System
* **OS:** Windows (Relies heavily on `ctypes.windll` for window management and GUI transparency).
* **Audio:** A working microphone input.

* ### Resource Usage

It is designed to remain running continuously without becoming a significant system resource drain.

| State | RAM |
|---|---:|
| Idle | ~300 MB |
| Peak While Running External Scripts | ~300 MB + Memory Footprint of External Script |


### Dependencies
Ensure you have the following Python packages installed:
```bash
pip install torch vosk pyaudio pyautogui pyttsx3 pywin32

```

(`pywin32` is required for the `pythoncom` module used in the TTS thread.)

### External Assets

* **Vosk Model:** You must download a compatible Vosk speech recognition model and place it inside a folder named `model` in the root directory of the project.



## Usage

1. Start the assistant by running the main script:
```bash
python main.py

```

2. The HUD will initialize in the bottom right corner of your screen.


3. Speak any of the registered commands (e.g., `"open code"`, `"pause"`, `"focus discord"`, `"read me a paper"`).


4. The system will process the audio chunks, trigger the corresponding function, and log the status to the on-screen overlay.


5. To close the program, say `"stop listening"` or use a keyboard interrupt in the terminal.

## Alternative Usage

1. Create a .vbs file with the following command
```vbs
Set WShell = CreateObject("WScript.Shell")
WShell.Run """...Project_directory\.venv\Scripts\python.exe"" ""...Project_directory\main.py""", 0, False
```
2. You can now use this .vbs file to launch the app
3. If you want it to run on startup, place it in your startup folder (accessed via win + R, followed by typing shell:startup)
4. To close the program, say `"stop listening"`



## Adding New Commands

You can easily map new spoken phrases to Python functions using the `@command` decorator. Add your new functions to the `commands.py` file.

```python
from registry import command

@command("open notepad")
def launch_notepad():
    subprocess.Popen(["notepad.exe"])
    overlay.log("Opening Notepad", "#00FF00")

```

Multiple phrases can be stacked on a single function to account for variations in speech recognition.

## Adding Commands with TTS and External Function Calling

- Here is a simple example of how you'd implement TTS, it'll read a string to you.


```python
# This is an example of how a chunk in the top_papers.txt file is stored
'''
--------------------------------------------------

Title: title
Link: http://arxiv.org/hahaha_something
Summary:
summary

--------------------------------------------------
'''

@command("say hello")
def read_top_paper():

    def tts_worker():
        text_to_say = f"Hello"
        
        try:
            # Initialize COM for the background thread
            pythoncom.CoInitialize()
            
            # Initialize locally within the thread
            engine = pyttsx3.init()
            
            # Adjust the speech rate (default is usually 200 wpm)
            engine.setProperty('rate', 150) 
            
            # Queue and play
            engine.say(text_to_say)
            engine.runAndWait()
            
            # Clean up
            pythoncom.CoUninitialize()
            
        except Exception as e:
            print(f"TTS Failed: {e}")
            overlay.log("TTS playback failed", "#FF3333")

    # the TTS in a daemon thread so you can keep using the voice assistant while the TTS speaks
    threading.Thread(target=tts_worker, daemon=True).start()   
```

- Here is an example on how to call an external file

```python
@command("run script 1")
def run_external_script():
    venv_python = r"...script_directory\.venv\Scripts\python.exe" # The path to the python.exe in your external scripts .venv
    target_script = r"...script_directory\main.py" # the external script
    
    if os.path.exists(venv_python) and os.path.exists(target_script):
        try:
            # project_dir = r"...script_directory" 
            # without this any file writes that are done by the external script will be done in the voice assistants directory
            # instead of the external scripts directory
            # but the idea of the files being stolen by the assistant and being put in this directory entertains me
            
            process = subprocess.Popen(
                [venv_python, target_script],
                # cwd=project_dir, -- Uncomment to not get files stolen from the external directory
                creationflags=0x08000000 # no terminal pop up
            )
            
            print(f"Executing invisibly via venv: {target_script}")
            overlay.log("Started Script 1", "#00FF00")

            # a worker function to monitor the process, optional but very nice to have so you know when the script is done executing
            def monitor_process():
                # blocks this specific thread until the external script finishes
                return_code = process.wait()
                
                # (0 means it finished without crashing)
                if return_code == 0:
                    print("Script completed successfully.")
                    overlay.log("finished!", "#00FF00")
                    overlay.log("I stole the generated files though :D.", "#00FF00")
                    overlay.log("They are in my directory.", "#00FF00")
                else:
                    print(f"Research script crashed with error code: {return_code}")
                    overlay.log(f"Research failed (Code: {return_code})", "#FF3333")

            # the monitor function in a background thread
            threading.Thread(target=monitor_process, daemon=True).start()

        except Exception as e:
            print(f"Failed to run script: {e}")
            overlay.log("Failed to launch script", "#FF3333")
    else:
        print("Error: Either the venv Python or the target script was not found.")
        overlay.log("Path error for script", "#FF3333")
```
