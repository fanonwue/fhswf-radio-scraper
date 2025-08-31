from __future__ import annotations
import os, typer
from zoneinfo import ZoneInfo
import pandas as pd
from typing import List, Optional
from rich import print
from .preprocess import preprocess_files, bucket_by_hour_sender, write_prompt_jsonl_for_buckets, discover_files
from .summarize import summarize_buckets
import typer
import pandas as pd
from typing import Optional
from radiomining.summarize import summarize_buckets
import typer

app = typer.Typer(no_args_is_help=True, add_completion=False)

@app.command()
def preprocess(
    path: str = typer.Argument(..., help="Ordner/Datei mit Transkripten (rekursiv erlaubt)"),
    tz: str = typer.Option("Europe/Berlin", help="Zeitzone für absolute Zeiten"),
    recursive: bool = typer.Option(True, help="Unterordner rekursiv durchsuchen"),
    pattern: str = typer.Option("*.txt", help="Dateimuster (z. B. *.txt)"),
    start: Optional[str] = typer.Option(None, help="Nur Zeilen mit abs_start >= START (ISO, z.B. 2025-07-01T08:00)"),
    end:   Optional[str] = typer.Option(None, help="Nur Zeilen mit abs_start < END (ISO, z.B. 2025-07-01T09:00)"),
):
    files = discover_files(path, pattern=pattern, recursive=recursive)
    if not files:
        print("[red]Keine .txt Dateien gefunden[/red]")
        raise typer.Exit(code=1)

    out_dir = os.path.join(os.path.dirname(path.rstrip('/')), "out") if path.endswith("transcripts") else os.path.join(os.path.dirname(path), "out")
    os.makedirs(out_dir, exist_ok=True)

    df = preprocess_files(files, out_dir=out_dir, tz=tz)

    for col in ["abs_start", "abs_end", "file_start", "file_end"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            if df[col].dt.tz is None:
                df[col] = df[col].dt.tz_localize(tz)
            else:
                df[col] = df[col].dt.tz_convert(tz)

    def _parse_bound(val: Optional[str]) -> Optional[pd.Timestamp]:
        if not val:
            return None
        ts = pd.to_datetime(val, errors="coerce")
        if pd.isna(ts):
            return None
        return ts.tz_localize(tz) if ts.tzinfo is None else ts.tz_convert(tz)

    start_ts = _parse_bound(start)
    end_ts = _parse_bound(end)

    if start_ts is not None or end_ts is not None:
        if "abs_start" not in df.columns:
            print("[red]Spalte 'abs_start' fehlt – kann Zeitfilter nicht anwenden.[/red]")
            raise typer.Exit(code=2)
        mask = pd.Series(True, index=df.index)
        if start_ts is not None:
            mask &= df["abs_start"] >= start_ts
        if end_ts is not None:
            mask &= df["abs_start"] < end_ts
        before = len(df)
        df = df.loc[mask].copy()
        print(f"[cyan]Zeitfilter:[/cyan] {before} → {len(df)} Zeilen in [{start or '-∞'}, {end or '+∞'})")

        per_file = os.path.join(out_dir, "preprocessed", "all_preprocessed.csv")
        os.makedirs(os.path.dirname(per_file), exist_ok=True)
        df.to_csv(per_file, index=False)

    buckets = bucket_by_hour_sender(df)
    write_prompt_jsonl_for_buckets(buckets, out_dir=out_dir)

    per_file = os.path.join(out_dir, "preprocessed", "all_preprocessed.csv")
    print(f"[green]Fertig.[/green] {len(df)} Zeilen → {per_file}")
    print(f"Prompts: {os.path.join(out_dir, 'prompts')}")

def _read_df(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    for col in ["abs_start", "abs_end", "file_start", "file_end"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _parse_user_dt(val: Optional[str], tz: Optional[str]) -> Optional[pd.Timestamp]:
    if not val:
        return None
    ts = pd.to_datetime(val, errors="raise")
    if ts.tzinfo is None:
        if tz:
            ts = ts.tz_localize(ZoneInfo(tz))
        else:
            typer.secho("Warnung: Naive Zeit ohne --tz → setze UTC.", fg=typer.colors.YELLOW)
            ts = ts.tz_localize("UTC")
    return ts


@app.command(help="Fasst Stunden-Buckets zusammen und schreibt JSON-Summaries.")
def summarize(
    path: str = typer.Option(..., "--path", "-p", help="Basisordner mit 'preprocessed/' und 'summaries/'"),
    model: str = typer.Option("gpt-5-nano", "--model", "-m", help="OpenAI-Modellname"),
    csv_path: Optional[str] = typer.Option(
        None, "--csv", help="Optionaler Pfad zur CSV. Default: {path}/preprocessed/all_preprocessed.csv"
    ),
    start: Optional[str] = typer.Option(
        None, "--start", help="Start (inkl.), ISO 8601, z.B. 2025-07-01T08:00 oder 2025-07-01T08:00+02:00"
    ),
    end: Optional[str] = typer.Option(
        None, "--end", help="Ende (exkl.), ISO 8601, z.B. 2025-07-01T09:00 oder 2025-07-01T09:00+02:00"
    ),
    tz: Optional[str] = typer.Option(
        None, "--tz", help="Zeitzone für **naive** --start/--end, z.B. Europe/Berlin"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Existierende Summary-Dateien überschreiben"),
):
    csv_path = csv_path or os.path.join(path, "preprocessed", "all_preprocessed.csv")
    if not os.path.isfile(csv_path):
        raise typer.BadParameter(f"CSV nicht gefunden: {csv_path}")

    typer.secho(f"Lese CSV: {csv_path}", fg=typer.colors.BLUE)
    df = _read_df(csv_path)

    s = _parse_user_dt(start, tz)
    e = _parse_user_dt(end, tz)

    if "abs_start" in df.columns:
        target_tz = None
        if s is not None and s.tzinfo is not None:
            target_tz = s.tzinfo
        elif e is not None and e.tzinfo is not None:
            target_tz = e.tzinfo
        elif tz:
            target_tz = ZoneInfo(tz)

        if target_tz is not None:
            if df["abs_start"].dt.tz is None:
                df["abs_start"] = df["abs_start"].dt.tz_localize(target_tz)
            else:
                df["abs_start"] = df["abs_start"].dt.tz_convert(target_tz)   

    if s is not None and e is not None and e <= s:
        raise typer.BadParameter("--end muss nach --start liegen.")

    if s is not None:
        df = df[df["abs_start"] >= s]
    if e is not None:
        df = df[df["abs_start"] < e]

    if df.empty:
        typer.secho("Keine Zeilen im gewählten Zeitraum.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=0)

    typer.secho(f"Zeilen nach Filter: {len(df)}", fg=typer.colors.BLUE)

    results = summarize_buckets(df, out_dir=path, model=model, force=force)
    out_dir = os.path.join(path, "summaries")
    typer.secho(f"Summaries geschrieben: {len(results)} Dateien in {out_dir}", fg=typer.colors.GREEN)

def main():
    app()

if __name__ == "__main__":
    main()
