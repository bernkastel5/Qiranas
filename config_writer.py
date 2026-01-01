# config_writer.py
import os

CONFIG_PATH = 'config.txt'


def update_config_value(key_to_update, new_value):
    """
    Находит строку с ключом в config.txt и заменяет её значение.
    Если ключ не найден, добавляет его в конец файла.
    """
    if not os.path.exists(CONFIG_PATH):
        print(f"Ошибка: Файл конфигурации '{CONFIG_PATH}' не найден.")
        return

    lines = []
    key_found = False
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            # Ищем строку, которая начинается с ключа и знака '='
            if line.strip().startswith(f"{key_to_update}="):
                lines[i] = f"{key_to_update}={new_value}\n"
                key_found = True
                break

        # Если ключ не был найден в файле, добавляем его
        if not key_found:
            lines.append(f"\n{key_to_update}={new_value}\n")

        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"Конфиг обновлен: {key_to_update} = {new_value}")

    except Exception as e:
        print(f"Ошибка при записи в файл конфигурации: {e}")
