# hotkey_manager.py

import keyboard

def register_hotkey(hotkey, callback):
    keyboard.add_hotkey(hotkey, callback)
