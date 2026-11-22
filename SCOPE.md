# How much of the reported protein-language-model gain is seed noise?

**Status:** scoping, 2026-11-22. Nothing run yet beyond a smoke test.

## The question

Papers that add a pretrained protein language model (PLM) to a predictor almost
always report an ablation: "with ESM-2 embeddings we get X, with one-hot /
k-mer / no embedding we get X − Δ". That Δ is the evidence for the
representation. In most papers it comes from **one training run per arm**.

In BindFormer (`~/bindformer`) the same ablation at n=1 gave Δ pearson_r = −0.050
with p = 0.095 — a gain worth claiming. Rerun at three seeds and paired
bootstrap, the same comparison is Δ = −0.021 [−0.064, +0.025], p = 0.356: the
effect is inside seed noise. The one-hot arm's seed spread (±0.025) was larger
than the ESM-2 arm's (±0.011), so a single run can land anywhere in a band wide
enough to manufacture the result either way.

If that is general, a measurable share of the published PLM-ablation literature
is reporting seed noise as a representation effect. **That is the claim to test.**

## Why this is not already done

Searched 2026-11-22. There is a large literature comparing PLMs to baselines
(verdicts vary with task, split and label budget), and there is general ML work
on benchmark variance (Bouthillier et al. 2021; Reimers & Gurevych 2017). A few
protein papers do report multi-seed error bars (one FLIP study uses 10 seeds; a
fine-tuning paper uses 5; the UQ benchmark uses 5). But no study asks the
meta-question: **of the PLM-vs-baseline gains actually claimed in the
literature, what fraction falls inside the seed-noise band of its own
benchmark?** That is the gap.

Same shape as the AUC-flip scan (`~/Downloads/auc-flip-scan`): measure the
prevalence of a methodological problem across a literature, then demonstrate its
size on data.

## Design

### Part A — literature scan (cheap, no compute)

Sample recent papers (2023–2026) that report a PLM-vs-baseline or
PLM-A-vs-PLM-B ablation on a *public* benchmark. For each, record:

| field | values |
|---|---|
| seeds per arm | 1 / k / not stated |
| variance reported | yes / no |
| significance test | none / unpaired / paired |
| claimed Δ | effect size in the paper's own metric |
| benchmark + split | e.g. FLIP GB1 low-vs-high |

Primary outcome: the distribution of `seeds per arm`, and the share of claimed
Δ smaller than the seed-noise band we measure in Part B for the same benchmark.

Sampling frame is **frozen in `FRAME.md`** (2026-11-22, written before the
candidate pool was built): arXiv API, 2023-01-01 to 2026-11-22, categories
q-bio.BM / q-bio.QM / cs.LG, title-or-abstract match on PLM names, screened
most-recent-first to n = 40 with logged exclusion codes, and pre-committed
interpretation thresholds. The draft frame that stood here is superseded by it.

### Part B — measure the band (runnable locally)

Tasks, all small and public:

- **FLIP GB1** — `data.bioembeddings.com/public/FLIP` + splits from
  `J-SNACKKB/FLIP` (verified reachable 2026-11-22). Four splits of
  increasing extrapolation difficulty.
- **FLIP AAV** — same source.
- **TAPE fluorescence** and **stability** —
  `s3.amazonaws.com/songlabdata/proteindata/data_pytorch/` (verified reachable).
- **CASF-2016 / PDBbind** — carried over from BindFormer as the in-house case
  where we already know the answer.

Representation arms, frozen features + a light head (so 10+ seeds is minutes,
not days):

1. one-hot
2. ESM-2 8M
3. ESM-2 150M
4. ESM-2 650M (already cached locally)

For each (task, split, arm): **k = 10 seeds**, then the paired bootstrap from
`bindformer/training/stats.py` on seed-mean predictions. Report per-seed spread,
the seed-mean delta with CI, and the **minimum detectable Δ at n = 1** — the
number a single-run paper would have to clear and usually does not check.

### Secondary axis (only where it is free)

FLIP ships random *and* designed splits. Reporting both costs nothing and
separates two confounds: one-hot looks strong on random splits because of
similarity leakage, and looks arbitrary across seeds. Keep this secondary —
the split-leakage story is already known; the seed story is not.

## What would make this a null result

If seeds per arm is usually ≥ 5 in recent work, or if the measured bands are
narrow enough that typical claimed Δ clears them comfortably, the answer is
"the literature is fine" — and that is still worth writing up briefly, because
nobody has checked.

## Non-goals

- No new architecture, no new PLM, no fine-tuning (frozen features only).
- Not another "do PLMs help?" benchmark. The object of study is the
  **evidential practice**, not the representation.

## Environment

M5 Max / 36 GB / MPS. Reuse `~/bindformer/.venv` (torch 2.15.0,
transformers 5.22.0); ESM-2 650M already in the HF cache.

## Next

1. Freeze the Part A sampling frame in this file.
2. Smoke test: FLIP GB1, one-hot vs ESM-2 650M, 10 seeds, paired bootstrap.
3. If the band is as wide as BindFormer's, scale to the full task × arm grid.
