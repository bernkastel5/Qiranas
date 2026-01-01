# main.py

import sys
import threading
import keyboard
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot

from hotkey_manager import register_hotkey, unregister_hotkey
from screen_capture import capture_area_with_selection
from text_extractor import extract_text_ja, extract_text_ar
from dictionary import load_all_yomichan_dictionaries, lookup_word_yomichan
from overlay import show_overlay
from clipboard_utils import get_selected_text
from config_manager import ConfigManager

# --- Глобальная инициализация Словарей ---
# Делаем это ДО запуска Qt приложения
DICTIONARIES_DIR = 'resources/dictionaries'
print("Загрузка словарей (подключение к SQLite)...")
# Теперь это просто путь к БД, но для совместимости распаковываем
db_path, _, _ = load_all_yomichan_dictionaries(DICTIONARIES_DIR)
# Упаковываем обратно, чтобы передавать в функции
dictionaries = (db_path, None, None)
print("Словари готовы.")

config_manager = ConfigManager('config.txt')
current_hotkeys = {}


# --- МОСТ МЕЖДУ ПОТОКАМИ (Qt Signal Bridge) ---
class SignalBridge(QObject):
    """
    Этот класс нужен, чтобы безопасно передавать данные из фонового потока (hotkey)
    в главный поток (GUI).
    """
    request_show_overlay = Signal(str)  # Сигнал, несущий текст для поиска

    def __init__(self):
        super().__init__()
        # Подключаем сигнал к слоту (функции обработки)
        self.request_show_overlay.connect(self.handle_show_request)

    @Slot(str)
    def handle_show_request(self, text):
        """Эта функция выполнится СТРОГО в главном потоке."""
        if not text: return

        # 1. Поиск в БД (SQLite быстрый, можно делать и в UI потоке)
        results, freq_results, pitch_results = lookup_word_yomichan(text, *dictionaries)

        # 2. Открытие окна
        show_overlay(text, results, freq_results, pitch_results, dictionaries)


# Создаем глобальный мост
bridge = None


# --- Обработчики горячих клавиш (Выполняются в фоновом потоке) ---
def on_hotkey_clipboard():
    selected_text = get_selected_text()
    if selected_text:
        # Берем первое слово и отправляем сигнал главному потоку
        first_word = selected_text.strip().split()[0]
        print(f"Clipboard: {first_word}")
        bridge.request_show_overlay.emit(first_word)
    else:
        print("Не удалось получить выделенный текст.")


def on_hotkey_ocr_ja():
    try:
        # Скриншот и OCR делаем в фоне, чтобы не морозить GUI
        img = capture_area_with_selection()
        if img:
            text = extract_text_ja(img).strip()
            print(f"OCR JA: {text}")
            bridge.request_show_overlay.emit(text)
    except Exception as e:
        print(f"Ошибка в OCR (ja): {e}")


def on_hotkey_ocr_ar():
    try:
        img = capture_area_with_selection()
        if img:
            text = extract_text_ar(img).strip()
            print(f"OCR AR: {text}")
            bridge.request_show_overlay.emit(text)
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

    key_clipboard = config_manager.get('on_hotkey_clipboard', 'ctrl+shift+t')
    key_ocr_ja = config_manager.get('on_hotkey_ocr_ja', 'ctrl+shift+y')
    key_ocr_ar = config_manager.get('on_hotkey_ocr_ar', 'ctrl+shift+a')

    current_hotkeys['clipboard'] = register_hotkey(key_clipboard, on_hotkey_clipboard)
    current_hotkeys['ocr_ja'] = register_hotkey(key_ocr_ja, on_hotkey_ocr_ja)
    current_hotkeys['ocr_ar'] = register_hotkey(key_ocr_ar, on_hotkey_ocr_ar)

    print(f"Хоткеи обновлены: Clip={key_clipboard}, JP={key_ocr_ja}, AR={key_ocr_ar}")


if __name__ == "__main__":
    # 1. Создаем Qt Application (обязательно в главном потоке)
    app = QApplication(sys.argv)

    # Чтобы приложение не закрывалось, когда закрыто последнее окно словаря
    app.setQuitOnLastWindowClosed(False)

    # 2. Инициализируем мост
    bridge = SignalBridge()

    # 3. Регистрируем хоткеи
    config_manager.on_change(lambda conf: register_all_hotkeys())
    register_all_hotkeys()

    print("Программа запущена. Qt Event Loop активен.")

    # 4. Запускаем бесконечный цикл обработки событий Qt.
    # Вместо keyboard.wait() теперь работает app.exec().
    # Библиотека keyboard продолжает работать в своих фоновых потоках.
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nВыход...")
    finally:
        config_manager.stop()