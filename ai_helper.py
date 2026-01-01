#ai_helper.py

import json
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, font, ttk
import requests
import sys
import os
import subprocess

# Импорт твоих модулей управления конфигом
try:
    from config_manager import config_manager
    from config_writer import update_config_value
except ImportError:
    print("Внимание: модули config_manager или config_writer не найдены.")
    config_manager = None


    def update_config_value(k, v):
        pass

# === ОБНОВЛЕННЫЙ СПИСОК МОДЕЛЕЙ ===
AVAILABLE_MODELS = [
    "google/gemini-2.0-flash-exp:free",  # Самая умная из бесплатных сейчас
    "meta-llama/llama-3-8b-instruct:free",  # Самая быстрая и стабильная
    "deepseek/deepseek-r1:free",  # Оригинальный DeepSeek R1 (без Llama)
    "microsoft/phi-3-mini-128k-instruct:free",  # Легкая модель
    "huggingfaceh4/zephyr-7b-beta:free",  # Хорошая альтернатива
    "xiaomi/mimo-v2-flash:free"
]

MODEL_DISPLAY_NAMES = {
    "google/gemini-2.0-flash-exp:free": "Gemini 2.0 Flash (Google)",
    "meta-llama/llama-3-8b-instruct:free": "Llama 3 8B (Meta)",
    "deepseek/deepseek-r1:free": "DeepSeek R1 (Original)",
    "microsoft/phi-3-mini-128k-instruct:free": "Phi-3 Mini (Microsoft)",
    "huggingfaceh4/zephyr-7b-beta:free": "Zephyr 7B (HuggingFace)",
    "xiaomi/mimo-v2-flash:free": "MiMo-v2-Flash (Xiaomi)"
}


