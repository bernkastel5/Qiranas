# main.py

from hotkey_manager import register_hotkey, unregister_hotkey
from screen_capture import capture_area_with_selection
from text_extractor import extract_text_ja, extract_text_ar
from dictionary import load_all_yomichan_dictionaries, lookup_word_yomichan
from overlay import show_overlay
from clipboard_utils import get_selected_text
from config import read_config
from config_manager import ConfigManager

DICTIONARIES_DIR = 'resources/dictionaries'
dictionaries = load_all_yomichan_dictionaries(DICTIONARIES_DIR)
config = read_config('config.txt')

config_manager = ConfigManager('config.txt')
current_hotkeys = {}

def on_hotkey_clipboard():
    selected_text = get_selected_text()
    if not selected_text:
        print("Не удалось получить выделенный текст.")
        return
    first_word = selected_text.strip().split()[0]
    print(f"Первое слово: {first_word}")
    results = lookup_word_yomichan(first_word, dictionaries)
    if results:
        show_overlay(results, dictionaries)
    else:
        print("Слово не найдено в словарях.")

def on_hotkey_ocr_ja():
    img = capture_area_with_selection()
    text = extract_text_ja(img)
    if not text.strip():
        print("Текст не распознан.")
        return
    print(f"Распознанный текст (японский): {text}")
    results = lookup_word_yomichan(text, dictionaries)
    if results:
        show_overlay(results, dictionaries)
    else:
        print("Слово не найдено в словарях.")

def on_hotkey_ocr_ar():
    img = capture_area_with_selection()
    text = extract_text_ar(img)
    if not text.strip():
        print("Текст не распознан.")
        return
    print(f"Распознанный текст (арабский): {text}")
    results = lookup_word_yomichan(text, dictionaries)
    if results:
        show_overlay(results, dictionaries)
    else:
        print("Слово не найдено в словарях.")

def register_all_hotkeys():
    for hotkey_id in list(current_hotkeys.values()):
        try:
            unregister_hotkey(hotkey_id)
        except Exception as e:
            print(f"Ошибка при удалении хоткея: {e}")
        current_hotkeys.clear()
        print("Регистрирую новые хоткеи")
        current_hotkeys['clipboard'] = register_hotkey(config_manager.get('on_hotkey_clipboard', 'ctrl+shift+t'),
                                                       on_hotkey_clipboard)
        current_hotkeys['ocr_ja'] = register_hotkey(config_manager.get('on_hotkey_ocr_ja', 'ctrl+shift+y'),
                                                    on_hotkey_ocr_ja)
        current_hotkeys['ocr_ar'] = register_hotkey(config_manager.get('on_hotkey_ocr_ar', 'ctrl+shift+a'),
                                                    on_hotkey_ocr_ar)
        print("Текущие хоткеи:", current_hotkeys)

    config_manager.on_change(lambda conf: register_all_hotkeys())
    register_all_hotkeys()

if __name__ == "__main__":
    print("Программа запущена.")
    print("Горячие клавиши:")
    print(f"  Выделенный текст: {config['on_hotkey_clipboard']}")
    print(f"  OCR японский: {config['on_hotkey_ocr_ja']}")
    print(f"  OCR арабский: {config['on_hotkey_ocr_ar']}")
    register_hotkey(config['on_hotkey_clipboard'], on_hotkey_clipboard)
    register_hotkey(config['on_hotkey_ocr_ja'], on_hotkey_ocr_ja)
    register_hotkey(config['on_hotkey_ocr_ar'], on_hotkey_ocr_ar)
    import keyboard
    keyboard.wait('esc')
