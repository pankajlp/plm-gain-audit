"""Pull targeted context out of one stored full text, for screening decisions.

    python src/look.py --texts scan/texts --id 2611.16881 --pat 'logistic|probe|train' --width 300 --cap 6
"""
from __future__ import annotations
import argparse, re
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--texts", type=Path, required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--pat", required=True)
    p.add_argument("--width", type=int, default=300)
    p.add_argument("--cap", type=int, default=6)
    a = p.parse_args()

    text = (a.texts / f"{a.id}.txt").read_text()
    seen, n = set(), 0
    for m in re.finditer(a.pat, text, flags=re.I):
        s = max(0, m.start() - a.width // 3)
        frag = " ".join(text[s : s + a.width].split())
        key = re.sub(r"\W+", "", frag[:50]).lower()
        if key in seen:
            continue
        seen.add(key)
        n += 1
        print(f"[{m.group(0)[:30]}] …{frag}…\n")
        if n >= a.cap:
            break
    if not n:
        print("(no match)")


if __name__ == "__main__":
    main()
