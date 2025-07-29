from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

class CoverageAnalyzer:
    def __init__(self, gap_minutes: int, warn_threshold: float):
        self.gap_minutes = gap_minutes
        self.warn_threshold = warn_threshold

    def analyze_intervals(self, files, parser):
        intervals = []
        by_sender = defaultdict(list)
        for f in files:
            f = Path(f)
            if f.suffix.lower() != ".txt":
                continue
            parsed = parser.parse_filename(f)
            if not parsed:
                continue
            sender, start, end = parsed
            if start >= end:
                continue
            intervals.append((start, end))
            by_sender[sender].append((start, end))
        return intervals, by_sender

    def merge_intervals(self, intervals):
        if not intervals:
            return []
        intervals.sort()
        merged = [list(intervals[0])]
        for s, e in intervals[1:]:
            if merged[-1][1] < s:
                merged.append([s, e])
            else:
                merged[-1][1] = max(merged[-1][1], e)
        return merged

    def compute_coverage(self, merged, span_seconds):
        total_duration = sum((e - s).total_seconds() for s, e in merged)
        coverage = round(100 * total_duration / span_seconds, 2) if span_seconds > 0 else 0.0
        return total_duration, coverage

    def compute_gaps(self, merged):
        gap_count = 0
        longest_gap = timedelta(0)
        prev_end = None
        for s, e in merged:
            if prev_end is not None:
                gap = s - prev_end
                if gap > timedelta(minutes=self.gap_minutes):
                    gap_count += 1
                    longest_gap = max(longest_gap, gap)
            prev_end = e
        return gap_count, longest_gap

    def analyze(self, files, parser, level: str, outdir: Path, root: Path):
        intervals, by_sender = self.analyze_intervals(files, parser)
        if not intervals:
            return None
        merged = self.merge_intervals(intervals)
        total_duration, coverage = self.compute_coverage(merged, (merged[-1][1] - merged[0][0]).total_seconds())
        gap_count, longest_gap = self.compute_gaps(merged)
        span_seconds = (merged[-1][1] - merged[0][0]).total_seconds()
        summary = {
            "level": level,
            "path": str(outdir.relative_to(root)),
            "total_recordings": len(intervals),
            "total_duration_minutes": round(total_duration / 60, 2),
            "coverage_percent": coverage,
            "gap_count": gap_count,
            "longest_gap_minutes": round(longest_gap.total_seconds() / 60, 2),
            "warn": coverage < self.warn_threshold,
            "per_sender": {}
        }
        for sender, segs in by_sender.items():
            segs.sort()
            merged_sender = self.merge_intervals(segs)
            dur = sum((e - s).total_seconds() for s, e in merged_sender)
            pct = round(100 * dur / span_seconds, 2) if span_seconds > 0 else 0.0
            summary["per_sender"][sender] = {
                "count": len(segs),
                "duration_minutes": round(dur / 60, 2),
                "coverage_percent": pct,
                "warn": pct < self.warn_threshold
            }
        return summary, intervals, merged
