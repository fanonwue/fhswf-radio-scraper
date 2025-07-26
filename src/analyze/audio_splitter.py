import os
import subprocess
import argparse
from datetime import datetime, timedelta

def parse_filename(filepath):
    """
    Parst den Dateinamen, um Präfix, Start- und End-Datetime-Objekte sowie die Erweiterung zu extrahieren.
    Dateiname-Schema: PREFIX_YYYYMMDD_HHMMSS_YYYYMMDD_HHMMSS.EXT
    """
    base_name = os.path.basename(filepath)
    name_part, ext = os.path.splitext(base_name)
    parts = name_part.split('_')

    if len(parts) != 5:
        raise ValueError(
            "Ungültiges Dateinamenformat. Erwartet: PREFIX_YYYYMMDD_HHMMSS_YYYYMMDD_HHMMSS.ext"
        )

    prefix = parts[0]
    try:
        start_dt_str = f"{parts[1]}_{parts[2]}"
        end_dt_str = f"{parts[3]}_{parts[4]}"
        start_dt = datetime.strptime(start_dt_str, "%Y%m%d_%H%M%S")
        end_dt = datetime.strptime(end_dt_str, "%Y%m%d_%H%M%S")
    except ValueError as e:
        raise ValueError(f"Ungültiges Datums-/Zeitformat im Dateinamen: {e}")

    if start_dt >= end_dt:
        raise ValueError("Startzeit im Dateinamen muss vor der Endzeit liegen.")

    return prefix, start_dt, end_dt, ext

def format_datetime_for_filename(dt_obj):
    """Formatiert ein Datetime-Objekt in den String YYYYMMDD_HHMMSS."""
    return dt_obj.strftime("%Y%m%d_%H%M%S")

def split_audio(input_filepath, segment_duration_sec, output_dir="output_segments"):
    """
    Teilt die Audiodatei in Segmente auf.
    """
    if not os.path.isfile(input_filepath):
        print(f"Fehler: Eingabedatei '{input_filepath}' nicht gefunden.")
        return

    try:
        prefix, original_start_dt, original_end_dt, original_ext = parse_filename(input_filepath)
    except ValueError as e:
        print(f"Fehler beim Parsen des Dateinamens '{input_filepath}': {e}")
        return

    os.makedirs(output_dir, exist_ok=True)
    print(f"Ausgabeverzeichnis: '{os.path.abspath(output_dir)}'")

    total_file_duration_seconds = (original_end_dt - original_start_dt).total_seconds()

    if total_file_duration_seconds <= 0:
        print("Fehler: Die Gesamtdauer der Datei gemäß Dateinamen ist null oder negativ.")
        return

    if segment_duration_sec <= 0:
        print("Fehler: Die Segmentdauer muss positiv sein.")
        return

    if segment_duration_sec >= total_file_duration_seconds:
        print(
            f"Fehler: Die Segmentdauer ({segment_duration_sec}s) muss kleiner sein als die "
            f"Gesamtdauer der Datei ({total_file_duration_seconds}s)."
        )
        return

    current_segment_start_dt = original_start_dt
    segment_counter = 0

    print(f"\nStarte Aufteilung für Datei: {os.path.basename(input_filepath)}")
    print(f"Originalzeitraum: {format_datetime_for_filename(original_start_dt)} bis {format_datetime_for_filename(original_end_dt)}")
    print(f"Gewünschte Segmentdauer: {segment_duration_sec} Sekunden")
    print("-" * 30)

    while current_segment_start_dt < original_end_dt:
        segment_counter += 1
        
        potential_segment_end_dt = current_segment_start_dt + timedelta(seconds=segment_duration_sec)
        actual_segment_end_dt = min(potential_segment_end_dt, original_end_dt)

        if (actual_segment_end_dt - current_segment_start_dt).total_seconds() <= 0:
            if current_segment_start_dt < original_end_dt :
                 print(f"Warnung: Überspringe Segment {segment_counter}, da die Dauer null oder negativ wäre.")
            break 

        output_filename_start_str = format_datetime_for_filename(current_segment_start_dt)
        output_filename_end_str = format_datetime_for_filename(actual_segment_end_dt)
        
        output_filename = f"{prefix}_{output_filename_start_str}_{output_filename_end_str}{original_ext}"
        output_filepath = os.path.join(output_dir, output_filename)

        ffmpeg_ss_offset_seconds = (current_segment_start_dt - original_start_dt).total_seconds()

        ffmpeg_t_duration_seconds = (actual_segment_end_dt - current_segment_start_dt).total_seconds()

        if ffmpeg_t_duration_seconds <= 0:
            print(f"Warnung: Überspringe Segment {segment_counter} für Startzeit {current_segment_start_dt}, da Dauer <= 0.")
            current_segment_start_dt = actual_segment_end_dt
            continue

        ffmpeg_cmd = [
            "ffmpeg",
            "-i", input_filepath,
            "-ss", str(ffmpeg_ss_offset_seconds),
            "-t", str(ffmpeg_t_duration_seconds),
            "-c", "copy",
            "-y",
            output_filepath
        ]

        print(f"\nErstelle Segment {segment_counter}: {output_filename}")
        print(f"  Zeitraum des Segments: {output_filename_start_str} bis {output_filename_end_str}")
        print(f"  Dauer des Segments: {timedelta(seconds=ffmpeg_t_duration_seconds)}")

        try:
            result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True, encoding='utf-8')
            print(f"  Erfolgreich erstellt: {output_filepath}")
        except subprocess.CalledProcessError as e:
            print(f"Fehler beim Erstellen des Segments {output_filename}:")
            print(f"  Befehl: {' '.join(e.cmd)}")
            print(f"  Fehlercode: {e.returncode}")
            if e.stdout:
                print(f"  FFmpeg stdout:\n{e.stdout}")
            if e.stderr:
                print(f"  FFmpeg stderr:\n{e.stderr}")
        current_segment_start_dt = actual_segment_end_dt

    print("-" * 30)
    print(f"Aufteilung abgeschlossen. {segment_counter-1 if segment_counter > 0 else 0} Segmente erstellt.")


def check_ffmpeg_installed():
    """Überprüft, ob ffmpeg installiert und im Pfad ist."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, text=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

if __name__ == "__main__":
    if not check_ffmpeg_installed():
        print("Fehler: ffmpeg nicht gefunden. Bitte stellen Sie sicher, dass ffmpeg installiert und im Systempfad ist.")
        exit(1)

    parser = argparse.ArgumentParser(
        description="Teilt eine Audiodatei basierend auf Zeitstempeln im Dateinamen auf.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_file",
        help="Eingabedatei im Format PREFIX_YYYYMMDD_HHMMSS_YYYYMMDD_HHMMSS.mp3\n"
             "Beispiel: swr3_20250521_081934_20250521_082435.mp3"
    )
    parser.add_argument(
        "segment_duration",
        type=int,
        help="Gewünschte Dauer jedes Segments in Sekunden."
    )
    parser.add_argument(
        "--output_dir",
        default="output_segments",
        help="Verzeichnis zum Speichern der aufgeteilten Segmente (Standard: output_segments)."
    )

    args = parser.parse_args()

    split_audio(args.input_file, args.segment_duration, args.output_dir)