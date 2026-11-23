# Part A — literature scan result

Pre-registered in [FRAME.md](FRAME.md) before the candidate pool was built.
Per-paper decisions, with the passage each one turned on, are in
`scan/decisions.jsonl`. Reproduce the numbers below with:

```bash
python src/scan_tally.py --decisions scan/decisions.jsonl
```

## What was screened

373 candidate papers, 160 fetched most-recent-first, 157 with retrievable full
text (3 coded E4). **73 papers screened in frozen pool order to reach 40
inclusions** — a 55% inclusion rate, so the scan stopped at pool index 72
(2026-06-01) and never needed the rest of the pool. Every seed count was set by
reading the matched passage, as the frame requires; the regex pass only located
candidate text.

Exclusions: **E2** no representation comparison (27), **E3** zero-shot or no
trained head (4), **E1** review (1), **E6** same-work duplicate (1).

## Primary outcome

Headline `seeds_per_arm` — the count attached to the arm carrying the
representation claim, fixed per paper in `HEADLINE_SEEDS` in `src/scan_tally.py`:

| seeds per arm | papers | share |
|---|---|---|
| not stated | 16 | 40.0% |
| 1 | 9 | 22.5% |
| 3 | 5 | 12.5% |
| 5 | 8 | 20.0% |
| 6 | 1 | 2.5% |
| 10 | 1 | 2.5% |

**25 of 40 (62.5%) report one run per arm or do not say.**

The frame's pre-committed branch at ≥50% is to **lead with the prevalence
figure**, and that is what the write-up will do. The threshold was fixed before
the pool existed, which is the only reason this number means anything.

### Sensitivity to the judgment calls

Three decisions during screening could have moved this. None changes the branch:

| variant | share |
|---|---|
| as screened | 62.5% |
| drop the 2 papers admitted by Amendment 3 | 63.2% |
| restore the Amendment-4 duplicate | 61.0% |
| drop the tiebreak inclusion (FLaG, 10 seeds) | 64.1% |

Range 61.0–64.1%. Amendment 4 is the one that cuts in this project's favour
(it drops a 10-seed paper), and it moves the figure by 1.5 points.

## The sharper finding: variance is reported, but not over runs

**32 of 40 papers report some variance. Only 15 repeat a training seed.**

Among the 25 papers with one run or no stated count, **17 still print a spread**
— bootstrap intervals over test items, or ±1 SD across cross-validation folds —
and **7 run a significance test**. The error bar is nearly standard practice;
re-running the model is not. A test-item bootstrap conditions on the one trained
model it was given, so it cannot see the quantity Part B measures, however many
resamples it draws.

Four papers say so themselves, in their own limitations:

- **LEMON-ZEST** (2609.37675): its intervals "capture variability over
  evaluation queries, not variability across independent training runs", and
  "the full-scale models were trained with a single seed".
- **AMPBench-MT** (2607.25518): intervals come from resamples of "retained
  single-run test predictions", and "the leading PLM rows overlap under this
  single-run prediction resampling view".
- **Cryptic-pocket ACF** (2610.00988): stability "across training splits and
  pairing seeds remain untested here; bootstrap-seed stability addresses a
  different question".
- **Pretraining-filtering** (2610.26651): "we limited our training runs above to
  a single seed per model, which reduces our confidence about the statistical
  significance of differences between models".

This is the result worth publishing. The field is not unaware of seed noise —
a meaningful minority names it precisely and then proceeds without the budget to
fix it. The gap is between knowing and measuring, not between knowing and not.

## Papers that already did Part B's job

Five independent groups measured, on their own benchmarks, the thing this
project set out to measure. They are the strongest evidence the effect is real
and not an artifact of our setup.

- **DegradoMap** (2606.04021) is the clearest case in the literature. Three
  seeds gave AUROC 0.646 against a gradient-boosting baseline of 0.607. The
  authors ran three more seeds; the six-seed mean fell to **0.603 ± 0.097 —
  below the baseline** (p = 0.556; the arXiv version gives the p-value without naming
  the test). Individual seeds span **0.502 to
  0.745**, and they write that "the best seed (0.7449, +23% over GB) reflects
  favorable initialization" and that ensembling over ≥6 seeds "is required for
  reliable deployment". A one-seed paper here could have reported anything from
  −0.11 to +0.14 against the same baseline.
- **PIT-GCL** (2610.04850) computes the ratio this project proposes: its margins
  are "between 6.4 and 9.6 times the combined standard deviation of the two
  methods". It also states what a seed varies per benchmark.
- **ProTok** (2610.18481) reruns its validation-selected configuration at five
  named seeds and prints the mean beside the single-run headline. On BioLIP2
  Cat.Fold the headline reads 85.79 against a 5-seed mean of 86.8 ± 0.2 — the
  published number sits roughly 5 seed-SDs below its own mean, while the gap to
  the best baseline is 2.6.
