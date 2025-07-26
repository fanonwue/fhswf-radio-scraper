#!/usr/bin/env python3
"""
Batch runner for audio_miner: prüft Verfügbarkeit von Befehlen und führt mehrere Durchläufe mit verschiedenen Sendern und Endzeiten durch.
"""
import shutil
import sys
import argparse
import subprocess

def check_command(cmd):
    """Prüft, ob ein Befehl im PATH verfügbar ist."""
    if shutil.which(cmd) is None:
        print(f"Fehler: '{cmd}' nicht gefunden. Bitte installieren Sie es oder prüfen Sie Ihren PATH.", file=sys.stderr)
        sys.exit(1)


def main():
    check_command('time')
    check_command('audio_miner')

    parser = argparse.ArgumentParser(
        description='Batch-Ablauf von audio_miner für mehrere Sender/Endzeiten.'
    )
    parser.add_argument(
        '--base-dir',
        required=True,
        help='Basisverzeichnis für audio_miner'
    )
    parser.add_argument(
        '--token',
        required=True,
        help='Zugriffstoken für Whisper-API'
    )
    parser.add_argument(
        '--sender',
        action='append',
        dest='senders',
        required=True,
        help='Name des Senders (mehrfach erlaubt)'
    )
    parser.add_argument(
        '--end-time',
        action='append',
        dest='end_times',
        required=True,
        help='Endzeitpunkt im Format YYYYMMDD_HHMMSS (mehrfach erlaubt)'
    )
    args = parser.parse_args()

    if len(args.senders) != len(args.end_times):
        print("Fehler: Die Anzahl der --sender und --end-time Parameter muss übereinstimmen.", file=sys.stderr)
        sys.exit(1)
    if len(set(args.senders)) != len(args.senders):
        print("Fehler: Jeder Sender darf nur einmal vorkommen.", file=sys.stderr)
        sys.exit(1)

    whisper_model = 'TURBO'

    for sender, end_time in zip(args.senders, args.end_times):
        cmd = [
            'time',
            'audio_miner',
            '--transcribe-only',
            '--end-time', end_time,
            '--sender', sender,
            '--base-dir', args.base_dir,
            '--whisper-model', whisper_model,
            '--token', args.token
        ]
        print(f"Starte: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Fehler beim Ausführen von audio_miner für Sender {sender}: {e}", file=sys.stderr)
            sys.exit(e.returncode)

if __name__ == '__main__':
    main()
