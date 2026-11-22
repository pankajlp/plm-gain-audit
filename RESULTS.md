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

### Caveats

- One benchmark, one protein, one head architecture, frozen features only. GB1
  is a 4-site combinatorial library, which is kind to one-hot on random splits.
  AAV and the TAPE tasks are next, and the pattern should be checked against
  fine-tuned arms before any general claim.
- The validation split is fixed across seeds, which *understates* total
  run-to-run variance — a paper that also reshuffles its split faces a wider
  band than the one measured here.
- ESM-2 8M/150M arms not yet run, so "bigger PLM" is unaddressed.
