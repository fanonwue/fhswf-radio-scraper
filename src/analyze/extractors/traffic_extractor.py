import re
import spacy
from spacy.matcher import Matcher
from langdetect import detect, LangDetectException

from .base_extractor import AbstractSegmentExtractor
from .shared_constants import is_sentence_ignorable

class TrafficSegmentExtractor(AbstractSegmentExtractor):
    """
    Extrahiert Verkehrsberichtssegmente aus einem spaCy Doc.
    """
    def __init__(self, nlp_vocab):
        self.nlp_vocab = nlp_vocab
        self.matcher = Matcher(self.nlp_vocab)
        self._setup_matcher()

        self.START_KEYWORDS = ["verkehrszentrum", "verkehrsmeldung", "verkehrsmeldungen", "achtung", "vorsicht"]
        self.RELEVANT_TRAFFIC_KEYWORDS = [
            "stau", "unfall", "sperrung", "gesperrt", "baustelle", "stockender",
            "zähfließender", "gefahrenstelle", "umleitung", "verzögerung", "geisterfahrer",
            "unfallstelle", "kilometer", "defekt", "langsam", "fahrbahn", "straße", "brücke", "tunnel",
            "fahrstreifen", "blockiert", "behinderung", "störung", "person", "personen",
            "polizei", "rettungskräfte", "zwischen", "richtung", "kreuz", "anschlussstelle",
            "dreieck", "höhe", "abschnitt", "frei", "behoben", "aufgelöst", "super",
            "perfekt", "endlich", "überbrückungsmeldung", "achtung", "vorsicht",
            "bis", "wegen", "nach", "stunde", "minute"
        ]
        self.END_SIGNAL_PHRASES = [
            "alle verkehrsinfos auch für eure strecke", "alle verkehrsinfos jetzt auf",
            "alle infos auf", "mehr infos auf", "weitere infos auf", "details auf",
            "jetzt auf swr3.de"
        ]
        self.MAX_SENTENCES_AFTER_START_FOR_ROAD = 15
        self.MAX_CONSECUTIVE_IRRELEVANT_SENTENCES_TO_END = 4

    def _setup_matcher(self):
        ROAD_PATTERNS = [
            [{"LOWER": "a"}, {"IS_DIGIT": True}],
            [{"LOWER": "b"}, {"IS_DIGIT": True}],
            [{"TEXT": {"REGEX": "^[AaBb]\\d+$"}}],
            [{"LOWER": "autobahn"}, {"IS_DIGIT": True}],
            [{"LOWER": "bundesstraße"}, {"IS_DIGIT": True}]
        ]
        self.matcher.add("ROAD", ROAD_PATTERNS)

    def get_name(self) -> str:
        return "traffic_report_segments"

    def extract_segments(self, doc: spacy.tokens.Doc):
        sentences = list(doc.sents)
        detected_reports = []
        current_sentence_index = 0

        while current_sentence_index < len(sentences):
            start_sentence_obj = sentences[current_sentence_index]
            start_sentence_text_lower = start_sentence_obj.text.lower()
            is_start_of_report = any(keyword in start_sentence_text_lower for keyword in self.START_KEYWORDS)

            if not is_start_of_report:
                current_sentence_index += 1
                continue

            segment_start_char = start_sentence_obj.start_char
            current_segment_base_sentences_obj = []
            road_found_in_window = False
            road_sentence_absolute_idx = -1

            for i_search_offset in range(self.MAX_SENTENCES_AFTER_START_FOR_ROAD + 1):
                search_idx = current_sentence_index + i_search_offset
                if search_idx >= len(sentences):
                    break
                sentence_to_check_obj = sentences[search_idx]
                if not current_segment_base_sentences_obj or sentence_to_check_obj != current_segment_base_sentences_obj[-1]:
                    current_segment_base_sentences_obj.append(sentence_to_check_obj)

                matches_in_sentence = self.matcher(sentence_to_check_obj)
                if any(self.nlp_vocab.strings[m_id] == "ROAD" for m_id, _, _ in matches_in_sentence):
                    road_found_in_window = True
                    road_sentence_absolute_idx = search_idx
                    break

            if not road_found_in_window:
                current_sentence_index += 1
                continue

            final_report_sentences_obj = list(current_segment_base_sentences_obj)
            consecutive_irrelevant_count = 0
            idx_for_extension = road_sentence_absolute_idx + 1

            while idx_for_extension < len(sentences):
                next_sentence_obj = sentences[idx_for_extension]
                next_sentence_text_lower = next_sentence_obj.text.lower()
                is_relevant_continuation = False

                if any(end_phrase in next_sentence_text_lower for end_phrase in self.END_SIGNAL_PHRASES):
                    break

                matches_in_next_sentence = self.matcher(next_sentence_obj)
                if any(self.nlp_vocab.strings[m_id] == "ROAD" for m_id, _, _ in matches_in_next_sentence):
                    is_relevant_continuation = True
                if not is_relevant_continuation:
                    if any(re.search(r'\b' + re.escape(rel_kw) + r'\b', next_sentence_text_lower) for rel_kw in self.RELEVANT_TRAFFIC_KEYWORDS):
                        is_relevant_continuation = True

                if not is_relevant_continuation and len(next_sentence_obj) <= 7 and \
                   (any(tok.pos_ == "PROPN" for tok in next_sentence_obj) or \
                    any(tok.is_digit or tok.like_num for tok in next_sentence_obj)):
                    is_relevant_continuation = True

                if is_relevant_continuation:
                    final_report_sentences_obj.append(next_sentence_obj)
                    consecutive_irrelevant_count = 0
                else:
                    consecutive_irrelevant_count += 1
                    if consecutive_irrelevant_count >= self.MAX_CONSECUTIVE_IRRELEVANT_SENTENCES_TO_END:
                        break
                idx_for_extension += 1

            german_report_sentences_texts = []
            for s_obj in final_report_sentences_obj:
                s_text = s_obj.text.strip()
                if not s_text:
                    continue
                if is_sentence_ignorable(s_text):
                    continue
                try:
                    lang = detect(s_text)
                    if lang == 'de':
                        german_report_sentences_texts.append(s_text)
                except LangDetectException:
                    if len(s_text.split()) <= 3 and (any(char.isdigit() for char in s_text) or re.search(r'\b[ABab]\d', s_text)):
                        german_report_sentences_texts.append(s_text)

            if german_report_sentences_texts:
                detected_reports.append({
                    "sentences_text": german_report_sentences_texts,
                    "start_char": segment_start_char,
                    "end_char": final_report_sentences_obj[-1].end_char
                })
            current_sentence_index = idx_for_extension
        return detected_reports