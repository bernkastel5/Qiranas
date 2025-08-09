import json
import webbrowser
import urllib.parse
import os
import subprocess
import sys

SETTINGS_FILE = 'settings.json'


def get_settings():
    if not os.path.exists(SETTINGS_FILE):
        print(f"ОШИБКА: Файл настроек '{SETTINGS_FILE}' не найден.")
        return None
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ОШИБКА: Не могу прочитать '{SETTINGS_FILE}'. Проверьте синтаксис JSON. Ошибка: {e}")
        return None


def _choose_default_service_name(settings):
    ai_services = settings.get('ai_services', []) if isinstance(settings, dict) else []
    names = [s.get('name') for s in ai_services if s.get('name')]
    if not names:
        return None
    if settings.get('default_service_name'):
        return settings.get('default_service_name')
    for prefer in ("ChatGPT", "Gemini", "DeepSeek"):
        if prefer in names:
            return prefer
    return names[0]


def open_in_ai(selection, service_name=None):
    settings = get_settings()
    if not settings:
        print("Не могу выполнить действие, так как настройки не были загружены.")
        return

    # Дефолтный промпт, если в настройках не задан
    prompt_template = settings.get(
        'prompt_template',
        "Объясни использование '{selection}' на русском языке. Приведи пример употребления с переводом."
    )
    prompt_text = prompt_template.format(selection=selection)
    encoded_prompt = urllib.parse.quote(prompt_text)

    ai_services = settings.get('ai_services', [])
    if not ai_services:
        print("В настройках нет ни одного сервиса (ai_services пуст).")
        return

    target_service_name = service_name or _choose_default_service_name(settings)
    # На случай, если и это не дало имени
    if not target_service_name:
        target_service_name = ai_services[0].get('name')

    # Ищем сервис по имени, иначе берём первый
    service = next((s for s in ai_services if s.get('name') == target_service_name), None)
    if not service:
        service = ai_services[0]
        target_service_name = service.get('name')

    service_url_template = service.get('url_template')
    if not service_url_template:
        print(f"У сервиса '{target_service_name}' отсутствует url_template.")
        return

    if '{prompt}' not in service_url_template:
        print(f"Предупреждение: шаблон URL сервиса '{target_service_name}' не содержит {{prompt}} — запрос может не передаться.")

    final_url = service_url_template.format(prompt=encoded_prompt)
    webbrowser.open_new_tab(final_url)


def open_settings_file():
    if not os.path.exists(SETTINGS_FILE):
        # Если файла нет, создаем его с дефолтным содержимым
        default_settings = {
            "ai_services": [
                {"name": "Gemini", "url_template": "https://gemini.google.com/app?q={prompt}"},
                {"name": "ChatGPT", "url_template": "https://chat.openai.com/?q={prompt}"},
                {"name": "DeepSeek", "url_template": "https://chat.deepseek.com/chat"}
            ],
            "default_service_name": "ChatGPT",
            "prompt_template": "Объясни использование '{selection}' на русском языке. Приведи пример употребления с переводом."
        }
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_settings, f, ensure_ascii=False, indent=2)
        print(f"Файл '{SETTINGS_FILE}' не был найден и был создан с настройками по умолчанию.")

    if sys.platform == "win32":
        os.startfile(SETTINGS_FILE)
    elif sys.platform == "darwin":  # macOS
        subprocess.call(["open", SETTINGS_FILE])
    else:  # linux
        subprocess.call(["xdg-open", SETTINGS_FILE])