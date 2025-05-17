import re
from datetime import datetime, time

class TimeExtractor:
    """
    Extrahiert Zeitinformationen aus einem Text.
    """
    def extract_time_mentions_from_doc(self, doc, base_date):
        """
        Extrahiert explizite Zeitnennungen (HH:MM oder HH.MM Uhr) aus dem Dokument.
        Gibt eine Liste von Tupeln zurück: (char_offset, datetime_obj), sortiert nach char_offset.
        """
        time_mentions = []
        pattern_time = re.compile(r"(\d{1,2})\s*[:.]\s*(\d{2})\s*(Uhr)?", re.IGNORECASE)

        for sent in doc.sents:
            for match in pattern_time.finditer(sent.text):
                try:
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        dt_object = datetime.combine(base_date, time(hour, minute))

                        time_mentions.append((sent.start_char + match.start(), dt_object))
                except ValueError:
                    continue

        time_mentions.sort(key=lambda x: x[0])

        unique_time_mentions = []
        if time_mentions:
            unique_time_mentions.append(time_mentions[0])
            for i in range(1, len(time_mentions)):
                prev_char, prev_dt = unique_time_mentions[-1]
                curr_char, curr_dt = time_mentions[i]

                if curr_dt == prev_dt and abs(curr_char - prev_char) < 5:
                    continue
                unique_time_mentions.append(time_mentions[i])
        return unique_time_mentions

    def get_refined_time_for_segment(self, segment_start_char, segment_sentences_texts, all_doc_time_mentions, max_char_offset_diff_for_prior=None):
        """
        Ermittelt eine präzisere Zeit für ein Segment.
        Gibt ein datetime-Objekt oder None zurück.
        max_char_offset_diff_for_prior: Maximaler Zeichenabstand, den eine vorherige Zeitnennung haben darf.
        """
        segment_text_length = sum(len(s_text) + 1 for s_text in segment_sentences_texts) - (1 if segment_sentences_texts else 0)
        segment_end_char_approx = segment_start_char + segment_text_length

        time_in_segment_dt = None
        for mention_char, mention_dt in all_doc_time_mentions:
            if segment_start_char <= mention_char < segment_end_char_approx:
                time_in_segment_dt = mention_dt
                break
        
        if time_in_segment_dt:
            return time_in_segment_dt

        latest_prior_dt_candidate = None
        latest_prior_char_offset_candidate = -1

        for mention_char, mention_dt in all_doc_time_mentions:
            if mention_char < segment_start_char:
                if mention_char > latest_prior_char_offset_candidate:
                    latest_prior_dt_candidate = mention_dt
                    latest_prior_char_offset_candidate = mention_char
            else:
                break
        
        if latest_prior_dt_candidate:
            if max_char_offset_diff_for_prior is not None and latest_prior_char_offset_candidate != -1:
                char_difference = segment_start_char - latest_prior_char_offset_candidate
                if char_difference <= max_char_offset_diff_for_prior:
                    return latest_prior_dt_candidate
                else:
                    return None
            else:
                return latest_prior_dt_candidate
        
        return None