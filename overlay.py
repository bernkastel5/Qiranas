# overlay.py

import tkinter as tk
from tkinter import messagebox
from anki_integration import add_note_to_anki
from dictionary import lookup_word_yomichan
from ai_helper import open_in_ai, get_settings, open_settings_file

MAX_WINDOWS = 32
open_windows = []

# --- Цвета, шрифты и иконки ---

DARK_BG = "#23232b"
WHITE = "#ffffff"
GRAY = "#b0b0b0"
BLUE = "#4a90e2"
SCARLET_RED = "#e54b4b"
GREEN = "#6ae28d"
GREEN_BG = "#6ae28d"
FONT_MAIN = ("Segoe UI", 14)
FONT_READING = ("Segoe UI", 12, "italic")
FONT_LABEL = ("Segoe UI", 10, "bold")
FONT_WORD = ("Segoe UI", 28, "bold")
PITCH_FONT = ("Meiryo", 14)
PITCH_LINE_WIDTH = 2
PITCH_V_OFFSET = 6
PITCH_PARTICLE_RADIUS = 3
PITCH_PADDING_X = 5
PITCH_PADDING_Y = 15

ICON = "⭐"

def draw_pitch_on_canvas(canvas, reading, pattern):
    canvas.delete("all")
    if not reading or not pattern:
        return

    x_cursor = PITCH_PADDING_X
    center_y = PITCH_PADDING_Y
    prev_point = None

    for i, p in enumerate(pattern):
        is_high = (p == '1')
        is_particle = (i >= len(reading))
        line_y = center_y - PITCH_V_OFFSET if is_high else center_y + PITCH_V_OFFSET

        if is_particle:
            start_x = x_cursor + PITCH_PARTICLE_RADIUS
            end_x = x_cursor + PITCH_PARTICLE_RADIUS * 3
            canvas.create_oval(
                start_x,
                line_y - PITCH_PARTICLE_RADIUS,
                end_x,
                line_y + PITCH_PARTICLE_RADIUS,
                outline=GRAY,
                width=1
            )
            x_cursor = end_x + 2
        else:
            text_id = canvas.create_text(
                x_cursor, center_y,
                text=reading[i],
                font=PITCH_FONT,
                fill=WHITE,
                anchor="w"
            )
            start_x, _, end_x, _ = canvas.bbox(text_id)

            if prev_point:
                canvas.create_line(
                    prev_point['x'], prev_point['y'],
                    start_x, line_y,
                    fill=GREEN,
                    width=PITCH_LINE_WIDTH
                )

            canvas.create_line(start_x, line_y, end_x, line_y, fill=GREEN, width=PITCH_LINE_WIDTH)
            prev_point = {'x': end_x, 'y': line_y}
            x_cursor = end_x + 2

    bbox = canvas.bbox("all")
    if bbox:
        canvas.config(width=bbox[2] + PITCH_PADDING_X, height=bbox[3] + 5)


