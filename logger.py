import queue
import ctypes
import tkinter as tk
import time
from helper import interpolate_color

# OVERLAY HUD (GUI) Highkey vibe coded 
class LogOverlay:
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass

        self.root = tk.Tk()
        self.root.title("Voice Assistant HUD")

        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)

        self.BG_COLOR = "#000001" 
        self.root.config(bg=self.BG_COLOR)
        self.root.wm_attributes("-transparentcolor", self.BG_COLOR)

        # Positioning: Bottom Right (Dynamic Work Area Detection)
        self.width, self.height = 500, 160
        
        # Define a RECT structure for the Windows API
        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long)
            ]
        
        rect = RECT()
        SPI_GETWORKAREA = 48  # Windows API constant for the desktop work area
        
        # Fetch the usable screen space (excludes the taskbar)
        ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
        
        # Place it 10 pixels from the right and 10 pixels from the bottom of the *usable* area
        x = rect.right - self.width - 10
        y = rect.bottom - self.height - 10
        
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=self.BG_COLOR,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.logs = []  
        self.queue = queue.Queue()
        
        # 1. PRE-ALLOCATE CANVAS SLOTS
        self.slots = []
        font_spec = ("Consolas", 11, "bold")
        x_pos = self.width - 15  
        start_y = 20
        line_height = 26
        
        # Optimized 8-point offset for a 2px outline
        self.outline_offsets = [
            (-2, -2), (0, -2), (2, -2),
            (-2,  0),          (2,  0),
            (-2,  2), (0,  2), (2,  2)
        ]

        # Create 5 reusable text slots (8 outlines + 1 main text per slot)
        for i in range(5):
            y_pos = start_y + (i * line_height)
            outline_ids = []
            
            for dx, dy in self.outline_offsets:
                item_id = self.canvas.create_text(
                    x_pos + dx, y_pos + dy,
                    text="", font=font_spec, fill=self.BG_COLOR, anchor="e"
                )
                outline_ids.append(item_id)
                
            main_id = self.canvas.create_text(
                x_pos, y_pos,
                text="", font=font_spec, fill=self.BG_COLOR, anchor="e"
            )
            self.slots.append({'outlines': outline_ids, 'main': main_id})

        self.root.update()

        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            if not hwnd:
                hwnd = self.root.winfo_id()
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_LAYERED = 0x00080000
            styles = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, styles | WS_EX_TRANSPARENT | WS_EX_LAYERED)
        except Exception as e:
            print(f"Overlay setup warning: {e}")

        self.log("HUD Initialized...", "#888888")
        self.root.after(30, self._render_loop)

    def log(self, text, color="#FFFFFF"):
        self.queue.put((text, color, time.time()))

    def _render_loop(self):
        now = time.time()

        while not self.queue.empty():
            text, color, timestamp = self.queue.get()
            self.logs.append({'text': text, 'color': color, 'time': timestamp})
            if len(self.logs) > 5:
                self.logs.pop(0)

        # Retain only items newer than 3.2 seconds
        self.logs = [item for item in self.logs if now - item['time'] < 3.2]

        # 2. UPDATE EXISTING SLOTS INSTEAD OF DELETING/RECREATING
        num_logs = len(self.logs)
        for i in range(5):
            # Offset the index so the logs anchor to the bottom slot (i=4) and push upwards
            log_index = i - (5 - num_logs)
            
            if 0 <= log_index < num_logs:
                item = self.logs[log_index]
                age = now - item['time']

                # Fade calculation
                if age <= 3.0:
                    factor = 1.0
                else:
                    factor = max(0.0, (3.2 - age) / 0.2) 

                text_color = interpolate_color(item['color'], self.BG_COLOR, factor)
                outline_color = interpolate_color("#000000", self.BG_COLOR, factor)

                # Update item properties
                self.canvas.itemconfig(self.slots[i]['main'], text=item['text'], fill=text_color)
                for outline_id in self.slots[i]['outlines']:
                    self.canvas.itemconfig(outline_id, text=item['text'], fill=outline_color)
            else:
                # Clear unused slots by setting text to empty and matching background color
                self.canvas.itemconfig(self.slots[i]['main'], text="", fill=self.BG_COLOR)
                for outline_id in self.slots[i]['outlines']:
                    self.canvas.itemconfig(outline_id, text="", fill=self.BG_COLOR)

        self.root.after(30, self._render_loop)

    def start(self):
        self.root.mainloop()