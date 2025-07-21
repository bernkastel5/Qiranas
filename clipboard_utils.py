# clipboard_utils.py

import keyboard
import time
import pyperclip

def get_selected_text():
    # Сохраняем старое содержимое буфера обмена
    old_clip = pyperclip.paste()
    keyboard.press_and_release('ctrl+c')
    time.sleep(0.1)  # Дать время системе скопировать текст
    text = pyperclip.paste()
    # Восстанавливаем старое содержимое буфера (по желанию)
    # pyperclip.copy(old_clip)
    return text
