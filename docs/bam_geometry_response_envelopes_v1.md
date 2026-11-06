# EOG × BAM: current geometry to partially identified response geometry

## Position
Original shared-reference EOG measures describe the geometry of realised G, not physiological A. The previous768-world work showed distinct A/B/M configurations share G; the1344-pair analysis measured geometry after a known constraint edit. This analysis asks: **when the generating configuration is unknown, do all configurations compatible with current G agree on the response direction?** It connects original geometry to the existing inverse-BAM framework. It does not claim generic partial identification is new or replace earlier manuscripts.

## Contract and measurement
Contract commit `a24b73faa98888ffae5e165c3cf5d6d614e2a501` predates the new scores. The12 landscapes and768 candidate worlds were already exposed; this is exploratory re-use, not independent confirmation. Ideal complete current presence/absence creates129 distinct G-fibres within landscapes.69 contain multiple A/B/M mask triples (632 world memberships). Parameter labels are not probabilities or independent biological replicates.

Use the existing idealised releases: remove A => B∩M, remove B => A∩M, remove M => A∩B. These are static logical probes, not literal climate, corridor or interaction interventions. Every conclusion is conditional on this finite candidate family and perfect current-map evidence.

One original median/MAD reference per landscape stays fixed. Primary target: change in positive-pair90th-percentile EOG span. Secondary targets: average centroid distance, planar convex-hull area (monotone extent control), separate geographic rook-component count. These are **full-census** summaries of every occupied cell. Cell number and placement changes are part of the target; do not mix the numbers with prior matched-size sampled contrasts.

For each fibre×release×target retain min/max change across ALL surviving worlds. Direction is identified only if every candidate agrees on negative/zero/positive at declared1e-10 tolerance. These envelopes are not confidence intervals, probabilities or guarantees against omitted mechanisms.

## Verified results
| Released constraint | Exact released map identified | Span direction identified | Direction known despite map ambiguity |
|---|---:|---:|---:|
| A |110/129|119/129|9|
| B |96/129|124/129|28|
| M |95/129|121/129|26|

All three span directions are identified in115/129 fibres (604/768 world memberships), including55/69 A/B/M-mask-ambiguous fibres. Direction-known/map-unknown cases all involve nonzero changes: A9 increases; B27 increases plus1 decrease; M25 increases plus1 decrease. Many other identified cases are no-change (85 A,64 B,59 M); aggregate rates do not imply uniformly useful intervention or natural ecological prevalence.

## Where abstention matters
Five M-release fibres retain **opposite span directions**. Lexicographically first example: S04_7x3_closed, G115586,7 occupied cells,24 compatible parameter worlds,3 released maps. Current span1.57232665; change ranges−0.20417290 to+0.51946102 (approximately−13% to+33%). All candidates increase convex-hull area. A pairwise-distance quantile can decrease while support extent increases; these are different estimands.

The first map-ambiguous/direction-known example is B release, S00_7x3_closed/G115073: two released maps both reduce span while increasing hull area. Example selection was lexicographically fixed rather than chosen for strongest effects.

## Evidence tied to the question
Ideal **complete B-mask** evidence raises uniformly identified M-response directions from121 to126/129 fibres. Of the5 opposite-sign fibres, **4/5** become uniformly direction-identified. The fifth (S07_9x5_gap/G2138792820255) becomes identified for4/8 parameter worlds but remains ambiguous for the other4; observing A as well resolves it. Complete M evidence alone does not uniformly resolve any of these5 conflicts. The net gain of5 current-G fibres includes another initially zero-versus-change ambiguity and must not be confused with resolving all5 opposite-sign fibres.

For B-release response, complete A information identifies direction in all129 fibres. These are finite-model diagnostic results, not claims that one field sample of B suffices, that B is always optimal to measure, or that the additional masks are empirically observed.

## Verified reproduction
Six test-first unit tests cover hull degeneracy, scalar span, release algebra, opposite responses at identical G, target identity without map identity, and evidence contraction. Offline fixtures reproduced all768 archived current spans, centroid means and geographic counts to1e-12.

Canonical GitHub run42224332364 uses the original generator (blobab852b02bccdfb2f065717f89b482b7cf15778d3), checks every release against `axis_release_outcome` and every current span against `infer_comparative_geometry`. All6168 evidence-envelope inclusion checks passed and no hull-inclusion failure occurred. Artifact13504738461 was downloaded and all5 output files matched local results **byte-for-byte**; result fingerprint `bea5a189435961e4ef8501d8c0ddced3ae0c7818810667c5d97d807a3c34ac14`.

The initial draft misread the total5 extra identified fibres as5 opposite-sign resolutions; the row-level evidence audit corrected the prose to4/5 before merge. No outcome, metric, criterion or analysis code was changed.

## Relation to the real-data result
Charaxes shows average concentration and upper extent need not give the same signal after composition matching. It does not supply independent A/B/M or validate these synthetic release envelopes. Keep evidence roles separate: empirical geometric-description example versus known-truth target-identification test.

The completed method chain is **current geometry → compatible BAM worlds → geometric response envelope → target-relevant additional evidence**. It is not EOG predictive superiority, new causal field validation, or EOG-WF endpoint4.

Reproduce: `python benchmarks/bam_geometry_response_envelopes_v1.py --output-dir results`. Offline bundle: add `--fixture source_fixture.json`. All129 fibres,2304 world×release rows and direct-evidence comparisons are retained.
