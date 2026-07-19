# Frozen comparative EOG example

This example is entirely synthetic. It demonstrates the audited comparative-geometry workflow; it is not a species distribution model, suitability analysis, or occupancy estimator.

## Files

- `examples/frozen_comparison/comparison.csv`: two artificial groups and two artificial environmental axes;
- `examples/frozen_comparison/reference.json`: an external robust reference frozen before the example groups;
- `examples/frozen_comparison/manifest.json`: all analytical choices and fingerprints;
- `examples/frozen_comparison/expected_result.json`: canonical deterministic output.

## Reproduce

From the repository root after installation:

```bash
python -m eog.runner \
  --manifest examples/frozen_comparison/manifest.json \
  --reference examples/frozen_comparison/reference.json \
  --input examples/frozen_comparison/comparison.csv \
  --output reproduced_result.json

cmp reproduced_result.json examples/frozen_comparison/expected_result.json
```

The CLI exposes no metric, resampling, permutation, support-class, or random-seed overrides. Those choices are frozen in the manifest.

## Interpretation

The primary effect is `log(span_B / span_A)` in one declared reference coordinate system. The example result is positive, so the synthetic `broader` cloud has greater comparative extent than the synthetic `baseline` cloud under that reference.

The sensitivity interval summarizes matched-size occurrence subsampling. It is not a confidence interval for ecological populations. The permutation diagnostic is meaningful only when the pooled rows are exchangeable under the comparison design; spatial clusters, repeated observations, temporal structure, survey-effort differences, or related samples require a design-aware alternative.

The result does not establish habitat suitability, occupancy probability, causal environmental effects, fragmentation, or a universal threshold. EOG does not produce a single headline score.

## Audit behavior

The CSV feature names and order must exactly match the manifest. Row IDs must be unique, group labels must match, and all feature values must be finite. Changing one value, row identifier, or group assignment changes the group fingerprint, so execution fails until a new manifest is intentionally frozen.

Ambiguous and negative results use the same output contract and must not be discarded or rewritten as directional findings.
