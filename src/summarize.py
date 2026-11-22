"""Collect run summaries into one table: seed band per (task, arm).

    python src/summarize.py --runs evidence/runs
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SPLIT_ORDER = ["sampled", "three_vs_rest", "two_vs_rest", "low_vs_high", "one_vs_rest"]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--runs", type=Path, required=True)
    p.add_argument("--out", type=Path, default=None)
    a = p.parse_args()

    rows = []
    for f in sorted(a.runs.glob("*.json")):
        d = json.loads(f.read_text())
        rows.append(d)

    def key(d):
        t = d["task"]
        return (SPLIT_ORDER.index(t) if t in SPLIT_ORDER else 99, t, d["rep"])

    rows.sort(key=key)
    head = (
        f"{'task':<16}{'arm':<12}{'k':>3}{'n_test':>8}"
        f"{'per-seed mean':>15}{'sd':>9}{'min':>9}{'max':>9}{'range':>9}{'seed-mean':>11}"
    )
    lines = [head, "-" * len(head)]
    for d in rows:
        sd = d.get("per_seed_sd") or 0.0
        rng = d["per_seed_max"] - d["per_seed_min"]
        lines.append(
            f"{d['task']:<16}{d['rep']:<12}{len(d['seeds']):>3}{d['n_test']:>8}"
            f"{d['per_seed_mean']:>15.4f}{sd:>9.4f}{d['per_seed_min']:>9.4f}"
            f"{d['per_seed_max']:>9.4f}{rng:>9.4f}{d['seed_mean_pred_spearman']:>11.4f}"
        )
    text = "\n".join(lines)
    print(text)
    if a.out:
        a.out.write_text(text + "\n")
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