def show_overlay(searched_text, results, freq_results, pitch_results, all_dictionaries, parent=None):
    if len(open_windows) >= MAX_WINDOWS:
        messagebox.showwarning("Ограничение", f"Открыто слишком много окон (>{MAX_WINDOWS})")
        return

    root = tk.Toplevel(parent) if parent else tk.Tk()
    open_windows.append(root)
    root.title("Qiranas")
    root.configure(bg=DARK_BG)
    root.attributes('-topmost', True)

    # Определяем, что будет отображаться
    word_to_display = results[0]['term'] if results else searched_text

    def on_close():
        try:
            open_windows.remove(root)
        except ValueError:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    # --- Верхняя панель (ИИ + Anki) ---
    top_frame = tk.Frame(root, bg=DARK_BG)
    top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

    right_btns = tk.Frame(top_frame, bg=DARK_BG)
    right_btns.pack(side=tk.RIGHT, padx=10)

    # Вычислим имя сервиса по умолчанию (если нет default_service_name — подберём)
    try:
        _settings = get_settings()
    except Exception:
        _settings = None

    def pick_default_service_name(st):
        if not st or not isinstance(st, dict):
            return None
        names = [s.get('name') for s in st.get('ai_services', []) if s.get('name')]
        if not names:
            return None
        if st.get('default_service_name'):
            return st.get('default_service_name')
        # Приоритет известных
        for prefer in ("ChatGPT", "Gemini", "DeepSeek"):
            if prefer in names:
                return prefer
        return names[0]

    default_ai_name = pick_default_service_name(_settings)

    # Кнопка ИИ — создаём и упаковываем сразу
    try:
        robot_icon = tk.PhotoImage(data=ICON)
        ai_btn = tk.Button(
            right_btns,
            image=robot_icon,
            bg=GREEN_BG,
            relief=tk.FLAT,
            activebackground=GRAY,
            cursor="hand2",
            command=lambda: open_in_ai(word_to_display, default_ai_name)
        )
        ai_btn.image = robot_icon  # держим ссылку
    except Exception:
        # Фоллбек, если иконка не загрузится
        ai_btn = tk.Button(
            right_btns, text="⭐",
            bg=GREEN_BG, fg=WHITE,
            relief=tk.FLAT,
            activebackground=GRAY,
            activeforeground=WHITE,
            cursor="hand2",
            command=lambda: open_in_ai(word_to_display, default_ai_name)
        )
    ai_btn.pack(side=tk.RIGHT, padx=(0, 6), pady=2)

    # Контекстное меню ИИ (ПКМ / Ctrl+ЛКМ)
    ai_menu = tk.Menu(root, tearoff=0, bg=GREEN_BG, fg=WHITE, activebackground=BLUE)
    if _settings and isinstance(_settings, dict) and 'ai_services' in _settings:
        for service in _settings['ai_services']:
            name = service.get('name')
            if name:
                ai_menu.add_command(label=name, command=lambda s=name: open_in_ai(word_to_display, s))
    ai_menu.add_separator()
    ai_menu.add_command(label="Настроить...", command=open_settings_file)
    ai_btn.bind("<Button-3>", lambda e: ai_menu.post(e.x_root, e.y_root))
    ai_btn.bind("<Control-Button-1>", lambda e: ai_menu.post(e.x_root, e.y_root))

    if results:
        # --- СЛОВО НАЙДЕНО ---
        root.geometry("800x650+100+100")
        active_indices = list(range(len(results)))
        reading = results[0].get('reading', '')

        def on_add_to_anki():
            filtered = [results[i] for i in active_indices]
            if not filtered:
                return messagebox.showinfo("Anki", "Нет выбранных переводов для добавления.")
            combined_definition = "\n\n".join([r.get('definition', '') for r in filtered if r.get('definition')])
            resp = add_note_to_anki(word_to_display, reading, combined_definition)
            msg = "Карточка добавлена!" if resp.get("error") is None else f"Ошибка: {resp.get('error')}"
            messagebox.showinfo("Anki", msg)

        plus_btn = tk.Button(
            right_btns, text="+", font=("Segoe UI", 16), bg=BLUE, fg=WHITE, command=on_add_to_anki,
            relief=tk.FLAT, activebackground=BLUE, activeforeground=WHITE, cursor="hand2", width=3
        )
        plus_btn.pack(side=tk.RIGHT, padx=(0, 0), pady=2)

        # Универсальная информация
        universal_info_frame = tk.Frame(root, bg=DARK_BG)
        universal_info_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(universal_info_frame, text=word_to_display, font=FONT_WORD, fg=WHITE, bg=DARK_BG).pack(anchor="w")
        if reading and reading != word_to_display:
            tk.Label(universal_info_frame, text=reading, font=FONT_READING, fg=GRAY, bg=DARK_BG).pack(anchor="w")

        if pitch_results and reading:
            pitch_container = tk.Frame(universal_info_frame, bg=DARK_BG)
            pitch_container.pack(anchor="w", pady=(5, 0))
            for fname, pattern in pitch_results:
                pitch_entry_frame = tk.Frame(pitch_container, bg=DARK_BG)
                pitch_entry_frame.pack(anchor="w", pady=2)
                tk.Label(
                    pitch_entry_frame, text=f"{fname.split('.')[0]}:", font=FONT_LABEL, fg=GRAY, bg=DARK_BG
                ).pack(side=tk.LEFT, padx=(0, 10))
                pitch_canvas = tk.Canvas(pitch_entry_frame, bg=DARK_BG, highlightthickness=0)
                pitch_canvas.pack(side=tk.LEFT)
                draw_pitch_on_canvas(pitch_canvas, reading, pattern)

        if freq_results:
            freq_strs = [f"{fname.split('.')[0]}: {freq}" for fname, freq in freq_results]
            tk.Label(
                universal_info_frame, text=" | ".join(freq_strs), font=FONT_LABEL, fg=BLUE, bg=DARK_BG
            ).pack(anchor="w", pady=(5, 10))

        # Скроллируемый фрейм
        main_content_frame = tk.Frame(root, bg=DARK_BG)
        main_content_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(main_content_frame, bg=DARK_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(main_content_frame, orient="vertical", command=canvas.yview)

        scroll_frame = tk.Frame(canvas, bg=DARK_BG)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for idx, result in enumerate(results):
            frame = tk.Frame(scroll_frame, bg=DARK_BG, bd=1, relief=tk.SOLID)
            frame.pack(fill="x", pady=8, padx=10)

            entry_header_frame = tk.Frame(frame, bg=DARK_BG)
            entry_header_frame.pack(fill="x", padx=10, pady=5)

            def hide_and_remove(i=idx, f=frame):
                if i in active_indices:
                    active_indices.remove(i)
                f.pack_forget()

            minus_btn = tk.Button(
                entry_header_frame, text="−", font=("Segoe UI", 12, "bold"), bg=SCARLET_RED, fg=WHITE,
                command=hide_and_remove, relief=tk.FLAT, width=2, cursor="hand2", activebackground=SCARLET_RED
            )
            minus_btn.pack(side=tk.RIGHT, anchor="n", padx=(5, 0))

            term = result.get('term', '')
            reading_r = result.get('reading', '')
            pos = result.get('pos', '')
            head_text = f"{term} [{reading_r}] ({pos})".strip()
            head_label = tk.Label(
                entry_header_frame, text=head_text, font=FONT_MAIN, fg=WHITE, bg=DARK_BG,
                justify=tk.LEFT, wraplength=600
            )
            head_label.pack(side=tk.LEFT, fill=tk.X, expand=True, anchor="w")

            def_text = tk.Text(
                frame, font=FONT_MAIN, fg=WHITE, bg=DARK_BG, wrap="word", height=4, relief=tk.FLAT, borderwidth=0
            )
            def_text.insert(tk.END, result.get('definition', ''))
            def_text.config(state=tk.DISABLED)
            def_text.pack(fill="x", expand=True, padx=10, pady=(0, 10))

            def create_double_click_handler(text_widget, current_dictionaries):
                def on_double_click(event):
                    try:
                        selected = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                    except tk.TclError:
                        selected = text_widget.get(
                            f"@{event.x},{event.y} wordstart",
                            f"@{event.x},{event.y} wordend"
                        )
                    selected = selected.strip(".,!?\"' ")
                    if selected:
                        show_overlay(
                            selected,
                            *lookup_word_yomichan(selected, *current_dictionaries),
                            current_dictionaries,
                            parent=root
                        )
                return on_double_click

            def_text.bind("<Double-Button-1>", create_double_click_handler(def_text, all_dictionaries))

    else:
        # --- СЛОВО НЕ НАЙДЕНО ---
        root.geometry("400x150+100+100")

        main_frame = tk.Frame(root, bg=DARK_BG)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        tk.Label(main_frame, text=f"'{word_to_display}'", font=FONT_WORD, fg=WHITE, bg=DARK_BG).pack(pady=(0, 5))
        tk.Label(main_frame, text="Не найдено в словарях.", font=FONT_MAIN, fg=GRAY, bg=DARK_BG).pack()

    root.bind("<Escape>", lambda e: on_close())
    if not parent:
        root.mainloop()