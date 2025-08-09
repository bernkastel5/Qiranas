# main.py

import keyboard
from hotkey_manager import register_hotkey, unregister_hotkey
from screen_capture import capture_area_with_selection
from text_extractor import extract_text_ja, extract_text_ar
from dictionary import load_all_yomichan_dictionaries, lookup_word_yomichan
from overlay import show_overlay
from clipboard_utils import get_selected_text
from config_manager import ConfigManager

# --- Глобальная инициализация ---
DICTIONARIES_DIR = 'resources/dictionaries'
print("Загрузка словарей...")
main_dicts, freq_dicts, pitch_dicts = load_all_yomichan_dictionaries(DICTIONARIES_DIR)
dictionaries = (main_dicts, freq_dicts, pitch_dicts)
print("Словари загружены.")

config_manager = ConfigManager('config.txt')
current_hotkeys = {}


# --- Вспомогательная функция для обработки текста ---
def process_and_show(text_to_search):
    if not text_to_search or not text_to_search.strip():
        print("Нет текста для поиска.")
        return

    cleaned_text = text_to_search.strip()
    print(f"Ищем: '{cleaned_text}'")

    results, freq_results, pitch_results = lookup_word_yomichan(cleaned_text, *dictionaries)

    show_overlay(cleaned_text, results, freq_results, pitch_results, dictionaries)


# --- Обработчики горячих клавиш ---
def on_hotkey_clipboard():
    selected_text = get_selected_text()
    if selected_text:
        first_word = selected_text.strip().split()[0]
        process_and_show(first_word)
    else:
        print("Не удалось получить выделенный текст.")


def on_hotkey_ocr_ja():
    try:
        img = capture_area_with_selection()
        text = extract_text_ja(img).strip()
        process_and_show(text)
    except Exception as e:
        print(f"Ошибка в OCR (ja): {e}")


def on_hotkey_ocr_ar():
    try:
        img = capture_area_with_selection()
        text = extract_text_ar(img).strip()
        process_and_show(text)
    except Exception as e:
        print(f"Ошибка в OCR (ar): {e}")


# --- Управление горячими клавишами ---
def register_all_hotkeys():
    for hotkey_id in current_hotkeys.values():
        try:
            unregister_hotkey(hotkey_id)
        except Exception as e:
            print(f"Ошибка при удалении старого хоткея: {e}")
    current_hotkeys.clear()

    print("Регистрирую новые горячие клавиши:")

    key_clipboard = config_manager.get('on_hotkey_clipboard', 'ctrl+shift+t')
    key_ocr_ja = config_manager.get('on_hotkey_ocr_ja', 'ctrl+shift+y')
    key_ocr_ar = config_manager.get('on_hotkey_ocr_ar', 'ctrl+shift+a')

    current_hotkeys['clipboard'] = register_hotkey(key_clipboard, on_hotkey_clipboard)
    current_hotkeys['ocr_ja'] = register_hotkey(key_ocr_ja, on_hotkey_ocr_ja)
    current_hotkeys['ocr_ar'] = register_hotkey(key_ocr_ar, on_hotkey_ocr_ar)

    print(f"  Выделенный текст: {key_clipboard}")
    print(f"  OCR японский: {key_ocr_ja}")
    print(f"  OCR арабский: {key_ocr_ar}")
    print("Горячие клавиши активны.")


if __name__ == "__main__":
    print("Программа запущена. Нажмите ESC в главном окне терминала, чтобы выйти.")

    # Устанавливаем слежение за изменениями в конфиге.
    config_manager.on_change(lambda conf: register_all_hotkeys())

    # Выполняем первоначальную регистрацию горячих клавиш
    register_all_hotkeys()

    # Держим основной поток живым, чтобы фоновые потоки (hotkeys, config watcher) работали
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("\nВыход...")
    finally:
        config_manager.stop()
