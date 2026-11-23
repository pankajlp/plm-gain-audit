# arXiv submission sheet

Everything the arXiv submission form asks for, in the order it asks. Paste the
fields verbatim; nothing here needs rewriting at the keyboard.

Build the PDF with `paper/build.sh` (pandoc + tectonic). Current build:
**15 pages, 4 tables, no figures.**

---

## 1. License

**arXiv.org perpetual, non-exclusive license** is the safe default and is what
most ML preprints use. CC BY 4.0 is also fine and slightly more permissive;
either is compatible with later journal submission. Do not pick CC0.

## 2. Primary category

**cs.LG** (Machine Learning).

Cross-list: **q-bio.QM** (Quantitative Methods), and optionally **stat.ME**.

Why not q-bio.BM: the outstanding endorsement there would block the submission.
cs.LG is also the honest primary — the contribution is methodological, about
how ablations are evaluated, not about biomolecular structure.

## 3. Title

```
Report your seed spread: how much of a published protein-language-model gain
is identifiable from one run per arm?
```

## 4. Authors

```
Pankaj Kumar
```

Affiliation on the form: Independent researcher. The PDF carries this as a
footnote on the title page.

## 5. Abstract (1,889 characters — arXiv's limit is 1,920)

Plain text, no markdown, hard-wrapped. arXiv strips bold anyway, so the
emphasis from the manuscript's abstract is gone and a couple of sentences are
tightened to fit the limit. The manuscript's own abstract is unchanged.

```
Ablation tables are how the protein-machine-learning literature argues that a
pretrained protein language model (PLM) representation helps. Such a table is
usually one training run per arm. We ask what that buys.

First, a pre-registered scan of 40 arXiv papers that report their own numeric
comparison between a PLM representation and a baseline representation on a
supervised protein task: 25 of 40 (62.5%) report one run per arm or do not say
how many they ran. The sharper figure is the cross-tab: 32 of 40 report some
variance, but only 15 repeat a training seed. Of the 25 papers with one run or
no stated count, 17 still print an error bar, from a bootstrap over test
items or a spread across cross-validation folds. The error bar is
near-universal; re-running the model is not.

Second, we measure the seed band directly: 10 seeds per arm, frozen features
and a light head, on four public tasks (FLIP GB1, FLIP AAV, TAPE fluorescence,
TAPE stability), 10 representation comparisons. The sign-flip rate
across the 100 single-run pairings from each 10x10 seed grid is governed not by
how hard the split is but by the true effect divided by the wider arm's
per-seed standard deviation. Below a ratio of about 2, 6-45% of single-run
pairings report the wrong sign; at or above it, 0-2%. On TAPE stability the
true effect is +0.027 Spearman while a single run per arm can report up to
+0.241.

We propose one checkable line: report your per-seed spread, and if the claimed
delta is not at least twice the wider arm's per-seed standard deviation, one
run per arm does not establish its sign.

We did not discover this phenomenon. Five of the included papers measure it on
their own benchmarks, one finding that three extra seeds turned a +0.039 AUROC
win into a 0.004 loss. Our contribution is the prevalence figure, the
cross-benchmark regularity, and a threshold cheap enough to adopt.
```

## 6. Comments

```
15 pages, 4 tables. Pre-registration frozen before screening; screening log,
seed grids and per-seed predictions released.
```

Add the repository URL to this field once the repo is pushed somewhere public.
Right now there is no remote, so do not promise a link that does not resolve.

## 7. ACM / MSC class (optional)

ACM class: `I.2.6; J.3` (Learning; Life and Medical Sciences).

## 8. Report number / DOI / journal ref

Leave blank. This is a preprint with no prior venue.

---

## Checks before clicking Submit

- [ ] Contact email: arXiv takes it from your account, so nothing goes in the
      PDF. It stays out of the repository until you decide otherwise.
- [ ] The PDF is 15 pages and the Section 4 crosstab is on one page, inside
      the margins.
- [ ] The "Notes for submission" block is an HTML comment and does not appear
      in the PDF (verified in the build).
- [ ] References render: 31 entries, no "[?]" placeholders.
- [ ] Decide whether `bindformer` stays as "manuscript in preparation". If
      BindFormer is posted first, swap in its arXiv id.
