# Arctic tern marked-departure MRR: rounded-colony coincidence and historical-source catalogue sensitivity v2

**Status:** protocol locked, follow-up **after** observing the 198 source-agnostic R=20km false-assurance events in [source-locked known-departure v1](tern_known_origin_geographic_minrelax_v1.md). This is **not a new independent biological study** or a new EOG-WF scored endpoint.

## Main question

The original v1 result found **10/87 adult breeding** and **188/491 natal** 1976+ derived movement events for which a documented origin required over 20km but *some* historical source from 115 rounded departure coordinates implied at most 20km, totalling **198/224 source-infeasible events**. However, both groups' *nearest source* radius had median **0 km**, because a destination can exactly coincide (under 0.01° rounding) with an earlier departure coordinate.

**What fraction of the 198 events depends on this co-location artefact or arbitrary source-roster breadth?**

We answer this by recomputing the **same** source-locked v1 estimand on all original events, with all possible cataloguing assumptions set in a new v2 [post-exposure frozen protocol](../validation/tern_source_catalogue_rounding_sensitivity_v2/protocol_v2.json) *before v2 original event rows are opened*. We do not call this a prospective or blinded confirmation, because original publication results and v1 analysis have already been exposed.

## Source, denominator, and original result cannot be changed

- Official Dryad [Li et al. 2026](https://doi.org/10.5061/dryad.x69p8czxh), version **466530**. SHA256/bytes for all five original published files must match the unmodified [publisher manifest](../validation/tern_published_departure_source_gate_v1/frozen_metadata_summary_v1.json).
- The original [v1 benchmark](../benchmarks/tern_known_origin_geographic_minrelax_v1.py) is imported **without changing its API** and called on the same original parsed event tables before v2 is permitted to continue. Mandatory parent invariants: **1,090/1,090** original distance comparisons, **115** unique earlier rounded departure positions, **87 adult + 491 natal** event rows, known source false-assurance counts **10 adult + 188 natal at 20km**, rounding-margin counts **9 + 171**. A mismatch means **STOP_PARENT_RESULT_DISAGREEMENT**.
- The actual published marked departure source is always included in the possible-source set. Each alternative catalogue can only *add* candidate departures recorded as origin coordinates in the appropriate historical event-year slice; **never original arrival coordinates**.
- Latitude/longitude remain at published **0.01° rounding**, geographic distance is the original haversine radius, and 5 / **20 primary** / 50 / 100 km thresholds and conservative ±2-km margin are unchanged. All 578 original 1976+ event rows are retained as **event records, not unique animals**.

## The ten prespecified source-existence sensitivity conditions

| Scenario | Earlier source roster / geometric restriction | Why it matters |
| --- | --- | --- |
| `v1_exact_baseline` | All 115 departure coordinate points from event years ≤1975 | Exact comparison to frozen 198/224 |
| `exclude_exact_destination_coordinate` | Same roster; disallow candidate at precisely the rounded target coordinate | Removes the most literal 0-km alternative-source artefact |
| `source_nonlocal_2km` | Same roster; candidate must be ≥2 km from target | Separates sub-2-km coordinate rounding/local aliasing |
| `source_nonlocal_5km` | Same roster; candidate must be ≥5 km from target | Tests more substantial candidate separation |
| `source_nonlocal_10km` | Same roster; candidate must be ≥10 km from target | Stronger, artificial nonlocal candidate set; not an ecological exclusion rule |
| `older_departures_through_1970` | Both published types, departure events ≤1970 | Tests candidate availability with fewer historical records |
| `older_departures_through_1965` | Both published types, departure events ≤1965 | Tests earlier source-roster sparsity |
| `source_site_with_two_earlier_departure_events` | Departure coordinate repeated at least twice before 1976 | More event evidence at a point, **not two independent animals or verified source occupancy** |
| `same_published_event_table_source_only` | For each target type, only earlier departures of that same type | Tests source evidence type dependence, not independent species ecology |
| `no_alternative_source_negative_control` | Only the actual marked origin | Must have zero source-choice optimism, by definition |

The v2 interpretation cannot turn the arbitrary exclusions into proof of a physically unavailable colony. If a 0-km candidate is removed but another earlier source is 1km away, false assurance may still remain. **The count remaining after exclusion, rather than the count of all events with a coincident candidate, is the answer to the proposed artefact question.**

## Analysis and failure gates

For every scenario and every later event `i`, calculate:

```text
r_known(i) = d(own marked origin, published arrival)
r_possible(i;C) = min{r_known(i), d(c, published arrival) : c in C and c passes
                       the frozen target-relative distance restriction}
F_R = count{r_known > R and r_possible <= R}
F_R_conservative = count{r_known > R+2 and r_possible < R-2}
```

Source-specific `r_known` never changes. Each scenario returns adult and natal denominators, all four radii, source catalogue size, `F_R`, conservative `F_R`, rounded co-located source counts and number of zero minima. We additionally verify that stricter source exclusion and earlier-year catalogue cutoffs cannot increase source-agnostic feasibility; the empty-catalogue negative control must give zero false assurance.

The result must preserve **all scenarios**, including null/unfavorable outcomes and empty historical catalogues, with no p-value, re-estimated dispersal kernel, observed source-occupancy status or new ecological response. The [benchmark](../benchmarks/tern_source_catalogue_rounding_sensitivity_v2.py), [synthetic tests](../tests/test_tern_source_catalogue_rounding_sensitivity_v2.py) and dedicated [GitHub Actions workflow](../.github/workflows/eog-tern-source-catalogue-sensitivity-v2.yml) do not export original ring event rows, UID, departure/arrival coordinates, precise years or individual per-row scores.

**Scope boundary:** This diagnoses source-catalogue sensitivity in an already published single-ring dataset. It does not establish which colonies were available as actual founders in 1975, the likelihood of true animal movement, environment/barrier constraints, or the generality of geographic MRR across taxa. The frozen EOG-WF scoring programme remains **3 scored / 31 scientific STOP / 3 administrative exclusions**.
