#overlay.py

import tkinter as tk
from tkinter import messagebox
from anki_integration import add_note_to_anki
from dictionary import lookup_word_yomichan

MAX_WINDOWS = 32
open_windows = []

# --- Цвета и шрифты для тёмной темы ---
DARK_BG = "#23232b"
WHITE = "#ffffff"
GRAY = "#b0b0b0"
BLUE = "#4a90e2"
PINK = "#e26a8d"
GREEN = "#6ae28d"
FONT_MAIN = ("Segoe UI", 14)
FONT_READING = ("Segoe UI", 12, "italic")
FONT_LABEL = ("Segoe UI", 10, "bold")
FONT_WORD = ("Segoe UI", 28, "bold")

# --- Новые константы для отрисовки питча ---
PITCH_FONT = ("Meiryo", 14)  # Используем японский шрифт для корректного отображения мор
PITCH_LINE_WIDTH = 2
PITCH_V_OFFSET = 6  # Вертикальное смещение линии от базовой линии текста
PITCH_PARTICLE_RADIUS = 3
PITCH_PADDING_X = 5
PITCH_PADDING_Y = 15  # Увеличим отступ сверху, чтобы линия не обрезалась


def draw_pitch_on_canvas(canvas, reading, pattern):
    """
    Отрисовывает графическое представление питч-акцента на tkinter.Canvas.
    - Линия рисуется над морой для высокого тона и под морой для низкого.
    - Обрабатывает тон частицы после слова.
    """
    # Очищаем холст на случай перерисовки
    canvas.delete("all")

    if not reading or not pattern:
        return

    # Координаты для отрисовки
    x_cursor = PITCH_PADDING_X
    center_y = PITCH_PADDING_Y
    prev_point = None

    # Проходим по всем элементам паттерна
    for i in range(len(pattern)):
        is_high = pattern[i] == '1'
        is_particle = i >= len(reading)

        # Определяем Y-координату линии питча
        # Для высокого тона Y выше, для низкого - ниже
        line_y = center_y - PITCH_V_OFFSET if is_high else center_y + PITCH_V_OFFSET

        if is_particle:
            # Рисуем кружок для частицы
            start_x = x_cursor + PITCH_PARTICLE_RADIUS
            end_x = x_cursor + PITCH_PARTICLE_RADIUS * 3
            canvas.create_oval(
                start_x, line_y - PITCH_PARTICLE_RADIUS,
                         start_x + PITCH_PARTICLE_RADIUS * 2, line_y + PITCH_PARTICLE_RADIUS,
                outline=GRAY, width=1
            )
            current_char_width = PITCH_PARTICLE_RADIUS * 4
        else:
            # Рисуем мору (слог)
            mora = reading[i]
            text_id = canvas.create_text(x_cursor, center_y, text=mora, font=PITCH_FONT, fill=WHITE, anchor="w")
            # Получаем реальные размеры отрисованного текста
            bbox = canvas.bbox(text_id)
            start_x, end_x = bbox[0], bbox[2]
            current_char_width = end_x - start_x

        # Соединяем с предыдущей точкой, если она есть
        if prev_point:
            # Рисуем вертикальную линию для смены тона
            canvas.create_line(prev_point['x'], prev_point['y'], start_x, line_y, fill=GREEN, width=PITCH_LINE_WIDTH)

        # Рисуем горизонтальную линию над/под морой
        canvas.create_line(start_x, line_y, end_x, line_y, fill=GREEN, width=PITCH_LINE_WIDTH)

        # Сохраняем конечную точку текущего сегмента для следующей итерации
        prev_point = {'x': end_x, 'y': line_y}
        x_cursor = end_x + 2  # Небольшой отступ между морами

    # Обновляем размеры canvas, чтобы вместить всю отрисовку
    bbox = canvas.bbox("all")
    if bbox:
        canvas.config(width=bbox[2] + PITCH_PADDING_X, height=bbox[3] + 5)


