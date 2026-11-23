"""Tally the Part A primary outcome from scan/decisions.jsonl.

FRAME.md's primary outcome is the distribution of seeds_per_arm over the 40
included papers. Several papers report different counts for different arms, so
HEADLINE_SEEDS fixes, per paper, the count attached to the arm that carries the
REPRESENTATION claim - the comparison I1 was satisfied by. The mapping is
written out in full so it can be audited and changed independently of the
free-text field.

    python src/scan_tally.py --decisions scan/decisions.jsonl
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

# idx -> (headline seed count, why this arm)
HEADLINE_SEEDS: dict[int, tuple[object, str]] = {
    0:  ("not_stated", "no seed language anywhere"),
    1:  (1, "'one trained model per configuration'"),
    2:  (5, "5 seeds averaged per CV fold"),
    5:  ("not_stated", "probes deterministic; count never given"),
    6:  (3, "3 seeds, per-seed AP reported"),
    7:  ("not_stated", "GLP arm's training count never given"),
    10: (3, "variant arms carry the ESM2-650M vs 8M swap"),
    12: (1, "'a single training run per model'"),
    13: (5, "best config retrained at 5 seeds"),
    14: (1, "the filtered-vs-unfiltered pretraining arms are the claim"),
    20: ("not_stated", "no seed language anywhere"),
    21: (1, "main tables single-run; 5-seed check is a separate appendix"),
    22: ("not_stated", "no seed language anywhere"),
    23: (5, "5 seeds for every supervised method"),
    24: (3, "the one-hot ablation arms ran at 3 seeds"),
    25: ("not_stated", "no seed repetition for the supervised probes"),
    26: (1, "the 12-architecture matrix is the claim; 3-seed subset is a check"),
    28: (5, "5 runs for the low-N regression table"),
    29: (1, "deterministic ACF arm, single released pLM checkpoint"),
    31: (3, "triplicate across 3 seeds"),
    32: (1, "full-scale tokenizer comparison used a single seed"),
    38: ("not_stated", "repeated CV only, no training-seed repetition"),
    39: (1, "only 'Seed = 0' in the hyperparameter table"),
    40: (5, "five aligned seeds 0-4"),
    41: (10, "10 random seeds"),
    42: (5, "5 seeds, seed-averaged SPCC as the paired unit"),
    43: ("not_stated", "'repeated runs', count never given"),
    45: ("not_stated", "seed check only on a different quantity"),
    47: ("not_stated", "5 CV folds, not seeds"),
    49: (5, "5 random seeds in the layer-selection procedure"),
    50: (3, "the frozen-ESM2 representation analysis ran at 3 seeds"),
    51: (1, "'retained single-run test predictions'"),
    53: (5, "5 seeds on most tasks"),
    55: ("not_stated", "5 CV folds, not seeds"),
    57: ("not_stated", "no seed language anywhere"),
    60: ("not_stated", "5 CV folds, not seeds"),
    64: ("not_stated", "no seed language anywhere"),
    67: ("not_stated", "bootstrap over test items only"),
    68: ("not_stated", "no seed language anywhere"),
    72: (6, "extended from 3 to 6 seeds"),
}

AMENDMENT_3 = {1, 10}   # entered under the structural/generative reading of I1
DUPLICATE_DROPPED = (69, 10)  # (idx, its seed count) excluded under Amendment 4


def share(rows: list[tuple[object, str]]) -> tuple[int, int, float]:
    weak = sum(1 for s, _ in rows if s == "not_stated" or s == 1)
    return weak, len(rows), 100.0 * weak / len(rows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--decisions", type=Path, required=True)
    a = p.parse_args()

    rows = [json.loads(l) for l in a.decisions.read_text().splitlines() if l.strip()]
    inc = [r for r in rows if r["decision"] == "include"]
    assert len(inc) == 40, f"expected 40 included, got {len(inc)}"
    missing = {r["idx"] for r in inc} - set(HEADLINE_SEEDS)
    assert not missing, f"no headline seed count for {sorted(missing)}"

    main_rows = [HEADLINE_SEEDS[r["idx"]] for r in inc]

    print("=== Primary outcome: headline seeds_per_arm over the 40 included ===\n")
    for k, v in sorted(Counter(str(s) for s, _ in main_rows).items(),
                       key=lambda x: (x[0] == "not_stated", x[0])):
        print(f"  {k:<14} {v:>3}   ({100*v/len(main_rows):.1f}%)")

    weak, n, pct = share(main_rows)
    print(f"\n  single-run or not stated: {weak}/{n} = {pct:.1f}%")
    thr = ("lead with the prevalence figure" if pct >= 50
           else "short note, Part B is the contribution" if pct < 20
           else "report flatly, no framing")
    print(f"  pre-committed branch: {thr}")

    print("\n=== Sensitivity to the three judgment calls ===\n")
    no_a3 = [HEADLINE_SEEDS[r["idx"]] for r in inc if r["idx"] not in AMENDMENT_3]
    w, n2, p2 = share(no_a3)
    print(f"  drop the 2 Amendment-3 papers:      {w}/{n2} = {p2:.1f}%")
    with_dup = main_rows + [(DUPLICATE_DROPPED[1], "duplicate restored")]
    w, n3, p3 = share(with_dup)
    print(f"  restore the Amendment-4 duplicate:  {w}/{n3} = {p3:.1f}%")
    no_tb = [HEADLINE_SEEDS[r["idx"]] for r in inc if r["idx"] != 41]
    w, n4, p4 = share(no_tb)
    print(f"  drop the tiebreak paper (FLaG, 10): {w}/{n4} = {p4:.1f}%")
    worst = min(pct, p2, p3, p4)
    print(f"\n  range across all four: {min(pct,p2,p3,p4):.1f}% - {max(pct,p2,p3,p4):.1f}%"
          f"  -> same branch throughout: {worst >= 50}")

    print("\n=== Secondary: variance and significance over the 40 ===\n")
    for field in ("variance_reported", "significance_test", "deterministic_probe"):
        c = Counter(str(r.get(field)) for r in inc)
        print(f"  {field}: " + ", ".join(f"{k}={v}" for k, v in c.most_common()))

    print("\n=== Exclusions ===\n")
    for k, v in Counter(r["decision"] for r in rows
                        if r["decision"] != "include").most_common():
        print(f"  {k:<14} {v}")
    print(f"\n  screened {len(rows)} to reach 40 inclusions "
          f"({100*40/len(rows):.0f}% inclusion rate)")


if __name__ == "__main__":
    main()
