"""Build the Part A candidate pool from the arXiv API, exactly as FRAME.md fixes it.

Query, window and categories are not parameters — they are the frozen frame.
Changing them means amending FRAME.md.

    python src/arxiv_pool.py --out scan/pool.json
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

API = "http://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}

# --- the frozen frame ---------------------------------------------------------
CATEGORIES = ["q-bio.BM", "q-bio.QM", "cs.LG"]
TERMS = [
    "ESM-2", "ESM2", "ESM-1b", "ProtT5", "ProtBERT",
    "protein language model", "protein language models",
]
DATE_FROM = "202301010000"
DATE_TO = "202611222359"
# Amendment 1 (2026-11-22), WITHDRAWN as to its reason, kept as to its code:
# it was raised on the belief that the API truncated the multi-year query. That
# was a misreading of the paging log (the last descending page's first entry was
# taken for the pool's oldest paper). The single-window query does return the
# full 2023-01-06..2026-11-19 range. Yearly slicing is retained only because it
# is a cheap redundancy check: it yields the identical 373 papers.
YEAR_SLICES = [
    ("202301010000", "202312312359"),
    ("202401010000", "202412312359"),
    ("202501010000", "202512312359"),
    ("202601010000", "202611222359"),
]
# -----------------------------------------------------------------------------

PAGE = 100
POLITE_DELAY = 3.0  # arXiv asks for one request every 3 s


def build_query(date_from: str = DATE_FROM, date_to: str = DATE_TO) -> str:
    cats = " OR ".join(f"cat:{c}" for c in CATEGORIES)
    terms = " OR ".join(f'all:"{t}"' for t in TERMS)
    return f"({cats}) AND ({terms}) AND submittedDate:[{date_from} TO {date_to}]"


def fetch_page(query: str, start: int) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": start,
            "max_results": PAGE,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    req = urllib.request.Request(f"{API}?{params}", headers={"User-Agent": "lit-scan/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        root = ET.fromstring(r.read())

    out = []
    for e in root.findall("a:entry", NS):
        raw_id = e.findtext("a:id", default="", namespaces=NS)
        arxiv_id = raw_id.rsplit("/", 1)[-1]
        cats = [c.attrib.get("term", "") for c in e.findall("a:category", NS)]
        out.append(
            {
                "arxiv_id": arxiv_id,
                "version_id": arxiv_id,
                "base_id": arxiv_id.split("v")[0],
                "published": e.findtext("a:published", default="", namespaces=NS),
                "updated": e.findtext("a:updated", default="", namespaces=NS),
                "title": " ".join(
                    e.findtext("a:title", default="", namespaces=NS).split()
                ),
                "abstract": " ".join(
                    e.findtext("a:summary", default="", namespaces=NS).split()
                ),
                "primary_category": cats[0] if cats else "",
                "categories": cats,
            }
        )
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--max", type=int, default=2000)
    a = p.parse_args()

    pool = []
    for date_from, date_to in YEAR_SLICES:
        query = build_query(date_from, date_to)
        print(f"slice {date_from[:4]}:")
        start, got = 0, 0
        while start < a.max:
            page = fetch_page(query, start)
            if not page:
                break
            pool.extend(page)
            got += len(page)
            start += PAGE
            time.sleep(POLITE_DELAY)
        print(f"  {got} results")

    # de-duplicate by base id, keeping the most recent version seen
    seen: dict[str, dict] = {}
    for r in pool:
        seen.setdefault(r["base_id"], r)
    deduped = sorted(seen.values(), key=lambda r: r["published"], reverse=True)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(
        json.dumps(
            {
                "frame": {
                    "categories": CATEGORIES, "terms": TERMS,
                    "date_from": DATE_FROM, "date_to": DATE_TO,
                    "query_template": build_query("<from>", "<to>"),
                    "year_slices": YEAR_SLICES,
                    "amendment": "queried in yearly slices; see Amendment 1",
                },
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "n_raw": len(pool),
                "n_deduped": len(deduped),
                "candidates": deduped,
            },
            indent=2,
        )
    )
    print(f"\n{len(pool)} raw, {len(deduped)} unique papers")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
