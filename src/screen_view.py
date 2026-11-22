"""Print a compact screening view for papers, in pool order, from stored full texts.

Shows only what the frame's decisions turn on: whether the paper reports its own
numeric representation comparison (I1/I2), and what it says about seeds,
variance and significance for that comparison.

    python src/screen_view.py --texts scan/texts --pool scan/pool.json \
        --skip 0 --n 5
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

COMPARISON = [
    r"\bone[- ]hot\b", r"\bk-?mer\b", r"\bBLOSUM\b", r"\bAAindex\b",
    r"\bphysicochemical\b", r"\bablat\w+\b",
    r"\bbaseline\s+(?:representation|encoding|features?|embedding)s?\b",
    r"\brandom(?:ly)?\s+initiali[sz]ed\s+(?:embedding|weights)\b",
    r"\bwithout\s+(?:the\s+)?(?:PLM|pretrain\w+|ESM\w*|language\s+model)\b",
    r"\bfrom\s+scratch\b",
    r"\breplac\w+\s+(?:the\s+)?(?:ESM\w*|PLM|embeddings?)\b",
]
SEEDS = [
    r"\b\d{1,3}\s+(?:different\s+|independent\s+|random\s+)*(?:seeds?|runs?|trials?|replicates?)\b",
    r"\b(?:three|five|ten|two|four|twenty)\s+(?:different\s+|independent\s+|random\s+)*(?:seeds?|runs?|trials?)\b",
    r"\b(?:random\s+)?seeds?\s*(?:=|:)\s*[\d\{\[]",
    r"\baverag\w+\s+(?:over|across)\s+\w+\s+(?:seeds?|runs?|trials?|folds?)\b",
    r"\bseed[- ]to[- ]seed\b",
    r"\bmean\s*±", r"±\s*\d", r"\bstandard\s+deviation\b", r"\berror\s+bars?\b",
    r"\bmanual_seed\b", r"\bfixed\s+(?:random\s+)?seed\b",
]
SIG = [r"\bp\s*[<=]\s*0?\.\d+", r"\bp-?values?\b", r"\bt-?test\b", r"\bWilcoxon\b",
       r"\bbootstrap\w*\b", r"\bconfidence\s+intervals?\b", r"\bsignifican\w+\b"]


def grab(text: str, pats: list[str], width: int, cap: int) -> list[str]:
    out, seen = [], set()
    for pat in pats:
        for m in re.finditer(pat, text, flags=re.I):
            s = max(0, m.start() - width // 3)
            frag = " ".join(text[s : s + width].split())
            key = re.sub(r"\W+", "", frag[:60]).lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(f"[{m.group(0)[:34]}] …{frag}…")
            if len(out) >= cap:
                return out
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--texts", type=Path, required=True)
    p.add_argument("--pool", type=Path, required=True)
    p.add_argument("--skip", type=int, default=0)
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--width", type=int, default=300)
    p.add_argument("--cap", type=int, default=4)
    a = p.parse_args()

    pool = json.loads(a.pool.read_text())["candidates"]
    shown = 0
    for rec in pool[a.skip :]:
        if shown >= a.n:
            break
        txt = a.texts / f"{rec['base_id']}.txt"
        idx = pool.index(rec)
        if not txt.exists():
            continue
        text = txt.read_text()
        shown += 1
        print("=" * 104)
        print(f"#{idx}  {rec['base_id']}  {rec['published'][:10]}  {rec['primary_category']}")
        print(f"TITLE  {rec['title'][:150]}")
        print(f"ABS    {' '.join(rec['abstract'].split())[:430]}")
        comp = grab(text, COMPARISON, a.width, a.cap)
        seeds = grab(text, SEEDS, a.width, a.cap)
        sig = grab(text, SIG, 170, 2)
        print(f"\n-- comparison evidence ({len(comp)}) --")
        for c in comp:
            print("  ", c[:330])
        print(f"-- seed / variance evidence ({len(seeds)}) --")
        for c in seeds:
            print("  ", c[:330])
        if sig:
            print("-- significance --")
            for c in sig:
                print("  ", c[:220])
        print()


if __name__ == "__main__":
    main()
