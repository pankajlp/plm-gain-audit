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

### Amendment 1 — 2026-11-22 — raised, then withdrawn as to its reason

**Raised:** the arXiv API appeared to truncate the frame's query when the date
range spanned multiple years — the full window reported 373 results while a
2023-only sub-query returned 34 that seemed absent from it. The window was
therefore queried in yearly slices and unioned.

**Withdrawn:** the premise was false. It came from misreading the paging log:
the first entry of the last descending page (2024-06-28) was taken for the
oldest paper in the pool. The single-window query does cover the whole frame —
the pool spans **2023-01-06 to 2026-11-19** and the yearly slices return the
**identical 373 papers** (2023: 34, 2024: 86, 2025: 105, 2026: 148).

**Effect on the scan:** none. The pool is what the frozen frame specifies.
The slicing code is kept purely as a redundancy check, and this entry stays so
the record shows the mistake rather than hiding it.

**Pool as built:** 373 unique papers, primary categories cs.LG 178,
q-bio.BM 93, q-bio.QM 68, cs.AI 10, cs.CL 8, q-bio.GN 6, cs.CE 4, cs.IR 1.

### Amendment 2 — 2026-11-23 — two additive extraction fields

Screening the first papers surfaced a case the frozen table cannot express.
**HyPLM** (2611.12000) fits its probes as closed-form ridge and L-BFGS logistic
regressions. Those arms are **deterministic**: there is no training seed to
vary, so `seeds_per_arm = not_stated` would be scored against a design that
has no seed-variance problem at all. Recording it as a flaw would be wrong.

Two fields are therefore added to the extraction table:

- **`deterministic_probe`** — `yes` / `no`. `yes` means the paper's head is
  fitted deterministically (closed-form or convex with a fixed solver), so a
  single run *is* the whole distribution for that arm.
- **`note`** — free text, for what the decision turned on.

**Effect on the rules:** none. No inclusion or exclusion criterion changes, and
no pre-committed threshold changes. `deterministic_probe = yes` papers are
still counted in the `seeds_per_arm` denominator exactly as the frame specifies
— the primary outcome is untouched. The field exists so the write-up can report
the deterministic subset **separately alongside** the headline figure instead of
quietly folding it in. That separate figure is secondary and is labelled as a
post-hoc split, because this distinction was not anticipated when the frame was
frozen.

### Amendment 3 — 2026-11-23 — I1 covers trained comparisons scored by structural or generative accuracy

**The gap.** I1 says "supervised protein downstream task", written with property
prediction in mind. Two early papers do not fit that wording but do fit its
purpose:

- **Calpha** (2611.20986) swaps one-hot, untrained-LLM states, protein-trained
  LLM states and ESM2-3B features into a trained structure head and reports mean
  TM per configuration.
- **Ablating Design Choices for Protein Ensemble Generators** (2611.05055)
  replaces ESM2-650M with ESM2-8M in a trained flow-matching model and reports
  seed-averaged log RMSE differences.

In both, a model is **trained**, a **representation is swapped**, and a
**numeric metric** is reported — so a training seed exists and could have been
varied. That is exactly the situation the primary outcome is about. The metric
being TM or RMSE rather than Spearman or F1 does not change whether a seed
exists.

**Decision.** I1 is read to cover any comparison where a model is trained from
the representation and scored numerically, including structural and conditional-
generative metrics. Zero-shot and likelihood-only comparisons remain **E3**,
unchanged — the test is whether a training seed exists, not what the metric is.

**Direction check** (the reason this is safe to decide mid-scan): the two papers
cut **opposite ways**. Calpha reports **one** trained model per configuration;
the ensemble-generator paper reports **five** seeds for the base and **three**
per variant and is among the most careful multi-seed ablations in the pool.
Reading I1 narrowly would have dropped both — removing one single-seed paper and
one exemplary multi-seed paper. So this choice is not a thumb on the scale in
either direction, and the alternative (keeping Calpha while excluding the
ensemble paper, or vice versa) would have been plainly inconsistent.

**Effect on the rules:** I1's scope is clarified; no exclusion code changes and
no pre-committed threshold changes. The write-up reports how many included
papers entered under this reading, so the headline figure can be recomputed
without them.
