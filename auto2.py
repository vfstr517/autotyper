# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import pyautogui
import threading
import time
import random
import keyboard
import os
import pyperclip

# Global state
typing_active = False
typing_paused = False
lock = threading.Lock()
start_time = 0
char_count = 0
theme = "light"  # default to light mode

# Config
TEXT_TO_TYPE = ""
MODE = "char"

# Theme colors
themes = {
    "dark": {"bg": "#1e1e1e", "fg": "#ffffff", "entry": "#2b2b2b", "status": "#00ffff"},
    "light": {"bg": "#ffffff", "fg": "#000000", "entry": "#f8f8f8", "status": "#0077cc"}
}

speed_profiles = {
    "Slow": 30,
    "Normal": 60,
    "Fast": 120,
    "Insane": 250
}

# GUI Setup
root = tk.Tk()
root.title("✨ Auto Typer GUI")
root.geometry("580x560")
root.resizable(False, False)
root.configure(bg=themes[theme]["bg"])

speed_var = tk.StringVar(value="Normal")

def get_delay():
    wpm = speed_profiles.get(speed_var.get(), 60)
    return 60 / (wpm * 5)

def safe_status(text):
    root.after(0, lambda: status_var.set(text))

def update_estimate(*args):
    try:
        text = text_input.get("1.0", tk.END).strip()
        wpm = speed_profiles.get(speed_var.get(), 60)
        mode = mode_var.get()
        count = len(text.split()) if mode == "word" else len(text)
        units_per_min = wpm if mode == "word" else wpm * 5
        estimated_time = count / units_per_min * 60
        mins, secs = divmod(round(estimated_time), 60)
        estimate_var.set(f"⏱ Estimated time: {mins}m {secs}s")
    except:
        estimate_var.set("")

def type_text():
    global typing_active, typing_paused, TEXT_TO_TYPE, MODE, start_time, char_count
    start_time = time.time()
    char_count = 0
    units = list(TEXT_TO_TYPE) if MODE == "char" else TEXT_TO_TYPE.split()

    for unit in units:
        while typing_paused and typing_active:
            time.sleep(0.1)
        if not typing_active:
            break

        with lock:
            pyautogui.write(unit)
            if MODE == "word":
                pyautogui.write(' ')
            char_count += len(unit) + (1 if MODE == "word" else 0)

        delay = get_delay()
        time.sleep(max(0.005, delay))

    typing_active = False
    elapsed = max(1, time.time() - start_time)
    actual_wpm = round((char_count / 5) / (elapsed / 60), 1)
    safe_status(f"✅ Done. Actual speed: {actual_wpm} WPM")

def start_typing():
    global typing_active, TEXT_TO_TYPE, MODE
    if typing_active:
        safe_status("⚠️ Already typing...")
        return

    try:
        TEXT_TO_TYPE = text_input.get("1.0", tk.END).strip()
        if not TEXT_TO_TYPE:
            safe_status("❌ Please enter text.")
            return

        MODE = mode_var.get()
        typing_active = True
        typing_paused = False
        safe_status("⏳ Typing will begin in 3 seconds...")
        threading.Thread(target=delayed_typing_start, daemon=True).start()
        threading.Thread(target=simulate_typos_randomly, daemon=True).start()
    except Exception as e:
        safe_status(f"❌ Error: {e}")

def delayed_typing_start():
    time.sleep(3)
    threading.Thread(target=type_text, daemon=True).start()

def simulate_typos_randomly():
    global typing_active, typing_paused
    while typing_active:
        time.sleep(random.uniform(15, 30))
        if not typing_active:
            break
        safe_status("⌛ Typo simulation...")
        typing_paused = True

        with lock:
            wrong_chars = random.randint(2, 4)
            typo = ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=wrong_chars))
            pyautogui.write(typo)
            time.sleep(0.05 * wrong_chars)
            for _ in range(wrong_chars):
                pyautogui.press('backspace')
                time.sleep(0.05)

        typing_paused = False
        safe_status("▶️ Resumed after typo.")

def pause_typing():
    global typing_paused
    if typing_active:
        typing_paused = True
        safe_status("⏸️ Paused.")

def resume_typing():
    global typing_paused
    if typing_active and typing_paused:
        typing_paused = False
        safe_status("▶️ Resumed.")

def stop_typing():
    global typing_active
    typing_active = False
    safe_status("🛑 Stopped.")

