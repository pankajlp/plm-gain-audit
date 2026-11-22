"""Train a light head on frozen features for k seeds and save per-seed test predictions.

The data split is held FIXED across seeds and arms; only parameter init and batch
order vary with the seed. That isolates the variance source a single-run ablation
silently gambles on.

    python src/run_task.py --csv data/gb1/splits/sampled.csv \
        --features features/gb1 --rep esm2_650m --seeds 10 --out evidence/runs
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr
from torch import nn

VAL_FRACTION = 0.1
VAL_SPLIT_SEED = 0  # fixed on purpose: the split is not what we are varying


def find_features(feature_dir: Path, rep: str, seq_sha12: str) -> Path:
    hits = sorted(feature_dir.glob(f"*.{rep}.{seq_sha12}.npy"))
    if not hits:
        raise FileNotFoundError(
            f"no features for rep={rep} sha={seq_sha12} in {feature_dir} — run src/features.py"
        )
    return hits[0]


class Head(nn.Module):
    def __init__(self, dim: int, hidden: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, hidden), nn.ReLU(), nn.Dropout(dropout), nn.Linear(hidden, 1)
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


def train_one(
    Xtr, ytr, Xva, yva, Xte, seed, device, hidden, dropout, lr, batch_size, max_epochs, patience
):
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = Head(Xtr.shape[1], hidden, dropout).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    lossf = nn.MSELoss()
    g = torch.Generator().manual_seed(seed)

    Xtr_t = torch.from_numpy(Xtr).to(device)
    ytr_t = torch.from_numpy(ytr).to(device)
    Xva_t = torch.from_numpy(Xva).to(device)
    Xte_t = torch.from_numpy(Xte).to(device)

    best_rho, best_state, bad = -np.inf, None, 0
    for _ in range(max_epochs):
        model.train()
        order = torch.randperm(len(Xtr_t), generator=g).to(device)
        for i in range(0, len(order), batch_size):
            idx = order[i : i + batch_size]
            opt.zero_grad()
            loss = lossf(model(Xtr_t[idx]), ytr_t[idx])
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            pva = model(Xva_t).cpu().numpy()
        rho = spearmanr(pva, yva).statistic
        if rho > best_rho:
            best_rho, bad = rho, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                break

    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        return model(Xte_t).cpu().numpy(), float(best_rho)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--features", type=Path, required=True)
    p.add_argument("--rep", required=True)
    p.add_argument(
        "--index-csv", type=Path, default=None,
        help="csv whose row order the feature matrix follows (for shared/union features)",
    )
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--seed-base", type=int, default=42)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--hidden", type=int, default=256)
    p.add_argument("--dropout", type=float, default=0.1)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--max-epochs", type=int, default=200)
    p.add_argument("--patience", type=int, default=10)
    a = p.parse_args()

    df = pd.read_csv(a.csv)
    if a.index_csv is None:
        sha = hashlib.sha256("".join(df["sequence"]).encode()).hexdigest()[:12]
        X = np.load(find_features(a.features, a.rep, sha))
    else:
        # features were built once over a union of sequences; gather this split's rows
        index = pd.read_csv(a.index_csv)
        sha = hashlib.sha256("".join(index["sequence"]).encode()).hexdigest()[:12]
        Xall = np.load(find_features(a.features, a.rep, sha), mmap_mode="r")
        row_of = {s: i for i, s in enumerate(index["sequence"])}
        missing = [s for s in df["sequence"] if s not in row_of]
        if missing:
            raise SystemExit(
                f"{len(missing)} of {len(df)} sequences are absent from {a.index_csv}"
            )
        X = np.ascontiguousarray(Xall[[row_of[s] for s in df["sequence"]]])
    y = df["target"].to_numpy(dtype=np.float32)

    is_train = (df["set"] == "train").to_numpy()
    is_test = (df["set"] == "test").to_numpy()
    tr_idx = np.flatnonzero(is_train)
    rng = np.random.default_rng(VAL_SPLIT_SEED)
    rng.shuffle(tr_idx)
    n_val = max(1, int(round(VAL_FRACTION * len(tr_idx))))
    va_idx, tr_idx = tr_idx[:n_val], tr_idx[n_val:]
    te_idx = np.flatnonzero(is_test)

    mu, sd = X[tr_idx].mean(0), X[tr_idx].std(0)
    sd[sd < 1e-6] = 1.0
    Xn = ((X - mu) / sd).astype(np.float32)
    ymu, ysd = y[tr_idx].mean(), y[tr_idx].std() or 1.0
    yn = ((y - ymu) / ysd).astype(np.float32)

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(
        f"{a.csv.stem} / {a.rep}: dim={X.shape[1]} train={len(tr_idx)} val={len(va_idx)} "
        f"test={len(te_idx)} device={device}",
        flush=True,
    )

    preds, per_seed, seeds = [], [], []
    for s in range(a.seed_base, a.seed_base + a.seeds):
        t0 = time.time()
        pte, val_rho = train_one(
            Xn[tr_idx], yn[tr_idx], Xn[va_idx], y[va_idx], Xn[te_idx], s, device,
            a.hidden, a.dropout, a.lr, a.batch_size, a.max_epochs, a.patience,
        )
        rho = float(spearmanr(pte, y[te_idx]).statistic)
        preds.append(pte)
        per_seed.append(rho)
        seeds.append(s)
        print(f"  seed {s}: test spearman {rho:.4f}  (val {val_rho:.4f})  {time.time()-t0:.1f}s",
              flush=True)

    per_seed_arr = np.array(per_seed)
    seed_mean_pred = np.mean(preds, axis=0)
    rho_mean_pred = float(spearmanr(seed_mean_pred, y[te_idx]).statistic)

    a.out.mkdir(parents=True, exist_ok=True)
    stem = f"{a.csv.stem}.{a.rep}.s{a.seed_base}x{a.seeds}"
    np.savez(
        a.out / f"{stem}.npz",
        preds=np.array(preds), y_test=y[te_idx], test_idx=te_idx, seeds=np.array(seeds),
    )
    summary = {
        "task": a.csv.stem,
        "rep": a.rep,
        "seeds": seeds,
        "n_test": int(len(te_idx)),
        "per_seed_spearman": per_seed,
        "per_seed_mean": float(per_seed_arr.mean()),
        "per_seed_sd": float(per_seed_arr.std(ddof=1)) if len(per_seed_arr) > 1 else None,
        "per_seed_min": float(per_seed_arr.min()),
        "per_seed_max": float(per_seed_arr.max()),
        "seed_mean_pred_spearman": rho_mean_pred,
        "hparams": {
            "hidden": a.hidden, "dropout": a.dropout, "lr": a.lr,
            "batch_size": a.batch_size, "max_epochs": a.max_epochs, "patience": a.patience,
        },
    }
    (a.out / f"{stem}.json").write_text(json.dumps(summary, indent=2))
    print(
        f"\n{a.rep}: per-seed {per_seed_arr.mean():.4f} +/- "
        f"{per_seed_arr.std(ddof=1) if len(per_seed_arr)>1 else 0:.4f}  "
        f"[{per_seed_arr.min():.4f}, {per_seed_arr.max():.4f}]  "
        f"seed-mean-pred {rho_mean_pred:.4f}"
    )
    print(f"wrote {a.out / (stem + '.json')}")


if __name__ == "__main__":
    main()
