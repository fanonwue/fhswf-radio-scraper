from __future__ import annotations

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=False)

import json
import os
from typing import Any, Optional
from openai import OpenAI

DEFAULT_MODEL = "gpt-5-nano"

_client_singleton: Optional[OpenAI] = None
def _client() -> OpenAI:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client_singleton



def responses_json(model: str, system: str, user: str, json_schema: dict, seed=None):
    client = _client()

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    params = {
        "model": model,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }

    if not ("gpt-5-nano" in (model or "").lower()):
        params["temperature"] = 0.2

    try:
        resp = client.chat.completions.create(**params)
    except Exception as e:
        msg = str(e).lower()
        if "temperature" in msg and "unsupported" in msg:
            params.pop("temperature", None)
            resp = client.chat.completions.create(**params)
        else:
            raise

    text = resp.choices[0].message.content
    return json.loads(text)
