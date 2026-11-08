# EOG × BAM — detection-model and prior sensitivity (v1)

## Scientific question

The preceding six-site repeated-detection analysis reported low expected
wrong-decision probability but high abstention, under a hypothetical
uniform prior on distinct A/B/M mask triples and a correctly specified
detection probability. This follow-up tests whether that result survives
**misspecified detection probability and alternative prior weighting**.

## Frozen design

Protocol committed before this scoring:
`validation/bam_detection_prior_calibration_v1/protocol.json`
(commit `03f995d699d1543143131781a51216e9b9312789`).

All 12 original synthetic landscapes, 768 source worlds, six fixed
target-blind selected sites per landscape, three visits per site, zero
false positives, original M-release EOG span response sign, and the
95% posterior decision/abstention rule are unchanged.

True detection probability p is 0.5 or 0.8; the decision model
assumes p=0.5 or 0.8, giving correctly specified and misspecified
cases. The **generating** distribution is held fixed at uniform
weight over distinct A/B/M masks for every comparison. The
**assumed decision prior** is one of:

- uniform over distinct A/B/M mask triples;
- uniform over distinct present-G masks, then uniform within G;
- uniform over response signs, then uniform within sign.

The latter two are explicitly hypothetical decision assumptions,
not alternative empirical frequencies. Every prior has strictly
positive mass on all candidate worlds.

For every scenario and landscape, enumerate all 64 detection patterns
and compute the posterior target-sign decision, expected correct,
wrong, and abstained outcomes under the **fixed generating prior**.
Retain the maximum wrong-decision probability across individual
possible truths as a caution against relying on mean risk alone.

## Critical interpretation

If a decision prior differs from the generating prior, a posterior
threshold of 0.95 is **not** automatically a frequentist error-rate
guarantee under the generating distribution. Even a small expected
error averaged across hypothetical worlds can conceal a large
truth-specific error for a particular candidate world.

The analysis must reproduce the earlier correctly specified
p=0.8, k=3, uniform-mask results:
correct 0.353909726564504, wrong 0.0008133028898816199,
abstention 0.6452769705456144 (mean across landscapes).
Any mismatch is a regression failure.

These are **retrospective sensitivity calculations on exposed
artificial worlds**. They do not estimate field detection p,
calibrate a biological prior, prove ecological transferability,
or add an EOG-WF endpoint.

## Reproduction

```bash
python -m pytest -q tests/test_bam_detection_prior_calibration_v1.py
python benchmarks/bam_detection_prior_calibration_v1.py --output result.json
```

The dedicated CI validates the source generator and likelihood
normalization, the original parent result, 12 sensitivity scenarios,
and exact correct/wrong/abstain mass conservation.
