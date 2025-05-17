import re
from langdetect import detect, LangDetectException
from .base_extractor import AbstractSegmentExtractor
import spacy

class WeatherSegmentExtractor(AbstractSegmentExtractor):
    """
    Extrahiert Wetterberichtssegmente aus einem spaCy Doc.
    """
    def __init__(self, nlp_vocab=None):
        self.nlp_vocab = nlp_vocab

        self.START_KEYWORDS = [
            "das wetter für deutschland",
            "wetterbericht",
            "wetteraussichten",
            "wettervorhersage",
            "und nun zum wetter",
            "kommen wir zum wetter",
            "ein blick auf das wetter"
        ]

        self.RELEVANT_WEATHER_KEYWORDS = [
            "grad", "celsius", "sonne", "sonnig", "wolken", "wolkig", "bewölkt", "regen",
            "regnerisch", "schauer", "gewitter", "wind", "windig", "klar", "heiter",
            "temperaturen", "tiefstwerte", "höchstwerte", "niederschlag", "schnee",
            "frost", "nebel", "morgen", "heute nacht", "tagsüber", "aussichten",
            "mittag", "vormittag", "nachmittag", "abend", "früh", "später",
            "wechselhaft", "trocken", "feucht", "sturm", "orkan", "böen",
            "vorhersage", "wetterlage", "wetterentwicklung"
        ]

        self.END_SIGNAL_PHRASES = [
            "das neueste aus dem verkehrszentrum",
            "verkehrsmeldungen",
            "die zeit",
            "uhrzeit",
            "nachrichten",
            "sport",
            "kultur",
            "wirtschaft",
            "und nun die meldungen",
            "das waren die wetteraussichten",
            "soweit das wetter"
        ]
        self.MAX_CONSECUTIVE_IRRELEVANT_SENTENCES_TO_END = 2

    def get_name(self) -> str:
        return "weather_report_segments"

    def _is_relevant_weather_sentence(self, sentence_text_lower: str) -> bool:
        """Prüft, ob ein Satz relevante Wetter-Keywords enthält."""
        return any(re.search(r'\b' + re.escape(rel_kw) + r'\b', sentence_text_lower) for rel_kw in self.RELEVANT_WEATHER_KEYWORDS)

    def extract_segments(self, doc: spacy.tokens.Doc):
        sentences = list(doc.sents)
        detected_reports = []
        current_sentence_index = 0

        while current_sentence_index < len(sentences):
            start_sentence_obj = sentences[current_sentence_index]
            start_sentence_text_lower = start_sentence_obj.text.lower().strip()

            is_start_of_report = False
            for keyword in self.START_KEYWORDS:
                if keyword in start_sentence_text_lower:
                    is_start_of_report = True
                    break
            
            if not is_start_of_report:
                current_sentence_index += 1
                continue

            segment_start_char = start_sentence_obj.start_char
            current_report_sentences_obj = [start_sentence_obj]
            
            consecutive_irrelevant_count = 0
            idx_for_extension = current_sentence_index + 1

            while idx_for_extension < len(sentences):
                next_sentence_obj = sentences[idx_for_extension]
                next_sentence_text_lower = next_sentence_obj.text.lower().strip()

                if any(end_phrase in next_sentence_text_lower for end_phrase in self.END_SIGNAL_PHRASES):
                    break 
                
                if self._is_relevant_weather_sentence(next_sentence_text_lower):
                    current_report_sentences_obj.append(next_sentence_obj)
                    consecutive_irrelevant_count = 0
                else:
                    if len(next_sentence_obj.text.split()) < 7 and not any(end_kw in next_sentence_text_lower for end_kw in self.START_KEYWORDS + self.END_SIGNAL_PHRASES):
                         current_report_sentences_obj.append(next_sentence_obj)
                         consecutive_irrelevant_count +=1
                    else:
                        consecutive_irrelevant_count += 1
                    
                    if consecutive_irrelevant_count >= self.MAX_CONSECUTIVE_IRRELEVANT_SENTENCES_TO_END:
                        break
                
                idx_for_extension += 1

            german_report_sentences_texts = []
            for s_obj in current_report_sentences_obj:
                s_text = s_obj.text.strip()
                if not s_text:
                    continue
                try:
                    if len(s_text.split()) < 4 or detect(s_text) == 'de':
                        german_report_sentences_texts.append(s_text)
                except LangDetectException:
                     if len(s_text.split()) <= 5 :
                        german_report_sentences_texts.append(s_text)


            if german_report_sentences_texts:
                detected_reports.append({
                    "sentences_text": german_report_sentences_texts,
                    "start_char": segment_start_char,
                    "end_char": current_report_sentences_obj[-1].end_char
                })
            
            current_sentence_index = idx_for_extension
        
        return detected_reports
