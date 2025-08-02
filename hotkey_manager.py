# hotkey_manager.py

import keyboard

def register_hotkey(hotkey, callback):
    return keyboard.add_hotkey(hotkey, callback)

def unregister_hotkey(hotkey_id):
    keyboard.remove_hotkey(hotkey_id)
