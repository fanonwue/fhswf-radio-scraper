import re
import spacy
from langdetect import detect, LangDetectException
from .base_extractor import AbstractSegmentExtractor

from .shared_constants import is_sentence_ignorable 

NEWS_END_KEYWORDS_SHARED = [
    "wetter", "verkehr", "nachrichten",
    "das wetter für deutschland", "wetterbericht", "wetteraussichten", "wettervorhersage",
    "und nun zum wetter", "kommen wir zum wetter", "ein blick auf das wetter"
]
WEATHER_KEYWORDS_SHARED = [
    "grad", "celsius", "sonne", "sonnig", "wolken", "wolkig", "bewölkt", "regen",
    "regnerisch", "schauer", "gewitter", "wind", "windig", "klar", "heiter",
    "temperaturen", "tiefstwerte", "höchstwerte", "niederschlag", "schnee",
    "frost", "nebel", "morgen", "heute nacht", "tagsüber", "aussichten"
]
TRAFFIC_KEYWORDS_SHARED = [
    "stau", "unfall", "sperrung", "gesperrt", "baustelle", "stockender", "zähfließender",
    "gefahrenstelle", "umleitung", "verzögerung", "kilometer", "defekt", "langsam", "fahrbahn",
    "straße", "brücke", "tunnel", "fahrstreifen", "blockiert", "behinderung", "störung",
    "polizei", "rettungskräfte", "zwischen", "richtung", "kreuz", "anschlussstelle",
    "dreieck", "höhe", "abschnitt", "frei", "behoben", "aufgelöst",
    "a[0-9]+", "b[0-9]+", "autobahn", "bundesstraße"
]
MUSIC_INDICATOR_KEYWORDS = ["musik", "song", "livemusik", "konzert", "album", "band", "musiktitel"]
CONVERSATIONAL_CUES_LIST = [
    "hallo", "hi", "tschüss", "guten morgen", "guten abend", "danke", "bitte",
    "entschuldigung", "frage", "antwort", "interview", "gast", "studiogast",
    "geschichte", "erlebnis", "erzähl", "sag", "finde", "denke", "glaube", "meine",
    "hörer", "zuhörer", "anrufer", "schreibt uns", "ruft an", "grüße",
    "schön, dass sie da sind", "willkommen bei", "thema heute", "sprechen wir über",
    "was meinst du", "wie geht's", "meine damen und herren", "liebe hörerinnen und hörer",
    "witzig", "lustig", "spannend", "interessant", "unglaublich", "wahnsinn",
    "super", "klasse", "toll", "echt", "hier ist", "hier spricht"
]

class ConversationSegmentExtractor(AbstractSegmentExtractor):
    """
    Extrahiert Gesprächs- oder Moderationssegmente und filtert Nachrichten-, Wetter-,
    Verkehrs- und Songtexte heraus.
    """
    MIN_UNIQUE_SENTENCE_RATIO = 0.5 
    MIN_CONVERSATION_SENTENCES = 1
    MIN_CONVERSATION_WORDS = 1

    def __init__(self, nlp_vocab=None):
        self.nlp_vocab = nlp_vocab
        self.other_segment_keywords = set(
            NEWS_END_KEYWORDS_SHARED + WEATHER_KEYWORDS_SHARED + TRAFFIC_KEYWORDS_SHARED + MUSIC_INDICATOR_KEYWORDS
        )
        # Regex-Muster für Verkehrsstraßen
        self.traffic_regex_patterns = [re.compile(r"\b" + pat + r"\b", re.IGNORECASE)
                                       for pat in ["a[0-9]+", "b[0-9]+"]]

    def get_name(self) -> str:
        return "conversation_segments"

    def _is_song_lyrics(self, segment_texts: list[str]) -> bool:
        """
        Erkannt englische Lyrics oder sich wiederholende Refrains.
        """
        full_text = " ".join(segment_texts)
        try:
            if detect(full_text) != 'de':
                return True
        except LangDetectException:
            pass
        unique_ratio = len(set(segment_texts)) / max(len(segment_texts), 1)
        return unique_ratio < self.MIN_UNIQUE_SENTENCE_RATIO

    def _is_other_specific_segment(self, text_lower: str) -> bool:
        for kw in self.other_segment_keywords:
            if kw in text_lower:
                return True
        for pat in self.traffic_regex_patterns:
            if pat.search(text_lower):
                return True
        return False

    def _has_conversational_cues(self, texts: list[str]) -> bool:
        if len(texts) < self.MIN_CONVERSATION_SENTENCES:
            return False
        if sum(len(t.split()) for t in texts) < self.MIN_CONVERSATION_WORDS:
            return False
        full_lower = " ".join(texts).lower()
        if any(cue in full_lower for cue in CONVERSATIONAL_CUES_LIST) or '?' in full_lower:
            return True
        pronouns = ["ich","du","er","sie","es","wir","ihr","mein","dein"]
        if any(re.search(rf"\b{p}\b", full_lower) for p in pronouns):
            return True
        if len(texts) >= 3 and sum(len(t.split()) for t in texts) > 20:
            return True
        return False

    def extract_segments(self, doc: spacy.tokens.Doc):
        sentences = list(doc.sents)
        segments = []
        buffer = []
        start_char = -1
        for sent in sentences:
            txt = sent.text.strip()
            lower = txt.lower()
            if is_sentence_ignorable(lower) or self._is_other_specific_segment(lower):
                if buffer:
                    texts = [s.text.strip() for s in buffer]
                    if self._has_conversational_cues(texts) and not self._is_song_lyrics(texts):
                        segments.append({"sentences_text": texts,
                                         "start_char": start_char,
                                         "end_char": buffer[-1].end_char})
                    buffer = []
                continue
            if not buffer:
                start_char = sent.start_char
            buffer.append(sent)

        if buffer:
            texts = [s.text.strip() for s in buffer]
            if self._has_conversational_cues(texts) and not self._is_song_lyrics(texts):
                segments.append({"sentences_text": texts,
                                 "start_char": start_char,
                                 "end_char": buffer[-1].end_char})
        return segments
