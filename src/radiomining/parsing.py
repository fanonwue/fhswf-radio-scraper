from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

FILENAME_RE = re.compile(r'^(?P<sender>swr1|swr3|wdr2)_(?P<sd>\d{8})_(?P<st>\d{6})_(?P<ed>\d{8})_(?P<et>\d{6})\.txt$')
LINE_RE = re.compile(r'^\[(?P<speaker>[^|]+)\s*\|\s*(?P<start>[\d.]+)-(?:\s*)?(?P<end>[\d.]+)\]\s*(?P<text>.*)$')

@dataclass
class FileWindow:
    sender: str
    start_dt: datetime
    end_dt: datetime
    tz: str = "Europe/Berlin"

def parse_filename(filename: str, tz: str = "Europe/Berlin") -> FileWindow:
    import os
    name = os.path.basename(filename)
    m = FILENAME_RE.match(name)
    if not m:
        raise ValueError(f"Unerwartetes Dateinamensmuster: {name}")
    sender = m.group("sender")
    sd, st, ed, et = m.group("sd"), m.group("st"), m.group("ed"), m.group("et")
    def to_dt(d, t):
        return datetime.strptime(d + t, "%Y%m%d%H%M%S").replace(tzinfo=ZoneInfo(tz))
    return FileWindow(sender=sender, start_dt=to_dt(sd, st), end_dt=to_dt(ed, et), tz=tz)

def iter_lines_with_abs_times(text: str, fw: FileWindow):
    for line in text.splitlines():
        m = LINE_RE.match(line.strip())
        if not m:
            continue
        start_s = float(m.group("start"))
        end_s = float(m.group("end"))
        abs_start = fw.start_dt + timedelta(seconds=start_s)
        abs_end = fw.start_dt + timedelta(seconds=end_s)
        yield {
            "speaker": m.group("speaker").strip(),
            "rel_start_s": start_s,
            "rel_end_s": end_s,
            "abs_start": abs_start,
            "abs_end": abs_end,
            "text": m.group("text").strip(),
            "sender": fw.sender,
            "file_start": fw.start_dt,
            "file_end": fw.end_dt,
        }
