---
title: "Report your seed spread: how much of a published protein-language-model gain is identifiable from one run per arm?"
author: "Pankaj Kumar^[Independent researcher]"
date: 2026-11-23
bibliography: references.bib
link-citations: true
keywords:
  - protein language models
  - reproducibility
  - seed variance
  - ablation studies
  - FLIP
  - TAPE
---

# Abstract

Ablation tables are how the protein-machine-learning literature argues that a
pretrained protein language model (PLM) representation helps. Such a table is
usually one training run per arm. We ask what that buys.

We do two things. First, a pre-registered scan of 40 arXiv papers that report
their own numeric comparison between a PLM representation and a baseline
representation on a supervised protein task: **25 of 40 (62.5%) report one run
per arm or do not say how many they ran**. The sharper figure is the cross-tab —
**32 of 40 report some variance, but only 15 repeat a training seed**. Of the 25
papers with one run or no stated count, 17 still print an error bar, drawn from
a bootstrap over test items or a spread across cross-validation folds, and 7 run
a significance test on it. The error bar is near-universal; re-running the model
is not, and a test-item bootstrap conditions on the single trained model it was
handed.

Second, we measure the seed band directly: 10 seeds per arm, frozen features and
a light head, on four public tasks (FLIP GB1, FLIP AAV, TAPE fluorescence, TAPE
stability), 10 representation comparisons in total, with paired bootstrap on
seed-mean predictions. The sign-flip rate across all 100 single-run pairings
available from each 10x10 seed grid is governed not by how hard the split is but
by the **true effect divided by the wider arm's per-seed standard deviation**.
Below a ratio of about 2, 6-45% of single-run pairings report the wrong sign;
at or above it, 0-2%. On TAPE stability — an ordinary split with 53,614 training
rows — the true effect is +0.027 Spearman while a single run per arm can report
up to **+0.241, an 8.8-fold inflation**, because the baseline arm has a long low
tail.

We propose one checkable line: *report your per-seed spread, and if the claimed
delta is not at least twice the wider arm's per-seed standard deviation, one run
per arm does not establish its sign.*

We did not discover this phenomenon. Five of the included papers measure it on
their own benchmarks, one of them finding that three extra seeds turned a
+0.039 AUROC win into a 0.004 loss. Our contribution is the prevalence figure,
the cross-benchmark regularity, and a threshold cheap enough to adopt.

---

# 1. Introduction

## 1.1 A concrete failure

This project began with a result that did not survive.

In earlier work on protein-binding affinity [@bindformer] we ran an ablation:
remove a
component, see what happens. One training run per arm gave a Spearman delta of
**-0.050 with p = 0.095** — the shape of a finding, a near-miss on conventional
significance, the kind of number that becomes a sentence in a paper. Re-running
the same ablation at three seeds gave **-0.021 with p = 0.356**. The effect was
not small; it was absent. What the first run had measured was the seed.

The one-hot arm's per-seed standard deviation in that experiment was about
0.025. The claimed delta was 0.050. The ratio is exactly 2.0 — right at the edge
of the threshold this paper ends up proposing, which is partly why the result
collapsed and partly why we went looking for the general case.

## 1.2 The question

A reader of an ablation table is being asked to believe a counterfactual: *had
the authors used the other representation, the number would have been worse by
this much.* With one run per arm, the observed difference contains the
representation effect and the difference between two draws from two seed
distributions, and nothing in the table separates them.

This is not a subtle point, and we do not claim it is new. What has not been
measured, as far as we can establish, is the pair of quantities that decides
whether it matters in practice:

1. **How often does the literature run one seed per arm?** If the answer is
   "rarely", the concern is academic.
2. **How wide is the seed band, relative to the effects papers claim?** If
   the band is narrow, one run is enough and the first question does not matter
   either.

Both questions have to be answered together, and neither had been. We answer the
first with a pre-registered literature scan (Part A, Section 3) and the second
by direct measurement on public benchmarks (Part B, Section 4).

## 1.3 What we are not claiming

Three disclaimers, stated here rather than buried in Section 7, because each one
limits the paper's reach:

- **We are not claiming PLM representations do not help.** Across our 10
  comparisons, frozen ESM-2 650M wins 4 and loses 6. There is no general verdict
  in our data and we do not offer one. An early draft of this work did claim
  "frozen ESM-2 is usually worse than one-hot" on the strength of GB1 alone;
  FLIP AAV contradicted it and the claim was withdrawn. Section 4.5 records that
  withdrawal rather than quietly deleting it.
- **We are not claiming the field is unaware.** A meaningful minority of the
  papers we screened names the problem precisely, in its own limitations
  section, and proceeds anyway for lack of compute. The gap we document is
  between knowing and measuring, not between knowing and not knowing.
