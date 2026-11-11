# ai_helper.py

import threading
import sys
import os
import subprocess
import traceback
import requests

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QPushButton, QTextBrowser, QLineEdit,
                                QComboBox, QMessageBox, QPlainTextEdit)
from PySide6.QtGui import QFont, QTextCursor, QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, Signal, QThread

try:
    from config_manager import config_manager
    from config_writer import update_config_value, save_api_key, load_api_key
    from ai_providers import PROVIDERS, fetch_models, get_chat_url, build_headers, check_model_health
except ImportError:
    config_manager = None

    def update_config_value(k, v):
        pass

    def save_api_key(p, k):
        pass

    def load_api_key(p):
        return ""

    PROVIDERS = {}
    fetch_models = lambda p, k: []
    get_chat_url = lambda p, m="": ""
    build_headers = lambda p, k: {}
    check_model_health = lambda p, k, m: False

PROVIDER_NAMES = list(PROVIDERS.keys())

_open_ai_windows = []

DARK_BG = "#23232b"
LIGHT_BG = "#2d2d36"
WHITE = "#ffffff"
GRAY = "#b0b0b0"
BLUE = "#4a90e2"
GREEN = "#2ecc71"
RED = "#e74c3c"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {DARK_BG};
    color: {WHITE};
    font-family: "Segoe UI";
}}
QLineEdit, QPlainTextEdit {{
    background-color: {LIGHT_BG};
    border: 1px solid #3e3e4a;
    border-radius: 5px;
    padding: 5px;
    color: {WHITE};
    selection-background-color: {BLUE};
}}
QComboBox {{
    background-color: {LIGHT_BG};
    border: 1px solid #3e3e4a;
    border-radius: 3px;
    padding: 5px;
    min-width: 100px;
    color: {WHITE};
}}
QComboBox::drop-down {{
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {LIGHT_BG};
    color: {WHITE};
    selection-background-color: {BLUE};
}}
QPushButton {{
    border-radius: 4px;
    padding: 5px;
    font-weight: bold;
    color: {WHITE};
}}
QPushButton:hover {{
    background-color: #3e3e4a;
}}
"""


def _log(msg):
    print(f"[AI] {msg}", flush=True)


_dot_icons = {}


def _get_dot_icon(color):
    if color not in _dot_icons:
        dpr = 2.0
        size = 16
        pixmap = QPixmap(int(size * dpr), int(size * dpr))
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 8, 8)
        painter.end()
        _dot_icons[color] = QIcon(pixmap)
    return _dot_icons[color]


class FetchModelsThread(QThread):
    models_loaded = Signal(list, dict)

    def __init__(self, provider_name, api_key):
        super().__init__()
        self.provider_name = provider_name
        self.api_key = api_key
        self._stopped = False

    def run(self):
        _log(f"FetchModelsThread started: provider={self.provider_name}")
        try:
            models = fetch_models(self.provider_name, self.api_key)
            _log(f"FetchModelsThread got {len(models)} models, checking health...")
            health = {}
            for model in models:
                if self._stopped:
                    break
                is_ok = check_model_health(self.provider_name, self.api_key, model)
                health[model] = is_ok
                _log(f"  Model {model}: {'OK' if is_ok else 'UNAVAILABLE'}")
            if not self._stopped:
                self.models_loaded.emit(models, health)
        except Exception as e:
            _log(f"FetchModelsThread error: {e}")
            traceback.print_exc()
            if not self._stopped:
                self.models_loaded.emit([], {})

    def stop(self):
        self._stopped = True


class SendRequestThread(QThread):
    response_received = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, provider_name, api_key, model, prompt):
        super().__init__()
        self.provider_name = provider_name
        self.api_key = api_key
        self.model = model
        self.prompt = prompt
        self._stopped = False

    def run(self):
        url = get_chat_url(self.provider_name, self.model)
        headers = build_headers(self.provider_name, self.api_key)

        _log(f"SendRequestThread started: provider={self.provider_name}, model={self.model}")
        _log(f"URL: {url}")

        if self.provider_name == "Gemini":
            contents = [{"parts": [{"text": self.prompt}]}]
            data = {
                "contents": contents,
                "generationConfig": {"maxOutputTokens": 2048}
            }
        else:
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": self.prompt}],
                "max_tokens": 2048,
            }

        try:
            _log(f"Sending request to {self.provider_name}...")
            response = requests.post(url, headers=headers, json=data, timeout=120)
            _log(f"Response status: {response.status_code}")

            if not response.ok:
                try:
                    err_text = response.json().get('error', {}).get('message', response.text)
                except Exception:
                    err_text = response.text

                final_msg = f"API Error ({response.status_code}):\n{err_text}"
                if response.status_code == 429:
                    final_msg += "\n\nRate limit reached. Wait or switch model."
                if response.status_code == 401:
                    final_msg += "\n\nInvalid API key."

                _log(f"API error: {response.status_code} - {err_text[:200]}")
                if not self._stopped:
                    self.error_occurred.emit(final_msg)
                return

            result = response.json()

            if self.provider_name == "Gemini":
                text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "Empty response.")
            else:
                text = result['choices'][0]['message']['content'] if 'choices' in result and result['choices'] else "Empty response."

            _log(f"Response received: {len(text)} chars")
            if not self._stopped:
                self.response_received.emit(text)

        except Exception as e:
            _log(f"Request error: {e}")
            traceback.print_exc()
            if not self._stopped:
                self.error_occurred.emit(f"Connection error:\n{e}")

    def stop(self):
        self._stopped = True


class AIWindow(QMainWindow):
    def __init__(self, prompt_text):
        super().__init__()
        _log(f"AIWindow.__init__ called, id={id(self)}")
        self.setWindowTitle("AI Assistant")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setGeometry(100, 100, 650, 560)
        self.setStyleSheet(STYLESHEET)

        self.current_provider = config_manager.get('ai_provider', PROVIDER_NAMES[0]) if config_manager else PROVIDER_NAMES[0]
        self.api_key = load_api_key(self.current_provider)
        self.current_model = config_manager.get(f'{self.current_provider.lower()}_model', '') if config_manager else ''
        self.available_models = []
        self.model_health = {}
        self.fetch_thread = None
        self.request_thread = None

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # --- Provider ---
        provider_layout = QHBoxLayout()
        lbl_provider = QLabel("Provider:")
        lbl_provider.setFont(QFont("Segoe UI", 10, QFont.Bold))
        provider_layout.addWidget(lbl_provider)

        self.combo_provider = QComboBox()
        self.combo_provider.addItems(PROVIDER_NAMES)
        self.combo_provider.setCurrentText(self.current_provider)
        self.combo_provider.currentTextChanged.connect(self.on_provider_change)
        provider_layout.addWidget(self.combo_provider, 1)
        layout.addLayout(provider_layout)

        # --- API Key ---
        key_layout = QHBoxLayout()
        self.lbl_key = QLabel(f"{self.current_provider} API Key:")
        self.lbl_key.setFont(QFont("Segoe UI", 10, QFont.Bold))
        key_layout.addWidget(self.lbl_key)

        self.entry_key = QLineEdit()
        self.entry_key.setEchoMode(QLineEdit.Password)
        if self.api_key:
            self.entry_key.setText(self.api_key)
        self.entry_key.editingFinished.connect(lambda: self.save_key(silent=True))
        key_layout.addWidget(self.entry_key, 1)

        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.save_key)
        key_layout.addWidget(btn_save)
        layout.addLayout(key_layout)

        self.lbl_hint = QLabel(self._get_hint_text())
        self.lbl_hint.setStyleSheet(f"color: {GRAY}; font-size: 8pt;")
        layout.addWidget(self.lbl_hint)

        # --- Model ---
        model_layout = QHBoxLayout()
        lbl_model = QLabel("Model:")
        lbl_model.setFont(QFont("Segoe UI", 10, QFont.Bold))
        model_layout.addWidget(lbl_model)

        self.combo_models = QComboBox()
        self.combo_models.currentTextChanged.connect(self.on_model_change)
        model_layout.addWidget(self.combo_models, 1)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh_models)
        model_layout.addWidget(self.btn_refresh)
        layout.addLayout(model_layout)

        # --- Prompt ---
        lbl_prompt = QLabel("Prompt:")
        lbl_prompt.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(lbl_prompt)

        self.input_text = QPlainTextEdit()
        self.input_text.setMaximumHeight(120)
        self.input_text.setPlainText(prompt_text)
        layout.addWidget(self.input_text)

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        self.btn_send = QPushButton("Send")
        self.btn_send.setStyleSheet(f"background-color: {BLUE}; color: white; font-size: 12pt; padding: 8px;")
        self.btn_send.clicked.connect(self.start_request)
        btn_layout.addWidget(self.btn_send, 1)

        btn_config = QPushButton("config.txt")
        btn_config.clicked.connect(open_config_file)
        btn_layout.addWidget(btn_config)
        layout.addLayout(btn_layout)

        # --- Output ---
        lbl_resp = QLabel("Response:")
        lbl_resp.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(lbl_resp)

        self.output_text = QTextBrowser()
        self.output_text.setReadOnly(True)
        self.output_text.setOpenExternalLinks(True)
        self.output_text.setStyleSheet(
            "background-color: #f3f3f3; color: #1a1a1a; "
            "border: 1px solid #3e3e4a; border-radius: 5px; padding: 8px;")
        self.output_text.document().setDefaultFont(QFont("Segoe UI", 11))
        layout.addWidget(self.output_text, 1)

        _log(f"AIWindow.__init__ complete, provider={self.current_provider}, has_key={bool(self.api_key)}")
        self.refresh_models()

    def _get_hint_text(self):
        hints = {
            "NVIDIA": "Get key: build.nvidia.com  (40 req/min, free)",
            "Gemini": "Get key: aistudio.google.com/apikey",
            "OpenRouter": "Get key: openrouter.ai/keys",
        }
        return hints.get(self.current_provider, "") + "  |  Ключ сохраняется автоматически"

    def save_key(self, silent=False):
        key = self.entry_key.text().strip()
        self.api_key = key
        save_api_key(self.current_provider, key)
        _log(f"Key saved for {self.current_provider}, length={len(key)}")
        if key and not silent:
            QMessageBox.information(self, "Saved",
                                    f"{self.current_provider} API key saved. "
                                    f"It will persist after restart and program updates.")

    def on_provider_change(self, text):
        new_provider = text
        if new_provider == self.current_provider:
            return
        _log(f"Provider changed: {self.current_provider} -> {new_provider}")
        self.current_provider = new_provider
        self.lbl_key.setText(f"{self.current_provider} API Key:")
        self.lbl_hint.setText(self._get_hint_text())
        self.entry_key.clear()
        self.api_key = load_api_key(self.current_provider)
        if self.api_key:
            self.entry_key.setText(self.api_key)
        update_config_value("ai_provider", self.current_provider)
        self.refresh_models()

    def on_model_change(self, text):
        if text:
            clean = text.strip()
            if clean and clean != self.current_model:
                _log(f"Model changed: {self.current_model} -> {clean}")
                self.current_model = clean
                update_config_value(f'{self.current_provider.lower()}_model', self.current_model)

    def refresh_models(self):
        if not self.api_key:
            _log("refresh_models: no API key, skipping")
            self.combo_models.blockSignals(True)
            self.combo_models.clear()
            self.combo_models.addItem("Enter API key first")
            self.combo_models.blockSignals(False)
            return

        _log(f"refresh_models: fetching for {self.current_provider}")
        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("Loading...")

        if self.fetch_thread and self.fetch_thread.isRunning():
            _log("refresh_models: stopping previous fetch thread")
            self.fetch_thread.stop()
            self.fetch_thread.wait(2000)

        self.fetch_thread = FetchModelsThread(self.current_provider, self.api_key)
        self.fetch_thread.models_loaded.connect(self._on_models_loaded)
        self.fetch_thread.start()

    def _on_models_loaded(self, models, health):
        _log(f"_on_models_loaded: {len(models)} models received, {sum(1 for v in health.values() if v)} healthy")
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("Refresh")
        self.available_models = models
        self.model_health = health
        self.combo_models.blockSignals(True)
        self.combo_models.clear()
        if models:
            for m in models:
                icon = _get_dot_icon(GREEN) if health.get(m, False) else _get_dot_icon(RED)
                self.combo_models.addItem(icon, m)
            if self.current_model in models:
                self.combo_models.setCurrentText(self.current_model)
            else:
                self.current_model = models[0]
                self.combo_models.setCurrentText(self.current_model)
                update_config_value(f'{self.current_provider.lower()}_model', self.current_model)
        else:
            self.current_model = ""
            self.combo_models.addItem("No models found")
        self.combo_models.blockSignals(False)

    def start_request(self):
        prompt = self.input_text.toPlainText().strip()
        if not prompt:
            _log("start_request: empty prompt, skipping")
            return
        self.save_key(silent=True)
        if not self.api_key:
            _log("start_request: no API key")
            QMessageBox.critical(self, "No key", f"Enter your {self.current_provider} API key above!")
            return
        if not self.current_model:
            _log("start_request: no model selected")
            QMessageBox.critical(self, "No model", "No model selected. Click Refresh or enter a valid API key.")
            return

        _log(f"start_request: provider={self.current_provider}, model={self.current_model}, prompt_len={len(prompt)}")
        self.btn_send.setEnabled(False)
        self.btn_send.setText("Loading...")
        self.output_text.clear()

        if self.request_thread and self.request_thread.isRunning():
            _log("start_request: stopping previous request thread")
            self.request_thread.stop()
            self.request_thread.wait(2000)

        self.request_thread = SendRequestThread(self.current_provider, self.api_key, self.current_model, prompt)
        self.request_thread.response_received.connect(self._on_response)
        self.request_thread.error_occurred.connect(self._on_error)
        self.request_thread.start()

    def _on_response(self, text):
        _log(f"_on_response: {len(text)} chars")
        self.output_text.setMarkdown(text)
        self.output_text.verticalScrollBar().setValue(0)
        self.btn_send.setEnabled(True)
        self.btn_send.setText("Send")

    def _on_error(self, text):
        _log(f"_on_error: {text[:100]}")
        self.output_text.setPlainText(text)
        self.btn_send.setEnabled(True)
        self.btn_send.setText("Send")

    def closeEvent(self, event):
        _log(f"closeEvent: window id={id(self)}, closing...")
        if self in _open_ai_windows:
            _open_ai_windows.remove(self)

        for thread_name, thread in [("fetch", self.fetch_thread), ("request", self.request_thread)]:
            if thread and thread.isRunning():
                _log(f"closeEvent: stopping {thread_name} thread")
                thread.stop()
                if not thread.wait(3000):
                    _log(f"closeEvent: {thread_name} thread did not stop in 3s, detaching")

        _log(f"closeEvent: done, windows remaining: {len(_open_ai_windows)}")
        event.accept()


def open_config_file():
    cfg_path = "config.txt"
    if not os.path.exists(cfg_path):
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write("ai_provider=NVIDIA\n")

    if sys.platform == "win32":
        os.startfile(cfg_path)
    elif sys.platform == "darwin":
        subprocess.call(["open", cfg_path])
    else:
        subprocess.call(["xdg-open", cfg_path])


def open_in_ai(selection):
    _log(f"open_in_ai: selection='{selection}'")
    template = config_manager.get('prompt_template',
                                  "Explain the word: '{selection}' in Russian. Give an example sentence in the original language: ") if config_manager else "Explain: {selection}"
    try:
        final_prompt = template.format(selection=selection)
    except Exception:
        final_prompt = f"Explain: '{selection}'"
    window = AIWindow(final_prompt)
    window.show()
    _open_ai_windows.append(window)
    _log(f"open_in_ai: window created, total windows: {len(_open_ai_windows)}")
