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
