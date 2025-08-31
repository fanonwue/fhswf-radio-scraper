from __future__ import annotations

import json
import os
import os.path as op
from typing import Optional, Dict, Tuple

import pandas as pd

from radiomining.prompts import SYSTEM_PROMPT, build_user_prompt
from radiomining.schemas import HOUR_SCHEMA
from radiomining.openai_client import responses_json, DEFAULT_MODEL
from radiomining.ids import make_story_id

from pathlib import Path
import json

from pathlib import Path


def _summary_is_valid(pathlike: str | Path) -> bool:
    p = Path(pathlike)
    if not p.exists() or p.stat().st_size == 0:
        return False

    tmp = p.with_suffix(p.suffix + ".tmp")
    if tmp.exists() and tmp.stat().st_mtime > p.stat().st_mtime:
        return False
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))

        sender_ok = bool(obj.get("sender") or obj.get("programm"))
        segs = obj.get("segments") or obj.get("segmente") or []
        segs_ok = isinstance(segs, list) and len(segs) > 0
        return sender_ok and segs_ok
    except Exception:
        return False


def summarize_buckets(
    df: pd.DataFrame,
    out_dir: str,
    model: str = DEFAULT_MODEL,
    force: bool = False,
    start_dt: Optional[pd.Timestamp] = None,
    end_dt: Optional[pd.Timestamp] = None,
) -> Dict[str, str]:
    if start_dt is not None:
        df = df[df["abs_start"] >= start_dt]
    if end_dt is not None:
        df = df[df["abs_start"] < end_dt]

    buckets = _bucket_by_hour_sender(df)

    out_summaries = op.join(out_dir, "summaries")
    os.makedirs(out_summaries, exist_ok=True)

    results: Dict[str, str] = {}

    for (sender, hour), g in buckets.items():
        key = f"{sender}_{hour.strftime('%Y%m%d')}_{hour.strftime('%H')}"
        out_path = op.join(out_summaries, f"{key}.json")
        results[key] = out_path

        if not force and _summary_is_valid(out_path):
            print(f"skipping: {out_path}")
            continue

        text = _join_llm_lines(g)
        user = build_user_prompt(
            sender=sender,
            hour_iso=hour.strftime("%Y-%m-%d %H:00:00"),
            hour_end_iso=(hour + pd.Timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00"),
            text=text,
        )

        data = responses_json(
            model=model, system=SYSTEM_PROMPT, user=user, json_schema=HOUR_SCHEMA, seed=None
        )

        data.setdefault("sender", sender)
        data.setdefault("hour_start", hour.strftime("%Y-%m-%d %H:00:00"))
        data.setdefault("hour_end", (hour + pd.Timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00"))
        data.setdefault("hosts", [])
        data.setdefault("main_topics", [])
        data.setdefault("news_topics", [])
        data.setdefault("weather_present", False)
        data.setdefault("traffic_present", False)
        data.setdefault("ads_present", False)
        data.setdefault("segments", [])

        for seg in data.get("segments", []):
            _normalize_segment(seg)
            seg.setdefault("tags", [])

            if not seg.get("story_key"):
                sk = _fallback_story_key(seg)
                if sk:
                    seg["story_key"] = sk
            if seg.get("story_key") and not seg.get("story_id"):
                try:
                    seg["story_id"] = make_story_id(seg["story_key"])
                except Exception:
                    seg.setdefault("story_id", None)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return results

def _bucket_by_hour_sender(df: pd.DataFrame) -> Dict[Tuple[str, pd.Timestamp], pd.DataFrame]:
    req_cols = {"sender", "abs_start", "llm_line"}
    missing = req_cols - set(df.columns)
    if missing:
        raise ValueError(f"Fehlende Spalten in CSV: {sorted(missing)}")

    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["abs_start"]):
        df["abs_start"] = pd.to_datetime(df["abs_start"], errors="coerce")

    df["hour_start"] = df["abs_start"].dt.floor("h")
    groups: Dict[Tuple[str, pd.Timestamp], pd.DataFrame] = {}
    for (sender, hour), g in df.groupby(["sender", "hour_start"], as_index=False):
        g = g.sort_values("abs_start", kind="stable")
        groups[(sender, hour)] = g
    return groups


def _join_llm_lines(g: pd.DataFrame) -> str:
    if "llm_line" in g.columns and g["llm_line"].notna().any():
        lines = [str(x) for x in g["llm_line"].tolist()]
    else:
        text_col = "text" if "text" in g.columns else ("content" if "content" in g.columns else None)
        if text_col:
            lines = [
                f"[{row['abs_start']:%Y-%m-%d %H:%M:%S}] {row[text_col]}"
                for _, row in g.iterrows()
            ]
        else:
            lines = [f"[{t:%Y-%m-%d %H:%M:%S}]" for t in g["abs_start"].tolist()]
    return "\n".join(lines)


def _normalize_segment(seg: dict) -> None:
    seg.setdefault("type", "other")
    seg.setdefault("title", None)
    seg.setdefault("topic", None)
    seg.setdefault("topics", [])
    seg.setdefault("start", None)
    seg.setdefault("end", None)
    seg.setdefault("speakers", [])
    seg.setdefault("summary", None)

    seg.setdefault("tags", [])
    seg.setdefault("story_key", None)
    seg.setdefault("story_id", None)

    if not isinstance(seg.get("topics"), list) or seg["topics"] is None:
        seg["topics"] = []
    if not isinstance(seg.get("speakers"), list) or seg["speakers"] is None:
        seg["speakers"] = []
    if not isinstance(seg.get("tags"), list) or seg["tags"] is None:
        seg["tags"] = []

    for k in ["type", "title", "topic", "summary", "story_key", "story_id"]:
        if seg.get(k) is not None:
            seg[k] = str(seg[k]).strip()

    for k in ["start", "end"]:
        if seg.get(k) is not None:
            seg[k] = str(seg[k]).strip()


def _fallback_story_key(seg: dict) -> Optional[str]:
    title = (seg.get("title") or "").strip()
    topic = (seg.get("topic") or "").strip()
    if title:
        return title
    if topic:
        return topic

    summary = (seg.get("summary") or "").strip()
    if summary:
        words = summary.split()
        if len(words) >= 6:
            return " ".join(words[:12])
    return None