def show_overlay(results, freq_results, pitch_results, dictionaries, parent=None):
    if len(open_windows) >= MAX_WINDOWS:
        messagebox.showwarning("Ограничение", f"Открыто слишком много окон (>{MAX_WINDOWS})")
        return

    active_indices = list(range(len(results)))

    def hide_result(idx, frame):
        if idx in active_indices:
            active_indices.remove(idx)
        frame.pack_forget()

    def on_add_to_anki():
        filtered = [results[i] for i in active_indices]
        if not filtered:
            messagebox.showinfo("Anki", "Нет выбранных переводов для добавления.")
            return
        all_definitions = [r['definition'] for r in filtered if r['definition']]
        combined_definition = "\n\n".join(all_definitions)
        term = filtered[0]['term']
        reading = filtered[0]['reading']
        resp = add_note_to_anki(term, reading, combined_definition)
        msg = "Карточка добавлена!" if resp.get("error") is None else f"Ошибка: {resp.get('error')}"
        messagebox.showinfo("Anki", msg)

    root = tk.Toplevel(parent) if parent else tk.Tk()
    open_windows.append(root)
    root.title("Qiranas")
    root.configure(bg=DARK_BG)
    root.geometry("800x650+100+100")
    root.attributes('-topmost', True)

    def on_close():
        open_windows.remove(root)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    # --- Верхняя панель с кнопкой Anki ---
    top_frame = tk.Frame(root, bg=DARK_BG)
    top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
    plus_btn = tk.Button(top_frame, text="+", font=("Segoe UI", 16), bg=BLUE, fg=WHITE, command=on_add_to_anki,
                         relief=tk.FLAT, activebackground=BLUE, activeforeground=WHITE)
    plus_btn.pack(side=tk.RIGHT, padx=10)

    # --- Верхняя часть: слово, чтение, питч, частотность ---
    # Главный фрейм для универсальной информации
    universal_info_frame = tk.Frame(root, bg=DARK_BG)
    universal_info_frame.pack(fill=tk.X, padx=20, pady=5)

    if results:
        main = results[0]
        word = main['term']
        reading = main.get('reading', '')
    else:
        word = reading = ""

    word_label = tk.Label(universal_info_frame, text=word, font=FONT_WORD, fg=WHITE, bg=DARK_BG)
    word_label.pack(anchor="w")

    if reading and reading != word:
        reading_label = tk.Label(universal_info_frame, text=reading, font=FONT_READING, fg=GRAY, bg=DARK_BG)
        reading_label.pack(anchor="w")

    # --- Питч (новая графическая реализация) ---
    if pitch_results and reading:
        # Контейнер для всех вариантов питча
        pitch_container = tk.Frame(universal_info_frame, bg=DARK_BG)
        pitch_container.pack(anchor="w", pady=(5, 0))

        for fname, pattern in pitch_results:
            # Создаем фрейм для одной записи питча (название словаря + графика)
            pitch_entry_frame = tk.Frame(pitch_container, bg=DARK_BG)
            pitch_entry_frame.pack(anchor="w", pady=2)

            # Название словаря
            dict_name_label = tk.Label(pitch_entry_frame, text=f"{fname.split('.')[0]}:", font=FONT_LABEL, fg=GRAY,
                                       bg=DARK_BG)
            dict_name_label.pack(side=tk.LEFT, padx=(0, 10), anchor='center')

            # Холст для отрисовки питча
            pitch_canvas = tk.Canvas(pitch_entry_frame, bg=DARK_BG, highlightthickness=0)
            pitch_canvas.pack(side=tk.LEFT, anchor='center')

            # Вызываем новую функцию отрисовки
            draw_pitch_on_canvas(pitch_canvas, reading, pattern)

    # --- Частотность ---
    if freq_results:
        freq_label = tk.Label(universal_info_frame,
                              text=" | ".join([f"{fname.split('.')[0]}: {freq}" for fname, freq in freq_results]),
                              font=FONT_LABEL, fg=BLUE, bg=DARK_BG)
        freq_label.pack(anchor="w", pady=(5, 10))

    # --- Скроллируемый фрейм для словарных выдач ---
    main_content_frame = tk.Frame(root, bg=DARK_BG)
    main_content_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(main_content_frame, bg=DARK_BG, highlightthickness=0)
    scrollbar = tk.Scrollbar(main_content_frame, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg=DARK_BG)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    for idx, result in enumerate(results):
        frame = tk.Frame(scroll_frame, bg=DARK_BG, bd=1, relief=tk.SOLID)
        frame.pack(fill="x", pady=8, padx=10)

        # --- Словарная выдержка ---
        entry_header_frame = tk.Frame(frame, bg=DARK_BG)
        entry_header_frame.pack(fill="x", padx=10, pady=5)

        head = f"{result['term']} [{result['reading']}]"
        head_label = tk.Label(entry_header_frame, text=head, font=FONT_MAIN, fg=WHITE, bg=DARK_BG, justify=tk.LEFT)
        head_label.pack(side=tk.LEFT, anchor="w")

        pos_label = tk.Label(entry_header_frame, text=f"({result['pos']})", font=FONT_READING, fg=GRAY, bg=DARK_BG)
        pos_label.pack(side=tk.LEFT, anchor="w", padx=5)

        # Кнопка "-" для скрытия
        minus_btn = tk.Button(entry_header_frame, text="−", font=("Segoe UI", 12, "bold"), bg=PINK, fg=WHITE,
                              command=lambda i=idx, f=frame: hide_result(i, f), relief=tk.FLAT, activebackground=PINK,
                              activeforeground=WHITE, width=2)
        minus_btn.pack(side=tk.RIGHT, anchor="n")

        # Перевод
        def_text = tk.Text(frame, font=FONT_MAIN, fg=WHITE, bg=DARK_BG, wrap="word", height=4, relief=tk.FLAT,
                           borderwidth=0)
        def_text.insert(tk.END, result.get('definition', ''))
        def_text.config(state=tk.DISABLED)
        def_text.pack(fill="x", expand=True, padx=10, pady=(0, 10))

        # Двойной клик по слову — открыть новое окно
        def create_double_click_handler(text_widget):
            def on_double_click(event):
                try:
                    selected = text_widget.selection_get()
                except tk.TclError:
                    selected = ""

                if not selected:
                    index = text_widget.index(f"@{event.x},{event.y}")
                    word_start = text_widget.search(r'\m\w', index, backwards=True, regexp=True, nocase=True)
                    word_end = text_widget.search(r'\w\M', f"{word_start}", forwards=True, regexp=True, nocase=True)
                    if word_start and word_end:
                        selected = text_widget.get(word_start, word_end)

                selected = selected.strip()
                if selected:
                    new_results, new_freq, new_pitch = lookup_word_yomichan(selected, dictionaries[0], dictionaries[1],
                                                                            dictionaries[2])
                    if new_results:
                        show_overlay(new_results, new_freq, new_pitch, dictionaries, parent=root)
                    else:
                        messagebox.showinfo("Нет результата", f"Слово '{selected}' не найдено в словарях.")

            return on_double_click

        def_text.bind("<Double-Button-1>", create_double_click_handler(def_text))

    root.bind("<Escape>", lambda e: on_close())
    root.mainloop()
