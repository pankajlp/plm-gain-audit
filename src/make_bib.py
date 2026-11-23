"""Generate paper/references.bib from scan/refs.json plus hand-verified entries.

arXiv entries are built from API metadata so author lists are not guessed.
The four non-arXiv entries were verified by hand against publisher records and
are kept in MANUAL with a source note.

    python src/make_bib.py --refs scan/refs.json --out paper/references.bib
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# base_id -> citation key
KEYS = {
    "2606.04021": "cheng2026degradomap",
    "2606.08100": "shivram2026constraint",
    "2607.25518": "zhou2026ampbench",
    "2608.10595": "xu2026degradequery",
    "2608.12090": "joeres2026task",
    "2608.30175": "tian2026peptide",
    "2609.01673": "li2026cliffrank",
    "2609.22184": "kong2026dptmdt",
    "2609.37675": "banerjee2026lemonzest",
    "2610.00672": "rahimimovassagh2026orbit",
    "2610.00988": "yu2026auditable",
    "2610.01891": "lv2026ripple",
    "2610.04850": "choi2026pitgcl",
    "2610.18481": "hardy2026protok",
    "2610.26651": "maiwald2026filtering",
    "2611.09046": "rahimimovassagh2026critics",
    "2611.09377": "kang2026kinecouple",
    "2611.12000": "lin2026hyplm",
    "2611.16881": "batra2026relabeling",
    "1906.08230": "rao2019tape",
    "2007.06225": "elnaggar2020prottrans",
    "2103.03098": "bouthillier2021variance",
    "1707.09861": "reimers2017distributions",
    "2002.06305": "dodge2020finetuning",
    "1709.06560": "henderson2018matters",
    "1707.05589": "melis2018state",
    "2109.08203": "picard2021seed",
}

# where the venue year differs from the arXiv posting year, the venue wins
YEAR_OVERRIDE = {
    "1709.06560": "2018",  # posted 2017, AAAI 2018
    "1707.05589": "2018",  # posted 2017, ICLR 2018
}

# venues the arXiv API does not carry; checked against publisher records
VENUE = {
    # named in the paper's own ACM template metadata, not in the arXiv record
    "2606.04021": "ACM-BCB '26: 17th ACM Conference on Bioinformatics, Computational Biology, and Health Informatics, Calabria, Italy",
    "1906.08230": "Advances in Neural Information Processing Systems 32 (NeurIPS 2019)",
    "2103.03098": "Proceedings of Machine Learning and Systems 3 (MLSys 2021)",
    "1707.09861": "Proceedings of EMNLP 2017",
    "1709.06560": "Proceedings of AAAI 2018",
    "1707.05589": "International Conference on Learning Representations (ICLR 2018)",
}

MANUAL = r"""
% --- Non-arXiv entries, verified against publisher records 2026-11-23 --------

@article{lin2023esm2,
  author  = {Lin, Zeming and Akin, Halil and Rao, Roshan and Hie, Brian and
             Zhu, Zhongkai and Lu, Wenting and Smetanin, Nikita and
             Verkuil, Robert and Kabeli, Ori and Shmueli, Yaniv and
             dos Santos Costa, Allan and Fazel-Zarandi, Maryam and
             Sercu, Tom and Candido, Salvatore and Rives, Alexander},
  title   = {Evolutionary-scale prediction of atomic-level protein structure
             with a language model},
  journal = {Science},
  volume  = {379},
  number  = {6637},
  pages   = {1123--1130},
  year    = {2023},
  doi     = {10.1126/science.ade2574},
  note    = {ESM-2. Preprint: bioRxiv 10.1101/2022.07.20.500902}
}

@inproceedings{dallago2021flip,
  author  = {Dallago, Christian and Mou, Jody and Johnston, Kadina E. and
             Wittmann, Bruce J. and Bhattacharya, Nicholas and
             Goldman, Samuel and Madani, Ali and Yang, Kevin K.},
  title     = {{FLIP}: Benchmark tasks in fitness landscape inference for
               proteins},
  booktitle = {Proceedings of the Neural Information Processing Systems Track on
               Datasets and Benchmarks 1 (NeurIPS Datasets and Benchmarks 2021)},
  editor    = {Vanschoren, Joaquin and Yeung, Sai Kit},
  year      = {2021},
  note      = {Preprint: bioRxiv 10.1101/2021.11.09.467890}
}

