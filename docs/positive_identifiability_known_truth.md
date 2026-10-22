# Positive-observation identifiability: known-truth benchmark

This separate synthetic benchmark exercises the existing temporal reconstruction
and positive-survey ranking APIs. It adds no empirical endpoint to the closed
EOG-WF programme and does not modify Layer A or Layer B.

## Question and exact boundary

Let S(w) be the candidate node/time positives supported by compatible world w,
and Q the declared survey menu. If w is the generating world, even observing
every possible positive in S(w) intersect Q leaves exactly the worlds v for
which S(w) intersect Q is a subset of S(v).

Thus a unique support signature is insufficient for identification from positives:
a world with a strict superset of support cannot be excluded by these observations.
This is an information ceiling. Reachability does not guarantee occupancy or
detection, so real surveys can supply fewer positives and leave more worlds.

## Fixed cases

| Case | Information at the positive ceiling |
| --- | --- |
| Disjoint B-only / C-only worlds | One distinguishing positive identifies either world. |
| Nested B-only / B-and-C worlds | C identifies the broad world; B cannot identify the narrow world. |
| Different edge weights, identical support | Both worlds survive all available positive evidence. |
| Distinct worlds, survey restricted to unsupported X | No admissible positive information is available; both survive. |
| Generating X-world omitted from B-only / C-only universe | Observing X falsifies the declared universe. |
| Generating B-and-X world omitted, survey restricted to B | B leaves only the wrong B-only world: uniqueness does not certify truth. |

The runner enumerates every subset of available generating positives for every
declared truth in each case, including the empty subset. A hand-declared support
oracle checks reconstruction independently of the propagation implementation.
Every candidate's positive-survey partition is checked against that oracle.
No non-detection is converted into an absence constraint. All worlds begin
compatible with a shared positive at A,t0; each has one transition to t1.

The six cases contain ten generating-world scenarios and twenty positive subsets.

Run from the repository root with the local source on PYTHONPATH:

```text
python benchmarks/positive_identifiability_known_truth.py
python -m pytest tests/test_positive_identifiability_known_truth.py tests/test_temporal_survey.py tests/test_temporal_reconstruction.py
```

The JSON report includes world fingerprints, all-positive survivors, and the
minimum positive count for exact truth identification (null if impossible).
The minimum is exhaustive for these tiny menus, not a scalable survey optimizer
or an expected information-gain score.

## Development consequence

Report positive-only identification limits before interpreting a survey ranking.
Additional positive sites cannot distinguish equal-support worlds or eliminate
a support superset. Testing independent directional evidence or a justified
detection/absence model is a different observation contract. The present result
does not establish empirical accuracy, historical truth, or predictive benefit.

## Independent directional evidence: boundary extension

`benchmarks/directional_identifiability_boundary.py` exercises the existing
qualitative directional-evidence module without changing the exact temporal-world
engine. Five candidate operators share A-to-B occurrence support. A separately
declared C/X order tests one-way forward, weaker one-way forward, reverse,
symmetric, and no-direction candidates. Both order orientations are checked in
five fixed universes (ten scenarios), against analytic one-step status expectations.
The order is a synthetic input, not derived from occurrences or real movement data.

The opposed two-candidate universe leaves one candidate not contradicted.
Adding a same-direction weight variant prevents separation in the forward case.
Adding a symmetric or no-direction candidate leaves ambiguity or unresolved
evidence in either orientation. Having only one **supported** candidate therefore
does not imply having only one candidate **not contradicted**. Existing candidate
statuses stay fixed under universe expansion; the non-contradicted set can grow.
This is not the exact reachability engine's admissibility/monotonicity contract:
in particular, no directional support is unresolved under this existing API,
not proof of impossibility. No winner or truth-identification field is introduced.

Run `python benchmarks/directional_identifiability_boundary.py` and
`python -m pytest tests/test_directional_identifiability_boundary.py
tests/test_directional_evidence_discrimination.py` with local source on PYTHONPATH.
The next scientific gate is an independently justified observation contract
specifying which measurement can exclude symmetric or unresolved candidates;
these qualitative labels alone cannot supply that contract. The frozen empirical
programme and its claim ceiling remain unchanged.

## Explicit detection contract: exact versus statistical exclusion

`benchmarks/detection_identifiability_boundary.py` adds a separate observation
model, not an absence adapter to the temporal reachability engine. Two stipulated
worlds differ in actual occupancy at a surveyed site. Occupancy is constant across
visits, visits are independent, and false positives are excluded by declaration.
These are synthetic assumptions, not conclusions from reachability.

The fixed occupied-site detection probabilities are 1, 1/2, and 0. For each,
every binary history of one, two, and three visits is enumerated (42 histories).
Exact rational likelihoods are checked against a separate support oracle and
must sum to one per world. No numerical threshold or posterior is used.

- Perfect detection: a non-detection excludes the stipulated occupied world.
  Mixed detection histories falsify this constant-occupancy, perfect-detection
  contract; they are not silently repaired.
- Imperfect detection: three non-detections have probability 1/8 under occupancy,
  so that world remains exactly compatible. Any finite run of non-detections has
  positive probability when detection probability is strictly between zero and
  one. Statistical rejection would require a separately fixed error contract.
- Zero detection probability: non-detections distinguish nothing; a positive
  observation falsifies both stipulated models.

Even perfect detection cannot turn *reachable* into *occupied*. Accordingly no
negative-observation API is added to the existing reachability core. A real-data
extension requires independently justified occupancy/persistence, detection,
false-positive, and visit-dependence assumptions before exclusions are allowed.
This completes the small synthetic boundary study, not an empirical validation.

Run `python benchmarks/detection_identifiability_boundary.py` and
`python -m pytest tests/test_detection_identifiability_boundary.py`.
