"""Fetch full text for pooled arXiv papers and extract seed/variance passages.

The regex pass NEVER sets a value on its own — it collects the surrounding
sentences so each included paper's seed count can be confirmed by reading
(FRAME.md, "Procedure for seeds_per_arm", step 2).

    python src/fetch_texts.py --pool scan/pool.json --out scan/texts --limit 120
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

DELAY = 2.5
UA = "lit-scan/1.0"

SEED_PATTERNS = [
    r"\b(?:random\s+)?seeds?\b",
    r"±",
    r"\+/-",
    r"\bs\.?d\.?\s*=",
    r"\bstd(?:ev)?\b",
    r"\b(\d+|one|two|three|four|five|ten)\s+(?:independent\s+|different\s+|separate\s+)?(?:runs?|trials?|replicates?|repetitions?)\b",
    r"\baverag(?:e|ed|ing)\s+over\b",
    r"\bmean\s*(?:±|\+/-|\+-)\b",
    r"\bstandard\s+(?:deviation|error)\b",
    r"\brepeated\s+(?:\d+|three|five|ten)\s+times\b",
    r"\b\d+-fold\s+cross[- ]validation\b",
    r"\berror\s+bars?\b",
]
BASELINE_PATTERNS = [
    r"\bone[- ]hot\b", r"\bk-?mer\b", r"\bBLOSUM\b", r"\bAAindex\b",
    r"\bablation\b", r"\bbaseline\s+(?:representation|encoding|features?|embedding)\b",
    r"\bphysicochemical\b", r"\brandom(?:ly)?\s+initiali[sz]ed\s+embedding\b",
]


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.parts))


def fetch_html(arxiv_id: str) -> tuple[str, str] | None:
    """arXiv HTML first (only exists for ~2024 onward), else the PDF."""
    try:
        req = urllib.request.Request(
            f"https://arxiv.org/html/{arxiv_id}", headers={"User-Agent": UA}
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read().decode("utf-8", errors="replace")
        p = Text()
        p.feed(raw)
        t = p.text()
        if len(t) > 4000:
            return t, f"https://arxiv.org/html/{arxiv_id}"
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        pass
    finally:
        time.sleep(DELAY)

    return fetch_pdf(arxiv_id)


def fetch_pdf(arxiv_id: str) -> tuple[str, str] | None:
    """Download the PDF to a temp file and extract text with pdftotext."""
    url = f"https://arxiv.org/pdf/{arxiv_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=90) as r:
            blob = r.read()
        if not blob.startswith(b"%PDF"):
            return None
        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "p.pdf"
            pdf.write_bytes(blob)
            res = subprocess.run(
                ["pdftotext", "-q", "-enc", "UTF-8", str(pdf), "-"],
                capture_output=True, timeout=120,
            )
        t = re.sub(r"\s+", " ", res.stdout.decode("utf-8", errors="replace"))
        return (t, url) if len(t) > 4000 else None
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            subprocess.TimeoutExpired, OSError):
        return None
    finally:
        time.sleep(DELAY)


def contexts(text: str, patterns: list[str], width: int = 260, cap: int = 14) -> list[str]:
    out, seen = [], set()
    for pat in patterns:
        for m in re.finditer(pat, text, flags=re.I):
            s = max(0, m.start() - width // 2)
            frag = text[s : s + width].strip()
            key = frag[:80]
            if key not in seen:
                seen.add(key)
                out.append(frag)
            if len(out) >= cap:
                return out
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pool", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--limit", type=int, default=120)
    p.add_argument("--start", type=int, default=0)
    a = p.parse_args()

    pool = json.loads(a.pool.read_text())["candidates"]
    a.out.mkdir(parents=True, exist_ok=True)

    done = fail = 0
    for i, rec in enumerate(pool[a.start : a.start + a.limit], start=a.start):
        dest = a.out / f"{rec['base_id']}.json"
        body = a.out / f"{rec['base_id']}.txt"
        if dest.exists() and (body.exists() or "no_fulltext" in dest.read_text()):
            done += 1
            continue
        got = fetch_html(rec["arxiv_id"])
        if got is None:
            dest.write_text(json.dumps({**rec, "status": "E4_no_fulltext"}, indent=2))
            fail += 1
            print(f"  [{i}] {rec['base_id']}  NO FULLTEXT")
            continue
        text, url = got
        payload = {
            **rec,
            "status": "ok",
            "source_url": url,
            "n_chars": len(text),
            "seed_contexts": contexts(text, SEED_PATTERNS),
            "baseline_contexts": contexts(text, BASELINE_PATTERNS),
        }
        dest.write_text(json.dumps(payload, indent=2))
        # keep the full text so extraction can be revised without re-fetching
        (a.out / f"{rec['base_id']}.txt").write_text(text)
        done += 1
        if i % 10 == 0:
            print(f"  [{i}] {rec['base_id']}  {len(text)} chars", flush=True)

    print(f"\nfetched/cached {done}, no full text {fail}, out {a.out}")


if __name__ == "__main__":
    main()
