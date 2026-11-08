# eMammal deer camera traps: real repeated detection, exploratory only

## Why this source

The NEON DP1.10072.001 source retrieval was attempted and
returned HTTP403 without authentication. Rather than continue
to treat synthetic BAM worlds as empirical validation, we
identified a publicly readable **real repeated-detection history**
at https://github.com/BrentPease1/single-season-occupancy.

The source README states that the deer camera-trap detection
history was originally downloaded from eMammal, with **87
sites**, approximately three weeks per site, daily intervals
as repeated occasions. The fixed CSV has **22 occasion columns**
(o1...o22), entries 0, 1 and NA. A 0 means no deer detected
during that recorded daily interval; **NA means an unavailable
occasion, not a nondetection**. The source does not provide
verified daily effort, coordinates or direct A/B/M measures.

Importantly, the same repository's `detection_covariates.csv`
contains **simulated detection covariates**; these are explicitly
excluded from this real-data biological analysis.

## Pre-score model

Source commit `f65b220d1c84240fa81cb457bf27522424fe1666`
and contract commit
`4c7d7ada3c527f2da541ab10609dbe4839ab14b5`.

A constant single-season occupancy/detection model estimates
site occupancy probability ψ and daily detection probability p
with no false positives. For n observed occasions and k
detections at a site:

- If k>0: likelihood ψ × p^k × (1-p)^(n-k).
- If k=0: likelihood (1-ψ) + ψ × (1-p)^n.

NA occasions are omitted from n, never imputed to zero.
Optimize both probabilities by multistart bounded maximum
likelihood. Report naïve site detection proportion separately
from latent occupancy ψ. Repeat at 7,14 and 22 occasion
columns as predeclared sensitivity, without selecting the
best-looking result.

## Limitations and interpretation

This is **real observation data**, but not a fully independent
field replication of EOG×BAM. The camera's daily detections
may be temporally correlated, deer may move into/out of the
detection zone, and no species-specific closure or consistent
daily effort has been verified. Consequently ψ is a
**model-dependent site-use/occupancy parameter**, not proof of
resident deer presence or independent abundance.

No direct abiotic A, biotic B or dispersal M constraints
are measured. No EOG environmental feature space or geometric
response is estimated in this module. The purpose is to
replace purely hypothetical detection-p values with a
transparent empirical *example of how detection likelihood
can be estimated* before attempting any EOG causal claims.

## Reproduce

```bash
python -m pytest -q tests/test_emammal_deer_detection_v1.py
curl -fL https://raw.githubusercontent.com/BrentPease1/single-season-occupancy/f65b220d1c84240fa81cb457bf27522424fe1666/deer_detection_history.csv -o deer_detection_history.csv
python benchmarks/emammal_deer_detection_v1.py --source deer_detection_history.csv --output result.json
```

The CI archives the exact analysis result with source SHA256,
counts of observed/missing/detected site-days, three model
fits and a deterministic fingerprint. No data are fabricated,
and no fourth EOG-WF endpoint is added.

## Canonical real-source results

[GitHub Actions run 42457480754](https://github.com/zuizui0223/eog/actions/runs/42457480754)
successfully downloaded the original source-pinned CSV, verified
the 87-site schema, ran the missingness-aware model and archived
the result. Source SHA-256:
`bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34`.

Across all 22 daily columns there are 1,699 observed site-days,
215 missing site-days, 471 detected site-days, 62 ever-detected
sites and 25 sites with no detections. The full source has 87 sites.

| Window | Valid site-days | Sites with >=1 detection | MLE daily p | MLE ψ |
|---|---:|---:|---:|---:|
| Days 1–7 | 604 | 54 | 0.441326 | 0.634123 |
| Days 1–14 | 1,188 | 58 | 0.413972 | 0.671668 |
| Days 1–22 | 1,699 | 62 | 0.367906 | 0.720140 |

These are **maximum likelihood estimates under the declared
constant-p, constant-ψ single-season model**, not empirically
verified truth. Changing the observation window changes both
available detection occasions and the effective temporal closure
assumption. The trend in p across windows must not be interpreted
as a proven biological decline in detectability.

Canonical result fingerprint:
`17c62ce1a00dc14d366e6e98fcdca452a8495eb313c41b96c58b83087e1aff72`.
Complete source and artifact SHA are recorded in
`validation/emammal_deer_detection_v1/result_receipt.json`.
