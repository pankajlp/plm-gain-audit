# Part A sampling frame — frozen 2026-11-22, before any screening

This file is written **before** the candidate pool is built, so the scan cannot
be steered by what turns up. Any later change is recorded as a dated amendment
at the bottom, never by editing the rules above it.

## Source

arXiv, via the official API (`export.arxiv.org/api/query`). Chosen because the
full text of recent submissions is machine-readable at `arxiv.org/html/<id>`,
which makes the seed-count extraction auditable rather than impressionistic.

**Known limitation, stated up front:** much protein-ML work appears on bioRxiv
or in journals only. This frame therefore measures reporting practice *on
arXiv*, not across the whole field, and the write-up must say so. A bioRxiv
extension is a separate pass.

## Query

Submitted **2023-01-01 to 2026-11-22**, in categories **q-bio.BM, q-bio.QM, or
cs.LG**, with title or abstract matching at least one of:

`ESM-2`, `ESM2`, `ESM-1b`, `ProtT5`, `ProtBERT`, `protein language model`,
`protein language models`

## Screening

Candidates are sorted **most recent first** and screened in that order until
**40 papers are included**. No skipping, no reordering, no substitution. Every
excluded paper is logged with its exclusion code, so the included set can be
reconstructed from the log.

### Include if all of:

- **I1** — reports at least one *numeric* comparison, on a supervised protein
  downstream task, between a pretrained PLM representation and either
  (a) a non-PLM representation (one-hot, k-mer, BLOSUM, AAindex,
  physicochemical descriptors, other handcrafted features), or
  (b) a different PLM / PLM scale.
- **I2** — that comparison is the paper's own result, presented as evidence
  about the representation (an ablation table, a benchmark table), not a
  number quoted from another paper.
- **I3** — full text retrievable (arXiv HTML, else PDF).

### Exclude with code:

- **E1** — review, survey, position paper, or dataset/tooling paper with no
  supervised evaluation.
- **E2** — no representation comparison at all (single representation
  throughout).
- **E3** — comparison exists but is unsupervised / zero-shot only (no trained
  head), so there is no training seed to vary.
- **E4** — full text not retrievable.
- **E5** — not actually about proteins (the query catches some RNA/DNA and
  general-ML papers).

## Extracted per included paper

| field | values |
|---|---|
| arxiv_id, date, title | — |
| benchmark(s) | free text, e.g. "FLIP GB1", "custom DTI set" |
| seeds_per_arm | integer, or `not_stated` |
| variance_reported | `yes` / `no` |
| significance_test | `none` / `unpaired` / `paired` |
| claimed_delta | the headline representation effect, in the paper's metric |
| basis | `regex` / `manual` — how seeds_per_arm was determined |

## Procedure for `seeds_per_arm`

1. Automated pass greps the full text for seed and repetition language
   (`seed`, `random seed`, `N runs`, `N independent`, `averaged over`,
   `mean ± `, `standard deviation`, `std`, `cross-validation`, `repeated`).
2. **Every included paper's value is then confirmed by reading the matched
   passage.** A regex hit alone never sets the value; `basis` records this.
3. If the text states repetitions without a number ("multiple runs"), the value
   is `not_stated`, not a guess.
4. k-fold cross-validation is **not** counted as seed repetition unless the
   paper also varies the training seed — CV varies the data split, which is a
   different variance source and usually reported as one number anyway. This is
   recorded in a separate `cross_validation` note.

## Primary outcome

The distribution of `seeds_per_arm` across the 40 included papers.

## Secondary outcome

For papers whose benchmark overlaps Part B (FLIP GB1/AAV, TAPE fluorescence/
stability), whether the claimed Δ clears **2× the wider arm's per-seed sd** as
measured in Part B. This is the only place Part A and Part B numbers meet, and
it applies the threshold from `evidence/crosstab.txt`.

## Pre-committed interpretation

- If **≥ 50%** of included papers report `seeds_per_arm = 1` or `not_stated`,
  the practice is widespread and the paper leads with the prevalence figure.
- If **< 20%** do, the field is in better shape than BindFormer's case
  suggested, and the write-up becomes a short note reporting that, with the
  Part B measurements as the contribution.
- Between 20% and 50%, report the figure plainly with no framing either way.

Writing these thresholds down now removes the freedom to decide afterwards
which number sounded like a finding.

---

## Amendments

*(none yet)*
