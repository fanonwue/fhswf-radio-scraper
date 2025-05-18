import re
from .base_extractor import AbstractSegmentExtractor
import spacy

class NewsSegmentExtractor(AbstractSegmentExtractor):
    """
    Extrahiert das gesamte Nachrichten-Segment aus einem spaCy Doc.
    Beginnt am Dokumentanfang und endet vor dem Wetter- oder Verkehrsteil.
    """
    def __init__(self, nlp_vocab=None):
        self.nlp_vocab = nlp_vocab
        self.END_KEYWORDS = [
            # Wetter
            "das wetter für deutschland", "wetterbericht", "wetteraussichten", "wettervorhersage",
            "und nun zum wetter", "kommen wir zum wetter", "ein blick auf das wetter",
            "das wetter in",
            # Verkehr
            "verkehrszentrum", "verkehrsmeldung", "verkehrsmeldungen", "achtung", "vorsicht",
            # WDR2
            "das war wdr aktuell.",  "das war wdr"
        ]

    def get_name(self) -> str:
        return "news_segments"

    def extract_segments(self, doc: spacy.tokens.Doc):
        sentences = list(doc.sents)
        segment_sents = []

        for sent in sentences:
            text_lower = sent.text.lower().strip()

            if any(end_kw in text_lower for end_kw in self.END_KEYWORDS):
                break
            segment_sents.append(sent)

        sentences_texts = [s.text.strip() for s in segment_sents if s.text.strip()]

        if sentences_texts:
            return [{
                "sentences_text": sentences_texts,
                "start_char": segment_sents[0].start_char,
                "end_char": segment_sents[-1].end_char
            }]
        return []
