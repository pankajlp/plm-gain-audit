"""Build frozen representations for a FLIP-style csv (sequence,target,set,validation).

Each representation is cached as an .npy next to a .json manifest so a run never
recomputes embeddings. Usage:

    python src/features.py --csv <path> --rep onehot|esm2_8m|esm2_150m|esm2_650m \
        --out <dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

AA = "ACDEFGHIKLMNPQRSTVWY"
AA_INDEX = {a: i for i, a in enumerate(AA)}

ESM_MODELS = {
    "esm2_8m": "facebook/esm2_t6_8M_UR50D",
    "esm2_35m": "facebook/esm2_t12_35M_UR50D",
    "esm2_150m": "facebook/esm2_t30_150M_UR50D",
    "esm2_650m": "facebook/esm2_t33_650M_UR50D",
}


def onehot(seqs: list[str]) -> tuple[np.ndarray, dict]:
    """Flattened per-position one-hot, right-padded with zeros to the longest sequence.

    Columns with no variance across the corpus carry no information for any head
    that standardizes its inputs (they reduce to a bias), so they are dropped and
    the count is recorded. FLIP AAV mutates a 28-residue window of a ~740 aa
    capsid, so this removes the overwhelming majority of the 15 000 raw columns.
    """
    L = max(len(s) for s in seqs)
    X = np.zeros((len(seqs), L * len(AA)), dtype=np.float32)
    for i, s in enumerate(seqs):
        for j, c in enumerate(s):
            k = AA_INDEX.get(c)
            if k is not None:
                X[i, j * len(AA) + k] = 1.0
    keep = X.std(axis=0) > 1e-8
    meta = {
        "padded_length": int(L),
        "raw_columns": int(X.shape[1]),
        "constant_columns_dropped": int((~keep).sum()),
        "length_range": [int(min(len(s) for s in seqs)), int(L)],
    }
    return np.ascontiguousarray(X[:, keep]), meta


def esm_embed(seqs: list[str], model_name: str, batch_size: int = 8) -> np.ndarray:
    import torch
    from transformers import AutoModel, AutoTokenizer

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device).eval()

    out = []
    with torch.no_grad():
        for start in range(0, len(seqs), batch_size):
            chunk = seqs[start : start + batch_size]
            enc = tok(chunk, return_tensors="pt", padding=True, truncation=False)
            enc = {k: v.to(device) for k, v in enc.items()}
            h = model(**enc).last_hidden_state  # (B, T, D)
            mask = enc["attention_mask"].unsqueeze(-1).float()
            # drop BOS/EOS from the mean by zeroing them in the mask
            mask[:, 0] = 0.0
            lens = enc["attention_mask"].sum(1)
            for b, n in enumerate(lens.tolist()):
                mask[b, n - 1] = 0.0
            pooled = (h * mask).sum(1) / mask.sum(1).clamp(min=1)
            out.append(pooled.float().cpu().numpy())
            if (start // batch_size) % 50 == 0:
                print(f"  {start + len(chunk)}/{len(seqs)}", flush=True)
    return np.concatenate(out).astype(np.float32)


def build(csv: Path, rep: str, out_dir: Path) -> Path:
    df = pd.read_csv(csv)
    seqs = df["sequence"].tolist()
    tag = hashlib.sha256(("".join(seqs)).encode()).hexdigest()[:12]
    out_dir.mkdir(parents=True, exist_ok=True)
    npy = out_dir / f"{csv.stem}.{rep}.{tag}.npy"
    if npy.exists():
        print(f"cached {npy.name}")
        return npy

    meta: dict = {}
    if rep == "onehot":
        X, meta = onehot(seqs)
    elif rep in ESM_MODELS:
        X = esm_embed(seqs, ESM_MODELS[rep])
    else:
        raise ValueError(f"unknown rep {rep!r}")

    np.save(npy, X)
    npy.with_suffix(".json").write_text(
        json.dumps(
            {
                "csv": str(csv),
                "rep": rep,
                "model": ESM_MODELS.get(rep),
                "n": len(seqs),
                "dim": int(X.shape[1]),
                "seq_sha12": tag,
                **meta,
            },
            indent=2,
        )
    )
    print(f"wrote {npy.name}  shape={X.shape}")
    return npy


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--rep", required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    build(a.csv, a.rep, a.out)
