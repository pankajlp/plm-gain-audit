"""Convert a TAPE task's LMDB splits into one FLIP-style csv.

Unlike FLIP, TAPE ships its own validation split, so the output keeps three
set labels (train / valid / test) and run_task.py uses the given valid rows
instead of carving its own. That removes one arbitrary choice from the
comparison.

    python src/tape_to_csv.py --task fluorescence --root data/tape --out data/tape/csv
"""
from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import lmdb
import pandas as pd

TARGET_KEY = {"fluorescence": "log_fluorescence", "stability": "stability_score"}


def read_split(lmdb_dir: Path, target_key: str) -> list[dict]:
    env = lmdb.open(str(lmdb_dir), readonly=True, lock=False)
    rows = []
    with env.begin(write=False) as txn:
        n = pickle.loads(txn.get(b"num_examples"))
        for i in range(n):
            rec = pickle.loads(txn.get(str(i).encode()))
            rows.append({"sequence": rec["primary"], "target": float(rec[target_key][0])})
    env.close()
    return rows


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--task", required=True, choices=sorted(TARGET_KEY))
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()

    key = TARGET_KEY[a.task]
    frames = []
    for split in ("train", "valid", "test"):
        rows = read_split(a.root / a.task / f"{a.task}_{split}.lmdb", key)
        df = pd.DataFrame(rows)
        df["set"] = split
        frames.append(df)
        print(f"{a.task} {split:<6} n={len(df):>6}  target {df['target'].min():.3f}..{df['target'].max():.3f}")

    full = pd.concat(frames).reset_index(drop=True)
    full["validation"] = ""
    lengths = full["sequence"].str.len()
    a.out.mkdir(parents=True, exist_ok=True)
    dest = a.out / f"{a.task}.csv"
    full.to_csv(dest, index=False)
    print(f"\nlengths {lengths.min()}-{lengths.max()}   total {len(full)}")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