def paste_from_clipboard():
    try:
        text = pyperclip.paste()
        text_input.delete("1.0", tk.END)
        text_input.insert(tk.END, text)
        safe_status("📋 Pasted from clipboard.")
    except Exception as e:
        safe_status(f"❌ Clipboard error: {e}")

def toggle_theme():
    global theme
    theme = "light" if theme == "dark" else "dark"
    apply_theme()

def apply_theme():
    theme_config = themes[theme]
    root.configure(bg=theme_config["bg"])
    text_input.configure(bg=theme_config["entry"], fg=theme_config["fg"], insertbackground=theme_config["fg"])
    for frame_widget in [frame, button_frame, theme_frame, speed_frame]:
        frame_widget.configure(bg=theme_config["bg"])
    for widget in frame.winfo_children():
        if isinstance(widget, tk.Label):
            widget.configure(bg=theme_config["bg"], fg=theme_config["fg"])
    status_label.configure(bg=theme_config["bg"], fg=theme_config["status"])
    estimate_label.configure(bg=theme_config["bg"], fg=theme_config["fg"])

# GUI Layout
style = ttk.Style()
style.configure("TButton", padding=6, font=("Segoe UI", 10))
style.configure("TLabel", font=("Segoe UI", 10))

frame = tk.Frame(root, bg=themes[theme]["bg"])
frame.pack(pady=(10, 0))
tk.Label(frame, text="📄 Enter text to type:", bg=themes[theme]["bg"], fg=themes[theme]["fg"], font=("Segoe UI", 11, "bold")).pack()

text_input = tk.Text(root, height=7, width=66, wrap='word', bd=2, relief="solid")
text_input.pack(pady=(5, 0))
text_input.bind("<KeyRelease>", update_estimate)

estimate_var = tk.StringVar(value="")
estimate_label = tk.Label(root, textvariable=estimate_var, font=("Segoe UI", 9), bg=themes[theme]["bg"], fg=themes[theme]["fg"])
estimate_label.pack(pady=(0, 8))

mode_var = tk.StringVar(value="char")
mode_var.trace_add("write", update_estimate)

# Typing mode
ttk.Label(root, text="📝 Typing Mode:").pack()
ttk.Radiobutton(root, text="Character by Character", variable=mode_var, value="char").pack()
ttk.Radiobutton(root, text="Word by Word", variable=mode_var, value="word").pack()

# Speed profile selector
speed_frame = tk.Frame(root, bg=themes[theme]["bg"])
speed_frame.pack(pady=(5, 0))
tk.Label(speed_frame, text="🚀 Speed Profile:", bg=themes[theme]["bg"], fg=themes[theme]["fg"], font=("Segoe UI", 10)).pack(side="left")
ttkspeed = ttk.OptionMenu(speed_frame, speed_var, speed_var.get(), *speed_profiles.keys(), command=update_estimate)
ttkspeed.pack(side="left", padx=5)

# Buttons
button_frame = tk.Frame(root, bg=themes[theme]["bg"])
button_frame.pack(pady=10)
ttk.Button(button_frame, text="▶️ Start (F8)", command=start_typing).grid(row=0, column=0, padx=6)
ttk.Button(button_frame, text="⏸ Pause (S)", command=pause_typing).grid(row=0, column=1, padx=6)
ttk.Button(button_frame, text="▶ Resume (R)", command=resume_typing).grid(row=0, column=2, padx=6)
ttk.Button(button_frame, text="⛔ Stop (Esc)", command=stop_typing).grid(row=0, column=3, padx=6)

# Paste and Theme
ttk.Button(root, text="📋 Paste from Clipboard", command=paste_from_clipboard).pack(pady=(4, 4))
theme_frame = tk.Frame(root, bg=themes[theme]["bg"])
theme_frame.pack()
ttk.Button(theme_frame, text="🌙 Toggle Dark/Light Mode", command=toggle_theme).pack()

status_var = tk.StringVar(value="💬 Ready.")
status_label = tk.Label(root, textvariable=status_var, font=("Segoe UI", 10), bg=themes[theme]["bg"], fg=themes[theme]["status"])
status_label.pack(pady=(8, 10))

# Hotkeys
keyboard.add_hotkey('F8', start_typing)
keyboard.add_hotkey('s', pause_typing)
keyboard.add_hotkey('r', resume_typing)
keyboard.add_hotkey('esc', stop_typing)

# Init
toggle_theme()  # set to default light mode visually
apply_theme()
update_estimate()
root.mainloop()
