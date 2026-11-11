# config_writer.py
import os
from ai_providers import encrypt_key, decrypt_key, get_machine_id
from key_storage import load_store, save_store

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
            if line.strip().startswith(f"{key_to_update}="):
                lines[i] = f"{key_to_update}={new_value}\n"
                key_found = True
                break

        if not key_found:
            lines.append(f"\n{key_to_update}={new_value}\n")

        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    except Exception as e:
        print(f"Ошибка при записи в файл конфигурации: {e}")


def save_api_key(provider_name: str, api_key: str):
    machine_id = get_machine_id()
    encrypted = encrypt_key(api_key, machine_id)
    config_key = f"enc_{provider_name.lower()}_api_key"
    store = load_store()
    store[config_key] = encrypted
    save_store(store)


def load_api_key(provider_name: str) -> str:
    machine_id = get_machine_id()
    config_key = f"enc_{provider_name.lower()}_api_key"
    store = load_store()
    if config_key in store:
        return decrypt_key(store[config_key], machine_id)

    # Миграция старых ключей из config.txt в постоянное хранилище
    from config_manager import config_manager
    encrypted = config_manager.get(config_key, '') if config_manager else ''
    if encrypted:
        plain = decrypt_key(encrypted, machine_id)
        if plain:
            save_api_key(provider_name, plain)
            return plain
    legacy_key = f"{provider_name.lower()}_api_key"
    legacy_value = config_manager.get(legacy_key, '') if config_manager else ''
    if legacy_value and not legacy_value.startswith("gAAAAA"):
        save_api_key(provider_name, legacy_value)
        return legacy_value
    return ""
