# anki_integration.py

import requests
from config import read_config
from config_manager import config_manager

config = read_config('config.txt')
deck_name = config.get('deckName', 'Mining')

def add_note_to_anki(term, reading, definition):
    deck_name = config_manager.get('deckName', 'Mining')
    fields = {
        "Key": f"{term}【{reading}】" if reading else term,
        "Word": term,
        "WordReading": reading,
        "PAOverride": "",
        "PAOverrideText": "",
        "AJTWordPitch": "",
        "PrimaryDefinition": definition,
        "PrimaryDefinitionPicture": "",
        "Sentence": "",
        "SentenceReading": "",
        "AltDisplayWord": "",
        "AltDisplaySentence": "",
        "AltDisplayPASentenceCard": "",
        "AltDisplayAudioCard": "",
        "AdditionalNotes": "",
        "Hint": "",
        "HintNotHidden": "",
        "IsSentenceCard": "",
        "IsTargetedSentenceCard": "",
        "IsClickCard": "",
        "IsHoverCard": "",
        "IsHintCard": "",
        "IsSentenceFirstCard": "",
        "IsAudioCard": "",
        "PAShowInfo": "",
        "PATestOnlyWord": "",
        "PADoNotTest": "",
        "PASeparateWordCard": "",
        "PASeparateSentenceCard": "",
        "SeparateAudioCard": "",
        "SeparateSentenceAudioCard": "",
        "Picture": "",
        "WordAudio": "",
        "SentenceAudio": "",
        "PAGraphs": "",
        "PAPositions": "",
        "FrequenciesStylized": "",
        "FrequencySort": "",
        "PASilence": "",
        "WordReadingHiragana": "",
        "YomichanWordTags": "",
        "SecondaryDefinition": "",
        "ExtraDefinitions": "",
        "UtilityDictionaries": "",
        "CardCache": "",
        "Comment": ""
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
        result = requests.post("http://localhost:8765", json={
            "action": "addNote",
            "version": 6,
            "params": {"note": note}
        }).json()
        return result
    except Exception as e:
        return {"error": str(e)}
