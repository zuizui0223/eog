# Real deer camera-trap detection heterogeneity by observation day

## Main question

Previous real 87-site eMammal deer analysis estimated daily detection
p≈0.368 and site-use parameter ψ≈0.720 under constant daily p.
The fixed-count temporal-order permutation did not reject its
specific null, but that is **not** evidence that detection
probability is constant.

This study compares three prespecified single-season
likelihoods on the **same original 87×22 detection history**:

1. Constant daily p, constant ψ (2 parameters).
2. Logistic linear detection p over ordered observation columns,
   constant ψ (3 parameters).
3. Separate early (columns 1–11) and late (12–22) detection
   probabilities, constant ψ (3 parameters).

All use the same occupied-versus-unoccupied site mixture,
zero false positives and omit NA occasions rather than
imputing them to nondetections. Compare AIC and AICc using
87 independent *site units as a model assumption*; AICc
does not repair site correlation or temporal closure.

Source pinned to
`BrentPease1/single-season-occupancy` commit
`f65b220d1c84240fa81cb457bf27522424fe1666`,
CSV SHA256
`bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34`.
Pre-score protocol commit:
`dedb58c851162f4c382517faeba075baf20def99`.

## Critical interpretation

The original columns are ordered daily occasions, but actual
calendar dates and per-day camera effort are not independently
verified in this file. A linear column effect may reflect
effort, deer movement, weather, changing occupancy or other
unmeasured influences. A lower AICc would establish relative
model fit **only under these candidate models and assumptions**,
not a biological temporal mechanism.

No real abiotic/biotic/movement constraints or EOG geometric
response are available from this source. This is a detection
model audit, not a full causal EOG×BAM test, a new field
replication, or a fourth EOG-WF endpoint.

## Reproduce

```bash
python -m pytest -q tests/test_deer_day_detection_heterogeneity_v1.py
python benchmarks/deer_day_detection_heterogeneity_v1.py \
  --source deer_detection_history.csv --output result.json
```
