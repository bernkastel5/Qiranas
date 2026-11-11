# text_extractor.py

import numpy as np
import google.generativeai as genai
from config_manager import config_manager
import easyocr
import os
from datetime import datetime

# Глобальные переменные для ленивой загрузки
_reader_ja = None
_reader_ar = None

# === НАСТРОЙКА ОТЛАДКИ ===
# Если True, программа будет сохранять скриншоты в папку, чтобы ты мог проверить,
# что именно видит нейросеть (не размыто ли, не обрезано ли).
DEBUG_SAVE_IMAGES = True


def get_reader_ja():
    global _reader_ja
    if _reader_ja is None:
        print("⚠ Gemini недоступен. Загрузка EasyOCR (JP)...")
        _reader_ja = easyocr.Reader(['ja', 'en'], gpu=False)
    return _reader_ja


def get_reader_ar():
    global _reader_ar
    if _reader_ar is None:
        print("⚠ Gemini недоступен. Загрузка EasyOCR (AR)...")
        _reader_ar = easyocr.Reader(['ar', 'en'], gpu=False)
    return _reader_ar


# Актуальный список моделей (от новых к старым)
CANDIDATE_MODELS = [
    'gemini-2.5-flash',  # Текущий стабильный стандарт (быстрый и умный)
]


def _gemini_ocr_request(image, lang_code):
    api_key = config_manager.get('google_api_key')
    if not api_key:
        raise ValueError("Нет ключа API")

    # Сохраняем картинку для проверки (если включен дебаг)
    if DEBUG_SAVE_IMAGES:
        if not os.path.exists("debug_screens"):
            os.makedirs("debug_screens")
        timestamp = datetime.now().strftime("%H-%M-%S")
        image.save(f"debug_screens/ocr_input_{timestamp}.png")

    genai.configure(api_key=api_key)

    # === 1. СИСТЕМНЫЙ ПРОМПТ (Роль) ===
    # Мы говорим модели, кто она, чтобы она не болтала лишнего.
    system_instruction = (
        "You are a specialized Optical Character Recognition (OCR) engine. "
        "Your ONLY job is to transcribe text from images with 100% precision. "
        "Do not explain, do not translate, do not add markdown formatting. "
        "Output strictly the text found in the image."
    )

    # === 2. ПОЛЬЗОВАТЕЛЬСКИЙ ПРОМПТ (Задача) ===
    if lang_code == 'ja':
        prompt = (
            "Transcribe the Japanese text in this image. "
            "If the text is vertical, read it from top to bottom, right to left. "
            "Ignore background noise. Output only the plain text."
        )
    elif lang_code == 'ar':
        prompt = (
            "Transcribe the Arabic text in this image including all diacritics (Harakat). "
            "Output only the plain text."
        )
    else:
        prompt = "Extract text from this image. Return ONLY the text."

    # === 3. КОНФИГУРАЦИЯ ГЕНЕРАЦИИ ===
    generation_config = genai.types.GenerationConfig(
        temperature=0.0,  # ВАЖНО: Ноль креативности. Только факты.
        top_p=1.0,
        max_output_tokens=200,
    )

    last_error = None

    for model_name in CANDIDATE_MODELS:
        try:
            # Создаем модель с системной инструкцией (доступно в новых версиях API)
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction
                )
            except TypeError:
                # Если библиотека старая и не поддерживает system_instruction
                model = genai.GenerativeModel(model_name=model_name)
                prompt = system_instruction + "\n\n" + prompt

            response = model.generate_content(
                [prompt, image],
                generation_config=generation_config
            )

            if response.text:
                cleaned_text = response.text.strip()
                # Иногда Gemini любит оборачивать код в ```text ... ```, убираем это
                cleaned_text = cleaned_text.replace("```text", "").replace("```", "").strip()
                return cleaned_text

        except Exception as e:
            error_str = str(e).lower()
            if "api key not valid" in error_str:
                raise e
            last_error = e
            # print(f"Модель {model_name} не сработала: {e}") # Раскомментируй для отладки
            continue

    raise last_error if last_error else ValueError("Все модели Gemini недоступны")


def extract_text_ja(image):
    try:
        if config_manager.get('google_api_key'):
            text = _gemini_ocr_request(image, 'ja')
            print(f"OCR (Gemini JP): {text}")
            return text
    except Exception as e:
        print(f"OCR: Gemini ошибка ({e}), переход на EasyOCR.")

    try:
        reader = get_reader_ja()
        img_np = np.array(image)
        results = reader.readtext(img_np, detail=1, paragraph=False)
        if not results: return ""
        best = max(results, key=lambda x: x[2])
        print(f"OCR (EasyOCR): {best[1]}")
        return best[1]
    except Exception as e:
        print(f"OCR (ja) Local error: {e}")
        return ""


def extract_text_ar(image):
    try:
        if config_manager.get('google_api_key'):
            text = _gemini_ocr_request(image, 'ar')
            print(f"OCR (Gemini AR): {text}")
            return text
    except Exception as e:
        print(f"OCR: Gemini ошибка ({e}), переход на EasyOCR.")

    try:
        reader = get_reader_ar()
        img_np = np.array(image)
        results = reader.readtext(img_np, detail=1, paragraph=False)
        if not results: return ""
        best = max(results, key=lambda x: x[2])
        print(f"OCR (EasyOCR): {best[1]}")
        return best[1]
    except Exception as e:
        print(f"OCR (ar) Local error: {e}")
        return ""