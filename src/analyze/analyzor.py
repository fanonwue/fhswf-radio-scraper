import sys
import spacy
import os
import glob

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.analyze.core.transcript_processor import TranscriptProcessor
from src.analyze.extractors.traffic_extractor import TrafficSegmentExtractor
from src.analyze.extractors.weather_extractor import WeatherSegmentExtractor
from src.analyze.extractors.news_extractor import NewsSegmentExtractor
from src.analyze.extractors.conversation_extractor import ConversationSegmentExtractor

try:
    nlp_global = spacy.load("de_core_news_lg")
    print("spaCy Modell 'de_core_news_lg' erfolgreich geladen.")
except OSError:
    print("Fehler: spaCy Modell 'de_core_news_lg' nicht gefunden.")
    print("Bitte installieren Sie es mit: python -m spacy download de_core_news_lg")
    nlp_global = None

def run_analysis(input_transcript_dir: str, output_analysis_dir: str, nlp_model):
    """
    Führt die Transkriptanalyse für Dateien in input_transcript_dir durch
    und speichert die Ergebnisse in output_analysis_dir.
    """
    if not nlp_model:
        print("NLP Modell nicht verfügbar. Analyse kann nicht durchgeführt werden.")
        return False

    if not os.path.isdir(input_transcript_dir):
        print(f"Fehler: Transkriptverzeichnis '{input_transcript_dir}' nicht gefunden.")
        return False

    os.makedirs(output_analysis_dir, exist_ok=True)

    print(f"Suche nach Transkripten in: {input_transcript_dir}")
    print(f"Speichere Analysen in: {output_analysis_dir}")

    processor = TranscriptProcessor(nlp_model=nlp_model)

    # Extractor-Registrierung
    news_extractor = NewsSegmentExtractor(nlp_vocab=nlp_model.vocab)
    processor.register_extractor(news_extractor)
    traffic_extractor = TrafficSegmentExtractor(nlp_vocab=nlp_model.vocab)
    processor.register_extractor(traffic_extractor)
    weather_extractor = WeatherSegmentExtractor(nlp_vocab=nlp_model.vocab)
    processor.register_extractor(weather_extractor)
    conversation_extractor = ConversationSegmentExtractor(nlp_vocab=nlp_model.vocab)
    processor.register_extractor(conversation_extractor)

    transcript_files = glob.glob(os.path.join(input_transcript_dir, "*.txt"))
    if not transcript_files:
        print(f"Keine .txt Dateien in {input_transcript_dir} gefunden.")
    else:
        print(f"{len(transcript_files)} Transkriptdateien gefunden.")

    for filepath in transcript_files:
        processor.process_file(filepath, output_analysis_dir)
        print("-" * 30)
    
    print(f"Alle Transkripte aus '{input_transcript_dir}' verarbeitet.")
    return True


if __name__ == "__main__":
    if not nlp_global:
        print("Globales NLP Modell konnte nicht geladen werden. Abbruch des Skripts.")
        exit(1)

    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(current_script_dir))
    default_transcript_directory = os.path.join(base_dir, "data", "swr3", "transkriptionen")
    default_analysis_results_directory = os.path.join(base_dir, "data", "swr3", "transkript_analysen")

    success = run_analysis(
        input_transcript_dir=default_transcript_directory,
        output_analysis_dir=default_analysis_results_directory,
        nlp_model=nlp_global
    )

    if success:
        print("Analyzeskript erfolgreich abgeschlossen.")
    else:
        print("Analyzeskript mit Fehlern abgeschlossen.")
        exit(1)