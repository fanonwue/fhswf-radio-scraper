# Transkript Analyse

Dieses Modul ist für die Analyse von transkribierten Audioinhalten zuständig. Es verwendet das `spaCy` Framework für Natural Language Processing (NLP), um verschiedene Arten von Segmenten in den Transkripten zu identifizieren und zu extrahieren.

## Funktionsweise

Das Hauptskript [`analyzor.py`](src/analyze/analyzor.py) führt die folgenden Schritte aus:

1.  **Laden des NLP-Modells**: Es wird versucht, das `de_core_news_lg` Modell von spaCy zu laden. Falls nicht vorhanden, wird eine Installationsanweisung ausgegeben.
2.  **Initialisierung des Prozessors**: Ein [`TranscriptProcessor`](src/analyze/core/transcript_processor.py) wird instanziiert.
3.  **Registrierung von Extraktoren**: Spezialisierte Extraktoren für verschiedene Inhaltstypen werden registriert:
    *   [`NewsSegmentExtractor`](src/analyze/extractors/news_extractor.py): Identifiziert Nachrichtenblöcke.
    *   [`TrafficSegmentExtractor`](src/analyze/extractors/traffic_extractor.py): Identifiziert Verkehrsmeldungen.
    *   [`WeatherSegmentExtractor`](src/analyze/extractors/weather_extractor.py): Identifiziert Wetterberichte.
    *   [`ConversationSegmentExtractor`](src/analyze/extractors/conversation_extractor.py): Identifiziert Gesprächssegmente.
4.  **Verarbeitung von Transkriptdateien**: Das Skript durchsucht ein angegebenes Verzeichnis nach `.txt`-Dateien (Transkripte).
5.  **Analyse und Speicherung**: Jede Transkriptdatei wird vom `TranscriptProcessor` verarbeitet. Die Ergebnisse der Extraktoren werden in einem Ausgabeordner gespeichert.

## Verwendung

Das Skript [`analyzor.py`](src/analyze/analyzor.py) kann direkt ausgeführt werden. Standardmäßig werden Transkripte aus `data/swr3/transkriptionen` gelesen und die Analyseergebnisse in `data/swr3/transkript_analysen` gespeichert. Diese Pfade können im Skript angepasst werden.

**Wichtiger Hinweis:** Die aktuellen Extraktoren und deren Konfigurationen wurden primär mit Transkripten des Senders SWR3 entwickelt und getestet. Für die Analyse von Transkripten anderer Radiosender sind möglicherweise Anpassungen an den Extraktoren (z.B. Schlüsselwörter, Muster) oder die Entwicklung neuer Extraktoren erforderlich, um optimale Ergebnisse zu erzielen.

Stellen Sie sicher, dass das `spaCy` Modell `de_core_news_lg` installiert ist:
```bash
python -m spacy download de_core_news_lg
```

## Tests

Die Funktionalität des Analysemoduls wird durch Integrationstests in der Datei [`tests/test_analyzer_integration.py`](tests/test_analyzer_integration.py) überprüft. Diese Tests stellen sicher, dass die Verarbeitung von Beispieltranskripten die erwarteten JSON-Ausgaben erzeugt.

Um die Tests auszuführen, navigieren Sie in das Hauptverzeichnis des Projekts und führen Sie folgenden Befehl aus:
```bash
python -m unittest tests/test_analyzer_integration.py
```
Oder, um alle Tests im `tests` Verzeichnis zu entdecken und auszuführen:
```bash
python -m unittest discover tests
```