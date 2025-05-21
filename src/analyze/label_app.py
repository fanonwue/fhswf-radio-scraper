import streamlit as st
import re
from pathlib import Path
import datetime
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Transkript-Tagging mit CLI-Parametern")
    parser.add_argument(
        "--input_folder", type=str,
        help="Pfad zum Quellordner (z.B. output/swr1/transkriptionen)"
    )
    parser.add_argument(
        "--output_folder", type=str,
        help="Pfad zum Zielordner (z.B. output/swr1/labeled)"
    )
    parser.add_argument(
        "--start_date", type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d").date(),
        help="Startdatum im Format YYYY-MM-DD"
    )
    parser.add_argument(
        "--end_date", type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d").date(),
        help="Enddatum im Format YYYY-MM-DD"
    )
    parser.add_argument(
        "--start_time", type=lambda s: datetime.datetime.strptime(s, "%H:%M").time(),
        help="Startzeit im Format HH:MM (default 00:00)"
    )
    parser.add_argument(
        "--end_time", type=lambda s: datetime.datetime.strptime(s, "%H:%M").time(),
        help="Endzeit im Format HH:MM (default 23:59)"
    )
    args, _ = parser.parse_known_args()
    return args

args = parse_args()

st.set_page_config(page_title="Transkript-Tagging", layout="wide")
st.title("Transkript-Tagging")

# Eingabe- und Ausgabeordner
if args.input_folder:
    input_folder = Path(args.input_folder)
else:
    input_folder = Path(st.sidebar.text_input("Quellordner", "output/swr1/transkriptionen"))

if args.output_folder:
    output_folder = Path(args.output_folder)
else:
    output_folder = Path(st.sidebar.text_input("Zielordner", "output/swr1/labeled"))

output_folder.mkdir(parents=True, exist_ok=True)

# Zeitfilter-Defaults aus Session-State oder CLI
now = datetime.datetime.now()
if 'start_date' not in st.session_state:
    st.session_state.start_date = args.start_date or now.date()
if 'start_time' not in st.session_state:
    st.session_state.start_time = args.start_time or datetime.time(0, 0)
if 'end_date' not in st.session_state:
    st.session_state.end_date = args.end_date or now.date()
if 'end_time' not in st.session_state:
    st.session_state.end_time = args.end_time or datetime.time(23, 59)

# Sidebar-Konfiguration
st.sidebar.header("Einstellungen")
input_folder = Path(st.sidebar.text_input("Quellordner", input_folder))
output_folder = Path(st.sidebar.text_input("Zielordner", output_folder))
start_date = st.sidebar.date_input("Startdatum", value=st.session_state.start_date, key="start_date")
start_time = st.sidebar.time_input("Startzeit", value=st.session_state.start_time, key="start_time")
end_date   = st.sidebar.date_input("Enddatum",   value=st.session_state.end_date,   key="end_date")
end_time   = st.sidebar.time_input("Endzeit",    value=st.session_state.end_time,   key="end_time")

# Kombiniere zu datetime und Validierung
start_dt = datetime.datetime.combine(start_date, start_time)
end_dt = datetime.datetime.combine(end_date, end_time)
if start_dt > end_dt:
    st.sidebar.error("Startzeitpunkt muss vor Endzeitpunkt liegen")

# Transkriptdateien filtern
all_files = sorted(input_folder.glob("*.txt"))
pattern_datetime = re.compile(r".*_(\d{8})_(\d{6})_(\d{8})_(\d{6})\.txt")
filtered_files = []
for f in all_files:
    m = pattern_datetime.match(f.name)
    if not m:
        continue
    sd, stime, ed, etime = m.groups()
    file_start = datetime.datetime.strptime(sd + stime, "%Y%m%d%H%M%S")
    file_end = datetime.datetime.strptime(ed + etime, "%Y%m%d%H%M%S")
    if file_start >= start_dt and file_end <= end_dt:
        filtered_files.append(f)
if not filtered_files:
    st.warning("Keine Dateien im gewählten Zeitintervall gefunden")
    st.stop()

# Datei-Navigation
if "file_idx" not in st.session_state:
    st.session_state.file_idx = 0
file_names = [f.name for f in filtered_files]
selected = st.sidebar.selectbox("Datei auswählen", file_names, index=st.session_state.file_idx)

if selected == file_names[st.session_state.file_idx]:
    idx = st.session_state.file_idx
else:
    idx = file_names.index(selected)
st.session_state.file_idx = idx
col_prev, col_next = st.sidebar.columns([1,1])
if col_prev.button("← Zurück"):
    st.session_state.file_idx = max(0, st.session_state.file_idx - 1)
if col_next.button("Vor →"):
    st.session_state.file_idx = min(len(filtered_files) - 1, st.session_state.file_idx + 1)

# Aktueller Dateikontext
file_idx = st.session_state.file_idx
file_name   = file_names[file_idx]
file_input  = input_folder / file_name
file_labeled = output_folder / file_name
file_path   = file_labeled if file_labeled.exists() else file_input

# Dateiinhalt anzeigen
with st.expander("Dateiinhalt anzeigen"):
    st.text_area("Inhalt", file_path.read_text(encoding="utf-8"), height=300)

# Tagging-Logik
pattern = re.compile(
    r"(\[SPEAKER_\d+ \| [\d\.]+-[\d\.]+)"
    r"(?: \| tag:([a-z_]+))?\] "
    r"(.+)"
)
orig_lines = file_input.read_text(encoding="utf-8").splitlines()

# Vorbefüllung: nur wenn labeled existiert
lines = orig_lines
tags  = {}
if file_labeled.exists():
    label_lines = file_labeled.read_text(encoding="utf-8").splitlines()
    for i, ln in enumerate(lines):
        if i < len(label_lines):
            m = pattern.match(label_lines[i])
        else:
            m = None
        existing = m.group(2) if m else None
        tags[i] = existing if existing in ["news","traffic","weather","moderation"] else "skip"
else:
    for i in range(len(lines)):
        tags[i] = "skip"

st.header(f"Tagging: {file_name}")
for i, ln in enumerate(lines):
    m = pattern.match(ln)
    if not m:
        st.text(ln)
        st.markdown("---")
        continue
    _, _, text = m.groups()
    options = ["skip","news","traffic","weather","moderation"]
    default_idx = options.index(tags[i])
    col1, col2 = st.columns([7,3], gap="small")
    col1.markdown(f"**Zeile {i+1}:** {text}")
    with col2:
        st.write("\n"*3)
        choice = st.selectbox("", options, index=default_idx, key=f"tag_{file_idx}_{i}")
    tags[i] = choice
    st.markdown("---")

# Speichern
if st.button("✏️ Änderungen speichern", key="save_bottom"):
    out_lines = []
    for i, ln in enumerate(lines):
        m = pattern.match(ln)
        if m:
            pr, _, tx = m.groups()
            tg = tags.get(i, "skip")
            out_lines.append(f"{pr} | tag:{tg}] {tx}")
        else:
            out_lines.append(ln)
    out_path = output_folder / file_name
    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    st.success(f"✅ Gespeichert nach {out_path}")
