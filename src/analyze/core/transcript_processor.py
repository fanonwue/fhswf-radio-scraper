import os
import json
import re
from datetime import datetime, timedelta
from .time_extractor import TimeExtractor
from ..extractors.base_extractor import AbstractSegmentExtractor

class TranscriptProcessor:
    """
    Verarbeitet Transkriptdateien, extrahiert Informationen und speichert Analysen.
    """
    def __init__(self, nlp_model):
        if not nlp_model:
            raise ValueError("Ein spaCy NLP-Modell wird benötigt.")
        self.nlp_model = nlp_model
        self.time_extractor = TimeExtractor()
        self.segment_extractors = []

    def register_extractor(self, extractor: AbstractSegmentExtractor):
        """
        Registriert einen Segment-Extractor.
        """
        self.segment_extractors.append(extractor)

    def _parse_filename_timestamps(self, filename_str):
        match = re.match(r'^.*_(\d{8})_(\d{6})_(\d{8})_(\d{6})\.txt$', filename_str)
        if match:
            start_date_str, start_time_str, end_date_str, end_time_str = match.groups()
            try:
                start_dt = datetime.strptime(f"{start_date_str}{start_time_str}", "%Y%m%d%H%M%S")
                end_dt   = datetime.strptime(f"{end_date_str}{end_time_str}", "%Y%m%d%H%M%S")
                return start_dt, end_dt
            except ValueError:
                return None, None
        return None, None

    def process_file(self, filepath: str, output_dir: str):
        filename_base = os.path.basename(filepath)
        print(f"Analysiere Datei: {filename_base}...")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f"Fehler beim Lesen der Datei {filename_base}: {e}")
            return

        if not text.strip():
            print(f"Datei {filename_base} ist leer. Übersprungen.")
            return

        doc = self.nlp_model(text)
        recording_start_dt, recording_end_dt = self._parse_filename_timestamps(filename_base)

        all_doc_time_mentions = []
        if recording_start_dt:
            all_doc_time_mentions = self.time_extractor.extract_time_mentions_from_doc(
                doc, recording_start_dt.date()
            )

        result_data = {
            "filename": filename_base,
            "recording_start_timestamp_iso": recording_start_dt.isoformat() if recording_start_dt else None,
            "recording_end_timestamp_iso":   recording_end_dt.isoformat()   if recording_end_dt else None,
            "explicit_time_mentions_in_doc": [
                (offset, dt.strftime("%Y-%m-%d %H:%M:%S"))
                for offset, dt in all_doc_time_mentions
            ],
        }

        total_text_length = len(text)

        for extractor in self.segment_extractors:
            extracted_segments_raw = extractor.extract_segments(doc)
            processed_segments = []
            for segment_raw in extracted_segments_raw:
                segment_sentences_texts = segment_raw["sentences_text"]
                segment_start_char = segment_raw["start_char"]
                segment_length = sum(len(s) for s in segment_sentences_texts)

                segment_mentions = [
                    (offset, dt) for offset, dt in all_doc_time_mentions
                    if segment_start_char <= offset < segment_start_char + segment_length
                ]

                if segment_mentions:
                    dt_in_seg = segment_mentions[-1][1]
                    estimated_time_str = dt_in_seg.strftime("%Y-%m-%d %H:%M:%S")

                elif recording_start_dt and recording_end_dt and total_text_length > 0:
                    relative_position = segment_start_char / total_text_length
                    duration_secs = (recording_end_dt - recording_start_dt).total_seconds()
                    if duration_secs < 0:
                        duration_secs = 0
                    offset_secs = duration_secs * relative_position
                    interpolated_dt = recording_start_dt + timedelta(seconds=offset_secs)
                    estimated_time_str = interpolated_dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    estimated_time_str = None

                processed_segments.append({
                    "sentences": segment_sentences_texts,
                    "estimated_report_time": estimated_time_str,
                    "segment_start_char_offset": segment_start_char
                })

            result_data[extractor.get_name()] = processed_segments

        os.makedirs(output_dir, exist_ok=True)
        output_filename_json = os.path.splitext(filename_base)[0] + "_analysis.json"
        output_path = os.path.join(output_dir, output_filename_json)

        try:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                json.dump(result_data, outfile, ensure_ascii=False, indent=4)
            print(f"Analyse für {filename_base} gespeichert in {output_path}")
        except Exception as e:
            print(f"Fehler beim Schreiben der Ergebnisdatei für {filename_base}: {e}")
