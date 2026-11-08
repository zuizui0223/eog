# EOG × BAM — repeated imperfect detection, six fixed sites

## Purpose

Previous work showed that one missed occupied cell and one corrupted
A/B/M site can alter whether the original EOG span response direction
is identifiable. This analysis replaces the *certified absence* premise
with a finite repeated-detection model, while keeping the original
12 synthetic landscapes, 768 candidate parameter worlds and M-release
EOG span response unchanged.

## Measurement model

At six fixed sites per landscape (selected using only the variability
of current occupancy among candidate worlds, not the response label),
conduct k independent visits per site. An occupied site yields a
detection on each visit with probability p; an unoccupied site cannot
yield a detection. We analyze the collapsed detection indicator
(at least one detection during k visits) at each site. Thus

`P(detected | occupied) = 1-(1-p)^k`

and `P(no detection | occupied) = (1-p)^k`.
No false positives are assumed.

The exact distribution of all 64 six-site detection patterns is
enumerated. Other landscape nodes are **unobserved**, not known absent.
This differs from the previous one-missed-G benchmark.

## Prior and decision

The analysis deliberately assigns equal hypothetical prior weight
to each **distinct (A,B,M) mask triple** within a landscape, rather
than counting parameter-label duplicates as independent hypotheses.
For each detection pattern, compatible mask triples receive their
exact detection likelihood; their posterior masses are summed by
the original EOG M-release span-response sign.

A response sign is reported only when its posterior probability
is at least 0.95; otherwise the planner abstains. Exact expected
correct, wrong and abstention probabilities are reported under this
same hypothetical prior predictive distribution. These are **not**
estimates of ecological truth or empirically calibrated risks.

Scenarios fixed in the protocol: p=0.5 or 0.8, visits k=1,3,6,
plus p=1,k=1 ideal detection at the six sites. Original source
full-G response-direction baseline: 121/129 classes, retained
for reference only and **not directly comparable** to six-site
probabilistic decisions.

## Scientific distinction

For any finite k and 0<p<1, observing zero detections at a site
never logically rules out occupancy: `(1-p)^k > 0`.
More effort can increase posterior confidence conditional on p and
the prior, but cannot turn an imperfect nondetection into logically
certain absence.

Even p=1 at the six surveyed sites says nothing about the remaining
unobserved landscape nodes. Hence the finite Bayesian decision and
the original complete-G identifiability certificate must not be
presented as the same estimand.

## Source, protocol and reproducibility

Pre-score protocol commit:
`e415f55e0e3109d8c36e02aa91dd581a6ac98865`.

```bash
python -m pytest -q tests/test_bam_detection_effort_v1.py
python benchmarks/bam_detection_effort_v1.py --output result.json
```

The dedicated CI checks the original known-truth generator SHA,
all 12 systems and 768 worlds, original 121/129 full-G baseline,
likelihood normalization, six-site site selection and exact
correct/wrong/abstention mass conservation.

## Limitations

No actual detection rate, field effort, occupancy, or A/B/M
measurements are available here. The repeated visits are independent
and detection p is constant across occupied sites and worlds;
these are sensitivity assumptions, not fitted estimates. The prior
is deliberately hypothetical. This does not establish true
probabilities of EOG geometric change, ecological universality,
causal M-release effects, or a fourth EOG-WF endpoint.
