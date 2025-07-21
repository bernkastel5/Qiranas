# dictionary.py

import zipfile
import json
import os

def extract_plaintext(definition):
    """
    Рекурсивно извлекает только текст из сложных структур Yomichan (dict/list/str).
    Игнорирует картинки, стили, теги, возвращает только текстовые значения.
    """
    if isinstance(definition, str):
        return definition
    elif isinstance(definition, list):
        return "\n".join([extract_plaintext(item) for item in definition if item])
    elif isinstance(definition, dict):
        # Если это картинка или нечто без текстового содержимого — пропускаем
        if definition.get('tag') == 'img':
            return ""
        # Если есть 'content', вытаскиваем из него
        if 'content' in definition:
            return extract_plaintext(definition['content'])
        # Если есть 'data' с текстом (редко, но бывает)
        if 'data' in definition and isinstance(definition['data'], str):
            return definition['data']
        # Если это тег li, ul, div, span и т.д. — вытаскиваем только из content
        # Если нет content, пропускаем
        # Рекурсивно обходим все значения, но только если это не img
        return "\n".join([extract_plaintext(v) for k, v in definition.items() if k != 'tag' and v])
    else:
        return ""


def load_yomichan_dictionary(zip_path):
    entries = []
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            if name.startswith('term_bank_') and name.endswith('.json'):
                with zf.open(name) as f:
                    data = json.load(f)
                    entries.extend(data)
    return entries

def load_all_yomichan_dictionaries(directory):
    dictionaries = []
    for filename in os.listdir(directory):
        if filename.endswith('.zip'):
            path = os.path.join(directory, filename)
            print(f"Загружаю словарь: {filename}")
            dictionaries.append(load_yomichan_dictionary(path))
    return dictionaries

def lookup_word_yomichan(text, dictionaries):
    results = []
    search = text.strip()
    for dict_entries in dictionaries:
        for entry in dict_entries:
            if entry and len(entry) > 5 and entry[0] == search:
                definition = extract_plaintext(entry[5])
                results.append({
                    'term': entry[0],
                    'reading': entry[1],
                    'pos': entry[2],
                    'definition': definition
                })
    return results
