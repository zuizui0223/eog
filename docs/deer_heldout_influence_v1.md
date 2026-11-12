# Deer held-out site influence: concentration, not universal improvement

## Executed result

Source: the original public 87-site eMammal-origin deer detection
history, fixed SHA256
`bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34`.

Pre-score protocol commit:
`a1803fb0e15126732df25a3b66082e13f6651ea2`.
Canonical GitHub Actions:
https://github.com/zuizui0223/eog/actions/runs/43048080033

The prior 5-fold whole-site held-out prediction comparison
gave Beta-mixture minus constant-p total log score **+95.57045**.
The 87 individual-site paired deltas were re-created using the
same source, folds and model code. The upstream source and
numeric total were verified, and its original fingerprint was
reproduced exactly.

| Most favorable beta sites excluded from score sum | Residual total log-score gain | Share of original net gain removed |
|---|---:|---:|
| 0 | +95.5705 | 0% |
| 1 | +82.4288 | 13.75% |
| 3 | +67.2355 | 29.65% |
| 5 | +55.8973 | 41.51% |
| 10 | +29.3144 | 69.33% |

The **site-level median delta is only +0.00760**.
The beta mixture wins 44 sites, while the constant-p
model wins 43. The sum of positive site deltas is
+118.2933, offset by negative site deltas of −22.7228.
Symmetric 5%-trimmed mean = +0.8375 per site;
10%-trimmed mean = +0.6854 per site.

All five fixed folds show positive aggregate deltas:
+29.4312, +13.4724, +13.1235, +12.7023, +26.8410.

## Interpretation

The overall predictive improvement is **concentrated in
a subset of sites**, especially the top 10, but it is not
attributable to one site alone. Removing the top 10 still
leaves a positive aggregate score. This is a **post-hoc
influence diagnostic** applied to the existing out-of-fold
site scores; it is **not** a refit or independent replication.

An AICc or held-out log-score gain is not proof that the
Beta mixture identifies a real ecological mechanism.
Unmeasured camera effort, serial dependence, site use,
closure violation and true site-level detection variation
are not distinguished. No independent A/B/M measurements
or EOG geometry are available, and no new EOG-WF endpoint
was created.

Result fingerprint:
`52aaea81661974ec316383179cc5b54f0e02cde02660298dd7988ac335c49574`.
The source and result artifact SHA are preserved in
`validation/deer_heldout_influence_v1/result_receipt.json`.

## Execution note

An initial CI run failed because it required bit-identical
JSON fingerprints across optimizer environments. This was
replaced with a strict source SHA and numeric total-score
tolerance, while retaining and reporting both the original
and recomputed fingerprints. The final CI reproduced the
original fingerprint exactly and passed.