- **HyPLM** (2611.12000) drops GB1 two-vs-rest, three-vs-rest and a FLIP2 split
  from every summary statistic because "numerically equivalent runs of the same
  model differ by up to 0.2" — independent corroboration of the GB1 instability
  Part B measured directly.
- **2608.12090** wires seed disagreement into its tool: if the five seeds
  disagree strongly on the best layer, the user is notified and more repetitions
  are requested. Seed variance as a signal, not an error bar.

Two more deserve the same credit without being included. **ORBIT-FMIB**
(2610.00672) and **2611.09046** retrain a 1,395-fit grid and find the two runs
produced genuinely different critics — and report a V100 and an H100 giving
different scores for identical inputs. That is a nondeterminism source outside
this project's seed bands, and the limitations concede it.

## Best practice seen in the pool

Worth naming, because the prescription should point at real examples:

- **Peptide-protein affinity benchmark** (2608.30175): every configuration
  refitted at five seeds, the **seed-averaged** metric used as the paired unit
  for Wilcoxon tests with Holm adjustment across 60 representation-regressor
  combinations.
- **DegradeQuery** (2608.10595): seed counts stated per analysis in a
  reproducibility table, and **all five paired gains reported individually**
  rather than only the mean.
- **ProtLink** (2611.11017): per-seed values printed, paired per-seed deltas,
  and an explicit refusal to infer significance from three repetitions.
- **GenFish** (2610.24458, excluded E2): reports which of its five seed pairs
  favour each arm — "leads in two of five seed pairs for R@10, three for R@50,
  and all five for MRR" — and declines the ordering. The n=1 gamble, drawn by
  the authors.
- **2606.08100** (excluded E2): "improves Spearman correlation on S669 from
  0.486 to 0.540 (σ = 0.002 across seeds)" — delta and across-seed σ side by
  side, which is exactly the reporting this project asks for.

## Two real-world points on the Part B curve

- **RipplePLM** (2610.01891): on Spike-ACE2, frozen ESM-2 (0.331 ± 0.041) sits
  *below* a ridge baseline (0.335 ± 0.052) — |Δ|/sd ≈ 0.08, deep in the
  coin-flip regime. The same two representations differ by 0.256 on avGFP. Same
  pair, two assays, opposite verdicts, legible only because of the multi-run SDs.
- **CliffRank** (2609.01673): on E. coli, non-PLM MACCS encoders beat both ESM2
  scales by ~0.18 Spearman against SDs of 0.005–0.03 — a very high ratio, where
  one run per arm would have reached the same verdict. The threshold cuts both
  ways, which is the point.

## Secondary outcome: largely unanswerable, and that is the finding

The frame asked, for papers whose benchmark overlaps Part B, whether the claimed
Δ clears 2× the wider arm's per-seed sd as measured there. Six included papers
touch FLIP or TAPE, and the comparison cannot be made for any of them:

- **HyPLM** overlaps most directly (FLIP GB1 two-vs-rest, three-vs-rest) and
  reports **no delta on those splits at all** — it removed them for the very
  instability Part B quantified. The non-answer is the answer.
- **2610.00665** (GB1) and **2611.05396** (GB1 closed-loop) use GB1 for
  quantization and search objectives, not a representation swap on the FLIP
  split, so the Part B band does not apply.
- **recAMPLIFY**, **ProtModernBERT** and **LEMON-ZEST** use TAPE or
  ProteinGym-style suites whose metrics and splits do not line up with the
  arms measured in Part B.

So this scan cannot apply the threshold to published deltas. Doing it properly
needs per-seed predictions, which almost nobody releases — itself an argument
for the prescription.

## Limitations

- **arXiv only.** Much protein-ML work appears on bioRxiv or in journals. This
  measures reporting practice on arXiv, as the frame said up front. A bioRxiv
  pass is a separate scan, not an extension of this one.
- **Twelve months, not four years.** The 40 inclusions came from the newest 73
  of 373 candidates, spanning 2026-06-01 to 2026-11-19. This is current
  practice, not a trend. The frame's stopping rule produced this; it was not
  chosen afterwards.
- **`not_stated` is not the same as 1.** 16 papers never say. Some of those
  (probes fitted in closed form, convex solvers) have no training seed to vary
  at all, and 2 of the 25 are recorded as deterministic. The honest reading of
  the 62.5% is "one run per arm, or no way for a reader to tell" — which is the
  actionable claim, since a reader cannot distinguish them either.
- **`seeds_per_arm` for mixed papers is a judgment.** Six papers report
  different counts for different arms. `HEADLINE_SEEDS` records the choice and
  the reason for each, so the tally can be recomputed under a different rule.
- **One screener.** No second rater, so no inter-rater agreement. The
  mitigation is that every decision logs the passage it turned on.
