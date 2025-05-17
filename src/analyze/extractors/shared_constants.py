import re

IGNORE_PHRASES_REGEX_LIST = [
    re.compile(r"Untertitelung des ZDF, \d{4}", re.IGNORECASE),
    re.compile(r"^\s*(werbung|jingle)\s*$", re.IGNORECASE),
    re.compile(r"^\s*SWR3\s*$", re.IGNORECASE),
    re.compile(r"^\s*Musik\s*$", re.IGNORECASE)
]

def is_sentence_ignorable(sentence_text: str) -> bool:
    """
    Prüft, ob ein Satz basierend auf der IGNORE_PHRASES_REGEX_LIST ignoriert werden soll.
    Beinhaltet auch eine Prüfung auf sehr kurze, nicht-alphabetische Zeilen.
    """
    text_processed = sentence_text.strip().lower()
    if not text_processed:
        return True

    for regex in IGNORE_PHRASES_REGEX_LIST:
        if regex.search(text_processed):
            return True
        
    if len(text_processed.split()) <= 2 and not any(c.isalpha() for c in text_processed):
        return True
        
    return False