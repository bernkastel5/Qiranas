# overlay.py

import sys
import threading
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton, QTextEdit,
                               QScrollArea, QFrame, QComboBox, QMenu, QSizePolicy)
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QAction, QCursor, QTextCursor
from PySide6.QtCore import Qt, QSize, Signal, QObject, QThread

from anki_integration import add_note_to_anki, get_deck_names
from config_manager import config_manager
from config_writer import update_config_value
from dictionary import lookup_word_yomichan
from ai_helper import open_in_ai, open_config_file

# --- Стили (без изменений) ---
DARK_BG = "#23232b"
LIGHT_BG = "#2d2d36"
WHITE = "#ffffff"
GRAY = "#b0b0b0"
BLUE = "#4a90e2"
RED = "#e54b4b"
GREEN = "#6ae28d"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {DARK_BG};
    color: {WHITE};
    font-family: "Segoe UI";
}}
QScrollArea {{
    border: none;
    background-color: {DARK_BG};
}}
QScrollBar:vertical {{
    border: none;
    background: {DARK_BG};
    width: 10px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: #555;
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QTextEdit {{
    background-color: {LIGHT_BG};
    border: 1px solid #3e3e4a;
    border-radius: 5px;
    padding: 5px;
    selection-background-color: {BLUE};
}}
QComboBox {{
    background-color: {LIGHT_BG};
    border: 1px solid #3e3e4a;
    border-radius: 3px;
    padding: 5px;
    min-width: 100px;
}}
QComboBox::drop-down {{
    border: none;
}}
QPushButton {{
    border-radius: 4px;
    padding: 5px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: #3e3e4a;
}}
"""

MAX_WINDOWS = 32
open_windows = []
app_instance = None


def get_qt_app():
    global app_instance
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app_instance = app
    return app


# --- Воркер для загрузки колод в фоне ---
class AnkiLoaderThread(QThread):
    decks_loaded = Signal(list)  # Сигнал, который передаст данные в GUI

    def run(self):
        # Это выполняется в отдельном потоке и не тормозит окно
        try:
            decks = get_deck_names()
            self.decks_loaded.emit(decks if decks else [])
        except Exception:
            self.decks_loaded.emit([])


# --- Виджеты PitchAccent и DefinitionTextEdit без изменений (опускаю для краткости, они те же) ---
# ... (вставь сюда PitchAccentWidget и DefinitionTextEdit из прошлого ответа) ...
# Чтобы не дублировать огромный код, я просто напомню, что классы
# PitchAccentWidget и DefinitionTextEdit остаются такими же, как в предыдущем сообщении.
# Если копируешь целиком, возьми их из прошлого ответа.
# Ниже я приведу только изменившийся класс окна.

# <--- ВСТАВЬ СЮДА КЛАССЫ PitchAccentWidget И DefinitionTextEdit --->
class PitchAccentWidget(QWidget):
    def __init__(self, reading, pattern, parent=None):
        super().__init__(parent)
        self.reading = reading
        self.pattern = pattern
        self.setMinimumHeight(40)
        self.setMinimumWidth(len(reading) * 25 + 30)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont("Meiryo", 14)
        painter.setFont(font)
        pen_line = QPen(QColor(GREEN));
        pen_line.setWidth(2)
        pen_circle = QPen(QColor(GRAY));
        pen_circle.setWidth(1)
        x_cursor = 5;
        center_y = 20;
        v_offset = 6;
        radius = 3;
        prev_point = None

        from PySide6.QtCore import QPoint  # Нужен импорт
        for i, p in enumerate(self.pattern):
            is_high = (p == '1')
            is_particle = (i >= len(self.reading))
            line_y = center_y - v_offset if is_high else center_y + v_offset
            if is_particle:
                center_x = x_cursor + radius * 2
                painter.setPen(pen_circle);
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPoint(center_x, line_y), radius, radius)
                x_cursor = center_x + radius + 2
            else:
                painter.setPen(QColor(WHITE))
                painter.drawText(x_cursor, center_y + 5, self.reading[i])
                metrics = painter.fontMetrics()
                char_width = metrics.horizontalAdvance(self.reading[i])
                center_x = x_cursor + (char_width / 2)
                if prev_point:
                    painter.setPen(pen_line)
                    painter.drawLine(prev_point, QPoint(center_x, line_y))
                painter.drawLine(QPoint(x_cursor, line_y), QPoint(x_cursor + char_width, line_y))
                prev_point = QPoint(x_cursor + char_width, line_y)
                x_cursor += char_width + 2
        painter.end()


class DefinitionTextEdit(QTextEdit):
    def __init__(self, text, all_dictionaries, parent_overlay, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlainText(text)
        self.all_dictionaries = all_dictionaries
        self.parent_overlay = parent_overlay
        self.setFont(QFont("Segoe UI", 12))
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        doc_height = self.document().size().height()
        self.setMinimumHeight(min(150, int(doc_height + 20)))

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        cursor = self.textCursor()
        selected_text = cursor.selectedText().strip(".,!?\"' ")
        if selected_text:
            QApplication.processEvents()
            results, freq, pitch = lookup_word_yomichan(selected_text, *self.all_dictionaries)
            show_overlay(selected_text, results, freq, pitch, self.all_dictionaries)


class OverlayWindow(QMainWindow):
    def __init__(self, searched_text, results, freq_results, pitch_results, all_dictionaries):
        super().__init__()
        self.searched_text = searched_text
        self.results = results
        self.freq_results = freq_results
        self.pitch_results = pitch_results
        self.all_dictionaries = all_dictionaries

        self.setWindowTitle("Qiranas")
        self.setStyleSheet(STYLESHEET)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        self.word_to_display = results[0]['term'] if results else searched_text
        self.active_indices = list(range(len(results))) if results else []
        self.primary_reading = results[0].get('reading', '') if results else ''

        # --- СТАРТ ЗАГРУЗКИ КОЛОД (АСИНХРОННО) ---
        self.combo_deck = None  # Пока пусто
        self.deck_loader = AnkiLoaderThread()
        self.deck_loader.decks_loaded.connect(self.on_decks_loaded)
        self.deck_loader.start()

        self.setup_header()

        if results:
            self.setup_found_ui()
        else:
            self.setup_not_found_ui()

        open_windows.append(self)

    def closeEvent(self, event):
        if self in open_windows:
            open_windows.remove(self)
        event.accept()

    def on_decks_loaded(self, deck_names):
        """Вызывается, когда поток закончил загрузку колод."""
        if deck_names and self.combo_deck:
            self.combo_deck.clear()
            self.combo_deck.addItems(deck_names)
            current_deck = config_manager.get('deckName', 'Mining')
            index = self.combo_deck.findText(current_deck)
            if index >= 0:
                self.combo_deck.setCurrentIndex(index)
            self.combo_deck.setEnabled(True)
        elif self.combo_deck:
            self.combo_deck.setPlaceholderText("Anki недоступен")
            self.combo_deck.setEnabled(False)

    def setup_header(self):
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addStretch()

        # Кнопка ИИ
        self.btn_ai = QPushButton("⭐")
        self.btn_ai.setFixedSize(40, 30)
        self.btn_ai.setStyleSheet(f"background-color: {GREEN}; border: none;")
        self.btn_ai.setCursor(Qt.PointingHandCursor)
        self.btn_ai.clicked.connect(lambda: open_in_ai(self.word_to_display))
        self.btn_ai.setContextMenuPolicy(Qt.CustomContextMenu)
        self.btn_ai.customContextMenuRequested.connect(self.show_ai_menu)
        header_layout.addWidget(self.btn_ai)

        if self.results:
            self.btn_add = QPushButton("+")
            self.btn_add.setFixedSize(40, 30)
            self.btn_add.setStyleSheet(f"background-color: {BLUE}; font-size: 18px; border: none;")
            self.btn_add.setCursor(Qt.PointingHandCursor)
            self.btn_add.clicked.connect(self.add_to_anki)
            header_layout.addWidget(self.btn_add)

            # Создаем комбобокс сразу, но пустой и заблокированный
            self.combo_deck = QComboBox()
            self.combo_deck.setPlaceholderText("Загрузка...")
            self.combo_deck.setEnabled(False)
            self.combo_deck.currentTextChanged.connect(
                lambda text: update_config_value('deckName', text)
            )
            header_layout.addWidget(self.combo_deck)

        self.main_layout.addWidget(header_frame)

    def show_ai_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"background-color: {LIGHT_BG}; color: {WHITE};")
        action_ai = QAction("Открыть помощника", self)
        action_ai.triggered.connect(lambda: open_in_ai(self.word_to_display))
        menu.addAction(action_ai)
        menu.addSeparator()
        action_cfg = QAction("Открыть Config.txt", self)
        action_cfg.triggered.connect(open_config_file)
        menu.addAction(action_cfg)
        menu.exec(self.btn_ai.mapToGlobal(pos))

    def setup_found_ui(self):
        self.resize(800, 700)
        info_layout = QVBoxLayout()

        lbl_word = QLabel(self.word_to_display)
        lbl_word.setFont(QFont("Segoe UI", 28, QFont.Bold))
        info_layout.addWidget(lbl_word)

        if self.primary_reading and self.primary_reading != self.word_to_display:
            lbl_reading = QLabel(self.primary_reading)
            lbl_reading.setFont(QFont("Segoe UI", 14, QFont.Normal, True))
            lbl_reading.setStyleSheet(f"color: {GRAY};")
            info_layout.addWidget(lbl_reading)

        if self.pitch_results and self.primary_reading:
            pitch_container = QWidget()
            pitch_layout = QVBoxLayout(pitch_container)
            pitch_layout.setContentsMargins(0, 0, 0, 0)
            for fname, pattern in self.pitch_results:
                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)
                lbl_name = QLabel(f"{fname.split('.')[0]}:")
                lbl_name.setStyleSheet(f"color: {GRAY}; font-weight: bold;")
                row_layout.addWidget(lbl_name)
                pitch_widget = PitchAccentWidget(self.primary_reading, pattern)
                row_layout.addWidget(pitch_widget)
                row_layout.addStretch()
                pitch_layout.addWidget(row)
            info_layout.addWidget(pitch_container)

        if self.freq_results:
            freq_strs = [f"{fname.split('.')[0]}: {freq}" for fname, freq in self.freq_results]
            lbl_freq = QLabel(" | ".join(freq_strs))
            lbl_freq.setStyleSheet(f"color: {BLUE}; font-weight: bold;")
            lbl_freq.setWordWrap(True)
            info_layout.addWidget(lbl_freq)

        self.main_layout.addLayout(info_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(15)

        for idx, result in enumerate(self.results):
            self.create_entry_widget(idx, result)

        self.content_layout.addStretch()
        scroll.setWidget(content_widget)
        self.main_layout.addWidget(scroll)

    def create_entry_widget(self, idx, result):
        entry_frame = QFrame()
        entry_frame.setStyleSheet(f"background-color: {DARK_BG}; border: 1px solid #3e3e4a; border-radius: 5px;")
        entry_layout = QVBoxLayout(entry_frame)
        header_layout = QHBoxLayout()

        term = result.get('term', '')
        reading = result.get('reading', '')
        pos = result.get('pos', '')
        head_text = f"{term} [{reading}] ({pos})"

        lbl_head = QLabel(head_text)
        lbl_head.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_head.setStyleSheet("border: none; color: white;")
        lbl_head.setWordWrap(True)
        lbl_head.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        btn_remove = QPushButton("−")
        btn_remove.setFixedSize(30, 30)
        btn_remove.setStyleSheet(f"background-color: {RED}; color: white; border: none; font-weight: bold;")
        btn_remove.setCursor(Qt.PointingHandCursor)
        btn_remove.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        def remove_entry(idx=idx, frame=entry_frame):
            if idx in self.active_indices:
                self.active_indices.remove(idx)
            frame.hide()

        btn_remove.clicked.connect(remove_entry)
        header_layout.addWidget(lbl_head)
        header_layout.addWidget(btn_remove)
        entry_layout.addLayout(header_layout)

        def_text = result.get('definition', '')
        txt_edit = DefinitionTextEdit(def_text, self.all_dictionaries, self)
        entry_layout.addWidget(txt_edit)
        self.content_layout.addWidget(entry_frame)

    def setup_not_found_ui(self):
        self.resize(400, 200)
        lbl_word = QLabel(f"'{self.word_to_display}'")
        lbl_word.setFont(QFont("Segoe UI", 20, QFont.Bold))
        lbl_word.setAlignment(Qt.AlignCenter)
        lbl_msg = QLabel("Не найдено в словарях.")
        lbl_msg.setFont(QFont("Segoe UI", 12))
        lbl_msg.setStyleSheet(f"color: {GRAY};")
        lbl_msg.setAlignment(Qt.AlignCenter)
        self.main_layout.addStretch()
        self.main_layout.addWidget(lbl_word)
        self.main_layout.addWidget(lbl_msg)
        self.main_layout.addStretch()

    def add_to_anki(self):
        filtered = [self.results[i] for i in self.active_indices]
        if not filtered:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Anki", "Нет выбранных переводов для добавления.")
            return

        combined_definition = "\n\n".join([r.get('definition', '') for r in filtered if r.get('definition')])
        resp = add_note_to_anki(self.word_to_display, self.primary_reading, combined_definition)
        from PySide6.QtWidgets import QMessageBox
        if resp.get("error") is None:
            QMessageBox.information(self, "Anki", "Карточка добавлена!")
        else:
            QMessageBox.warning(self, "Anki", f"Ошибка: {resp.get('error')}")


def show_overlay(searched_text, results, freq_results, pitch_results, all_dictionaries, parent=None):
    if len(open_windows) >= MAX_WINDOWS:
        print("Слишком много окон")
        return

    app = get_qt_app()
    window = OverlayWindow(searched_text, results, freq_results, pitch_results, all_dictionaries)
    window.show()

    if len(open_windows) == 1:
        app.exec()