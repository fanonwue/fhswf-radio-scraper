from __future__ import annotations
import os, json
import pandas as pd
from datetime import datetime
from typing import Iterable, Dict
from .parsing import parse_filename, iter_lines_with_abs_times

def discover_files(path: str, pattern: str = "*.txt", recursive: bool = True) -> list[str]:
    import os, glob
    path = path.rstrip('/').rstrip('\\')
    if os.path.isfile(path):
        return [path]
    if recursive:
        return sorted(glob.glob(os.path.join(path, '**', pattern), recursive=True))
    else:
        return sorted(glob.glob(os.path.join(path, pattern)))

def preprocess_files(files: list[str], out_dir: str, tz: str = "Europe/Berlin") -> pd.DataFrame:
    rows = []
    for path in files:
        fw = parse_filename(path, tz=tz)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        for row in iter_lines_with_abs_times(text, fw):
            rows.append(row)
    if not rows:
        return pd.DataFrame(columns=["sender","abs_start","abs_end","text","speaker","rel_start_s","rel_end_s","file_start","file_end"])
    df = pd.DataFrame(rows).sort_values(["sender","abs_start"]).reset_index(drop=True)

    df["llm_line"] = df.apply(lambda r: f"[{r['abs_start']:%Y-%m-%d %H:%M:%S} - {r['abs_end']:%Y-%m-%d %H:%M:%S}] {r['text']}", axis=1)

    per_file = os.path.join(out_dir, "preprocessed", "all_preprocessed.csv")
    os.makedirs(os.path.dirname(per_file), exist_ok=True)
    df.to_csv(per_file, index=False)
    return df

def bucket_by_hour_sender(df: "pd.DataFrame") -> Dict[tuple, "pd.DataFrame"]:
    if df.empty:
        return {}
    df = df.copy()
    df["hour_start"] = df["abs_start"].dt.floor("h")
    buckets: Dict[tuple, "pd.DataFrame"] = {}
    for (sender, hour), g in df.groupby(["sender","hour_start"], sort=True):
        buckets[(sender, hour)] = g.sort_values("abs_start")
    return buckets

def write_prompt_jsonl_for_buckets(buckets: Dict[tuple, "pd.DataFrame"], out_dir: str):
    os.makedirs(os.path.join(out_dir, "prompts"), exist_ok=True)
    for (sender, hour), g in buckets.items():
        key = f"{sender}_{hour:%Y%m%d}_{hour:%H}.jsonl"
        path = os.path.join(out_dir, "prompts", key)
        with open(path, "w", encoding="utf-8") as f:
            for line in g["llm_line"].tolist():
                f.write(json.dumps({"text": line}, ensure_ascii=False) + "\n")
