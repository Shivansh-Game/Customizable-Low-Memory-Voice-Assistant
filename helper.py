import ctypes
from ctypes import wintypes
import os

def focus_process(target_exe):
    """Finds a window by its underlying executable name (e.g., 'spotify.exe') and focuses it."""
    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
    OpenProcess = ctypes.windll.kernel32.OpenProcess
    CloseHandle = ctypes.windll.kernel32.CloseHandle
    QueryFullProcessImageName = ctypes.windll.kernel32.QueryFullProcessImageNameW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            # checks only visible windows that actually have a title frame
            if ctypes.windll.user32.GetWindowTextLengthW(hwnd) > 0:
                pid = wintypes.DWORD()
                GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                
                # Open the process to read its file path
                h_process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
                if h_process:
                    buffer_size = wintypes.DWORD(260)
                    buffer = ctypes.create_unicode_buffer(260)
                    if QueryFullProcessImageName(h_process, 0, buffer, ctypes.byref(buffer_size)):
                        # Extract just the "app.exe" part from the full path
                        current_exe = os.path.basename(buffer.value).lower()
                        
                        if current_exe == target_exe.lower():
                            ctypes.windll.user32.ShowWindow(hwnd, 9)  # 9 = SW_RESTORE
                            ctypes.windll.user32.SetForegroundWindow(hwnd)
                            CloseHandle(h_process)
                            return False  # Stop once found
                    CloseHandle(h_process)
        return True

    EnumWindows(EnumWindowsProc(foreach_window), 0)
    
# logger helpers
def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c * 2 for c in hex_str])
    return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def interpolate_color(start_hex, end_hex, factor):
    """Interpolates between start_hex and end_hex based on factor (1.0 = start, 0.0 = end)."""
    try:
        r1, g1, b1 = hex_to_rgb(start_hex)
        r2, g2, b2 = hex_to_rgb(end_hex)
        r = int(r1 * factor + r2 * (1 - factor))
        g = int(g1 * factor + g2 * (1 - factor))
        b = int(b1 * factor + b2 * (1 - factor))
        return rgb_to_hex((max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
    except Exception:
        return start_hex