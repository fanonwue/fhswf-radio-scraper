from __future__ import annotations

SYSTEM_PROMPT = """Du bist ein Analyst für deutsche Radiosender-Transkripte.
Du lieferst strukturierte, kurze, präzise Zusammenfassungen pro Stunde."""

def build_user_prompt(sender: str, hour_iso: str, hour_end_iso: str, text: str) -> str:
    return f"""
Analysiere die folgende Stunde eines Radiosenders. Die Zeilen sind bereits mit **absoluten Uhrzeiten** versehen.

Metadaten:
- Sender: {sender}
- Stunde: {hour_iso} - {hour_end_iso}

Aufgabe:
- Erzeuge eine JSON-Struktur mit:
  - sender (string)
  - hour_start (string, ISO)
  - hour_end (string, ISO)
  - show_title (string|null)
  - hosts (string[])
  - main_topics (string[])
  - news_topics (string[])
  - weather_present (boolean)
  - traffic_present (boolean)
  - ads_present (boolean)
  - segments (array von Objekten)
- Jedes Segment-Objekt:
  - {{ type, title, topic, topics, start, end, speakers, summary, tags?, story_key?, story_id? }}
  - type: z.B. "moderation" | "news" | "weather" | "traffic" | "ad" | "music" | "sports" | "other"
  - tags: kurze Schlagworte (z.B. ["Wetter", "Stau", "Politik/Bundestag"])
  - story_key/story_id: nur setzen, wenn es sich um eine klar identifizierbare Meldung/Serie handelt.
- Halte dich an präzise, faktennahe Formulierungen. Keine Halluzinationen. Lass Felder weg, wenn unklar UND nicht gefordert.

Transkript (mit absoluten Zeiten):
{text}
""".strip()
