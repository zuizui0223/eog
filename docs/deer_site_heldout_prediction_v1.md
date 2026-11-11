# Real deer detection: held-out whole-site predictive test

## Protocol and evaluation

Source: eMammal-origin public deer detection history, 87 sites ×
22 ordered occasions, pinned SHA256
`bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34`.

Pre-score protocol:
`validation/deer_site_heldout_prediction_v1/protocol.json`,
commit `6bdd27ab9c27e1bc65ce9def9231b2a327640c5e`.

Five disjoint whole-site folds (seed 20261111). Each fold
trains the constant-p and latent beta-mixture detection
models on the remaining 69 or 70 sites. All 22 days
for every held-out site are excluded from training. Score
the **exact observed binary sequence probability** with
NA occasions omitted, no binomial combinatorial factor.

## Source-exact result

Canonical CI:
https://github.com/zuizui0223/eog/actions/runs/42912578452

| Held-out log predictive score | Value |
|---|---:|
| Constant detection model | −897.1652 |
| Beta-mixture site detection model | −801.5948 |
| Beta minus constant, all 87 sites | **+95.5705** |
| Mean per held-out site | **+1.0985** |
| Paired site bootstrap 95% descriptive interval | **+0.5676 to +1.6908** |

The beta mixture has a higher log predictive score in
**44 sites**, while constant p scores higher in **43 sites**.
Thus this is not a universal per-site improvement; a
subset of sites contributes large score gains. The
bootstrap is over these already explored sites and
is not an independent external-validation interval.

The exact result fingerprint:
`78ce643a8418954e834300a4c6e56129839fc84de0375536d53bf296a6defe2f`.
The source and artifact SHA are recorded in
`validation/deer_site_heldout_prediction_v1/result_receipt.json`.

## Interpretation boundary

This test goes beyond in-sample AICc by excluding entire
sites from fitting, but the same public source has already
been explored and the site population is not independently
sampled. There are no verified coordinates to block
geographically, no effort histories or true closure checks.
The beta mixture can represent site-level detection
heterogeneity, unmeasured effort, correlated daily
detections or changing deer availability.

No independently measured A/B/M constraints, EOG geometry,
causal intervention, or new EOG-WF endpoint is implied.
