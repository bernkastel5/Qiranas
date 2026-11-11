# main.py

import sys
import threading
import keyboard
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot

from hotkey_manager import register_hotkey, unregister_hotkey
# Импортируем наш новый класс
from screen_capture import get_snipper
from text_extractor import extract_text_ja, extract_text_ar
from dictionary import load_all_yomichan_dictionaries, lookup_word_yomichan
from overlay import show_overlay
from clipboard_utils import get_selected_text
from config_manager import ConfigManager

# --- Инициализация ---
DICTIONARIES_DIR = 'resources/dictionaries'
print("Загрузка словарей...")
db_path, _, _ = load_all_yomichan_dictionaries(DICTIONARIES_DIR)
dictionaries = (db_path, None, None)
print("Словари готовы.")

config_manager = ConfigManager('config.txt')
current_hotkeys = {}


# --- BRIDGE (Мост между потоками) ---
class SignalBridge(QObject):
    request_show_overlay = Signal(str)  # Показать результат (для Clipboard)
    request_start_ocr = Signal(str)  # Запустить процесс OCR ('ja' или 'ar')

    def __init__(self):
        super().__init__()
        self.request_show_overlay.connect(self.handle_show_request)
        self.request_start_ocr.connect(self.handle_start_ocr)

        # Переменная, чтобы помнить, какой язык мы сейчас скриним
        self.current_lang_mode = 'ja'

        # Подключаем сигнал от самого скриншотера
        self.snipper = get_snipper()
        self.snipper.captured.connect(self.handle_image_captured)

    @Slot(str)
    def handle_show_request(self, text):
        """Обработка готового текста (из буфера или после OCR)"""
        if not text: return
        results, freq_results, pitch_results = lookup_word_yomichan(text, *dictionaries)
        show_overlay(text, results, freq_results, pitch_results, dictionaries)

    @Slot(str)
    def handle_start_ocr(self, lang):
        """Запуск скриншотера (выполняется в GUI потоке)"""
        self.current_lang_mode = lang
        self.snipper.start_snip()

    @Slot(object)
    def handle_image_captured(self, image):
        """Когда пользователь выделил область и отпустил мышь"""
        if image is None:
            print("Выделение отменено.")
            return

        print("Скриншот получен, распознавание...")

        # Важно: Распознавание (особенно EasyOCR) может быть долгим.
        # Чтобы интерфейс не завис намертво, лучше запустить это в отдельном потоке.
        threading.Thread(target=self._process_ocr_in_background, args=(image, self.current_lang_mode),
                         daemon=True).start()

    def _process_ocr_in_background(self, image, lang):
        try:
            text = ""
            if lang == 'ja':
                text = extract_text_ja(image).strip()
                print(f"OCR JA: {text}")
            elif lang == 'ar':
                text = extract_text_ar(image).strip()
                print(f"OCR AR: {text}")

            if text:
                # Результат отправляем обратно в GUI через сигнал
                self.request_show_overlay.emit(text)
        except Exception as e:
            print(f"Ошибка распознавания: {e}")


# Создаем глобальный мост
bridge = None


# --- Хоткеи (Фоновый поток) ---
def on_hotkey_clipboard():
    selected_text = get_selected_text()
    if selected_text:
        first_word = selected_text.strip().split()[0]
        bridge.request_show_overlay.emit(first_word)
    else:
        print("Не удалось получить текст из буфера.")


def on_hotkey_ocr_ja():
    # Просто просим главный поток начать процесс
    bridge.request_start_ocr.emit('ja')


def on_hotkey_ocr_ar():
    bridge.request_start_ocr.emit('ar')


# --- Регистрация ---
def register_all_hotkeys():
    for hotkey_id in current_hotkeys.values():
        try:
            unregister_hotkey(hotkey_id)
        except Exception:
            pass
    current_hotkeys.clear()

    key_clip = config_manager.get('on_hotkey_clipboard', 'ctrl+shift+t')
    key_ja = config_manager.get('on_hotkey_ocr_ja', 'ctrl+shift+y')
    key_ar = config_manager.get('on_hotkey_ocr_ar', 'ctrl+shift+a')

    current_hotkeys['clipboard'] = register_hotkey(key_clip, on_hotkey_clipboard)
    current_hotkeys['ocr_ja'] = register_hotkey(key_ja, on_hotkey_ocr_ja)
    current_hotkeys['ocr_ar'] = register_hotkey(key_ar, on_hotkey_ocr_ar)

    print(f"Хоткеи: {key_clip} - буфер обмена, {key_ja} - OCR японский, {key_ar} - OCR арабский")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Не закрывать программу без окон

    bridge = SignalBridge()

    config_manager.on_change(lambda conf: register_all_hotkeys())
    register_all_hotkeys()

    print("Qiranas запущен. Нажмите хоткеи для работы.")

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("Выход...")
    finally:
        config_manager.stop()