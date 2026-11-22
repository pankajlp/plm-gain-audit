"""Cut a large FLIP task down to a fixed, reproducible budget.

FLIP AAV is 284 009 sequences of ~740 aa; embedding all of it with ESM-2 650M
is ~10 h on this machine. We instead draw a fixed subsample per split (all
train rows when the split's train set is already small, so the low-label regime
is preserved exactly), write the reduced split CSVs, and emit the UNION of the
selected sequences as one fasta-less csv to embed once.

    python src/subsample.py --splits data/aav/splits --out data/aav/subsampled \
        --tasks sampled low_vs_high one_vs_many --train-cap 5000 --test-cap 5000
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

DRAW_SEED = 0  # fixed: the subsample must not move between runs


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--splits", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--tasks", nargs="+", required=True)
    p.add_argument("--train-cap", type=int, default=5000)
    p.add_argument("--test-cap", type=int, default=5000)
    a = p.parse_args()

    a.out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(DRAW_SEED)
    kept_seqs: dict[str, None] = {}  # insertion-ordered set
    manifest = {"draw_seed": DRAW_SEED, "train_cap": a.train_cap,
                "test_cap": a.test_cap, "tasks": {}}

    for task in a.tasks:
        df = pd.read_csv(a.splits / f"{task}.csv")
        out_parts = []
        for which, cap in (("train", a.train_cap), ("test", a.test_cap)):
            idx = np.flatnonzero((df["set"] == which).to_numpy())
            n_full = len(idx)
            if n_full > cap:
                idx = rng.choice(idx, size=cap, replace=False)
            out_parts.append(df.iloc[np.sort(idx)])
            manifest["tasks"].setdefault(task, {})[which] = {
                "full": int(n_full), "kept": int(len(idx)), "capped": bool(n_full > cap)
            }
        sub = pd.concat(out_parts).reset_index(drop=True)
        sub.to_csv(a.out / f"{task}.csv", index=False)
        for s in sub["sequence"]:
            kept_seqs.setdefault(s, None)
        t = manifest["tasks"][task]
        print(f"{task:<15} train {t['train']['kept']}/{t['train']['full']}"
              f"   test {t['test']['kept']}/{t['test']['full']}"
              f"   -> {len(sub)} rows")

    union = pd.DataFrame({"sequence": list(kept_seqs)})
    union["target"] = 0.0  # placeholder; features.py only reads `sequence`
    union["set"] = "train"
    union["validation"] = ""
    union.to_csv(a.out / "_union.csv", index=False)
    sha = hashlib.sha256("".join(union["sequence"]).encode()).hexdigest()[:12]
    manifest["union"] = {"n": int(len(union)), "seq_sha12": sha}
    (a.out / "_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nunion: {len(union)} unique sequences  sha12={sha}")
    print(f"wrote {a.out}/_union.csv and _manifest.json")


if __name__ == "__main__":
    main()