class AIWindow:
    def __init__(self, prompt_text):
        self.root = tk.Tk()
        self.root.title("AI Assistant")
        self.root.geometry("600x750")

        self.api_key = config_manager.get('openrouter_api_key', '') if config_manager else ''
        self.current_model = config_manager.get('openrouter_model', AVAILABLE_MODELS[0]) if config_manager else \
        AVAILABLE_MODELS[0]

        # ШРИФТЫ
        if "Segoe UI" in font.families():
            main_font_family = "Segoe UI"
        elif "Verdana" in font.families():
            main_font_family = "Verdana"
        else:
            main_font_family = "Arial"

        self.ui_font = (main_font_family, 10)
        self.text_font = (main_font_family, 11)
        self.bold_font = (main_font_family, 10, "bold")

        style = ttk.Style()
        style.configure("TCombobox", font=self.ui_font)

        # --- Блок выбора модели ---
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        lbl_model = tk.Label(top_frame, text="Модель:", font=self.bold_font)
        lbl_model.pack(side=tk.LEFT, padx=(0, 5))

        display_values = [MODEL_DISPLAY_NAMES.get(m, m) for m in AVAILABLE_MODELS]
        self.combo_models = ttk.Combobox(top_frame, values=display_values, state="readonly", font=self.ui_font)
        self.combo_models.pack(side=tk.LEFT, fill=tk.X, expand=True)

        current_display = MODEL_DISPLAY_NAMES.get(self.current_model, self.current_model)
        # Если старая модель из конфига больше недоступна, ставим первую из списка
        if current_display not in display_values:
            self.current_model = AVAILABLE_MODELS[0]
            current_display = MODEL_DISPLAY_NAMES[self.current_model]

        self.combo_models.set(current_display)
        self.combo_models.bind("<<ComboboxSelected>>", self.on_model_change)

        # --- Поле ввода ---
        lbl_prompt = tk.Label(self.root, text="Запрос:", font=self.bold_font)
        lbl_prompt.pack(pady=(10, 2), padx=10, anchor="w")

        self.input_text = scrolledtext.ScrolledText(self.root, height=5, font=self.text_font, wrap=tk.WORD)
        self.input_text.pack(fill=tk.X, padx=10, pady=5)
        self.input_text.insert(tk.END, prompt_text)

        # --- Кнопки ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        self.btn_send = tk.Button(btn_frame, text="Отправить запрос", command=self.start_request_thread,
                                  bg="#0078D7", fg="white", font=self.bold_font, height=2)
        self.btn_send.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_config = tk.Button(btn_frame, text="Config.txt", command=open_config_file, font=self.ui_font)
        btn_config.pack(side=tk.RIGHT)

        # --- Ответ ---
        lbl_resp = tk.Label(self.root, text="Ответ:", font=self.bold_font)
        lbl_resp.pack(pady=(10, 2), padx=10, anchor="w")

        self.output_text = scrolledtext.ScrolledText(self.root, font=self.text_font, wrap=tk.WORD, bg="#f3f3f3")
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # === ИСПРАВЛЕНИЕ КОПИРОВАНИЯ ===
        # Мы НЕ отключаем виджет (state=DISABLED), иначе нельзя копировать.
        # Вместо этого мы перехватываем нажатия клавиш и блокируем их.
        self.output_text.bind("<Key>", lambda e: self.block_input(e))

        self.root.mainloop()

    def block_input(self, event):
        # Разрешаем копирование (Ctrl+C или Command+C)
        if (event.state & 4 and event.keysym.lower() == 'c') or \
                (event.state & 8 and event.keysym.lower() == 'c'):  # Mac command
            return None  # Стандартное поведение

        # Разрешаем выделение всего (Ctrl+A)
        if (event.state & 4 and event.keysym.lower() == 'a'):
            return None

            # Блокируем любой другой ввод текста
        return "break"

    def on_model_change(self, event):
        selected_display = self.combo_models.get()
        real_model_id = next((k for k, v in MODEL_DISPLAY_NAMES.items() if v == selected_display), None)
        if real_model_id:
            self.current_model = real_model_id
            update_config_value("openrouter_model", self.current_model)

    def start_request_thread(self):
        prompt = self.input_text.get("1.0", tk.END).strip()
        if not prompt: return
        if not self.api_key:
            messagebox.showerror("Нет ключа", "В config.txt не найден 'openrouter_api_key'!")
            open_config_file()
            return

        self.btn_send.config(state=tk.DISABLED, text="Загрузка...")
        # Очистка поля (программно это можно делать, т.к. state=NORMAL)
        self.output_text.delete("1.0", tk.END)

        threading.Thread(target=self.send_request, args=(self.api_key, self.current_model, prompt), daemon=True).start()

    def send_request(self, api_key, model, prompt):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:1234",
            "X-Title": "Dictionary Helper"
        }
        data = {"model": model, "messages": [{"role": "user", "content": prompt}]}

        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            if not response.ok:
                try:
                    err_text = response.json().get('error', {}).get('message', response.text)
                except:
                    err_text = response.text

                final_msg = f"Ошибка API ({response.status_code}):\n{err_text}"
                if response.status_code == 429:
                    final_msg += "\n\nСОВЕТ: Модель перегружена. Выберите другую в списке сверху!"
                if response.status_code == 404:
                    final_msg += "\n\nСОВЕТ: Эта модель больше недоступна. Выберите другую!"

                self.root.after(0, self.update_output, final_msg)
                return

            result = response.json()
            text = result['choices'][0]['message']['content'] if 'choices' in result and result[
                'choices'] else "Пустой ответ."
            self.root.after(0, self.update_output, text)

        except Exception as e:
            self.root.after(0, self.update_output, f"Ошибка соединения:\n{e}")
        finally:
            self.root.after(0, self.reset_gui)

    def update_output(self, text):
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)

    def reset_gui(self):
        self.btn_send.config(state=tk.NORMAL, text="Отправить запрос")


# --- ЭКСПОРТИРУЕМЫЕ ФУНКЦИИ ---

def open_config_file():
    cfg_path = "config.txt"
    if not os.path.exists(cfg_path):
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write("openrouter_api_key=\nopenrouter_model=meta-llama/llama-3-8b-instruct:free\n")

    if sys.platform == "win32":
        os.startfile(cfg_path)
    elif sys.platform == "darwin":
        subprocess.call(["open", cfg_path])
    else:
        subprocess.call(["xdg-open", cfg_path])


def open_in_ai(selection):
    template = config_manager.get('prompt_template',
                                  "Объясни значение: '{selection}' на русском.") if config_manager else "Объясни: {selection}"
    try:
        final_prompt = template.format(selection=selection)
    except:
        final_prompt = f"Объясни значение: '{selection}'"
    AIWindow(final_prompt)