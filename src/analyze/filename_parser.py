from datetime import datetime
from pathlib import Path

class FilenameParser:
    @staticmethod
    def parse_datetime(s: str) -> datetime:
        return datetime.strptime(s, "%Y%m%d_%H%M%S")

    @staticmethod
    def parse_filename(filepath: Path):
        stem = filepath.stem
        parts = stem.split("_")
        if len(parts) < 5:
            return None
        try:
            sender = parts[0]
            start = FilenameParser.parse_datetime(parts[1] + "_" + parts[2])
            end   = FilenameParser.parse_datetime(parts[3] + "_" + parts[4])
            return sender, start, end
        except ValueError:
            return None
