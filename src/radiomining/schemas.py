from __future__ import annotations

HOUR_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "sender": {"type": "string"},
        "hour_start": {"type": "string"},
        "hour_end": {"type": "string"},
        "show_title": {"type": ["string", "null"]},
        "hosts": {"type": "array", "items": {"type": "string"}},
        "main_topics": {"type": "array", "items": {"type": "string"}},
        "news_topics": {"type": "array", "items": {"type": "string"}},
        "weather_present": {"type": "boolean"},
        "traffic_present": {"type": "boolean"},
        "ads_present": {"type": "boolean"},
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "title": {"type": ["string", "null"]},
                    "topic": {"type": ["string", "null"]},
                    "topics": {"type": "array", "items": {"type": "string"}},
                    "start": {"type": ["string", "null"]},
                    "end": {"type": ["string", "null"]},
                    "speakers": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": ["string", "null"]},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "story_key": {"type": ["string", "null"]},
                    "story_id": {"type": ["string", "null"]},
                },
            },
        },
    },
    "required": [
        "sender",
        "hour_start",
        "hour_end",
        "hosts",
        "main_topics",
        "news_topics",
        "weather_present",
        "traffic_present",
        "ads_present",
        "segments",
    ],
}
