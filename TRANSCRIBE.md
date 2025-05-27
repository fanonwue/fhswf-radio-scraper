# Audio Miner Batch Runner

Dieses Repository enthält ein Python-Skript zur Stapelverarbeitung von `audio_miner`, um Audios von verschiedenen Hörfunk-Sendern nacheinander zu transkribieren.

## Übersicht

Der Workflow besteht aus zwei Schritten:

1. **Audio-Sammlung:** Mit `audio_miner` nur das Audio der gewünschten Sender über einen bestimmten Zeitraum sammeln (nicht Teil dieses Projektes).
2. **Transkription:** Mit dem Batch-Skript alle gesammelten Audiodateien bis zu definierten Endzeiten transkribieren.

## Voraussetzungen

- Ubuntu (oder ein anderes Linux mit Bash)
- Python 3.6+
- `audio_miner` im PATH
- `time` im PATH
- Internet-Zugang und gültiger Hugging Face Token für Whisper


## Batch-Transkription

Verwende das Python-Skript `audio_miner_batch.py`, um für mehrere Sender gleichzeitig die Transkription durchzuführen. Dabei wird das Argument `--transcribe-only` genutzt, sodass nur schon vorhandene Audiodateien transkribiert werden.

### Aufruf

```bash
python src/analyze/audio_miner_batch.py \
  --base-dir /mnt/audio_mining/ \
  --token <Replace with Token> \
  --sender swr1 --end-time 20250527_073501 \
  --sender swr3 --end-time 20250527_073458 \
  --sender wdr2 --end-time 20250527_073439
```

- `--base-dir`  : Pfad zum Basisverzeichnis, in dem die Audiodateien liegen.
- `--token`     : Dein Hugging Face API-Token (ersetze `REPLACE_ME`).
- `--sender`    : Kurzbezeichnung des Senders (z. B. `swr1`, `wdr2`). Jeder Sender darf nur einmal vorkommen.
- `--end-time`  : Endzeitpunkt der Sammlung/Transkription im Format `YYYYMMDD_HHMMSS`. Die Anzahl der `--sender` und `--end-time`-Parameter muss gleich sein.

Das Skript prüft vorab, ob `time` und `audio_miner` verfügbar sind, validiert die Parameter und führt dann für jede Sender-/Endzeit-Kombination den Befehl aus.

## Hinweise

- Stelle sicher, dass zu jedem Sender bereits Audiodaten im angegebenen `--base-dir` liegen bis zur jeweiligen `--end-time`.
- Bei Fehlern in einem Durchlauf bricht das Skript ab und gibt den entsprechenden Fehlercode zurück.
- Passe bei Bedarf im Skript selbst das Whisper-Modell an (Standard: `TURBO`).