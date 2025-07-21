# overlay.py

import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox
from anki_integration import add_note_to_anki
from dictionary import lookup_word_yomichan

MAX_WINDOWS = 32
open_windows = []

def show_overlay(results, dictionaries, parent=None):
    if len(open_windows) >= MAX_WINDOWS:
        messagebox.showwarning("Ограничение", f"Открыто слишком много окон (>{MAX_WINDOWS})")
        return

    # Список активных (не скрытых) индексов
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
    root.title("Результаты поиска")
    root.attributes('-topmost', True)
    root.geometry("600x500+100+100")

    def on_close():
        open_windows.remove(root)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    # Кнопка "Добавить в Anki"
    plus_btn = tk.Button(root, text="+", font=("Arial", 16), command=on_add_to_anki)
    plus_btn.pack(side=tk.TOP, anchor="ne", padx=10, pady=5)

    # Скроллируемый фрейм для выдач
    canvas = tk.Canvas(root)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Для каждой выдачи — отдельный фрейм с кнопкой "-" и ScrolledText
    for idx, result in enumerate(results):
        frame = tk.Frame(scroll_frame, bd=2, relief=tk.GROOVE, padx=5, pady=5)
        frame.pack(fill="x", pady=3, padx=5)
        text = f"{result['term']} [{result['reading']}] ({result['pos']}):\n{result['definition']}"

        minus_btn = tk.Button(frame, text="-", font=("Arial", 12), command=lambda i=idx, f=frame: hide_result(i, f))
        minus_btn.pack(side="right", padx=5, anchor="n")

        st = ScrolledText(frame, wrap=tk.WORD, font=("Arial", 13), height=6, width=40)
        st.insert(tk.END, text)
        st.config(state=tk.DISABLED)
        st.pack(side="left", fill="both", expand=True)

        # Двойной клик по слову — открыть новое окно
        def on_double_click(event, st=st):
            try:
                # Получаем выделенный текст, если есть
                selected = st.selection_get()
            except tk.TclError:
                selected = ""
            if not selected:
                # Если не выделено — пробуем взять слово под курсором
                index = st.index("@%d,%d" % (event.x, event.y))
                word_start = st.search(r'\m\w', index, backwards=True, regexp=True)
                word_end = st.search(r'\M\w', index, forwards=True, regexp=True)
                if word_start and word_end:
                    selected = st.get(word_start, word_end)
            selected = selected.strip()
            if selected:
                new_results = lookup_word_yomichan(selected, dictionaries)
                if new_results:
                    show_overlay(new_results, dictionaries, parent=root)
                else:
                    messagebox.showinfo("Нет результата", f"Слово '{selected}' не найдено в словарях.")

        st.bind("<Double-Button-1>", on_double_click)

    root.bind("<Escape>", lambda e: on_close())
    root.mainloop()