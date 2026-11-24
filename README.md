# How much of a published protein-language-model gain survives seed noise?

Code, data and manuscript for a two-part audit of how protein-machine-learning
ablations are evaluated.

**Part A** — a pre-registered scan of 40 arXiv papers that report their own
numeric comparison between a protein-language-model (PLM) representation and a
baseline representation on a supervised protein task. **25 of 40 (62.5%)
report one training run per arm, or do not say how many they ran.** The sharper
figure is the cross-tab: 32 of 40 report some variance, but only 15 repeat a
training seed. Error bars are near-universal; re-running the model is not.

**Part B** — a direct measurement of the seed band: 10 seeds per arm, frozen
features and a light head, on FLIP GB1, FLIP AAV, TAPE fluorescence and TAPE
stability. Across the 100 single-run pairings available from each 10x10 seed
grid, the sign-flip rate is governed not by how hard the split is but by the
**true effect divided by the wider arm's per-seed standard deviation**. Below a
ratio of about 2, 6-45% of single-run pairings report the wrong sign; at or
above it, 0-2%.

The prescription is one line: *report your per-seed spread, and if the claimed
delta is not at least twice the wider arm's per-seed standard deviation, one
run per arm does not establish its sign.*

## The paper

`paper/paper.md`, with `paper/references.bib`. Build the PDF with:

```sh
./paper/build.sh
```

Needs `pandoc` and a LaTeX engine (`tectonic` by default). `paper/arxiv-submission.md`
holds the submission metadata.

## Layout

| what | where |
|---|---|
| Part A sampling frame, frozen before the pool was built | `FRAME.md` |
| Part A per-paper decisions, with the passage each turned on | `scan/decisions.jsonl` |
| Part A tally and sensitivity to the judgment calls | `src/scan_tally.py`, `evidence/scan_tally.txt` |
| Part A write-up | `SCAN.md` |
| Part B per-seed runs | `evidence/runs/`, `evidence/runs_aav/`, `evidence/runs_tape/` |
| Part B seed bands | `evidence/seed_bands_*.txt` |
| Part B paired comparisons, with per-seed predictions | `evidence/comparisons*/` |
| Part B synthesis | `evidence/crosstab.txt`, `RESULTS.md` |
| original scoping note | `SCOPE.md` |

Reproduce the Part A numbers without rerunning anything:

```sh
python src/scan_tally.py --decisions scan/decisions.jsonl
```

## On the pre-registration

`FRAME.md` was written and committed **before** the candidate pool was built,
so the scan could not be steered by what turned up. Every later change is a
dated amendment at the bottom of that file rather than an edit to the rules
above it, and each amendment states which way the judgment call pushes the
hypothesis — including Amendment 4, which removes a 10-seed paper and so pushes
the headline figure in the direction that *favours* the hypothesis. The git
history is part of the record: the commit that froze the frame precedes the
commit that built the pool.

Amendment 1 documents a mistake. It was raised on a false premise, found to be
false, and withdrawn, and the entry stays so the record shows the error instead
of hiding it.

## What is not in this repository

- **`scan/texts/`** — the full text of each screened paper, fetched from arXiv
  to confirm seed counts by reading rather than by regex. These are other
  authors' papers and are not ours to redistribute. Regenerate them with
  `python src/fetch_texts.py --pool scan/pool.json --out scan/texts`. The
  screening remains auditable without them: `scan/decisions.jsonl` records the
  passage each decision turned on, with the arXiv id.
- **`data/` and `features/`** — benchmark downloads and extracted embeddings,
  a few GB. Rebuild with `src/features.py`; the benchmarks themselves are
  public (FLIP, TAPE).

## Licence

Code in `src/` and `paper/build.sh`: MIT, see `LICENSE`.

Manuscript, write-ups and derived results (`paper/`, `*.md`, `evidence/`,
`scan/decisions.jsonl`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

arXiv metadata in `scan/pool.json` and `scan/refs.json` comes from the arXiv
API and is CC0, per arXiv's terms.

One author put a contact address in their abstract. It is redacted in
`scan/pool.json` rather than republished here, since a scraped copy in a second
repository only feeds address harvesters. Nothing in the screening used it, and
a refetch of the pool restores it.