@inproceedings{notin2023proteingym,
  author    = {Notin, Pascal and Kollasch, Aaron W. and Ritter, Daniel and
               van Niekerk, Lood and Paul, Steffanie and Spinner, Han and
               Rollins, Nathan J. and Shaw, Ada and Orenbuch, Rose and
               Weitzman, Ruben and Frazer, Jonathan and Dias, Mafalda and
               Franceschi, Dinko and Gal, Yarin and Marks, Debora S.},
  title     = {{ProteinGym}: Large-Scale Benchmarks for Protein Fitness
               Prediction and Design},
  booktitle = {Advances in Neural Information Processing Systems 36
               (NeurIPS 2023), Datasets and Benchmarks Track},
  year      = {2023},
  note      = {Preprint: bioRxiv 10.1101/2023.12.07.570727, which carries a
               slightly different title}
}

@unpublished{bindformer,
  author = {Kumar, Pankaj},
  title  = {{BindFormer}: a transformer model for protein-binding affinity},
  year   = {2026},
  note   = {Manuscript in preparation. The ablation described in Section 1.1 is
            from this work; it is cited here only as the origin of the question,
            and no result of this paper depends on it}
}
"""

HEADER = """% references.bib for paper/paper.md
%
% arXiv entries are generated by src/make_bib.py from arXiv API metadata
% (scan/refs.json), so author lists are taken from the record rather than
% recalled. Regenerate with:
%
%     python src/fetch_refs.py --out scan/refs.json --ids <comma-separated>
%     python src/make_bib.py --refs scan/refs.json --out paper/references.bib
%
% Hand-written entries are confined to the MANUAL block at the end.
"""


def fmt_authors(names: list[str], cap: int = 8) -> str:
    def one(n: str) -> str:
        parts = n.split()
        if len(parts) < 2:
            return f"{{{n}}}"
        return f"{parts[-1]}, {' '.join(parts[:-1])}"

    if len(names) > cap:
        return " and ".join(one(n) for n in names[:cap]) + " and others"
    return " and ".join(one(n) for n in names)


def brace_acronyms(title: str) -> str:
    """Protect capitalisation of acronyms and model names in BibTeX."""
    return re.sub(r"(?<![{\w])([A-Z][A-Za-z0-9]*[A-Z0-9][A-Za-z0-9-]*)", r"{\1}", title)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--refs", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()

    rows = {r["base_id"]: r for r in json.loads(a.refs.read_text())}
    missing = [k for k in KEYS if k not in rows]
    if missing:
        raise SystemExit(f"no metadata for {missing}; rerun src/fetch_refs.py")

    chunks = [HEADER]
    for bid, key in sorted(KEYS.items(), key=lambda kv: kv[1]):
        r = rows[bid]
        year = YEAR_OVERRIDE.get(bid, r["published"][:4])
        fields = [
            f"  author       = {{{fmt_authors(r['authors'])}}}",
            f"  title        = {{{brace_acronyms(r['title'])}}}",
            f"  year         = {{{year}}}",
            f"  eprint       = {{{bid}}}",
            "  archivePrefix = {arXiv}",
            f"  primaryClass = {{{r['primary_category']}}}",
        ]
        if r["doi"]:
            fields.append(f"  doi          = {{{r['doi']}}}")
        # A paper with a known venue is a published proceedings paper, not a
        # preprint: emit @inproceedings so the venue actually renders. csl
        # styles drop `note` on @misc, which silently hid these.
        venue = r["journal_ref"] or VENUE.get(bid)
        if venue:
            fields.insert(3, f"  booktitle    = {{{venue}}}")
            chunks.append("@inproceedings{" + key + ",\n" + ",\n".join(fields) + "\n}\n")
        else:
            chunks.append("@misc{" + key + ",\n" + ",\n".join(fields) + "\n}\n")

    chunks.append(MANUAL)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text("\n".join(chunks))
    print(f"{len(KEYS)} arXiv entries + 4 manual -> {a.out}")


if __name__ == "__main__":
    main()
