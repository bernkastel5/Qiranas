# dictionary.py

import zipfile
import json
import os


def convert_pitch_to_pattern(reading: str, pitch_value: int) -> str:
    """
    Конвертирует числовое значение питча (стиль Yomichan) в бинарную строку.
    """
    mora_count = len(reading)
    if mora_count == 0 or pitch_value < 0:
        return ""

    if pitch_value == 0:  # Heiban
        return "0" + "1" * (mora_count - 1) + "0" if mora_count > 1 else "10"
    elif pitch_value == 1:  # Atamadaka
        return "1" + "0" * mora_count
    elif pitch_value == mora_count:  # Odaka
        return "0" + "1" * (mora_count - 1) + "0"
    elif 1 < pitch_value < mora_count:  # Nakadaka
        return "0" + "1" * (pitch_value - 1) + "0" * (mora_count - pitch_value + 1)

    return ""


def extract_plaintext(definition):
    """
    Рекурсивно извлекает только текст из сложных структур Yomichan.
    """
    if isinstance(definition, str): return definition
    if isinstance(definition, list): return "\n".join(filter(None, [extract_plaintext(item) for item in definition]))
    if isinstance(definition, dict):
        if definition.get('tag') == 'img': return ""
        if 'content' in definition: return extract_plaintext(definition['content'])
        return "\n".join(filter(None, [extract_plaintext(v) for k, v in definition.items() if k != 'tag']))
    return ""


def load_yomichan_dictionary(zip_path):
    # Словарь для хранения данных, разделенных по типу (term, term_meta)
    entries = {}
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                # ИСПРАВЛЕНО: Заменена ненадёжная логика со split на явную startswith
                file_key = None
                if name.startswith('term_meta_bank_'):
                    file_key = 'term_meta'
                elif name.startswith('term_bank_'):
                    file_key = 'term'

                # Если файл не подходит, пропускаем его
                if not file_key:
                    continue

                with zf.open(name) as f:
                    if file_key not in entries:
                        entries[file_key] = []
                    entries[file_key].extend(json.load(f))
    except (zipfile.BadZipFile, json.JSONDecodeError) as e:
        print(f"Ошибка при чтении словаря {zip_path}: {e}")
    return entries


def load_all_yomichan_dictionaries(directory):
    main_dicts = []
    freq_dicts = []
    pitch_dicts = []
    for filename in os.listdir(directory):
        if filename.endswith('.zip'):
            path = os.path.join(directory, filename)
            print(f"Загружаю словарь: {filename}")
            dict_data = load_yomichan_dictionary(path)

            is_pitch = False
            is_freq = False

            # Проверяем term_meta_bank, если он есть
            if 'term_meta' in dict_data:
                sample = dict_data['term_meta'][:20]
                if any(isinstance(e, list) and len(e) > 1 and e[1] == 'pitch' for e in sample):
                    is_pitch = True
                if any(isinstance(e, list) and len(e) > 1 and e[1] == 'freq' for e in sample):
                    is_freq = True

            if is_pitch:
                pitch_dicts.append((filename, dict_data['term_meta']))
            elif is_freq:
                freq_dicts.append((filename, dict_data['term_meta']))

            # Словарь может быть одновременно и питч-, и основным
            if 'term' in dict_data:
                main_dicts.append((filename, dict_data['term']))

    print(f"Загружено: {len(main_dicts)} основных, {len(freq_dicts)} частотных, {len(pitch_dicts)} питч-словарей.")
    return main_dicts, freq_dicts, pitch_dicts


def lookup_word_yomichan(text, main_dicts, freq_dicts, pitch_dicts):
    results = []
    search = text.strip()

    # 1. Поиск в основных словарях
    for fname, dict_entries in main_dicts:
        for entry in dict_entries:
            if isinstance(entry, list) and len(entry) > 5 and entry[0] == search:
                results.append({
                    'term': entry[0], 'reading': entry[1], 'pos': entry[2],
                    'definition': extract_plaintext(entry[5]),
                    'dict_name': fname.split('.')[0]
                })

    # 2. Поиск частотности (заглушка)
    freq_results = []

    # 3. Поиск питча
    pitch_results = []
    if results and pitch_dicts:
        readings_found = {res['reading'] for res in results if res.get('reading')}

        for fname, dict_entries in pitch_dicts:
            for entry in dict_entries:
                if isinstance(entry, list) and len(entry) == 3 and entry[0] == search and entry[1] == 'pitch':
                    pitch_data_obj = entry[2]
                    reading_from_pitch_dict = pitch_data_obj.get('reading')

                    if reading_from_pitch_dict in readings_found:
                        if pitch_data_obj.get('pitches') and len(pitch_data_obj['pitches']) > 0:
                            pitch_value = pitch_data_obj['pitches'][0].get('position')
                            if pitch_value is not None:
                                pattern = convert_pitch_to_pattern(reading_from_pitch_dict, pitch_value)
                                if pattern:
                                    pitch_results.append((fname, pattern, reading_from_pitch_dict))

    # Если для основного чтения питч не найден, а для других чтений есть, надо отобразить
    # Переделываем, как питч отдается, чтобы он был привязан к чтению.
    # Для простоты пока оставим как есть, в overlay.py будет использоваться чтение из results[0]
    final_pitch_results = []
    if pitch_results:
        # Для отображения в overlay.py пока берем питч, который соответствует первому чтению
        primary_reading = results[0].get('reading')
        for fname, pattern, reading in pitch_results:
            if reading == primary_reading:
                final_pitch_results.append((fname, pattern))

    return results, freq_results, final_pitch_results