# dictionary.py

import zipfile
import orjson
import os
import sqlite3
import gc  # Garbage Collector для принудительной очистки памяти

DB_FILENAME = "dictionaries.db"


def convert_pitch_to_pattern(reading: str, pitch_value: int) -> str:
    mora_count = len(reading)
    if mora_count == 0 or pitch_value < 0:
        return ""
    if pitch_value == 0:
        return "0" + "1" * (mora_count - 1) + "0" if mora_count > 1 else "10"
    elif pitch_value == 1:
        return "1" + "0" * mora_count
    elif pitch_value == mora_count:
        return "0" + "1" * (mora_count - 1) + "0"
    elif 1 < pitch_value < mora_count:
        return "0" + "1" * (pitch_value - 1) + "0" * (mora_count - pitch_value + 1)
    return ""


def extract_plaintext(definition):
    if isinstance(definition, str): return definition
    if isinstance(definition, list): return "\n".join(filter(None, [extract_plaintext(item) for item in definition]))
    if isinstance(definition, dict):
        if definition.get('tag') == 'img': return ""
        if 'content' in definition: return extract_plaintext(definition['content'])
        return "\n".join(filter(None, [extract_plaintext(v) for k, v in definition.items() if k != 'tag']))
    return ""


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('PRAGMA synchronous = OFF')  # Ускоряет запись
    c.execute('PRAGMA journal_mode = MEMORY')  # Ускоряет запись

    c.execute('''CREATE TABLE IF NOT EXISTS main_dict (
                    term TEXT, reading TEXT, pos TEXT, definition TEXT, dict_name TEXT
                )''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_main_term ON main_dict (term)''')
    c.execute('''CREATE TABLE IF NOT EXISTS meta_dict (
                    term TEXT, mode TEXT, reading TEXT, value INTEGER, dict_name TEXT
                )''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_meta_term ON meta_dict (term)''')
    conn.commit()
    return conn


def import_zip_to_db(zip_path, conn):
    try:
        dict_name = os.path.basename(zip_path).replace('.zip', '')
        c = conn.cursor()

        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if name.startswith('term_bank_'):
                    with zf.open(name) as f:
                        # orjson.loads работает быстрее и читает bytes напрямую
                        data = orjson.loads(f.read())
                        rows = []
                        for entry in data:
                            if isinstance(entry, list) and len(entry) > 5:
                                definition_text = extract_plaintext(entry[5])
                                rows.append((entry[0], entry[1], entry[2], definition_text, dict_name))
                        if rows:
                            c.executemany("INSERT INTO main_dict VALUES (?, ?, ?, ?, ?)", rows)

                elif name.startswith('term_meta_bank_'):
                    with zf.open(name) as f:
                        data = orjson.loads(f.read())
                        meta_rows = []
                        for entry in data:
                            if isinstance(entry, list) and len(entry) >= 3:
                                term = entry[0]
                                mode = entry[1]
                                content = entry[2]
                                if mode == 'freq':
                                    freq_val = None
                                    reading = None
                                    if isinstance(content, int):
                                        freq_val = content
                                    elif isinstance(content, dict):
                                        freq_val = content.get('value')
                                        reading = content.get('reading')
                                    if freq_val is not None:
                                        meta_rows.append((term, 'freq', reading, freq_val, dict_name))
                                elif mode == 'pitch':
                                    if isinstance(content, dict):
                                        reading = content.get('reading')
                                        pitches = content.get('pitches', [])
                                        if pitches:
                                            pos_val = pitches[0].get('position')
                                            if pos_val is not None:
                                                meta_rows.append((term, 'pitch', reading, pos_val, dict_name))
                        if meta_rows:
                            c.executemany("INSERT INTO meta_dict VALUES (?, ?, ?, ?, ?)", meta_rows)

            conn.commit()
            print(f"Импортирован: {dict_name}")

        # Принудительная очистка памяти после каждого тяжелого словаря
        gc.collect()

    except Exception as e:
        print(f"Ошибка при чтении {zip_path}: {e}")


def load_all_yomichan_dictionaries(directory):
    db_path = os.path.join(directory, DB_FILENAME)
    if not os.path.exists(db_path):
        print("Создание базы данных словарей (с использованием orjson)...")
        conn = init_db(db_path)
        files = [f for f in os.listdir(directory) if f.endswith('.zip')]
        for i, filename in enumerate(files):
            print(f"Обработка [{i + 1}/{len(files)}]: {filename}")
            import_zip_to_db(os.path.join(directory, filename), conn)
        conn.commit()
        conn.close()
        print("База данных готова!")
        gc.collect()
    else:
        print("Найдена существующая база данных словарей.")
    return db_path, None, None


def lookup_word_yomichan(text, db_path, _freq_ignored, _pitch_ignored):
    results = []
    freq_results = []
    pitch_results = []
    search = text.strip()
    if not search or not db_path:
        return [], [], []

    try:
        # Используем контекстный менеджер для авто-закрытия
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()

            c.execute("SELECT term, reading, pos, definition, dict_name FROM main_dict WHERE term = ?", (search,))
            rows = c.fetchall()

            readings_found = set()
            for r in rows:
                term, reading, pos, definition, dict_name = r
                results.append({
                    'term': term, 'reading': reading, 'pos': pos,
                    'definition': definition, 'dict_name': dict_name
                })
                if reading: readings_found.add(reading)

            c.execute("SELECT dict_name, reading, value FROM meta_dict WHERE term = ? AND mode = 'freq'", (search,))
            for r in c.fetchall():
                d_name, reading, val = r
                if reading is None or reading in readings_found:
                    freq_results.append((d_name, val))

            c.execute("SELECT dict_name, reading, value FROM meta_dict WHERE term = ? AND mode = 'pitch'", (search,))
            primary_reading = results[0]['reading'] if results else None
            for r in c.fetchall():
                d_name, reading, pos_val = r
                if reading and reading in readings_found:
                    pattern = convert_pitch_to_pattern(reading, pos_val)
                    if pattern:
                        if primary_reading and reading == primary_reading:
                            pitch_results.append((d_name, pattern))
    except Exception as e:
        print(f"Ошибка поиска в БД: {e}")

    return results, freq_results, pitch_results