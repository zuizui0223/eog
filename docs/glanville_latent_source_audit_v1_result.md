# Glanville recorded-zero source ambiguity: audited exploratory result

## Receipt and validation boundary

- Branch: PR #701, scientific sensitivity after prior EOG results were exposed; NOT a new EOG-WF endpoint.
- Frozen original protocol: validation/glanville_latent_source_audit_v1/protocol_v1.json.
- First source run 44513808990 scientifically STOPped on incorrectly stated matrix cardinality (48). This remains in the record.
- Erratum: validation/glanville_latent_source_audit_v1/protocol_erratum_v1_1.json retains the original protocol; the declared 6 years × 2 ordinal host gates × 2 radii × 2 recorded-zero pools × 2 same-site policies yield **96**, not 48, panels. No biological parameter changed.
- Source run 44514892720 generated a scientific result status EXPLORATORY_LATENT_SOURCE_COMPATIBILITY_AUDIT_PASSED, 96 panels, all invariants and 48 prior strict-result cells verified. The CI wrapper still failed because it asserted the obsolete count of 48; the wrapper was corrected in subsequent commit.
- Full original science receipt: [Actions run 44514892720](https://github.com/zuizui0223/eog/actions/runs/44514892720), artifact ID 14526041364; SHA256 of full JSON payload without its self-hash field: 1329713b58fc8dc9103ae9a7b18c3d5536b7db90b8070f6d1f65f18164a8e017 (independently recomputed from downloaded bytes).
- Durable aggregate: validation/glanville_latent_source_audit_v1/frozen_aggregate_summary_v1.json (only counts, no patch IDs, coordinates, occupancy histories or genotypes).

## What was estimated

Target = original 2007–2012 positive in year t following a recorded zero in t−1, valid hosts and coordinates. A fixed t−1 recorded-positive source can explain a target if the one-hop Euclidean patch separation is at most r in {2,5} km and the maximum absolute ordinal Plantago/Veronica host-score gap is at most delta in {1,3}. This is conditional landscape geometry and **not a realized movement history**.

To assess the possibility of unobserved source occupancy, consider two strictly hypothetical t−1 recorded-zero source pools: (a) all eligible recorded zeros, (b) their subset with a positive t−2 record. The main comparison excludes same-patch candidate sources to avoid classifying within-patch persistence as dispersal. Exact enumeration finds the best single hidden source; a greedy algorithm finds a FEASIBLE (not globally optimal) additional selection of five or ten candidate sources **per year**, chosen using the already-known target locations. The all-candidate union is a mathematically optimistic upper bound, never an occupancy posterior.

## Across the six source years (1814 positive-transition targets)

| Radius / host gap | Recorded-positive sources only | Adding 10/year from all t−1 zero records | Adding 10/year from t−2 positive subset | All t−2 positive candidates (optimistic union) |
|---|---:|---:|---:|---:|
| 2 km / delta=3 | 1708 | 1800 | 1756 | 1765 |
| 2 km / delta=1 | 1630 | 1747 | 1698 | 1723 |
| 5 km / delta=3 | 1807 | 1814 | 1814 | 1814 |
| 5 km / delta=1 | 1777 | 1812 | 1803 | 1803 |

At 2 km and delta=3, the original observed-positive sources leave **106** targets unexplained. Ten retrospectively selected recorded-zero sources per year from all eligible zeros can geometrically cover another **92**, leaving **14**. Restricting hypothetical candidates to patches positive at t−2 and zero at t−1 still covers another **48**, leaving **58**. These percentages are NOT estimated missed-detection rates.

At a wider 5 km threshold, the original sources already cover **1807/1814** targets for delta=3, so at most seven targets remain outside the local source explanation in the 6-year aggregate. With those seven already known, five hypothetical candidate sources per year suffice in the declared geometry. This is not direct biological support for a 5 km dispersal kernel.

## Why this does NOT choose between competing processes

One recorded-zero site could have been truly empty, could have hosted a small missed population, or could have been colonized between observation windows. The annual survey table lacks repeat-visit detection records sufficient to estimate patch-specific detection. The cited Ojanen et al. (2013; DOI 10.1002/ece3.733) nest-level detection evidence and retrospective control checks cannot be turned into site-specific false-negative probabilities; none were used as weights.

Source candidate placement is optimized against the SAME observed target records. Thus the large apparent explanatory gain is an upper-bound **identifiability diagnostic**, not cross-validated accuracy or independent evidence of undetected source occupancy. The genotype full-sib location information does not independently fix source direction. The broad all-zero source pool (roughly 3000 candidate patches/year) is an exceptionally permissive scenario, not an estimated ecological truth.

## Required next independent data

To distinguish failed detection from longer-range dispersal, obtain independently recorded repeat-visit detection histories at patch-year resolution and/or verifiable time-ordered mark–recapture or parental-source assignments. Predeclare these constraints before checking held-out transitions. Do not reopen EOG-WF's closed 3-scored/31-scientific-STOP/3-administrative-exclusion validation program.
