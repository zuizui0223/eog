# Real deer detection: latent site heterogeneity sensitivity

Previous real 87-site deer camera-trap analyses estimated
constant daily p≈0.368 and ψ≈0.720. Day-index linear and
early/late detection models had nearly identical AICc and ψ.
This does **not** address between-site variation in detectability.

## Frozen comparison

Pre-score contract:
`validation/deer_site_detection_heterogeneity_v1/protocol.json`,
commit `534951d03ba42feb02358e245a6492317ddf9269`.

- Baseline: constant p and ψ (two parameters).
- Sensitivity: constant ψ, latent site pᵢ drawn from
  Beta(α,β), and daily detections conditionally Bernoulli
  given pᵢ (three parameters).

For each site with n observed visits and k detections,
integrate pᵢ analytically:

`L(k>0) = ψ × B(α+k,β+n-k)/B(α,β)`

`L(k=0) = (1-ψ)+ψ × B(α,β+n)/B(α,β)`

These are *exact binary-sequence* likelihoods; no
binomial coefficient is appropriate. NA occasions are
excluded, not treated as zeros. Report ψ, mean and SD of
the fitted site-level p distribution, AICc, and the
difference from the original model.

## Interpretive boundary

The latent beta distribution is a **statistical mixture**,
not directly measured site-level detection probabilities.
Its extra dispersion can absorb serial dependence,
heterogeneous camera effort, changing availability,
site-use heterogeneity or violated closure. A better
AICc does not isolate any one of these mechanisms.

Original public eMammal example, source commit
`f65b220d1c84240fa81cb457bf27522424fe1666`,
SHA256 `bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34`.
No direct A/B/M measurements or EOG response
geometry are available, and no fourth EOG-WF endpoint
is added.

## Reproduction

```bash
python -m pytest -q tests/test_deer_site_detection_heterogeneity_v1.py
python benchmarks/deer_site_detection_heterogeneity_v1.py \
  --source deer_detection_history.csv --output result.json
```
