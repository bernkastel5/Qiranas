# anki_integration.py

import requests
from config_manager import config_manager


def get_deck_names():
    """
    Запрашивает у AnkiConnect список всех доступных колод.
    Таймаут очень короткий (0.5с), чтобы не тормозить интерфейс, если Anki закрыт.
    """
    try:
        response = requests.post("http://localhost:8765", json={
            "action": "deckNames",
            "version": 6
        }, timeout=0.5).json()

        if response.get("error") is None:
            return sorted(response.get("result", []))
        else:
            return []
    except requests.exceptions.RequestException:
        # Anki закрыт или недоступен - это норма, просто возвращаем пустой список
        return []


def add_note_to_anki(term, reading, definition):
    # Читаем имя колоды прямо сейчас, чтобы настройки применялись без перезагрузки
    deck_name = config_manager.get('deckName', 'Mining')

    fields = {
        "Key": f"{term}【{reading}】" if reading else term,
        "Word": term,
        "WordReading": reading,
        "PrimaryDefinition": definition,
        # Остальные поля оставлены пустыми для совместимости с шаблоном "JP Mining Note"
        "PAOverride": "", "PAOverrideText": "", "AJTWordPitch": "",
        "PrimaryDefinitionPicture": "", "Sentence": "", "SentenceReading": "",
        "AltDisplayWord": "", "AltDisplaySentence": "", "AltDisplayPASentenceCard": "",
        "AltDisplayAudioCard": "", "AdditionalNotes": "", "Hint": "", "HintNotHidden": "",
        "IsSentenceCard": "", "IsTargetedSentenceCard": "", "IsClickCard": "",
        "IsHoverCard": "", "IsHintCard": "", "IsSentenceFirstCard": "", "IsAudioCard": "",
        "PAShowInfo": "", "PATestOnlyWord": "", "PADoNotTest": "", "PASeparateWordCard": "",
        "PASeparateSentenceCard": "", "SeparateAudioCard": "", "SeparateSentenceAudioCard": "",
        "Picture": "", "WordAudio": "", "SentenceAudio": "", "PAGraphs": "",
        "PAPositions": "", "FrequenciesStylized": "", "FrequencySort": "", "PASilence": "",
        "WordReadingHiragana": "", "YomichanWordTags": "", "SecondaryDefinition": "",
        "ExtraDefinitions": "", "UtilityDictionaries": "", "CardCache": "", "Comment": ""
    }

    note = {
        "deckName": deck_name,
        "modelName": "JP Mining Note",
        "fields": fields,
        "tags": ["mined"],
        "options": {
            "allowDuplicate": False
        }
    }
    try:
        response = requests.post("http://localhost:8765", json={
            "action": "addNote",
            "version": 6,
            "params": {"note": note}
        }, timeout=2)  # Тут таймаут побольше, нам важен результат
        return response.json()
    except Exception as e:
        return {"error": str(e)}