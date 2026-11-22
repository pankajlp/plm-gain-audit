"""Cross-benchmark table: does a single run get the sign of the delta right?

The column that matters is |delta| / sd, the true effect divided by the wider
arm's seed spread. The sign-flip rate tracks that ratio, not the nominal
difficulty of the split.

    python src/crosstab.py --dirs evidence/comparisons:GB1 \
        evidence/comparisons_aav:AAV evidence/comparisons_tape:TAPE \
        --out evidence/crosstab.txt
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dirs", nargs="+", required=True, help="path:label pairs")
    p.add_argument("--out", type=Path, default=None)
    a = p.parse_args()

    rows = []
    for spec in a.dirs:
        path, _, label = spec.partition(":")
        for f in sorted(Path(path).glob("*.json")):
            j = json.loads(f.read_text())
            sm, sr = j["seed_mean_pred"], j["single_run_delta_range"]
            band = max(j["a_per_seed"]["sd"], j["b_per_seed"]["sd"])
            rows.append(
                {
                    "bench": label or path,
                    "task": j["arm_a"].split(".")[0],
                    "n_test": j["n_test"],
                    "delta": sm["delta"],
                    "p": sm["p"],
                    "band": band,
                    "ratio": abs(sm["delta"]) / band if band else float("inf"),
                    "lo": sr["min"],
                    "hi": sr["max"],
                    "flip": sr["share_sign_flipped_vs_seed_mean"],
                    "corr": j["prediction_correlation_between_arms"],
                }
            )

    rows.sort(key=lambda r: -r["flip"])
    head = (
        f"{'bench':<6}{'task':<16}{'n_test':>7}{'true d':>9}{'p':>8}"
        f"{'band sd':>9}{'|d|/sd':>8}{'n=1 delta range':>22}{'flip%':>7}"
    )
    lines = [
        "sign-flip rate against effect-to-noise ratio",
        "band sd = the wider arm's per-seed sd; flip% = share of the 100 single-run",
        "pairings whose sign disagrees with the 10-seed result",
        "",
        head,
        "-" * len(head),
    ]
    for r in rows:
        rng = f"{r['lo']:+.3f} .. {r['hi']:+.3f}"
        lines.append(
            f"{r['bench']:<6}{r['task']:<16}{r['n_test']:>7}{r['delta']:>+9.4f}"
            f"{r['p']:>8.3f}{r['band']:>9.4f}{r['ratio']:>8.2f}{rng:>22}{100 * r['flip']:>7.0f}"
        )

    below = [r for r in rows if r["ratio"] < 2.0]
    above = [r for r in rows if r["ratio"] >= 2.0]
    lines += [
        "",
        f"ratio < 2.0  ({len(below)} comparisons): flip rate "
        f"{100 * min(r['flip'] for r in below):.0f}-{100 * max(r['flip'] for r in below):.0f}%",
        f"ratio >= 2.0 ({len(above)} comparisons): flip rate "
        f"{100 * min(r['flip'] for r in above):.0f}-{100 * max(r['flip'] for r in above):.0f}%",
    ]
    text = "\n".join(lines)
    print(text)
    if a.out:
        a.out.write_text(text + "\n")
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
