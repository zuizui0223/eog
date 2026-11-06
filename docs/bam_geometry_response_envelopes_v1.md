# EOG × BAM: current geometry to partially identified response geometry

## Position
The original shared-reference EOG measures describe the geometry of realised G, not physiological A. The previous 768-world work showed many distinct A/B/M configurations share G; the 1344-pair work measured how geometry differs after a known constraint edit. This analysis asks a different, operational question: **when the generating configuration is unknown, do all configurations compatible with current G agree on the response direction?** This connects original geometry to the existing inverse-BAM framework. It neither discovers generic partial identification anew nor replaces previous manuscript results.

## Contract and measurement
Contract commit `a24b73faa98888ffae5e165c3cf5d6d614e2a501` predates new scores. The12 landscapes and768 candidate worlds are already exposed; this is exploratory re-use, not independent confirmation. Perfect current presence/absence groups worlds into129 distinct G-fibres within landscapes.69 fibres contain multiple distinct A/B/M mask triples (632 model-world memberships). Parameter labels are not treated as probabilities.

Use original idealised releases: remove A => B∩M, remove B => A∩M, remove M => A∩B. These are static logical probes, not literal climate, corridor or interaction interventions. Every result is conditional on this finite candidate family and perfect current map evidence.

One original median/MAD reference per landscape is held fixed. Primary target is change in positive-pair90th-percentile EOG span. Secondary targets: average centroid distance, planar convex-hull area (monotone extent control), and geographic rook-component count. These are **full-census** summaries of every occupied cell; cell number/placement changes are part of the target. Do not mix these numbers with the prior matched-size sampled contrasts.

For every fibre×axis×target, retain minimum/maximum change across all surviving worlds. Direction is identified only when every candidate agrees on negative/zero/positive at a declared1e-10 numerical tolerance. A min/max envelope is not a confidence interval, predictive probability or guarantee against omitted worlds.

## Local descriptive result (pending independent canonical CI replay)
| Released constraint | Exact released map identified | Span direction identified | Direction known despite map ambiguity |
|---|---:|---:|---:|
| A |110/129|119/129|9|
| B |96/129|124/129|28|
| M |95/129|121/129|26|

All three span directions are identified in115/129 fibres (604/768 world memberships). This includes55/69 A/B/M-mask-ambiguous fibres; it is not merely recovery of known mechanisms. Direction-known/map-unknown cases concern real nonzero changes: A9 increases; B27 increases plus1 decrease; M25 increases plus1 decrease. Nonetheless many other direction-known cases are predicted no-change (85 A,64 B,59 M); do not present aggregate identification rates as uniformly useful interventions or ecological frequencies.

## Where abstention matters
Five M-release fibres retain **opposite span directions**, not just different magnitudes. Lexicographically first example: S04_7x3_closed, G mask115586,7 currently occupied cells,24 compatible parameter worlds and3 possible released maps. Span=1.57232665; change ranges−0.20417290 to+0.51946102 (approximately−13% to+33%). Every candidate increases convex-hull area. Thus uncertainty about a pairwise-distance quantile does not mean uncertainty about support-set expansion. This is why span, average concentration and extent must remain distinct.

The lexicographically first map-ambiguous/direction-known example instead has B release, S00_7x3_closed/G115073. Two possible released maps both reduce span while increasing hull area. We retain this result rather than choosing an aesthetically easier example.

## Evidence tied to the question
Adding an ideal **complete B mask** raises M-release span-direction identification from121 to126/129 fibres uniformly over its possible observed values. All5 opposite-sign fibres are resolved in this finite panel; complete M information does not uniformly resolve those five. B-release uncertainty is resolved in all129 fibres by complete A information. These are model-specific diagnostic results, not a universal claim that one field observation of B suffices or that measuring B is always optimal.

## Verification and scope
Six test-first unit tests check hull degeneracy, scalar span parity, release algebra, opposite responses at identical current G, target identity without map identity, and contraction under valid evidence. Offline environmental fixtures matched all768 archived current spans, centroid means and geographic counts to1e-12. Canonical CI uses the unchanged original generator and verifies every release against `axis_release_outcome` and every current span against `infer_comparative_geometry`. All6168 tested evidence/target envelopes contract or stay unchanged; no hull-inclusion failures.

Keep the Charaxes real-data result separate: it shows concentration and upper extent can respond differently under survey-composition controls, but it has no independently observed A/B/M and cannot validate these synthetic release envelopes. The scientific contribution here is a usable **current geometry → compatible BAM worlds → geometric response envelope → target-relevant additional evidence** workflow, not EOG predictive superiority, new causal field evidence, or a fourth EOG-WF endpoint.

Reproduce: `python benchmarks/bam_geometry_response_envelopes_v1.py --output-dir results`. Local offline bundle additionally supports `--fixture source_fixture.json`. All129 fibres,2304 world×release rows, and direct-evidence comparisons are retained.
