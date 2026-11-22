"""Compare two arms of a task: seed spread, paired bootstrap, and the n=1 gamble.

The headline number is `single_run_delta_range`: the largest delta a single
training run of each arm could have produced by seed luck alone. A paper
reporting one run per arm is sampling from that range.

    python src/compare.py --a evidence/runs/sampled.onehot.s42x10.npz \
        --b evidence/runs/sampled.esm2_650m.s42x10.npz --out evidence/comparisons
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr


def paired_bootstrap(pa, pb, y, n_boot=10000, seed=0):
    """Bootstrap over test complexes, both arms resampled on the SAME indices."""
    rng = np.random.default_rng(seed)
    n = len(y)
    deltas = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        if len(np.unique(y[idx])) < 3:
            deltas[i] = 0.0
            continue
        deltas[i] = spearmanr(pb[idx], y[idx]).statistic - spearmanr(pa[idx], y[idx]).statistic
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    # two-sided p: proportion of resamples on the far side of zero, doubled
    p = 2 * min((deltas <= 0).mean(), (deltas >= 0).mean())
    return float(lo), float(hi), float(min(p, 1.0)), deltas


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--a", type=Path, required=True, help="baseline arm .npz")
    p.add_argument("--b", type=Path, required=True, help="treatment arm .npz")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--n-boot", type=int, default=10000)
    args = p.parse_args()

    A, B = np.load(args.a), np.load(args.b)
    if not np.array_equal(A["test_idx"], B["test_idx"]):
        raise SystemExit("arms were evaluated on different test sets — not comparable")
    y = A["y_test"]
    name_a, name_b = args.a.stem, args.b.stem

    rho_a = np.array([spearmanr(pr, y).statistic for pr in A["preds"]])
    rho_b = np.array([spearmanr(pr, y).statistic for pr in B["preds"]])

    # every single-run pairing a one-seed-per-arm paper could have reported
    pairwise = np.array([rb - ra for ra, rb in itertools.product(rho_a, rho_b)])

    mean_a, mean_b = A["preds"].mean(0), B["preds"].mean(0)
    rho_mean_a = float(spearmanr(mean_a, y).statistic)
    rho_mean_b = float(spearmanr(mean_b, y).statistic)
    lo, hi, pval, _ = paired_bootstrap(mean_a, mean_b, y, args.n_boot)

    resid_corr = float(np.corrcoef(mean_a, mean_b)[0, 1])

    out = {
        "arm_a": name_a,
        "arm_b": name_b,
        "n_test": int(len(y)),
        "n_seeds": [int(len(rho_a)), int(len(rho_b))],
        "a_per_seed": {"mean": float(rho_a.mean()), "sd": float(rho_a.std(ddof=1)),
                       "min": float(rho_a.min()), "max": float(rho_a.max())},
        "b_per_seed": {"mean": float(rho_b.mean()), "sd": float(rho_b.std(ddof=1)),
                       "min": float(rho_b.min()), "max": float(rho_b.max())},
        "seed_mean_pred": {"a": rho_mean_a, "b": rho_mean_b, "delta": rho_mean_b - rho_mean_a,
                           "ci95": [lo, hi], "p": pval},
        "single_run_delta_range": {
            "min": float(pairwise.min()), "max": float(pairwise.max()),
            "mean": float(pairwise.mean()), "sd": float(pairwise.std(ddof=1)),
            "share_favouring_b": float((pairwise > 0).mean()),
            "share_sign_flipped_vs_seed_mean": float(
                (np.sign(pairwise) != np.sign(rho_mean_b - rho_mean_a)).mean()
            ),
        },
        "prediction_correlation_between_arms": resid_corr,
    }

    args.out.mkdir(parents=True, exist_ok=True)
    stem = f"{name_a}__vs__{name_b}"
    (args.out / f"{stem}.json").write_text(json.dumps(out, indent=2))

    lines = [
        f"{name_a}  vs  {name_b}     n_test={len(y)}  spearman",
        "",
        f"  A {name_a:<34} per-seed {rho_a.mean():.4f} +/- {rho_a.std(ddof=1):.4f}"
        f"  [{rho_a.min():.4f}, {rho_a.max():.4f}]",
        f"  B {name_b:<34} per-seed {rho_b.mean():.4f} +/- {rho_b.std(ddof=1):.4f}"
        f"  [{rho_b.min():.4f}, {rho_b.max():.4f}]",
        "",
        f"  seed-mean predictions: {rho_mean_a:.4f} -> {rho_mean_b:.4f}"
        f"   delta {rho_mean_b - rho_mean_a:+.4f} [{lo:+.4f}, {hi:+.4f}]  p={pval:.4f}",
        f"  prediction correlation between arms: {resid_corr:.3f}",
        "",
        "  the n=1 gamble: over all single-run pairings a one-seed-per-arm paper could report",
        f"    delta ranges {pairwise.min():+.4f} to {pairwise.max():+.4f}"
        f"  (mean {pairwise.mean():+.4f}, sd {pairwise.std(ddof=1):.4f})",
        f"    {100 * (pairwise > 0).mean():.1f}% of pairings favour B",
        f"    {100 * (np.sign(pairwise) != np.sign(rho_mean_b - rho_mean_a)).mean():.1f}% "
        "report the OPPOSITE sign to the seed-mean result",
    ]
    text = "\n".join(lines)
    (args.out / f"{stem}.txt").write_text(text + "\n")
    print(text)
    print(f"\nwrote {args.out / (stem + '.json')}")


if __name__ == "__main__":
    main()
