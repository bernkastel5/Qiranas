# text_extractor.py

import easyocr
import numpy as np

reader_ja = easyocr.Reader(['ja', 'en'], gpu=False)
reader_ar = easyocr.Reader(['ar', 'en'], gpu=False)

def extract_text_ja(image):
    img_np = np.array(image)
    results = reader_ja.readtext(img_np, detail=1, paragraph=False)
    if not results:
        return ""
    best = max(results, key=lambda x: x[2])
    return best[1]

def extract_text_ar(image):
    img_np = np.array(image)
    results = reader_ar.readtext(img_np, detail=1, paragraph=False)
    if not results:
        return ""
    best = max(results, key=lambda x: x[2])
    return best[1]
