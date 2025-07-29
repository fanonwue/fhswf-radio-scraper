import matplotlib.pyplot as plt
import numpy as np
from datetime import timedelta

class CoveragePlotter:
    @staticmethod
    def plot_intervals(intervals, merged, start_time, end_time, gap_minutes, level, outdir, coverage):
        fig, ax = plt.subplots(figsize=(10, 1))
        for s, e in intervals:
            ax.plot([s, e], [0, 0], color='green', linewidth=6)
        for i in range(1, len(merged)):
            gs, ge = merged[i-1][1], merged[i][0]
            if (ge - gs) > timedelta(minutes=gap_minutes):
                ax.plot([gs, ge], [0, 0], color='red', linewidth=4)
        ax.set_yticks([])
        ax.set_xlim(start_time, end_time)
        ax.set_title(f"{level.upper()} {outdir.name} ({coverage}%)")
        plt.tight_layout()
        fig.savefig(outdir / "summary.png")
        plt.close(fig)

    @staticmethod
    def plot_heatmap(heat, day_dirs, month_dir):
        n_days = len(day_dirs)
        fig, ax = plt.subplots(figsize=(12, n_days * 0.3 + 1))
        cax = ax.imshow(heat, aspect='auto', origin='lower', cmap='YlGn', vmin=0, vmax=100)
        ax.set_yticks(range(n_days))
        ax.set_yticklabels([d.name for d in day_dirs])
        ax.set_xticks(range(0, 24, 2))
        ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)])
        ax.set_xlabel("Stunde")
        ax.set_title(f"Monats-Heatmap {month_dir.name}")
        fig.colorbar(cax, label="Coverage (%)")
        plt.tight_layout()
        fig.savefig(month_dir / "heatmap.png")
        plt.close(fig)
