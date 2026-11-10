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

## Verified exploratory result

Canonical run: https://github.com/zuizui0223/eog/actions/runs/42843250119

| Model | ψ MLE | first p | last p | AICc | ΔAICc |
|---|---:|---:|---:|---:|---:|
| Constant |0.720140|0.367906|0.367906|1788.366|0|
| Linear day index |0.719158|0.399520|0.333716|1788.486|0.120|
| Early/late split |0.719399|0.385566|0.347844|1788.572|0.206|

All three models were fitted to exactly 87 sites and 1,699
valid site-days, with 215 missing site-days and 471 detected
site-days. The original constant-p model was reproduced
numerically within the preregistered tolerance.

The AICc differences are **tiny**, providing no decisive
preference among these three candidate descriptions. Across
them, ψ varies only from 0.719158 to 0.720140. This is a
*within-model-family stability result*, not evidence of true
occupancy, temporal closure, detection independence, or a
biological day effect.

Canonical fingerprint:
`733a027a121384d70c70adb83fb6e7f5592c54bd8abb399ea920345a38e986cb`.
The exact result artifact and source SHA are pinned in
`validation/deer_day_detection_heterogeneity_v1/result_receipt.json`.
