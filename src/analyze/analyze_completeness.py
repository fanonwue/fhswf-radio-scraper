import argparse
from collections import defaultdict
from datetime import datetime, timedelta
from html import escape
import json
from pathlib import Path
import numpy as np

from coverage_analyzer import CoverageAnalyzer
from coverage_plotter import CoveragePlotter
from filename_parser import FilenameParser


class CompletenessAnalyzer:
    TXT_PATTERN = "*.txt"

    def __init__(self, root_dir: str, gap_minutes: int = 5, warn_threshold: float = 80.0):
        self.root = Path(root_dir)
        self.gap_minutes = gap_minutes
        self.warn_threshold = warn_threshold
        self.all_summaries = []
        self.parser = FilenameParser()
        self.analyzer = CoverageAnalyzer(gap_minutes, warn_threshold)
        self.plotter = CoveragePlotter()

    def analyze_unit(self, files, outdir: Path, level: str):
        result = self.analyzer.analyze(files, self.parser, level, outdir, self.root)
        if not result:
            return
        summary, intervals, merged = result
        outdir.mkdir(parents=True, exist_ok=True)
        with open(outdir / "summary.json", "w", encoding="utf-8") as jf:
            json.dump(summary, jf, indent=2, ensure_ascii=False)
        self.plotter.plot_intervals(intervals, merged, merged[0][0], merged[-1][1], self.gap_minutes, level, outdir, summary["coverage_percent"])
        self.all_summaries.append(summary)
    
    def hour_coverage(self, day_dir, h):
        hour_start = datetime.strptime(f"{day_dir.name}_{h:02d}0000", "%Y-%m-%d_%H%M%S")
        hour_end = hour_start + timedelta(hours=1)
        intervals = []
        hour_dir = day_dir / f"{h:02d}"
        if hour_dir.is_dir():
            for f in hour_dir.glob(self.TXT_PATTERN):
                parsed = self.parser.parse_filename(f)
                if not parsed:
                    continue
                _, s, e = parsed
                s_clipped = max(s, hour_start)
                e_clipped = min(e, hour_end)
                if s_clipped < e_clipped:
                    intervals.append((s_clipped, e_clipped))
        if not intervals:
            return 0.0
        intervals.sort()
        merged = [list(intervals[0])]
        for ss, ee in intervals[1:]:
            if merged[-1][1] < ss:
                merged.append([ss, ee])
            else:
                merged[-1][1] = max(merged[-1][1], ee)
        total_sec = sum((ee - ss).total_seconds() for ss, ee in merged)
        return round(100 * total_sec / 3600, 2)
    
    def heatmap_month(self, month_dir: Path):
        day_dirs = sorted([d for d in month_dir.iterdir() if d.is_dir() and '-' in d.name])
        if not day_dirs:
            return
        n_days = len(day_dirs)
        heat = np.zeros((n_days, 24))
        for i, day_dir in enumerate(day_dirs):
            for h in range(24):
                heat[i, h] = self.hour_coverage(day_dir, h)
        self.plotter.plot_heatmap(heat, day_dirs, month_dir)

    def cleanup_outputs(self):
        for p in self.root.rglob("summary.json"): p.unlink(missing_ok=True)
        for p in self.root.rglob("summary.png"): p.unlink(missing_ok=True)
        for p in self.root.rglob("heatmap.png"): p.unlink(missing_ok=True)
        rpt = self.root / "summary_report.html"
        if rpt.exists(): rpt.unlink()

    def walk_structure(self):
        # Neue Struktur: root/Jahr/Monat/Tag
        for year_dir in sorted(self.root.glob("20??")):
            for month_dir in sorted(year_dir.glob("??")):
                self.analyze_unit(month_dir.rglob(self.TXT_PATTERN), month_dir, "month")
                self.heatmap_month(month_dir)
                for day_dir in sorted(month_dir.glob("20??-??-??")):
                    self.analyze_unit(day_dir.rglob(self.TXT_PATTERN), day_dir, "day")
                    for hour_dir in sorted(day_dir.glob("??")):
                        if hour_dir.is_dir():
                            self.analyze_unit(hour_dir.rglob(self.TXT_PATTERN), hour_dir, "hour")
        self._analyze_weeks()

    def _analyze_weeks(self):
        weeks = defaultdict(list)
        for year_dir in sorted(self.root.glob("20??")):
            for month_dir in sorted(year_dir.glob("??")):
                for day_dir in sorted(month_dir.glob("20??-??-??")):
                    try:
                        d = datetime.strptime(day_dir.name, "%Y-%m-%d")
                        y, w, _ = d.isocalendar()
                        key = f"{y}-W{w:02d}"
                        weeks[key].extend(day_dir.rglob(self.TXT_PATTERN))
                    except ValueError:
                        continue
        for wk, files in weeks.items():
            self.analyze_unit(files, self.root / wk, "week")

    def write_html_report(self):
        html = [
            "<html><head><meta charset='utf-8'>",
            "<title>Vollständigkeitsanalyse</title>",
            "<style>",
            "body { font-family: sans-serif; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ccc; padding: 6px; }",
            ".warn { background-color: #ffe6e6; }",
            ".ok { background-color: #e6ffe6; }",
            ".filters { margin: 10px 0; }",
            "img { max-width: 100%; margin: 10px 0; }",
            "</style>",
            "<script>",
            "function applyFilter() {",
            "  var lvl = document.getElementById('levelFilter').value;",
            "  var snd = document.getElementById('senderFilter').value;",
            "  document.querySelectorAll('.row').forEach(function(r) {",
            "    var show = (lvl === 'ALL' || r.dataset.level === lvl) &&",
            "               (snd === 'ALL' || r.dataset.senders.split(',').includes(snd));",
            "    r.style.display = show ? '' : 'none';",
            "  });",
            "}",
            "</script>",
            "</head><body onload='applyFilter()'>",
            "<h1>Vollständigkeitsanalyse</h1>",
            "<div class='filters'>Ebene: <select id='levelFilter' onchange='applyFilter()'>",
            "<option value='ALL'>ALL</option><option value='hour'>hour</option><option value='day'>day</option><option value='week'>week</option><option value='month' selected>month</option>",
            "</select> Sender: <select id='senderFilter' onchange='applyFilter()'>",
            "<option value='ALL'>ALL</option>"
        ]
        senders = sorted({s for e in self.all_summaries for s in e['per_sender']})
        for s in senders:
            html.append(f"<option value='{escape(s)}'>{escape(s)}</option>")
        html += [
            "</select></div>",
            "<table><tr><th>Ebene</th><th>Pfad</th><th>Coverage</th><th>Warn</th><th>PNG</th><th>JSON</th><th>Heatmap</th></tr>"
        ]
        for e in sorted(self.all_summaries, key=lambda x: (x['level'], x['path'])):
            lvl, pt, cov, wr = e['level'], e['path'], e['coverage_percent'], e['warn']
            send_str = ','.join(e['per_sender'].keys())
            cls = 'warn' if wr else 'ok'
            heat_link = f"<a href='{pt}/heatmap.png'>Heatmap</a>" if lvl=='month' else ''
            html.append(
                f"<tr class='row {cls}' data-level='{lvl}' data-senders='{send_str}'>"
                f"<td>{lvl}</td><td>{escape(pt)}</td><td>{cov}%</td>"
                f"<td>{'⚠️' if wr else ''}</td>"
                f"<td><a href='{pt}/summary.png'>PNG</a></td>"
                f"<td><a href='{pt}/summary.json'>JSON</a></td>"
                f"<td>{heat_link}</td></tr>"
            )
        html += ["</table></body></html>"]
        with open(self.root / "summary_report.html", "w", encoding='utf-8') as hf:
            hf.write("\n".join(html))

    def run(self):
        self.cleanup_outputs()
        self.walk_structure()
        self.write_html_report()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vollständigkeitsanalyse für strukturierte Aufnahmen")
    parser.add_argument('path', help='Root-Ordner mit Jahr/Monat/Tag/Stunde')
    parser.add_argument('--gap', type=int, default=5, help='Lücken-Minuten-Schwelle')
    parser.add_argument('--warn', type=float, default=80.0, help='Warnschwelle in Prozent')
    args = parser.parse_args()
    CompletenessAnalyzer(args.path, args.gap, args.warn).run()
