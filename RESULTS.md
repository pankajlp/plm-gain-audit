# Results

## Run 1 — FLIP GB1, one-hot vs frozen ESM-2 650M, 10 seeds per arm (2026-11-22)

Setup: FLIP GB1 (8733 sequences, 265 aa, all equal length), the five official
splits. Frozen features, light head (Linear-ReLU-Dropout-Linear, hidden 256),
Adam 1e-3, early stopping on a validation Spearman carved from train with a
**fixed** split seed — so the only thing the seed varies is parameter init and
batch order. Metric: Spearman on the official test set. Paired bootstrap
(10 000 resamples) on seed-mean predictions.

Sanity check: one-hot on the random `sampled` split reaches ρ = 0.926, in line
with FLIP's own published one-hot numbers, so the pipeline is behaving.

### Seed bands

`evidence/seed_bands_gb1.txt`

| task | arm | per-seed mean | sd | min | max | range |
|---|---|---|---|---|---|---|
| sampled | onehot | 0.9255 | 0.0020 | 0.9237 | 0.9306 | 0.007 |
| sampled | esm2_650m | 0.9047 | 0.0072 | 0.8924 | 0.9129 | 0.021 |
| three_vs_rest | onehot | 0.8399 | 0.0059 | 0.8304 | 0.8527 | 0.022 |
| three_vs_rest | esm2_650m | 0.8232 | 0.0100 | 0.8038 | 0.8348 | 0.031 |
| two_vs_rest | onehot | 0.6960 | 0.0201 | 0.6639 | 0.7211 | 0.057 |
| two_vs_rest | esm2_650m | 0.6333 | 0.0124 | 0.6066 | 0.6469 | 0.040 |
| low_vs_high | onehot | 0.4652 | 0.0525 | 0.3534 | 0.5311 | 0.178 |
| low_vs_high | esm2_650m | 0.4312 | 0.0747 | 0.3480 | 0.5253 | 0.177 |
| one_vs_rest | onehot | 0.0208 | 0.0681 | −0.0564 | 0.1445 | 0.201 |
| one_vs_rest | esm2_650m | 0.2096 | 0.0666 | 0.0947 | 0.3327 | 0.238 |

**The seed band widens by a factor of ~35 from the easiest split to the hardest**
(sd 0.002 → 0.075). On `one_vs_rest` the one-hot arm's own Spearman ranges from
−0.056 to +0.145 across seeds: the same features and the same data give either
"no signal" or "a modest positive", depending on nothing but the seed.

### Representation deltas

`evidence/comparisons/`. Δ is ESM-2 650M minus one-hot on seed-mean predictions.

| split | Δ seed-mean | CI95 | p | n=1 Δ range | % of n=1 pairings with the opposite sign |
|---|---|---|---|---|---|
| sampled | −0.0173 | [−0.025, −0.010] | <1e-4 | −0.038 … −0.011 | 0% |
| three_vs_rest | −0.0170 | [−0.023, −0.011] | <1e-4 | −0.049 … +0.004 | 6% |
| two_vs_rest | −0.0604 | [−0.073, −0.048] | <1e-4 | −0.115 … −0.017 | 0% |
| low_vs_high | −0.0078 | [−0.026, +0.011] | 0.409 | **−0.183 … +0.172** | **37%** |
| one_vs_rest | +0.1590 | [+0.138, +0.180] | <1e-4 | −0.050 … +0.389 | 2% |

"n=1 Δ range" is over all 100 single-run pairings available from the 10×10 seeds
— the distribution a one-seed-per-arm paper is sampling from.

### What this says

