# key_storage.py
import json
import os
import sys

_FILENAME = "ai_keys.json"


def get_storage_dir():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "Qiranas")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Qiranas")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "Qiranas")


def load_store():
    path = os.path.join(get_storage_dir(), _FILENAME)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_store(store):
    directory = get_storage_dir()
    path = os.path.join(directory, _FILENAME)
    try:
        os.makedirs(directory, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2)
        os.replace(tmp, path)
    except Exception as e:
        print(f"[keys] Не удалось сохранить ключи: {e}")
