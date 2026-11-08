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

## Canonical sensitivity result (exploratory)

GitHub Actions run
https://github.com/zuizui0223/eog/actions/runs/42445337190
completed successfully. Exact result fingerprint:
`594624f13c40ae69f949f9c76cb2bccacdb3837a007ac056b5e6c1972c62d04c`.
The original p=0.8, assumed p=0.8, uniform-mask
correct/wrong/abstention triple reproduced PR #682 exactly.

With the generating prior held uniform over distinct BAM masks:

| True p | Assumed p | Assumed prior | Correct | Wrong | Abstain |
|---|---|---|---:|---:|---:|
|0.8|0.8|uniform mask|0.353910|0.000813|0.645277|
|0.5|0.5|uniform mask|0.264091|0.001525|0.734384|
|0.5|0.8|uniform mask|0.350633|0.013449|0.635918|
|0.8|0.5|uniform mask|0.274710|0.000041|0.725249|
|0.5|0.5|uniform G|0.243837|0.000947|0.755216|
|0.8|0.5|uniform G|0.256081|0.000004|0.743915|

Other predeclared scenarios are retained in the archived output.
In the particular p=0.8 *assumed* model, all three tested prior
families yielded identical decision outcomes; this is a property
of these finite candidate landscapes, site selections and 95%
decision threshold, **not evidence that priors never matter**.
At assumed p=0.5, uniform-G weighting changed decisions and
their expected risks.

The largest source of sensitivity in this grid is detection
probability misspecification. For true p=0.5, assuming p=0.8
raises the mean wrong-decision probability from 0.001525 to
0.013449 (about 8.8-fold), while reducing abstention.
This is a tradeoff between selective decisions and incorrect
confidence under the declared hypothetical generating prior.
The worst truth-specific wrong-decision probability reaches
0.125 in this scenario, much larger than its mean.

No actual field prior or detection rate was estimated.