- **We are not claiming our threshold is a constant.** It is a clean separation
  across 10 comparisons with one head architecture and frozen features. That is
  an observation with a mechanism behind it, not a law.

---

# 2. Related work

**Seed variance in machine learning generally.** That reported gains can be
swamped by initialisation and data-order noise is long established outside
biology [@reimers2017distributions; @henderson2018matters; @melis2018state;
@dodge2020finetuning; @bouthillier2021variance], and the standard remedies —
report distributions, use paired tests, state the number of runs — are well
known; @bouthillier2021variance in particular sets out how to budget
repetitions across variance sources, and @picard2021seed makes the point
uncomfortably concrete. We take that literature as given and do not restate
it. What is specific to our setting is that the protein-ML ablation table has
not inherited those remedies, and that the effects at stake are often smaller
than the band.

**Protein-ML benchmarking.** FLIP [@dallago2021flip] introduced designed splits
of increasing extrapolation difficulty for protein fitness prediction, and TAPE
[@rao2019tape] assembled standard supervised tasks with fixed splits.
ProteinGym [@notin2023proteingym] plays the same role for zero-shot
variant-effect prediction, and the representations under test are usually ESM-2
[@lin2023esm2] or the ProtTrans family [@elnaggar2020prottrans]. Both are widely used as the
substrate for exactly the ablation tables we study. Neither prescribes a number
of training repetitions, and in practice the published leaderboards are
single-number-per-cell.

**Work that already measures what we measure.** This is the honest heart of our
related work, and it is substantial. Five of the 40 papers in our own included
set measure run-to-run variance on their own benchmarks and reach our
conclusion:

- **DegradoMap** [@cheng2026degradomap] ran three seeds and obtained AUROC
  0.646 +/- 0.124 against a gradient-boosting baseline of 0.607. They then ran
  three more — 0.657, 0.520 and 0.502. The six-seed mean fell to
  **0.603 +/- 0.097 — below the baseline** (p = 0.556; the arXiv version
  reports this p-value without naming the test, while the ACM camera-ready
  source in the authors' own repository calls it a bootstrap p-value). Individual seeds span **0.502 to 0.745**.
  The authors write that
  "individual seeds span 0.25 AUROC and may underperform simple baselines",
  that "ensembling across >= 6 seeds is required for reliable deployment", and
  that "the best seed (0.7449, +23% over GB) reflects favorable initialization".
  A one-seed-per-arm paper on that setup could have reported anything from
  -0.11 to +0.14 against the same baseline. The same paper also reports three
  evaluation protocols side by side, including a 5-fold cross-validation spread
  of +/- 0.052 against its seed spread of +/- 0.097 — the conflation of
  Section 3.5 made visible inside one paper, although the two protocols use
  different splits, so the ratio is indicative rather than matched.
- **PIT-GCL** [@choi2026pitgcl] computes our ratio independently: its margins
  are "between 6.4 and 9.6 times the combined standard deviation of the two
  methods". It also states, per benchmark, what a seed varies — on one of them
  the seed redraws the whole data partition, so the spread covers split,
  initialisation and negative sampling together.
- **ProTok** [@hardy2026protok] reruns its validation-selected configuration at
  five named seeds and prints the five-seed mean beside the single-run headline
  from its main table. On one task the headline reads 85.79 against a five-seed
  mean of 86.8 +/- 0.2 — the published number sits roughly five seed-standard-
  deviations below its own mean, while the gap to the best baseline is 2.6.
- **HyPLM** [@lin2026hyplm] excludes FLIP GB1 two-vs-rest, three-vs-rest and
  a FLIP2 split from every summary statistic because "numerically equivalent
  runs of the same model differ by up to 0.2". This independently corroborates
  the GB1 instability we measure in Section 4.
- **Joeres et al.** [@joeres2026task] wire seed disagreement into its released tool: if the
  five seeds disagree strongly about which layer is best, the user is notified
  and more repetitions are requested. Seed variance as a signal rather than an
  error bar.

Two further papers, excluded from our set on scope grounds, belong here.
**ORBIT-FMIB** [@rahimimovassagh2026orbit] and its companion audit
[@rahimimovassagh2026critics] retrain a
31-layer x 15-subset x 3-seed grid (1,395 fits) from scratch and conclude the
two runs produced genuinely different trained models, not noisy re-evaluations
of one. They also report **a V100 and an H100 returning different scores for
identical inputs** — a nondeterminism source our own seed bands do not capture,
and one we concede in Section 7.

**What is left for us.** Given the above, our contribution is narrower than
"PLM ablations are noisy". It is: (i) a pre-registered measurement of how
common single-run arms are, which none of these papers provides; (ii) a
cross-benchmark relationship between the effect-to-noise ratio and the
probability a single run gets the sign wrong; and (iii) a threshold stated so it
can be checked from one extra printed line.

---

# 3. Part A — how reporting practice stands

## 3.1 Pre-registration

The sampling frame was written and committed **before the candidate pool was
built**, so the scan could not be steered by what turned up. It fixes the
source (the arXiv API), the query, the window, the screening order, the
inclusion and exclusion criteria, the fields to extract, and — critically — the
interpretation thresholds. It is reproduced in `FRAME.md` with four dated
amendments, each recorded before the decisions it governs.

**Query.** Submissions from 2023-01-01 to 2026-11-22 in q-bio.BM, q-bio.QM or
cs.LG, matching any of: `ESM-2`, `ESM2`, `ESM-1b`, `ProtT5`, `ProtBERT`,
`protein language model(s)` — the model families of @lin2023esm2 and
@elnaggar2020prottrans. This returned **373 unique papers**.

**Screening.** Candidates sorted most-recent-first and screened in that order
until **40 were included**. No skipping, no substitution; every exclusion
logged with its code.

**Inclusion** required all of: (I1) at least one numeric comparison, on a
supervised protein task, between a pretrained PLM representation and either a
non-PLM representation or a different PLM / PLM scale; (I2) the comparison is
the paper's own result, presented as evidence about the representation, not a
number quoted from elsewhere; (I3) full text retrievable.

**Exclusion codes:** E1 review or no supervised evaluation; E2 no
representation comparison; E3 comparison is zero-shot or has no trained head,
so there is no training seed to vary; E4 full text not retrievable; E5 not
proteins; E6 same-work duplicate (added by amendment, Section 3.2).

**Pre-committed interpretation**, fixed before any paper was seen: at **>= 50%**
single-run-or-not-stated, lead with the prevalence figure; at **< 20%**, write a
short note and let Part B carry the paper; **between 20% and 50%**, report the
figure flatly with no framing either way. Writing these down in advance removes
the freedom to decide afterwards which number sounded like a finding.

**Seed counts were set by reading.** The frame requires that every included
paper's seed count be confirmed against the matched passage; a regex hit never
sets the value. This was not a formality. Two examples from the screened set
show why: one paper's "three seeds" are **alphabet-relabeling seeds** in a
contact-prediction diagnostic [@batra2026relabeling], not training seeds;
another's [@kang2026kinecouple] "10 folds x 3
random seeds" belongs to an ablation over readout architecture, where the
representation is held fixed in every arm and the comparison our criteria ask
about does not exist. An automated pass would have credited both.

## 3.2 Amendments

Four, all dated, all recorded with a direction check — a statement of which way
the change pushes our own hypothesis:

1. **(withdrawn)** We initially believed the arXiv API truncated multi-year
   boolean queries and queried the window in yearly slices. The premise was
   false: it came from misreading a paging log, taking the last descending
   page's first entry for the pool's oldest paper. The single-window query
   covers the frame, and the yearly slices return the identical 373 papers. The
   amendment is kept in the record as **raised and withdrawn** rather than
   deleted.
2. **Two additive fields.** `deterministic_probe` and `note`. One included
   paper fits its probes as closed-form ridge and L-BFGS logistic regressions:
   those arms have no training seed at all, and scoring them as "not stated"
   would penalise a design with no seed-variance problem. No rule changed; such
   papers stay in the denominator exactly as the frame specifies, and the
   deterministic subset is reported separately.
3. **I1 covers structural and generative metrics.** Two papers train a model,
   swap a representation and report a numeric score, but the score is TM or
   RMSD rather than Spearman. A training seed exists in both, which is what the
   primary outcome is about. *Direction check:* the two cut opposite ways — one
   reports a single trained model per configuration, the other five base seeds
   and three per variant — so the reading is not a thumb on the scale.
4. **Same-work duplicates.** Two pool entries are the same module from the same
   lab, releasing the same code and the same experiments at 10 aligned seeds.
   The later-screened one is coded E6. *Direction check:* this drops a 10-seed
   paper, pushing our headline **up**, in the direction that favours us. We
   therefore report the figure both ways (Section 3.4).

We also adopted one tiebreak, recorded with the decisions: where an I2 call is
genuinely balanced, settle it in the direction that **disfavours** our
hypothesis. It was applied once, to include a paper with 10 seeds per arm — the
most-repeated design in the pool.

## 3.3 What was screened

Of 373 candidates, 160 were fetched most-recent-first; 157 yielded full text
and 3 were coded E4. **73 papers were screened in frozen order to reach 40
inclusions** — a 55% inclusion rate — so the scan stopped at pool index 72
(2026-06-01) and the remaining 300 candidates were never needed.

Exclusions among the 73: **E2** no representation comparison (27), **E3**
zero-shot or no trained head (4), **E1** review (1), **E6** duplicate (1).

The large E2 count is informative in itself. The most common reason a paper
mentioning ESM-2 does not qualify is that the PLM is a **fixed component in
every arm** — the ablations vary the readout, the pooling, the loss, the graph
or the fine-tuning depth, never the representation. Papers that do swap the
representation are a minority of papers that use one.

## 3.4 Primary outcome

Headline `seeds_per_arm` is the count attached to the arm carrying the
representation claim. Six papers report different counts for different arms; the
choice and its reason are recorded per paper in `HEADLINE_SEEDS`
(`src/scan_tally.py`), so the tally can be recomputed under a different rule.

| seeds per arm | papers | share |
|---|---|---|
| not stated | 16 | 40.0% |
| 1 | 9 | 22.5% |
| 3 | 5 | 12.5% |
| 5 | 8 | 20.0% |
| 6 | 1 | 2.5% |
| 10 | 1 | 2.5% |

**25 of 40 (62.5%) report one run per arm or do not say.** This crosses the
pre-committed 50% threshold, so we lead with it.

**Sensitivity.** Three judgment calls could have moved this; none changes the
branch:

| variant | share |
|---|---|
| as screened | 62.5% |
| drop the 2 papers admitted by Amendment 3 | 63.2% |
| restore the Amendment-4 duplicate | 61.0% |
| drop the tiebreak inclusion (10 seeds) | 64.1% |

Range 61.0-64.1%. The amendment that favours us moves the figure by 1.5 points.

A caveat on reading the 40%: **`not_stated` is not the same as 1.** Some of
those papers may have run several seeds and not said; two of the 25 are recorded
as having deterministic probes and so no training seed to vary. The defensible
reading of 62.5% is **"one run per arm, or no way for a reader to tell"** —
which is the actionable claim, because a reader cannot distinguish them either.

## 3.5 The sharper finding: variance is reported, but not over runs

**32 of 40 papers report some variance. Only 15 repeat a training seed.**

Among the 25 papers with one run or no stated count, **17 still print a spread**
and **7 run a significance test on it**. The spread is a bootstrap over test
items, or +/- 1 SD across cross-validation folds. Both are legitimate
quantities. Neither is the one at issue: a test-item bootstrap conditions on the
single trained model it was given, and resampling it 10,000 times does not
widen that conditioning. Cross-validation varies the data split, which is a
different variance source, usually reported as one number, and under our frame
is recorded separately from seed repetition.

So the modal paper in this literature does not omit uncertainty. It quantifies
the uncertainty it can afford — over test examples — and that quantity is
silent about the one that flipped our own ablation.

Four of the included papers say this themselves, in their own limitations:

> "the bootstrap intervals we report for our tokenizer comparison and ablations
> capture variability over evaluation queries, not variability across
> independent training runs. Due to limited compute, the full-scale models were
> trained with a single seed."
> --- LEMON-ZEST [@banerjee2026lemonzest]

> "the leading PLM rows overlap under this single-run prediction resampling
> view" ... "Repeated-seed gaps keep the results at the level of endpoint
> test-set evidence rather than statistical-significance claims."
> --- AMPBench-MT [@zhou2026ampbench]

> "stability of individual weights across training splits and pairing seeds
> remain untested here; bootstrap-seed stability addresses a different
> question."
> --- the cryptic-pocket counting field [@yu2026auditable]

> "we limited our training runs above to a single seed per model, which reduces
> our confidence about the statistical significance of differences between
> models"
> --- the pretraining-filtering study [@maiwald2026filtering]

This is the result we consider most worth publishing. The diagnosis is not
ignorance. It is a compute constraint that the field has learned to describe
accurately and work around.

## 3.6 Secondary outcome: unanswerable, which is itself the finding

The frame asked whether, for papers whose benchmark overlaps Part B, the
claimed delta clears twice the wider arm's per-seed standard deviation as
measured there. Six included papers touch FLIP or TAPE and the comparison
cannot be made for any of them:

- **HyPLM** overlaps most directly — FLIP GB1 two-vs-rest and three-vs-rest —
  and reports **no delta on those splits at all**, having removed them for
  precisely the instability Part B quantifies. The non-answer is the answer.
- Two papers use GB1 for quantization or closed-loop search objectives rather
  than a representation swap on the FLIP split, so our band does not apply.
- Three use TAPE [@rao2019tape] or ProteinGym-style [@notin2023proteingym]
  suites whose metrics and splits do not line
  up with the arms we measured.

Applying the threshold to published deltas needs **per-seed predictions**, which
almost nobody releases. That is itself an argument for the prescription in
Section 6.

---

# 4. Part B — measuring the seed band

## 4.1 Design

The aim is to isolate the cheapest, most defensible slice of run-to-run
variance and measure it well, rather than to estimate total variance badly.

**Representations.** Two arms: amino-acid one-hot, and mean-pooled frozen
ESM-2 650M [@lin2023esm2] (`facebook/esm2_t33_650M_UR50D`) over non-special
tokens. Frozen
features mean 10 seeds costs minutes, not days, which is what makes a 10x10
grid affordable at all.

**Head.** Linear(d, 256) - ReLU - Dropout(0.1) - Linear(256, 1). Adam, lr 1e-3,
batch 64, at most 200 epochs, early stopping with patience 10 on validation
Spearman.

**What a seed varies.** Parameter initialisation and batch order, and nothing
else. The validation split is carved with a **fixed** split seed (or, on TAPE,
taken from the benchmark's own shipped validation rows — one fewer arbitrary
choice). Consequently **every band we report is a lower bound** on the variance
a paper faces if it also reshuffles its split.

**Tasks.** All four are public. FLIP [@dallago2021flip] GB1 (8,733 sequences,
265 aa, five official splits); FLIP AAV
(284,009 sequences of 734-750 aa, three splits spanning the difficulty range,
subsampled to a 5,000/5,000 budget with a fixed draw seed, with `one_vs_many`
keeping all 1,170 training rows so the low-label regime is intact); TAPE
fluorescence (54,025 sequences) and TAPE stability (68,977) [@rao2019tape],
both at full size.

**Statistics.** Paired bootstrap, 10,000 resamples, on seed-mean predictions
over the same test items; arms with differing test indices are refused by the
comparison code. Separately, we enumerate all **100 single-run pairings**
available from each 10x10 seed grid — the distribution a one-seed-per-arm paper
samples from — and report its range and the share whose sign disagrees with the
10-seed result.

**Sanity check.** One-hot on GB1's random `sampled` split reaches Spearman
0.926, in line with FLIP's published one-hot figures. Absolute AAV numbers are
not comparable to published leaderboards because of the subsample; all
within-AAV comparisons are unaffected, since every arm sees identical rows.

## 4.2 Seed bands widen with extrapolation difficulty

On GB1 the per-seed standard deviation rises from **0.002** on the random split
to **0.075** on `low_vs_high` — a factor of about 37. On `one_vs_rest` the
one-hot arm's own Spearman ranges from **-0.056 to +0.145** across seeds: the
same features and the same data give either "no signal" or "a modest positive",
depending on nothing but the seed. AAV replicates the pattern on an unrelated
protein (0.004 to 0.050, a factor of about 13).

## 4.3 The headline table

Delta is ESM-2 650M minus one-hot on seed-mean predictions. "band sd" is the
wider arm's per-seed standard deviation. "flip%" is the share of the 100
single-run pairings whose sign disagrees with the 10-seed result.

| bench | task | n_test | true delta | p | band sd | **\|d\|/sd** | n=1 delta range | flip% |
|-----|--------------|-------|---------|------|--------|---------|-------------------|------|
| AAV | low_vs_high | 5,000 | -0.0095 | 0.500 | 0.0496 | **0.19** | -0.140 .. +0.094 | **45** |
| GB1 | low_vs_high | 3,644 | -0.0078 | 0.409 | 0.0747 | **0.10** | -0.183 .. +0.172 | **37** |
| TAPE | stability | 12,851 | +0.0274 | <1e-4 | 0.0605 | **0.45** | -0.058 .. +0.241 | **23** |
| GB1 | three_vs_rest | 5,743 | -0.0170 | <1e-4 | 0.0100 | 1.70 | -0.049 .. +0.004 | 6 |
| GB1 | one_vs_rest | 8,705 | +0.1590 | <1e-4 | 0.0681 | 2.34 | -0.050 .. +0.389 | 2 |
| GB1 | sampled | 1,745 | -0.0173 | <1e-4 | 0.0072 | 2.42 | -0.038 .. -0.011 | 0 |
| AAV | sampled | 5,000 | +0.0106 | 0.023 | 0.0044 | 2.38 | +0.003 .. +0.029 | 0 |
| GB1 | two_vs_rest | 8,309 | -0.0604 | <1e-4 | 0.0201 | 3.01 | -0.115 .. -0.017 | 0 |
| TAPE | fluorescence | 27,217 | -0.0494 | <1e-4 | 0.0111 | 4.45 | -0.077 .. -0.039 | 0 |
| AAV | one_vs_many | 5,000 | +0.3866 | <1e-4 | 0.0217 | 17.85 | +0.311 .. +0.433 | 0 |

Sorted by ratio, the separation is clean. **Below |d|/sd ~ 2: flip rates
6-45%. At or above: 0-2%.**

Note what does *not* predict the flip rate. Split difficulty does not: GB1
`one_vs_rest` is the hardest split in the set and flips 2% of the time, because
its effect is large. Sample size does not: TAPE stability has 12,851 test items
and flips 23% of the time. Nor does the p-value of the 10-seed result: stability
has p < 1e-4 and still flips 23% of the time, because the paired bootstrap
answers a question about test items, not about runs.

## 4.4 The sharpest case is an ordinary split

TAPE **stability** is not a designed extrapolation split. It is the standard
split everyone reports, with **53,614 training examples**. On it:

- the true effect is small but real: delta = +0.027, p < 1e-4;
- a single run per arm could report anything from **-0.058 to +0.241**;
- **23% of single-run pairings get the sign backwards**;
- the largest single-run report, +0.241, is **8.8x the true effect**.

So a one-seed-per-arm experiment on this benchmark can honestly report "ESM-2
embeddings improve Spearman by 0.24" when the real figure is 0.027. The
inflation is not symmetric noise. The one-hot arm has a long low tail — one seed
at 0.4497 against a mean of 0.5920 — so an unlucky *baseline* run manufactures a
large apparent gain. This removes the easy defence that the problem is confined
to contrived extrapolation splits.

## 4.5 A claim we withdrew

After GB1 alone we wrote, and said aloud, that "frozen ESM-2 650M is usually
worse than one-hot". It lost on four of five GB1 splits, so the sentence
described the data in front of us.

FLIP AAV contradicted it: on AAV's random split ESM-2 **wins**, modestly but
significantly (+0.011, p = 0.023). The GB1 result was an artifact of the
benchmark — GB1 is a four-site combinatorial library, which one-hot can
essentially memorise when train and test are drawn from the same pool. The
over-general claim is withdrawn. Across all 10 comparisons frozen ESM-2 650M
wins 4 and loses 6, and we offer no general verdict.

We record this because it is the same error in miniature that the paper is
about: a real pattern, measured correctly, over-generalised from one benchmark.
Our own original annotation of it is left in place in `RESULTS.md` rather than
rewritten.

## 4.6 Why the ratio, and why 2

The mechanism is unremarkable. For a one-run-per-arm estimate, the reported
difference is the true effect plus a draw from the difference of two seed
distributions. If that difference has standard deviation s, the sign is wrong
whenever the draw exceeds the effect in the opposite direction, which under
roughly symmetric noise happens with probability falling steeply once
|delta| exceeds about 2s. Two standard deviations is the familiar place where
that probability becomes small.

The complication, and the reason our ratio is a diagnostic rather than a
formula, is that s depends on **both** arms' spreads *and the correlation
between their predictions*. GB1 `low_vs_high` has the larger band standard
deviation (0.075 against AAV's 0.050) yet the lower flip rate (37% against
45%), because its two arms correlate at 0.81 while AAV's correlate at 0.48.
Correlated arms share their bad seeds; the paired difference is then tighter
than either margin suggests. A paper using the wider arm's sd, as we do, is
therefore being conservative in the right direction — it will over-estimate the
noise when the arms are correlated, and that is the safe way to be wrong.

## 4.7 Two published points on the same curve

Two papers from the Part A set happen to report enough to be placed on this
curve, one at each end, which is some evidence the regularity is not an
artifact of our setup.

**RipplePLM** [@lv2026ripple] reports low-N fitness regression over five runs.
On Spike-ACE2, frozen ESM-2 scores 0.331 +/- 0.041 against a ridge baseline at
0.335 +/- 0.052 — a gap of 0.004 against standard deviations an order of
magnitude larger, so |d|/sd is about 0.08, deep in the coin-flip regime. The
same two representations differ by 0.256 on avGFP. One pair of
representations, two assays, opposite verdicts, legible only because the
authors ran five seeds.

**CliffRank** [@li2026cliffrank] reports five aligned seeds across handcrafted,
ECFP, MACCS and two ESM-2 scales. On E. coli activity-cliff ranking the non-PLM
MACCS encoders beat both ESM-2 scales by roughly 0.18 Spearman against standard
deviations of 0.005-0.03 — a high ratio, where one run per arm would have
reached the same verdict.

The threshold cuts both ways, which is the point. It is not an argument that
published PLM results are generally unsafe; it is a test for telling which
ones are.

---

# 5. Putting the two parts together

Part A says 62.5% of qualifying papers run one seed per arm or do not say. Part
B says that in the regime below |d|/sd ~ 2, such a design gets the sign wrong
6-45% of the time, and can inflate a true effect by nearly an order of
magnitude on a standard benchmark split.

The two parts do not compose into an estimate of how much published work is
wrong, and we want to be explicit that we are not providing one. To do that we
would need each paper's effect-to-noise ratio, which needs its per-seed
spread — the very thing the 25 papers do not report. Our secondary outcome
(Section 3.6) failed for exactly this reason.

What the two parts jointly support is narrower and still useful: **a large
fraction of this literature reports deltas whose identifiability cannot be
assessed, from either the paper or the outside**, and when the ratio can be
measured, a substantial minority of such deltas sit in the regime where the
sign is not established.

The one quantitative bridge available to us is the motivating case. BindFormer's
one-run ablation reported -0.050 against a one-hot per-seed sd of about 0.025 —
a ratio of 2.0, right at the edge — and the three-seed rerun duly collapsed it
to -0.021 (p = 0.356). The rule below would have flagged it.

---

# 6. The prescription

One line, checkable from numbers a paper could print in one extra column:

> **Report your per-seed spread. If your claimed delta is not at least twice the
> wider arm's per-seed standard deviation, one run per arm does not establish
> its sign.**

Why this and not "run more seeds":

- **It is affordable where it matters.** Frozen-feature probing, which is how
  most representation comparisons are done, costs minutes per seed. The papers
  that genuinely cannot repeat — those pretraining a PLM from scratch — are
  identifiable, and one of them states its single-seed limitation plainly
  (Section 3.5).
- **It is checkable by a reader**, which a request for diligence is not. Two
  numbers per arm suffice.
- **It is a floor, not a ceiling.** Three seeds already give a usable estimate
  of the spread; 10 is better. The point is to report the spread at all.
- **It tells you when you are safe.** Six of our 10 comparisons clear the
  threshold comfortably, including every one with a large effect. A paper with
  a ratio of 4 does not need more seeds, and the rule says so.

Three practices from the included set are worth copying directly. One states
seed counts per analysis in a reproducibility table and reports **all five
paired gains individually** rather than only their mean [@xu2026degradequery].
One uses the **seed-averaged** metric as the paired unit for its significance
tests across 60 representation-regressor combinations [@tian2026peptide]. One
prints the delta and the across-seed sigma side by side — "improves Spearman on
S669 from 0.486 to 0.540 (sigma = 0.002 across seeds)" [@shivram2026constraint].

And one practice is worth asking for beyond our own rule: **release per-seed
test predictions.** It costs almost nothing, it makes paired tests possible for
readers, and its absence is why our secondary outcome could not be computed. One
included paper declines to claim significance explicitly because "paired
per-seed predictions are not available for all baselines" [@kong2026dptmdt] —
which is the right instinct and also a description of the problem.

---

# 7. Limitations

We have put these in one place rather than distributing them where they are
least visible.

## On Part B

- **Ten comparisons, four tasks, one head architecture, frozen features only.**
  The threshold near 2 is an observation with a mechanism, not an established
  constant. A different head, a fine-tuned arm, or a different metric could
  move it.
- **Every band is a lower bound.** A seed varies initialisation and batch order
  only; the validation split is fixed. Papers that also reshuffle splits face
  wider bands than we report.
- **No fine-tuned arm.** The most expensive and most commonly claimed setting
  is untested here. We expect wider bands, which would strengthen the
  conclusion, but we have not measured it and do not assert it.
- **ESM-2 8M/150M arms not run**, so "bigger PLM is better" is unaddressed.
- **AAV is subsampled** and three of seven splits were used; `des_mut`/`mut_des`
  are untouched.
- **Hardware nondeterminism is outside our bands entirely.** ORBIT-FMIB reports
  a V100 and an H100 giving different scores for identical inputs. Our grid
  holds hardware fixed, so our variance estimates omit this source.

## On Part A

- **arXiv only.** Much protein-ML work appears on bioRxiv or in journals. This
  measures reporting practice on arXiv, as the frame said up front. A bioRxiv
  pass is a separate scan, not an extension of this one.
- **Twelve months, not four years.** The 40 inclusions came from the newest 73
  of 373 candidates, spanning 2026-06-01 to 2026-11-19. This is a snapshot of
  current practice, **not a trend**. The frame's stopping rule produced the
  window; we did not choose it afterwards, and we make no claim about whether
  practice is improving.
- **`not_stated` is not `1`** (Section 3.4).
- **Mixed-arm papers require a judgment.** Six report different counts for
  different arms; `HEADLINE_SEEDS` records each choice and its reason.
- **One screener, no second rater**, so no inter-rater agreement statistic. The
  mitigation is that every one of the 73 decisions logs the passage it turned
  on, in `scan/decisions.jsonl`, so any disagreement is locatable.
- **I2 is the softest criterion.** Whether a comparison is "presented as
  evidence about the representation" is a reading. We recorded a tiebreak for
  balanced cases and applied it against our own hypothesis, but a different
  screener would include and exclude a somewhat different set.

## On the whole

- We measure identifiability, not correctness. A paper with an unidentifiable
  delta may still be right. Our claim is that its table does not establish it.

---

# 8. Conclusion

Of 40 arXiv papers that argue for a protein-language-model representation with
their own numeric comparison, 25 report one training run per arm or do not say
how many they ran — and 17 of those 25 nonetheless print an error bar, computed
over test items or cross-validation folds rather than over runs. Measured
directly on four public tasks, the probability that such a design reports the
wrong sign is governed by the true effect divided by the wider arm's per-seed
standard deviation: below a ratio of about 2 it runs from 6% to 45%, and on an
ordinary TAPE split with 53,614 training rows a single run can inflate a true
+0.027 effect to +0.241.

The remedy is one printed column and one sentence of arithmetic. Several groups
have already adopted it independently, one of them discovering in the process
that three extra seeds turned their win into a loss. We are asking for that to
be the default rather than the exception.

---

# References

::: {#refs}
:::

# Reproducibility

All code, logs and per-seed outputs are in the project repository.

Two things are deliberately absent. The full texts we fetched to confirm seed
counts are other authors' papers and are not ours to redistribute; the fetcher
regenerates them from the pool, and `scan/decisions.jsonl` records the passage
each decision turned on, with its arXiv id, so the screening is auditable
without them. Benchmark downloads and extracted embeddings are a few gigabytes
and rebuild from public sources with `src/features.py`.

| what | where |
|---|---|
| Part A frame, frozen before the pool | `FRAME.md` |
| Part A per-paper decisions and passages | `scan/decisions.jsonl` |
| Part A tally and sensitivity | `src/scan_tally.py`, `evidence/scan_tally.txt` |
| Part A write-up | `SCAN.md` |
| Part B per-seed runs | `evidence/runs/`, `evidence/runs_aav/`, `evidence/runs_tape/` |
| Part B seed bands | `evidence/seed_bands_*.txt` |
| Part B comparisons | `evidence/comparisons*/` |
| Part B synthesis | `evidence/crosstab.txt`, `RESULTS.md` |
| feature extraction | `src/features.py` |
| training and evaluation | `src/run_task.py` |
| paired bootstrap and n=1 enumeration | `src/compare.py` |

Rebuild the Part A numbers with:

```bash
python src/scan_tally.py --decisions scan/decisions.jsonl
```

---

<!--
# Notes for submission

Open items before this goes anywhere:

1. AUTHOR AND AFFILIATION are filled in: Pankaj Kumar, independent
   researcher. This is independent work, so naming an employer would imply
   institutional involvement that does not exist. Change the name if you want
   it to read differently.
2. CONTACT EMAIL deliberately omitted — add it at submission time rather than
   committing it to a public repository earlier than needed.
3. CATEGORY: cs.LG is the natural primary, with q-bio.QM cross-list. Note that
   q-bio.BM endorsement is still outstanding from the BindFormer submission;
   cs.LG may avoid that blocker, but check before relying on it.
4. CITATIONS are done and both earlier TODOs are closed. 31 entries in
   `paper/references.bib`, rendering under `pandoc --citeproc`. Author lists for
   the 27 arXiv entries come from the arXiv API via `src/fetch_refs.py`, not
   from memory, and are regenerated by `src/make_bib.py`; the regenerated file
   is byte-identical to the committed one.
   - `dallago2021flip` now cites the proceedings version, confirmed against the
     NeurIPS Datasets and Benchmarks 2021 table of contents, which lists FLIP
     in "Proceedings of the Neural Information Processing Systems Track on
     Datasets and Benchmarks 1", edited by Vanschoren and Yeung.
   - `bindformer` is now an `@unpublished` entry, "manuscript in preparation",
     with a note saying it is cited only as the origin of the question and that
     no result here depends on it. If it is posted before this preprint,
     replace the entry with the arXiv id.
5. DEGRADOMAP AUTHORS: no contact address is obtainable without an account of
   yours. arXiv's submitter-email link now answers "Login Required", and
   `dl.acm.org` serves a bot-verification interstitial. See
   `outreach/degradomap-email.md` for the drafted note and the four routes.
   Nothing in this paper waits on them: every figure quoted is from their own
   published text. Note also that their ACM camera-ready source (in their
   repository) names the second author as Jasper Zhang, not Austin Jin as on
   arXiv; our citation follows arXiv, and this should be re-checked against the
   ACM record.
6. Section 3.6 (secondary outcome failed) should stay. It is the honest record
   of a pre-registered analysis that could not be run.
-->