1. **Frozen ESM-2 650M is worse than one-hot on four of the five GB1 splits.**
   The familiar framing — "add a PLM, get a gain" — is simply false here except
   in the extreme-extrapolation case.
   *(Annotated 2026-11-22 after Run 2: this holds for GB1 but does NOT
   generalise — on AAV's random split ESM-2 wins. See "What replicates, and
   what does not" below. Left in place as the pre-AAV record.)*

2. **The one place it wins, it wins decisively**: `one_vs_rest`, 28 training
   sequences, Δ = +0.159. PLM embeddings buy generalisation when there is almost
   no label budget, not accuracy when there is.

3. **Seed noise is largest exactly where the claims are made.** On `low_vs_high`
   the true effect is zero (p = 0.41), yet a single run per arm reports anything
   from −0.18 to +0.17, and **37% of such reports get the sign backwards**. On
   `one_vs_rest` the effect is real but a single run reports it as anywhere from
   −0.05 to +0.39 — an eightfold spread in the headline number.

   This is the finding the project is about: seed variance grows with the
   difficulty of the split, so the designed-split regime that papers single out
   as their evidence is the regime where single-run evidence is worth least.

4. It reproduces the BindFormer pattern on an independent benchmark: there, a
   one-run ablation gave Δ = −0.050 (p = 0.095) and three seeds gave
   −0.021 (p = 0.356).

### Caveats (GB1)

- One benchmark, one protein, one head architecture, frozen features only. GB1
  is a 4-site combinatorial library, which is kind to one-hot on random splits.
  AAV and the TAPE tasks are next, and the pattern should be checked against
  fine-tuned arms before any general claim.
- The validation split is fixed across seeds, which *understates* total
  run-to-run variance — a paper that also reshuffles its split faces a wider
  band than the one measured here.
- ESM-2 8M/150M arms not yet run, so "bigger PLM" is unaddressed.

---

## Run 2 — FLIP AAV, one-hot vs frozen ESM-2 650M, 10 seeds per arm (2026-11-22)

Same protocol. AAV is 284 009 sequences of 734–750 aa, so three splits spanning
the difficulty range were cut to a 5000/5000 train/test budget with a fixed draw
seed (`src/subsample.py`, `data/aav/subsampled/_manifest.json`). `one_vs_many`
keeps **all 1170** of its train rows, so the low-label regime is intact.
Features were built once over the 23 473-sequence union. One-hot pads the
variable lengths and drops 12 740 of 14 980 constant columns, leaving 2240
(112 variable positions × 20).

Absolute numbers will not match published FLIP figures because of the
subsample. Within-AAV comparisons are unaffected: every arm sees the identical
rows, and n_test = 5000 is larger than either GB1 split used above.

### Seed bands

`evidence/seed_bands_aav.txt`

| task | arm | per-seed mean | sd | min | max | range |
|---|---|---|---|---|---|---|
| sampled | onehot | 0.8427 | 0.0044 | 0.8318 | 0.8464 | 0.015 |
| sampled | esm2_650m | 0.8535 | 0.0037 | 0.8496 | 0.8604 | 0.011 |
| low_vs_high | onehot | 0.2372 | 0.0291 | 0.1919 | 0.2851 | 0.093 |
| low_vs_high | esm2_650m | 0.2263 | 0.0496 | 0.1446 | 0.2864 | 0.142 |
| one_vs_many | onehot | 0.1780 | 0.0217 | 0.1477 | 0.2147 | 0.067 |
| one_vs_many | esm2_650m | 0.5529 | 0.0185 | 0.5252 | 0.5807 | 0.056 |

### Representation deltas

`evidence/comparisons_aav/`

| split | Δ seed-mean | CI95 | p | n=1 Δ range | % opposite sign |
|---|---|---|---|---|---|
| sampled | +0.0106 | [+0.001, +0.020] | 0.023 | +0.003 … +0.029 | 0% |
| low_vs_high | −0.0095 | [−0.036, +0.018] | **0.500** | **−0.141 … +0.095** | **45%** |
| one_vs_many | +0.3866 | [+0.361, +0.411] | <1e-4 | +0.311 … +0.433 | 0% |

### What replicates, and what does not

**Replicates — the central claim.** The seed band widens with extrapolation
difficulty on an unrelated protein: sd 0.004 on the random split, 0.050 on
`low_vs_high`, a factor of ~13. And `low_vs_high` lands in the same place it did
on GB1: a true effect of zero (p = 0.50) with **45% of single-run pairings
reporting the opposite sign** — against 37% on GB1. Two unrelated proteins, the
same named split type, and in both cases a one-seed-per-arm experiment is close
to a coin flip that still yields a reportable-looking effect size
(up to ±0.14 here, ±0.18 on GB1).

**Replicates — the low-label win.** `one_vs_many` (1170 train rows) gives
Δ = +0.387, the largest effect anywhere in this project; GB1's `one_vs_rest`
(28 train rows) gave +0.159. Frozen PLM embeddings buy generalisation when the
label budget is tiny. That effect is far too large to be seed noise, and the
n=1 range never crosses zero.

**Does not replicate — "one-hot wins the easy splits."** On GB1, ESM-2 lost on
four of five splits. On AAV's random split ESM-2 *wins*, modestly but
significantly (+0.011, p = 0.023). So the GB1 result was specific to that
benchmark: GB1 is a 4-site combinatorial library, which one-hot can essentially
memorise when train and test are drawn from the same pool. The earlier framing
("frozen ESM-2 is usually worse") was over-general and is withdrawn — AAV
corrects it.

The claim that survives both benchmarks is narrower and is the one the project
is about: **the magnitude and often the sign of a reported PLM gain is not
identifiable from one run per arm, and the problem is worst on the designed
splits papers lead with.**

### Caveats (AAV)

- Subsampled, so not comparable to published AAV leaderboards.
- Three of seven splits. `des_mut` / `mut_des` (the designed-vs-mutant
  direction pair) are untouched and would be the interesting next cut.
- Still one head architecture and frozen features on both benchmarks.

---

## Run 3 — TAPE fluorescence and stability, 10 seeds per arm (2026-11-22)

Both tasks at full size, no subsampling: fluorescence 54 025 sequences
(GFP, 235–237 aa), stability 68 977 (designed mini-proteins, 43–50 aa).
TAPE ships its own validation split, so `run_task.py` now uses the given
`valid` rows instead of carving 10% off train — one fewer arbitrary choice
than on GB1 and AAV.

### Seed bands

`evidence/seed_bands_tape.txt`

| task | arm | per-seed mean | sd | min | max | range |
|---|---|---|---|---|---|---|
| fluorescence | onehot | 0.6689 | 0.0031 | 0.6646 | 0.6730 | 0.008 |
| fluorescence | esm2_650m | 0.6134 | 0.0111 | 0.5957 | 0.6256 | 0.030 |
| stability | onehot | 0.5920 | 0.0605 | 0.4497 | 0.6420 | 0.192 |
| stability | esm2_650m | 0.6429 | 0.0382 | 0.5836 | 0.6906 | 0.107 |

### Representation deltas

`evidence/comparisons_tape/`

| task | Δ seed-mean | CI95 | p | n=1 Δ range | % opposite sign |
|---|---|---|---|---|---|
| fluorescence | −0.0494 | [−0.054, −0.044] | <1e-4 | −0.077 … −0.039 | 0% |
| stability | +0.0274 | [+0.015, +0.040] | <1e-4 | **−0.058 … +0.241** | **23%** |

### The sharpest result in the project so far

TAPE **stability** is not a designed extrapolation split. It is the ordinary
split everyone reports, with **53 614 training examples**. And on it:

- the true effect is small but real: Δ = +0.027, p < 1e-4
- a single run per arm could report anything from **−0.058 to +0.241**
- **23% of single-run pairings get the sign backwards**
- the largest single-run report, +0.241, is **8.8× the true effect**

So a one-seed-per-arm experiment on this benchmark can honestly report
"ESM-2 embeddings improve Spearman by 0.24" when the real figure is 0.027.
The inflation is not symmetric noise: the one-hot arm has a long low tail
(one seed at 0.4497 against a 0.592 mean), so an unlucky baseline run
manufactures a large apparent gain.

This removes the easy defence that the problem only affects contrived
extrapolation splits. It affects a standard split with 50k training rows.

### Fluorescence goes the other way

ESM-2 loses clearly on fluorescence (Δ = −0.049, p < 1e-4, 0% sign flips) —
a tight, reliable, negative result. Together with AAV `sampled` (+0.011) and
AAV `one_vs_many` (+0.387), frozen ESM-2 650M now wins 4 of the 10
task-split comparisons in this project and loses 6. There is no general
verdict, which is consistent with the withdrawal recorded in Run 2.

---

## Cross-benchmark synthesis (10 comparisons, 4 tasks)

`evidence/crosstab.txt`

What governs the sign-flip rate is **not** how hard the split is. It is the
true effect divided by the wider arm's seed spread, |Δ|/sd:

| bench | task | true Δ | band sd | **|Δ|/sd** | n=1 Δ range | flip% |
|---|---|---|---|---|---|---|
| AAV | low_vs_high | −0.0095 | 0.0496 | **0.19** | −0.140 … +0.094 | 45 |
| GB1 | low_vs_high | −0.0078 | 0.0747 | **0.10** | −0.183 … +0.172 | 37 |
| TAPE | stability | +0.0274 | 0.0605 | **0.45** | −0.058 … +0.241 | 23 |
| GB1 | three_vs_rest | −0.0170 | 0.0100 | 1.70 | −0.049 … +0.004 | 6 |
| GB1 | one_vs_rest | +0.1590 | 0.0681 | 2.34 | −0.050 … +0.389 | 2 |
| GB1 | sampled | −0.0173 | 0.0072 | 2.42 | −0.038 … −0.011 | 0 |
| AAV | sampled | +0.0106 | 0.0044 | 2.38 | +0.003 … +0.029 | 0 |
| GB1 | two_vs_rest | −0.0604 | 0.0201 | 3.01 | −0.115 … −0.017 | 0 |
| TAPE | fluorescence | −0.0494 | 0.0111 | 4.45 | −0.077 … −0.039 | 0 |
| AAV | one_vs_many | +0.3866 | 0.0217 | 17.85 | +0.311 … +0.433 | 0 |

**The threshold is about 2.** Below |Δ|/sd ≈ 2, flip rates run 6–45%. At or
above it, 0–2%. Ten comparisons is too few to call that a law, but it is a
clean separation and it gives authors something to act on that is cheaper
than "run more seeds and hope":

> Report your seed spread. If your claimed Δ is not at least twice the wider
> arm's per-seed sd, one run per arm does not establish its sign.

That rule is checkable from numbers a paper could print in one extra line,
and it would have flagged BindFormer's original n=1 claim
(Δ = −0.050 against a one-hot sd of 0.025, ratio 2.0 — right at the edge,
and the three-seed rerun duly collapsed it to −0.021, p = 0.356).

### Caveats on the synthesis

- Ten comparisons, four tasks, one head architecture, frozen features only.
  The threshold is an observation, not an established constant.
- `band sd` uses the wider arm. The flip rate really depends on both arms'
  spreads *and* the correlation between their predictions (GB1 `low_vs_high`
  has the larger sd yet a lower flip rate than AAV's, because its arms
  correlate at 0.81 against AAV's 0.48).
- Seed here varies init and batch order only. Varying the data split too
  would widen every band, so these are lower bounds.
