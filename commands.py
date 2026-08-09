from registry import command
import os
import subprocess
import pyautogui
import threading
from helper import focus_process
import re
import pyttsx3
import pythoncom

overlay = None

def set_overlay(hud):
    global overlay
    overlay = hud

@command("open opera")
def open_browser():
    user_home = os.path.expanduser("~")
    gx_path = os.path.join(user_home, r"AppData\Local\Programs\Opera GX\opera.exe")
    if os.path.exists(gx_path):
        subprocess.Popen(gx_path)
    else:
        print(f"Path not found: {gx_path}")

@command("close opera")
def close_browser():
    subprocess.run(["taskkill", "/F", "/IM", "opera.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

#@command("open steam")
#def open_library():
#    # 'start' is a cmd built-in, so we call cmd explicitly
#    subprocess.run(["cmd", "/c", "start", "steam://open/library"])
#
#@command("close steam")
#def close_library():
#    subprocess.run(["taskkill", "/F", "/IM", "steam.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#
#@command("open peak")
#def open_peak():
#    subprocess.run(["cmd", "/c", "start", "steam://run/3527290"])

@command("open code")
def open_code():
    try:
        subprocess.Popen("code", shell=True)
    except Exception:
        print("VS Code not found in PATH. Trying default location...")
        user_home = os.path.expanduser("~")
        code_path = os.path.join(user_home, r"AppData\Local\Programs\Microsoft VS Code\Code.exe")
        if os.path.exists(code_path):
            subprocess.Popen(code_path)

@command("close code")
def close_code():
    subprocess.run(["taskkill", "/F", "/IM", "Code.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

@command("open discord")
def open_discord():
    print("Launching Discord...")
    discord_path = os.path.join(os.getenv('LOCALAPPDATA', ''), r"Discord\Update.exe")
    if os.path.exists(discord_path):
        subprocess.Popen([discord_path, "--processStart", "Discord.exe"])
    else:
        print(f"Could not find Discord at: {discord_path}")

@command("close discord")
def close_discord():
    subprocess.run(["taskkill", "/F", "/IM", "Discord.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

@command("open music")
def open_spot():
    subprocess.run(["cmd", "/c", "start", "spotify:"])

@command("close music")
def close_spot():
    subprocess.run(["taskkill", "/F", "/IM", "spotify.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

#@command("close everything")
#def close_all():
#    print("Closing all heavy applications...")
#    apps_to_kill = [
#        "opera.exe", "chrome.exe", "msedge.exe", 
#        "steam.exe", "spotify.exe",  
#        "Discord.exe", "RiotClientServices.exe"  
#    ]
#    for app in apps_to_kill:
#        subprocess.run(["taskkill", "/F", "/IM", app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

@command("mini all")
def minimize_windows():
    pyautogui.hotkey('win', 'd')

@command("pause")
@command("play")
def toggle_media():
    pyautogui.press("playpause")

@command("next")
def next_track():
    pyautogui.press("nexttrack")
    
@command("go back")
def prev_track():
    # done twice because going back once in spotify usually just puts you at the start of a song again
    pyautogui.press("prevtrack")
    pyautogui.press("prevtrack")
    
@command("volume")
def mute():
    pyautogui.press("volumemute")
    
@command("open settings")
def open_settings():
    pyautogui.hotkey('win', 'i')
    
@command("stop listening")
def aura_kill_yourself():
    print("Shutting down voice assistant...")
    os._exit(0)

@command("calculator")
def open_calculator():
    try:
        subprocess.Popen(["calc.exe"])
        print("Opening calculator...")
    except Exception as e:
        print(f"Failed to open calculator: {e}")

@command("exit")
def close():
    pyautogui.hotkey('alt', 'f4')
    
@command("flush net")
def flush_dns():
    try:
        subprocess.run(["ipconfig", "/flushdns"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("DNS cache flushed successfully.")
        overlay.log(f"DNS cache flushed successfully.", "#00FF00")  # Green
    except Exception as e:
        print(f"Failed to flush DNS: {e}")
        overlay.log(f"DNS flush failed.", "#FFFF00")
        
@command("focus discord")
def switch_discord():
    focus_process("discord.exe")

@command("focus code")
def switch_code():
    focus_process("code.exe")

@command("focus opera")
def switch_opera():
    focus_process("opera.exe")

@command("focus music")
def switch_spotify():
    focus_process("spotify.exe")
    
@command("[unk] find top research papers")
@command("find top research papers")
@command("[unk] find research papers")
@command("find research papers")
def run_external_script():
    venv_python = r"C:\Users\hi\Desktop\projects\Project1\.venv\Scripts\python.exe"
    target_script = r"C:\Users\hi\Desktop\projects\Project1\main.py"
    
    if os.path.exists(venv_python) and os.path.exists(target_script):
        try:
            # project_dir = r"C:\Users\hi\Desktop\projects\Project1" 
            # okay look do it like this if you want to use it to model your own file execution
            # but the idea of the files being stolen by the AI and being put in this directory entertains me
            
            process = subprocess.Popen(
                [venv_python, target_script],
                # cwd=project_dir,
                creationflags=0x08000000
            )
            
            print(f"Executing invisibly via venv: {target_script}")
            overlay.log("Started researching...", "#00FF00")

            # a worker function to monitor the process
            def monitor_process():
                # blocks this specific thread until the external script finishes
                return_code = process.wait()
                
                # (0 means it finished without crashing)
                if return_code == 0:
                    print("Research script completed successfully.")
                    overlay.log("Research finished!", "#00FF00")
                    overlay.log("I stole the file though.", "#00FF00")
                    overlay.log("It's in my directory.", "#00FF00")
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
        
        
@command("read me a paper")
@command("[unk] read me a paper")
def read_top_paper():
    top_papers_file = r"C:\Users\hi\Desktop\jarvis\top_papers.txt"
    read_papers_file = r"C:\Users\hi\Desktop\jarvis\read_papers.txt"

    def tts_worker():
        overlay.log("Starting paper read...", "#00FF00")
        
        if not os.path.exists(top_papers_file):
            overlay.log("top_papers.txt not found", "#FF3333")
            return
            
        # Reads the entire file content
        with open(top_papers_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parses the first paper block matching the exact structure
        # Group 1 = Full block, Group 2 = Title, Group 3 = Summary
        pattern = r"((?:\d+\.\s+)?Title:\s*(.*?)\nLink:\s*.*?\nSummary:\s*\n(.*?)\n+-{40,}\n*)"
        match = re.search(pattern, content, flags=re.DOTALL)
        
        if not match:
            overlay.log("No unread papers found!", "#FF3333")
            return
            
        full_block = match.group(1)
        title = match.group(2).strip()
        summary = match.group(3).strip()
        
        # Remove the exact block from the unread file and write it back
        new_content = content.replace(full_block, "", 1)
        with open(top_papers_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        # Append the block to the read_papers file
        with open(read_papers_file, 'a', encoding='utf-8') as f:
            f.write(full_block)
            
        # the speech string
        text_to_say = f"Sure, The title is {title}. The paper can be summarized as {summary}"
        
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
            
            overlay.log("Finished reading paper.", "#00FF00")
            
        except Exception as e:
            print(f"TTS Failed: {e}")
            overlay.log("TTS playback failed", "#FF3333")

    # the TTS and file manipulation in a daemon thread
    threading.Thread(target=tts_worker, daemon=True).start()   