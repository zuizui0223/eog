# Real deer histories: which observed patterns explain predictive-score gains?

## Source and method

Original eMammal-origin 87-site × 22-occasion deer detection history
(source SHA256 `bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34`).
The source-pinned 5-fold held-out site predictions were reproduced.
For each site, the paired score delta is beta-mixture minus
constant-p log predictive score. Prespecified descriptive
history features include detected days, valid and missing
days, detection fraction, longest consecutive zero run
(broken by NA), and switches across adjacent valid days.

Pre-score protocol commit:
`bf1c955ad27b5e10b1e5934603697d65e664799c`.
Canonical CI:
https://github.com/zuizui0223/eog/actions/runs/43125623191

## Verified findings

The total held-out beta-mixture gain is **+95.57046**
across 87 sites, with a site-level median of +0.00760.

| Observed detection days | Sites | Sum of beta minus constant held-out log scores |
|---|---:|---:|
| 0 |25|+0.2583|
| 1–2 |13|**+62.7751**|
| 3–8 |24|−12.4995|
| 9+ |25|+45.0365|

The 13 sites with 1–2 detected days account for
approximately **65.7%** of the net total score gain.
This is not a universal advantage: sites with 3–8
detected days have a negative aggregate score delta.

Across sites, adjacent observed-day switches have a
Spearman correlation with paired score delta of
**ρ=−0.36194 (exploratory p=0.000572)**.
The top 10 score-gain sites average 2.5 switches,
versus 5.36 in the other 77 sites.

Other prespecified associations are weak:
detected days ρ=−0.0780, detection fraction ρ=−0.0687,
missing days ρ=+0.0239, longest zero run ρ=+0.0661.
Their unadjusted exploratory p-values all exceed 0.47.

## Critical limits

**The explanatory features and outcome are functions of
the same binary detection histories.** Associations may
reflect the mathematical structure of the likelihood,
not an independently measured ecological mechanism.
The p-values are exploratory and not corrected for
multiple comparisons; this is a post hoc follow-up
within the same already explored dataset.

Site coordinates, verified effort, true occupancy and
closure, and independently measured abiotic A, biotic B
or movement M constraints are unavailable. This is
not a field test of EOG×BAM or a new EOG-WF endpoint.

Canonical result fingerprint:
`3da1d1477c2b690c17a09303572442328624a6bb2eb7223d841783b8fc6135f8`.
The machine-readable summary is in
`validation/deer_history_predictive_drivers_v1/result_receipt.json`.
