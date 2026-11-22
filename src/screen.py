"""Pre-screen fetched texts into a compact digest for manual confirmation.

This assigns a *provisional* class only. FRAME.md requires that every included
paper's seed count be set by reading the matched passage, so the digest exists
to make that reading fast, not to replace it.

    python src/screen.py --texts scan/texts --pool scan/pool.json --out scan/digest.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

WORD_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "twenty": 20, "thirty": 30, "fifty": 50, "hundred": 100,
}

# a count attached to repetition language
MULTI = [
    r"\b(\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|twenty|thirty|fifty)\s+"
    r"(?:different\s+|independent\s+|distinct\s+|separate\s+|random\s+)*"
    r"(?:random\s+)?(?:seeds?|runs?|trials?|replicates?|repetitions?)\b",
    r"\b(?:seeds?|runs?|trials?)\s*(?:=|:)?\s*\{?\s*(?:\d+\s*[,–-]\s*){1,}\d+",
    r"\bover\s+(\d{1,3}|three|five|ten|twenty)\s+(?:random\s+)?(?:seeds?|runs?)\b",
    r"\b(?:averaged|repeated|replicated)\s+(?:over|across)?\s*"
    r"(\d{1,3}|three|five|ten|twenty)\s*(?:times|seeds?|runs?)\b",
]
SINGLE = [
    r"\ba\s+single\s+(?:run|seed|training\s+run)\b",
    r"\bone\s+(?:run|seed)\b",
    r"\b(?:fixed|fix(?:ed)?\s+the|set\s+the)\s+(?:random\s+)?seed\b",
    r"\bseed\s*(?:=|:)\s*\d+\b",
    r"\brandom[_\s]?seed\s*(?:=|:)\s*\d+\b",
    r"\btorch\.manual_seed\b",
]
VARIANCE = [r"±", r"\+/-", r"standard\s+deviation", r"standard\s+error",
            r"error\s+bars?", r"\bstd\b", r"\bs\.?d\.?\b", r"confidence\s+interval"]
CV = [r"\b(\d{1,2})-fold\s+cross[- ]validation\b", r"\bcross[- ]validation\b"]
SIGTEST = [r"\bp\s*[<=>]\s*0?\.\d+", r"\bp-?value", r"\bt-?test\b", r"\bWilcoxon\b",
           r"\bbootstrap\b", r"\bMann[-\s]Whitney\b", r"\bstatistically\s+significant\b"]
BASELINE = [r"\bone[- ]hot\b", r"\bk-?mer\b", r"\bBLOSUM\b", r"\bAAindex\b",
            r"\bphysicochemical\b", r"\bablation\b",
            r"\bbaseline\s+(?:representation|encoding|features?|embedding)\b",
            r"\brandom(?:ly)?\s+initiali[sz]ed\b"]
PROTEIN = [r"\bprotein\b", r"\bresidue\b", r"\bamino\s+acid\b", r"\bpeptide\b",
           r"\benzyme\b", r"\bantibody\b"]


def hits(text: str, pats: list[str]) -> list[str]:
    out = []
    for p in pats:
        m = re.search(p, text, flags=re.I)
        if m:
            out.append(m.group(0)[:60])
    return out


def max_count(text: str) -> int | None:
    best = None
    for p in MULTI:
        for m in re.finditer(p, text, flags=re.I):
            g = next((x for x in m.groups() if x), None)
            if g is None:
                continue
            n = WORD_NUM.get(g.lower()) if not g.isdigit() else int(g)
            if n and 1 < n <= 200 and (best is None or n > best):
                best = n
    return best


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--texts", type=Path, required=True)
    p.add_argument("--pool", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()

    order = [c["base_id"] for c in json.loads(a.pool.read_text())["candidates"]]
    rows = []
    for bid in order:
        f = a.texts / f"{bid}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        if d.get("status") != "ok":
            rows.append({"base_id": bid, "title": d.get("title", ""),
                         "provisional": "E4_no_fulltext"})
            continue
        blob = " ".join(d.get("seed_contexts", []) + d.get("baseline_contexts", []))
        abstract = d.get("abstract", "")
        joined = blob + " " + abstract
        k = max_count(blob)
        if k:
            prov = f"multi_k={k}"
        elif hits(blob, SINGLE):
            prov = "single_explicit"
        elif hits(blob, VARIANCE):
            prov = "variance_only"
        elif hits(blob, CV):
            prov = "cv_only"
        else:
            prov = "no_seed_evidence"
        rows.append({
            "base_id": bid,
            "date": d.get("published", "")[:10],
            "title": d.get("title", "")[:110],
            "primary_category": d.get("primary_category", ""),
            "provisional": prov,
            "baseline_terms": hits(joined, BASELINE),
            "sig_terms": hits(joined, SIGTEST),
            "protein_terms": bool(hits(joined, PROTEIN)),
            "n_chars": d.get("n_chars", 0),
            "seed_contexts": d.get("seed_contexts", [])[:6],
        })

    a.out.write_text(json.dumps(rows, indent=2))
    from collections import Counter
    print(f"{len(rows)} screened")
    for k, v in Counter(r["provisional"] for r in rows).most_common():
        print(f"  {k:<20} {v}")
    print(f"  with baseline terms: {sum(1 for r in rows if r.get('baseline_terms'))}")
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
