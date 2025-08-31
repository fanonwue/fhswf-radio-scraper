from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv(override=True)

@dataclass
class Settings:
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    base_url: str | None = os.getenv("OPENAI_BASE_URL") or None
    timezone: str = os.getenv("TZ", "Europe/Berlin")

SETTINGS = Settings()
