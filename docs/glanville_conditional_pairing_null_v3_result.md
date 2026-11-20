# A conditional pairing signal, not yet evidence of habitat-based dispersal choice

## Status and scope — 2026-11-20

**Post-exposure, conditional, historical analysis** of genetically *inferred* (not directly observed) origins in Åland Glanville fritillary butterflies. Same two publisher-authenticated original sources as merged PRs #707/#708. The original EOG-WF prospective evaluation is **not reopened**: 3 scored / 31 scientific STOP / 3 administrative exclusions.

- Frozen *before v3 survey reacquisition/scoring*: `validation/glanville_conditional_pairing_null_v3/protocol_v3.json`.
- Published 2022 genetic family-assignment file `fullsibfamLevelData.csv` (Dryad `10.5061/dryad.7h44j0zws`): SHA256 `140e5361f9bced20a434bfee01bae6ce7c925e028718cdb9c6fd8aa635cc912a`.
- 2019 Schulz annual survey/network ZIP (Zenodo 4987060): SHA256 `c70f43544f61e7273afebfa42ed1d488c3b945efe4d5c68e6557030087ee7fd9`.
- Source-only encrypted acquisition: [GitHub Actions run 44679961668](https://github.com/zuizui0223/eog/actions/runs/44679961668), succeeded; ciphertext-only artifact ID `14603368669`. Private key never entered GitHub. The source file itself was authenticated under AES-GCM in the local sandbox, no individual site/year data exported.
- Full local science receipt fingerprint without its self-hash: `15101996c38e6831715ae07370642335bd157a0df99faf2bf06dacca18e1385b`.
- Original parent 2008–2012 source/target rosters, **163** eligible genetic assignment rows / **100** recorded 0→positive target patch-years / **157** distinct inferred full-sib family IDs, 2019 two-host scores, and all eight previous EOG-vs-specific-origin host/radius comparisons were rechecked. An **independent pandas join** and alternate-seed **699-permutation** implementation reproduced observed statistics and near-identical null means.

## Falsifiable question, conditional null, and why it is necessary

EOG's prior result asks whether **at least one** t−1 source is compatible with geography and plant environment; it does not infer *which* source was the biological origin. DiLeo et al. (2022; DOI `10.1098/rspb.2022.0322`) assigned parts of genetically reconstructed full-sib families to sources among their previous-year **sampled** reference populations using GENECLASS2, retaining score-100 assignments. The uploaded family table lacks per-assignment scores. This is a genetically assigned-origin source, **not a measured natal location**.

To test whether genetic source→destination pairs show a nontrivial tendency toward spatial/environmental matching *beyond the observed availability of source labels*, the v3 protocol declares exactly one **year-conditional source-label recombination null**:

1. Preserve all 163 selected genetically inferred assignment rows, their destinations, arrival years, target-year family record multiplicities and t−1 year.
2. Within each of the **five source years** independently, uniformly shuffle the *complete empirical multiset* of source-patch labels among these assignment rows, **preserving the exact observed source frequency for each year**. Reject a hypothetical source=destination pair. This preserves only the **assigned-origin sample's** source-label counts, NOT all biologically available source patches or the full GENECLASS2 reference set.
3. For each shuffled source/target pair, recompute patch-centroid Euclidean distance and max absolute ordinal `Plantago`/`Veronica` host-score difference using the **same t−1 survey scores** as EOG. Use a **target-patch-year-equal** statistic: for each destination patch-year, median over its family/destination rows; average those 100 medians. Distance statistic uses `log(1+km)`. Host statistic is ordinal gap on 0–3.
4. Repeat **1,999 successful** permutations using fixed seed `20261120`, compare the observed statistic to the one-sided lower-tail conditional randomization distribution. No thresholds were tuned after scoring.

## Primary results

| Target-equal statistic | Observed genetic assignment | Year-conditional source-label null mean | Null 2.5–97.5% interval | Conditional one-sided tail p |
|---|---:|---:|---:|---:|
| Mean within-target median **log(1 + distance in km)** | **0.8552** | 1.5806 | 1.4914–1.6662 | **0.0005** |
| Mean within-target median **two-host ordinal gap** | **1.320** | 1.459 | 1.3198–1.5953 | **0.030** |

The source/destination **distance statistic was lower than the year-conditional null in all 5/5 years**. The host-gap statistic was lower in only 3/5 years and higher in 2/5, despite the pooled nominal one-sided tail probability. Exactly 9,995 year-stratified permutation proposals for the 1,999 complete draws; all were accepted because t−1 recorded-positive source patches and t−1 recorded-zero destination patches are disjoint by the original eligibility rule.

**The geographic pairing signal is stronger and more consistent than the naive host gap signal.** The p-values are **conditional randomization values of an already selected, genetically assigned reference sample**; they are NOT field-sampling p-values establishing habitat selection, evolutionary drivers or natural dispersal probability. Family and patch-year dependence as well as genetic assignment algorithm selection remain.

## Geography-matched host comparison: key limitation

Host scores are spatially autocorrelated. A global source-label shuffle makes sources farther away, potentially producing larger environmental contrasts without any independent preference for host similarity. The **predeclared separate sensitivity** therefore forms local-distance-matched pools **within each source year**:

- Candidate source sites are (A) the set of distinct sites appearing as inferred source labels anywhere in all **799** original family/destination rows in the year, restricted to t−1 recorded-positive, host-complete and mapped sites; or (B) the broader entire EOG t−1 recorded-positive host-complete source roster.
- Match candidate patch→target separation within `max(0.5 km, 0.25 × observed assigned distance)`; exclude the target itself; require at least **3 distinct eligible source sites**. **Never widen the caliper** in response to results.
- Compare the assigned source's `Plantago`/`Veronica` gap with the **mean host gap of same-distance candidate sources**. Weight alternative source sites uniformly or by **t−1 recorded-positive population**, capped at the year-specific 90th percentile *within that source roster*. Survey population is only a sensitivity weight, **not a direct estimate of sampling effort**.

| Distance-matched candidate roster | Eligible target patch-years | Mean assigned-source gap minus uniform candidate gap | Same difference, recorded-population weighted |
|---|---:|---:|---:|
| Genetically assigned-origin site roster (all 799 original records) | 76 | **+0.0556** | **+0.0286** |
| All EOG t−1 recorded-positive candidate sources | 85 | **+0.0681** | **+0.0459** |

For the genetically assigned-source roster, 127 of 163 rows had at least three matched source opportunities (median **6** candidates); under the broader EOG roster, 141 rows/85 targets qualified (median **7** candidates). Positive differences mean that genetically assigned origins are *slightly less host-similar* to the destinations than equally distant alternatives on this particular ordinal measure. **No evidence of additional host similarity after geographic matching is supported.** This descriptive result has **no p-value** and does not assert evidence of avoidance or repulsion either.

## Interpretation and next actual inferential obstacle

**Supported:** The genetic algorithm's inferred source→destination labels are more spatially paired than chance year-conditional recombination of those same assigned labels across recorded-positive-transition destinations. That is not merely EOG's nested-set tautology; it is an empirical difference in how already-inferred source labels are paired with destinations.

**Not supported:** Independent host-environment matching beyond distance; direct tracking of true natal dispersers; a dispersal kernel or source preference calibrated to all candidate populations; independent EOG predictive superiority. EOG's existential minimum and a particular inferred origin remain different estimands and should be kept distinct.

The next science-blocking input for interpreting *choice* rather than genetic *assignment* is the **complete year-specific GENECLASS2 sampled-reference source roster and assignment confidence/alternatives**, plus repeated-detection or tracked flight information. Within these historical source tables, a perfect genetic assignment confidence label for each CSV row is unavailable. Do not fit a causal source-selection model by treating assignment outputs as known ground-truth migrants.

Reproducible local-only script: `scripts/glanville_conditional_source_pairing_local_v3.py`. Original tables stay local; GitHub preserves only protocol, deterministic tests, summary, source fingerprints and caveated narrative.

**Original EOG-WF validation closure unchanged: 3 scored / 31 scientific STOP / 3 administrative exclusions.**
