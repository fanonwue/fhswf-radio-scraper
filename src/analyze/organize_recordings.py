import argparse
from pathlib import Path
import shutil
from datetime import datetime

def parse_datetime_from_filename(filename: str):
    try:
        parts = filename.split("_")
        return datetime.strptime(parts[1] + "_" + parts[2], "%Y%m%d_%H%M%S")
    except Exception:
        return None

def is_in_range(file_time: datetime, start: datetime, end: datetime):
    if start and file_time < start:
        return False
    if end and file_time > end:
        return False
    return True

def organize_files(source_dir: Path, target_dir: Path, start: datetime = None, end: datetime = None):
    for file in source_dir.glob("*.txt"):
        file_time = parse_datetime_from_filename(file.name)
        if not file_time:
            print(f"⚠️  Ungültiger Dateiname: {file.name}")
            continue
        if not is_in_range(file_time, start, end):
            continue

        # Struktur: target/YYYY/MM/DD/HH/
        year = f"{file_time.year:04d}"
        month = f"{file_time.month:02d}"
        day = f"{file_time.day:02d}"
        hour = f"{file_time.hour:02d}"

        target_path = target_dir / year / month / f"{year}-{month}-{day}" / hour
        target_path.mkdir(parents=True, exist_ok=True)

        dest_file = target_path / file.name
        if dest_file.exists():
            print(f"⚠️  Datei schon vorhanden: {dest_file}")
        else:
            shutil.copy2(file, dest_file)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Quellordner mit .txt-Dateien")
    parser.add_argument("target", help="Zielordner für organisierte Dateien")
    parser.add_argument("--start", type=str, help="Startdatum (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="Enddatum (YYYY-MM-DD)")

    args = parser.parse_args()

    source = Path(args.source)
    target = Path(args.target)

    start_date = datetime.strptime(args.start, "%Y-%m-%d") if args.start else None
    end_date = datetime.strptime(args.end, "%Y-%m-%d") if args.end else None
    if end_date:
        end_date = end_date.replace(hour=23, minute=59, second=59)

    organize_files(source, target, start=start_date, end=end_date)

if __name__ == "__main__":
    main()
