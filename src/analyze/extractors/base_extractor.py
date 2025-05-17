from abc import ABC, abstractmethod
import spacy
import datetime

class AbstractSegmentExtractor(ABC):
    """
    Abstrakte Basisklasse für Segment-Extraktoren.
    Definiert die Schnittstelle für das Extrahieren von Segmenten
    (z.B. Nachrichten, Wetter, Verkehr) aus einem spaCy Doc.
    """

    @abstractmethod
    def get_name(self) -> str:
        """
        Gibt den Namen des Segmenttyps zurück, den dieser Extraktor liefert.
        z.B. "news_segments", "weather_report_segments".
        """
        pass

    @abstractmethod
    def extract_segments(self, doc: spacy.tokens.Doc, estimated_time: datetime.datetime = None):
        """
        Extrahiert relevante Segmente aus dem gegebenen spaCy-Dokument.

        Args:
            doc (spacy.tokens.Doc): Das zu analysierende spaCy-Dokument.
            estimated_time (datetime.datetime, optional): Die geschätzte Startzeit
                des Dokuments oder des relevanten Audio-Abschnitts.
                Kann von Extraktoren genutzt werden, um zeitabhängige
                Muster zu erkennen (z.B. Nachrichten zur vollen Stunde).
                Standardmäßig None.

        Returns:
            list: Eine Liste von Dictionaries, wobei jedes Dictionary ein Segment repräsentiert.
                  Jedes Segment-Dictionary sollte mindestens "sentences_text" (Liste von Strings)
                  und "start_char" (Integer) enthalten.
                  Beispiel: [{"sentences_text": ["Satz 1.", "Satz 2."], "start_char": 0}]
        """
        pass