"""Fetch authoritative metadata for cited arXiv ids via the official API.

Authors are not stored in scan/pool.json, so citations must come from the API
rather than from the stored full texts.

    python src/fetch_refs.py --ids 2606.04021,1906.08230 --out scan/refs.json
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
NS = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
CHUNK = 25


def fetch(ids: list[str]) -> list[dict]:
    q = urllib.parse.urlencode({"id_list": ",".join(ids), "max_results": len(ids)})
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": "lit-scan/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        root = ET.fromstring(r.read())
    out = []
    for e in root.findall("a:entry", NS):
        raw = e.findtext("a:id", default="", namespaces=NS).rsplit("/", 1)[-1]
        out.append({
            "arxiv_id": raw,
            "base_id": raw.split("v")[0],
            "title": " ".join(e.findtext("a:title", default="", namespaces=NS).split()),
            "authors": [
                " ".join(a.findtext("a:name", default="", namespaces=NS).split())
                for a in e.findall("a:author", NS)
            ],
            "published": e.findtext("a:published", default="", namespaces=NS),
            "primary_category": next(
                (c.attrib.get("term") for c in e.findall("x:primary_category", NS)), ""
            ),
            "journal_ref": e.findtext("x:journal_ref", default="", namespaces=NS) or "",
            "doi": e.findtext("x:doi", default="", namespaces=NS) or "",
        })
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ids", required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()

    ids = [i.strip() for i in a.ids.split(",") if i.strip()]
    rows: list[dict] = []
    for i in range(0, len(ids), CHUNK):
        rows.extend(fetch(ids[i : i + CHUNK]))
        time.sleep(3.0)

    got = {r["base_id"] for r in rows}
    missing = [i for i in ids if i not in got]
    a.out.write_text(json.dumps(rows, indent=2))
    for r in sorted(rows, key=lambda r: r["base_id"]):
        n = len(r["authors"])
        first = r["authors"][0] if r["authors"] else "?"
        extra = f"  [{r['journal_ref']}]" if r["journal_ref"] else ""
        print(f"{r['base_id']:<12} {r['published'][:10]}  {n:>2}a  {first:<24}"
              f" {r['title'][:58]}{extra}")
    if missing:
        print("\nMISSING:", ", ".join(missing))
    print(f"\n{len(rows)}/{len(ids)} -> {a.out}")


if __name__ == "__main__":
    main()
