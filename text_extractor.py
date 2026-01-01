# text_extractor.py

import numpy as np
import google.generativeai as genai
from config_manager import config_manager
import easyocr # Импортируем, но НЕ инициализируем сразу

# Глобальные переменные для ленивой загрузки (по умолчанию None)
_reader_ja = None
_reader_ar = None

def get_reader_ja():
    """Загружает EasyOCR для японского только при первом обращении."""
    global _reader_ja
    if _reader_ja is None:
        print("⚠ Gemini недоступен. Загрузка EasyOCR (JP) в память... Подождите...")
        _reader_ja = easyocr.Reader(['ja', 'en'], gpu=False)
    return _reader_ja

def get_reader_ar():
    """Загружает EasyOCR для арабского только при первом обращении."""
    global _reader_ar
    if _reader_ar is None:
        print("⚠ Gemini недоступен. Загрузка EasyOCR (AR) в память... Подождите...")
        _reader_ar = easyocr.Reader(['ar', 'en'], gpu=False)
    return _reader_ar


CANDIDATE_MODELS = [
    'gemini-2.0-flash-exp',
    'gemini-flash-latest',
    'gemini-pro-latest',
    'gemini-2.0-flash-lite-preview-02-05',
]

def _gemini_ocr_request(image, lang_code):
    api_key = config_manager.get('google_api_key')
    if not api_key:
        raise ValueError("Нет ключа API")

    genai.configure(api_key=api_key)

    if lang_code == 'ja':
        prompt = "Transcribe the Japanese text from this image exactly as it is. Return ONLY the text."
    elif lang_code == 'ar':
        prompt = "Transcribe the Arabic text from this image exactly as it is. Return ONLY the text."
    else:
        prompt = "Extract text from this image. Return ONLY the text."

    last_error = None
    for model_name in CANDIDATE_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content([prompt, image])
            if response.text:
                return response.text.strip()
        except Exception as e:
            error_str = str(e).lower()
            if "api key not valid" in error_str:
                raise e
            last_error = e
            continue
    raise last_error if last_error else ValueError("Все модели Gemini недоступны")


def extract_text_ja(image):
    # 1. Попытка Gemini
    try:
        if config_manager.get('google_api_key'):
            text = _gemini_ocr_request(image, 'ja')
            print(f"OCR (Gemini): {text}")
            return text
    except Exception as e:
        print(f"OCR: Gemini не справился, включаем локальный движок.")

    # 2. Фоллбек EasyOCR (Ленивая загрузка)
    try:
        reader = get_reader_ja() # <-- ВОТ ЗДЕСЬ происходит загрузка в память, только если мы сюда дошли
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
    # 1. Попытка Gemini
    try:
        if config_manager.get('google_api_key'):
            text = _gemini_ocr_request(image, 'ar')
            print(f"OCR (Gemini): {text}")
            return text
    except Exception as e:
        print(f"OCR: Gemini не справился, включаем локальный движок.")

    # 2. Фоллбек EasyOCR (Ленивая загрузка)
    try:
        reader = get_reader_ar() # <-- Ленивая загрузка
        img_np = np.array(image)
        results = reader.readtext(img_np, detail=1, paragraph=False)
        if not results: return ""
        best = max(results, key=lambda x: x[2])
        print(f"OCR (EasyOCR): {best[1]}")
        return best[1]
    except Exception as e:
        print(f"OCR (ar) Local error: {e}")
        return ""