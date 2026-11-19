# Glanville minimum required relaxation — exploratory real-source result v2

## Source/CI state — 2026-11-19

**Exploratory and source-conditioned, NOT an independently confirmed colonization rate or EOG-WF endpoint.**

- **GitHub Actions:** [run 44483614057](https://github.com/zuizui0223/eog/actions/runs/44483614057)
- Run conclusion: `success`; dedicated v2 guard tests passed.
- Original failed v1 source run: [44482618167](https://github.com/zuizui0223/eog/actions/runs/44482618167), `STOP_CRS_NUMERICAL_CONCORDANCE_FAILED` with zero ecological result panels. **Preserved; not overwritten.**
- Metadata-only coordinate diagnosis: [44483096052](https://github.com/zuizui0223/eog/actions/runs/44483096052).
- Final source-gated status: `EXPLORATORY_CONDITIONAL_EMPIRICAL_RELAXATION_ESTIMATED`; 12/12 year×source-policy panels.
- Full aggregate source result is saved in Actions artifact `glanville-unit-corrected-minrelax-v2` (ID `14509468111`, retention 30d); result JSON fingerprint without its self-hash: `e5e4da4088aef5ca9337f913e644d324190a230934ac0dcf2bbc360fb09dd68a`.
- Parent exploratory estimand frozen in `validation/glanville_minrelax_empirical_v1/protocol_v1.json`; **only** 2019 patch-network coordinate x/y unit conversion frozen in `validation/glanville_minrelax_empirical_unitfix_v2/protocol_v2.json`.
- No previous ecological response panels were successfully scored prior to v2. No EOG-WF predictive denominator or public API changed.

## Pinned publisher archives and repair provenance

| Source | Digest (SHA-256, exact publisher archive) | Scientific scope |
| --- | --- | --- |
| Schulz et al. (2019), `ECOG-04799.zip` (Zenodo 4987060) | `c70f43544f61e7273afebfa42ed1d488c3b945efe4d5c68e6557030087ee7fd9` | Patch-year survey; host-plant scores; patch network |
| Fountain et al. (2017), `supplementary-data-COLONY2.tar.gz` (Zenodo 5010194) | `90df549e41ae2c069758d3d6872fdc144cef5fcd32fb868af3d2e8cd408a8459` | Individual/year, putative full-sib families, genotype patch centroid |

2019 `README.rst` explicitly states EPSG:3067 patch coordinates are **in kilometers**. 2017 `Patch Centroid_X/Y (ETRS-TM35FIN)` are in meters. After multiplication of only 2019 patch centroids by 1000, 308 common coordinate patches have median residual **0.00285 m** and q95 **3.6231 m**. No tolerance, source definition, habitat covariate, analysis year or target selection was changed.

Input grain: 74,065 annual survey rows, 4,656 mapped patch coordinates, 8,322 genotype individual×year keys and 8,322 family keys. All **8,322/8,322** genotype–family individual/year keys match. This makes schema/coordinates comparable **but does not certify source direction**.

## Precisely what was estimated

For each calendar year `t=2007..2012`, define a **recorded-positive transition target** as a patch with positive numerical population at `t` and recorded numerical zero at `t-1`, with both pre-target-year host scores, complete coordinates and source-candidate eligibility.

A declared source set `S` consists of eligible recorded-positive patch(es) in `t−1` (primary), or in `t−1` or `t−2` (sensitivity). In the two-year policy a same-patch source at t−2 followed by a t−1 recorded zero is allowed; this may represent *recurrence or missed detection*, NOT measured emigration. The environment transition between source and target is a predeclared max absolute difference on **ordinal** `plantago` and `veronica` scores. `delta=0,1,2,3` is the fixed host-gap tolerance.

For each target `i`, the minimum Euclidean projected distance to a candidate source `j` satisfying host-gap `<=delta` is computed. The annual radius is
```
r*(delta,t) = max_{target i in recorded-positive transitions at t}
              min_{source j in S(t), host_gap(i,j)<=delta} distance_km(i,j).
```
If any target has no eligible source for the declared gap threshold, `r*` is **non-estimable** (NOT biologically impossible); such rows are retained. Taking the non-dominated (`r*,delta`) pairs yields the conditional **geography × host-environment frontier**.

This is a *one-hop fixed-source-eligibility benchmark*, not the full multi-hop EOG dynamic process, an actual dispersal kernel, a causal relaxation or a historical migration trajectory. Distances are the **maximum nearest-compatible-source requirement** over observed transitions, sensitive to a small number of extreme records; they are **not the minimum or maximum dispersal distance ever made by butterflies**.

## Primary results — previous-year recorded-positive sources

| Year | Candidate sources | Recorded-positive transition targets | `r*(delta=0)` km | `r*(delta=1)` km | `r*(delta=2)` km | `r*(delta=3)` km |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2007 | 458 | 349 | non-estimable (11 unmatched targets) | **9.2617** | 9.2617 | **4.4426** |
| 2008 | 695 | 157 | 22.4825 | **4.6078** | 4.6078 | **2.6796** |
| 2009 | 508 | 285 | non-estimable (5 unmatched) | **9.7447** | 5.9531 | **5.9531** |
| 2010 | 587 | 102 | 18.3985 | **7.6746** | 3.3101 | **3.3101** |
| 2011 | 298 | 521 | non-estimable (11 unmatched) | **11.2827** | 8.0498 | **8.0498** |
| 2012 | 764 | 400 | non-estimable (3 unmatched) | **7.8742** | 5.1150 | **5.1150** |

`delta=3` is the predeclared host-unrestricted nearest-source comparator (bounded original ordinal scale). `delta=1` raises the required geographic step in all six years **by construction of a nested set of permitted sources**; the *magnitudes* are empirical geometry conditional on the source roster. There is **no permutation test or confidence interval** establishing an ecological driver.

Some strict `delta=0` comparisons are not merely large values; they are **undefined** because specified source classes are absent for one or more targets. The output correctly distinguishes those STOPs from finite radii.

## Source-policy sensitivity — adding t−2 positive-source candidates

| Year | t−1 sources: `r*(delta=3)` km | t−1 or t−2 sources: `r*(delta=3)` km | Reduction (km) |
| --- | ---: | ---: | ---: |
| 2007 | 4.4426 | 2.6813 | 1.7613 |
| 2008 | 2.6796 | 2.6796 | 0 |
| 2009 | 5.9531 | 3.8175 | 2.1357 |
| 2010 | 3.3101 | 3.3101 | 0 |
| 2011 | 8.0498 | 4.1820 | 3.8677 |
| 2012 | 5.1150 | 3.7788 | 1.3362 |

Four of six years have a smaller conditional maximum when the candidate-source history is extended by one year; two are unchanged. This is an *assumption sensitivity*, not evidence for two-year dispersal or true source locations.

## Reconstructed family spatial evidence is a **different estimand**

Across the 2007–2012 source/year subset, `3077` reconstructed `(year, region, family)` groups have coordinate-linked members. **263** groups span 2+ patches and generate **322** undirected unique cross-patch pair comparisons. Cross-patch separation median **0.3818 km**, q90 **2.2275 km**, maximum **11.0045 km**. These are **distances between sampled reconstructed siblings**, not natal movement distances, reliable parental locations, founder origins, or a validation target for `r*`. Differences between this distribution and `r*` do NOT confirm long-distance dispersal or reveal causal drivers.

## Claims supported, not supported, and next independent test

**Supported within declared observation/analysis contract:**
1. The existing finite Pareto-relaxation concept can be instantiated using source-checked multi-year ecological records and independently aligned genetic patch coordinates.
2. For a given target roster and declared candidate sources, the joint minimum geographic-step requirement depends on the allowed host-score difference; multiple non-dominated tradeoff points exist.
3. Source-year eligibility materially affects inferred requirements in some years.
4. Family reconstruction has geographically dispersed same-year sampled groups, but no evidence of direction in this readout.

**Not supported:**
- Genetic or realized dispersal distance has been inferred from family pair distances.
- Observed zero means true absence, or zero-to-positive is certified colonization.
- Any single candidate source is identified as the actual founder.
- Host scores are independently calibrated niche tolerances.
- An independent **barrier** dimension was quantified: `NOT_IDENTIFIABLE_FROM_THIS_SOURCE`.
- This historical exploratory use demonstrates EOG predictive superiority over existing SDM, dispersal or occupancy models.
- The result contributes a new EOG-WF prospectively fresh empirical endpoint.

**Next valid independent analysis:** determine whether a truly *held-out* source/target clock and independently recorded source-to-target colonization or mark-recapture/genetic parentage can validate these **conditional minimum assumption bounds** without reusing already explored outcomes. Keep the frozen EOG-WF original 3 scored / 31 scientific STOP / 3 administrative exclusions unchanged.

To reproduce only with the same source versions and science definition (not as a fresh independent validation):

```bash
python -m pytest -q tests/test_glanville_minrelax_empirical_unitfix_v2.py
python benchmarks/glanville_minrelax_empirical_unitfix_v2.py \
  --parent-protocol validation/glanville_minrelax_empirical_v1/protocol_v1.json \
  --unit-protocol validation/glanville_minrelax_empirical_unitfix_v2/protocol_v2.json \
  --output results/glanville_minrelax_empirical_unitfix_v2/result.json
```
