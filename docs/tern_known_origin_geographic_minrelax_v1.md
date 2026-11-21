# Source-locked geographic minimum required relaxation from Arctic tern banding-derived events (v1)

**Status:** pre-event protocol frozen; independent published external event-level **geographic** diagnostic. This work is not three-axis A/B/M EOG, not prospective independent ecological confirmation, and cannot estimate dispersal probability.

## Grounded source and distinct scope

We moved beyond the **synthetic source-uncertain MRR** and the still **unscored** experimental toad H1 by selecting a different empirical dataset: [Li et al. (2026) Danish Arctic tern natal vs breeding dispersal](https://doi.org/10.5061/dryad.x69p8czxh) ([paper](https://doi.org/10.1002/ece3.74372)).

The official publisher metadata and SHA-256 roster were qualified without any event data opened in [source-only gate v1](tern_published_departure_source_gate_v1.md); the [frozen source manifest](../validation/tern_published_departure_source_gate_v1/frozen_metadata_summary_v1.json) confirms **version 466530, 2026-09-30**, and the published original tables `U_DaD.csv` (890 natal events) and `Ad_DaD.csv` (200 adult breeding events). Publisher file SHA256/bytes, both event-table headers, original event years and expected counts are frozen in [pre-event protocol](../validation/tern_known_origin_geographic_minrelax_v1/protocol_v1.json), first commit `44912cef511b0b4f981db28f2d076ae49ab9ebe8`, before reading *any* of the individual event rows.

**Meaning of source:** `depart_lat/depart_lon` is a colony at which the bird had been marked, either as a chick or as a breeding adult, while `arrive_lat/arrive_lon` is a later breeding colony. This is much stronger than selecting arbitrary nearby plausible sources: it is a documented mark-derived departure/arrival pairing. But it is not the animal's complete migration path or a direct record of one uninterrupted flight.

## Frozen source-aware and origin-agnostic estimands

For event `i`, published rounded WGS84 locations `s_i` (departure) and `t_i` (later breeding), define `d` as great-circle distance in km.

```text
r_actual(i) = d(s_i, t_i)

C_early = unique departure-colony coordinates from Ad_DaD and U_DaD
          with *published event year* <= 1975; DO NOT USE arrivals
          or any >=1976 event to construct this source index.

r_any(i) = min [ r_actual(i), min_{c in C_early} d(c,t_i) ]

g_i = r_actual(i) - r_any(i) >= 0

FalseAssurance_i(R) = 1{r_actual(i)>R AND r_any(i)<=R}

RoundConservative_i(R) = 1{r_actual(i)>R+2 km AND r_any(i)<R-2 km}
```

Both age groups use the **same early departure-colony catalogue**. Post-1975 events are analyzed by their *published event year*. The actual marked departure location is always included in the hypothetical "some-source" set to make this an explicit comparison of **known origin vs any pre-indexed candidate**. `r_any<=r_actual` is pure set inclusion and **not itself scientific novelty**; *how frequently an actual marker-supported origin would be ignored under fixed 5/20/50/100-km movement requirements* is an empirical property of this specific published dataset and catalogue.

**Primary frozen descriptive radius = 20 km** for both groups; evaluate all four thresholds with full denominator and the 2-km conservative coordinate-rounding margins. No outcome-selected radius tuning, significance test, species-general dispersal "law", or source probability. One published event row is the unit, **not one independent animal**.

## Important time and observation limits

- `year` is **the year of the derived published dispersal event**, not verified moment at which the ringing/arrival observation or record entered an archived database. A catalogue restricted to events with year≤1975 is a **retrospective historical index** and cannot claim "available as of 1975" or *prospective* target testing.
- Raw individual ring numbers, full ringing/recapture histories and non-dispersing birds are absent. Some adults dispersed repeatedly. No probability of movement, survival, source-founder attribution, unbiased dispersal kernel or independent-event standard error is estimable from these two shared tables alone.
- 0.01° coordinate rounding creates ~km-scale source/target positional uncertainty. Publisher `distance_km` must agree with haversine on published coordinates within **2 km** in ≥95% of all 1,090 events, or scientific **STOP**. Every false-assurance event is also classified under a conservative ±2 km separation-margin check; do not infer sub-km physical dispersal boundaries.
- Source catalogue itself includes only earlier **observed departures among derived movement records**, not a census of all potential occupied colonies, environmental suitability, or hard barriers. Other colonies may be available and unknown; hence numbers are **catalogue-conditional**.
- The original paper already reported longer natal than adult breeding dispersal: repeating that is not an original discovery. A new source-aware/any-source contrast cannot be equated with improved SDM predictive skill unless a separate outcome-hidden, source-independent design exists.

## Source-authenticated result: 20 km false assurance is frequent under the retrospective catalogue

Publisher SHA and event checks passed in dedicated [Actions run #44848269676](https://github.com/zuizui0223/eog/actions/runs/44848269676). All **200 adult + 890 natal original event rows** were admitted, and **1,090/1,090** published distances agreed with great-circle calculations from 0.01°-rounded locations within the frozen ±2 km tolerance. The year≤1975 catalogue contained **115 distinct rounded departure coordinates**. It was held fixed when evaluating the year≥1976 rows: **87 adult breeding** and **491 natal** derived movement events.

| Predeclared primary threshold **R=20 km** | Adult breeding events | Natal events |
| --- | ---: | ---: |
| Events in published-year post-1975 partition | **87** | **491** |
| Known marked-departure `r_actual≤20` | **77** | **277** |
| Optimistic some-source `r_any≤20` | **87** | **465** |
| **False assurance:** known origin `>20` but any source `≤20` | **10** | **188** |
| **Conservative ±2 km margin false assurance** | **9** | **171** |
| All known-source `>20` events (denominator for conditional gap fraction) | 10 | 214 |
| Conditional false-assurance share of actual `>20` events | **100%** | **87.85%** |

Across the **578 post-1975 derived events**, *198* actual marked-source transitions require more than 20 km while some earlier-indexed alternative colony appears within 20 km of the destination. *180* remain classified this way when requiring 2-km separation around both distance boundaries. This is a quantified **conditional event-level source-identity loss**, not an estimate of movement probability or independent populations.

The mean/median known-source geographic lower bound is **10.21/3.41 km** among the 87 adult events and **46.78/15.20 km** among the 491 natal events. The corresponding *nearest hypothetical source* median is **0.0 km for both groups**. **This zero is a warning, not evidence of zero bird movement:** a destination colony can coincide exactly at the archive's 0.01° rounding resolution with one of the earlier source-catalogue coordinates, even though the bird's documented departure colony was somewhere else. Such a candidate is **not verified to be an active contemporary source**. The hypothetical source catalogue may include colonies only retrospectively known from later banding records. The resulting "optimism" cannot be interpreted as an actual dispersal explanation.

All four originally frozen radii (5, 20, 50, 100 km) and all QA denominators are retained in the [source-SHA-bound frozen numeric receipt](../validation/tern_known_origin_geographic_minrelax_v1/frozen_aggregate_summary_v1.json). Original full source result fingerprint without self field: `feaad217d8b105af4fddae81d50055a30a3e259f2716bbdc0100b1a7d878b68f`. Publisher-verified artifact ID `14684570611`, ZIP SHA256 `b1062c806cff299a268787f3456f67cea5b663291753ad0fb701d6438fb40733`.

**Failure/repair trace:** the first source-analysis CI `44848183666` completed the data analysis and exported the same fingerprint, but its *post-run wrapper* failed because it asserted a nonexistent key `published_distance_total_rows` instead of the actual `publisher_distance_total_rows`. The code/protocol/numeric values were not changed; a wrapper-only fix followed, and `44848269676` passed. This is a CI-key error, not a science-quality failure.

**What was positively verified:** on a third-party bird ringing-derived event archive with known departure and arrival *colony endpoints*, the EOG distinction between source-specific required geographic separation and weaker existence of any source has a large realized **retrospective catalogue-conditional** difference. The direction `r_any≤r_actual` is mathematical; the 10/87 and 188/491 counts are data dependent. None of this identifies full routes, validates source occupancy at the year, improves predictive loss, or supports universal ecological claims.

## Verification and output

The [research-only benchmark](../benchmarks/tern_known_origin_geographic_minrelax_v1.py) opens the one official original source ZIP only after checking all five publisher file SHA256 values/bytes and provenance, validates the precise original 200+890 event rows, UID uniqueness within source tables, year/coordinate format, nonnegative published distance, matched original derived distances, and original protocol eligibility. The [synthetic regressions](../tests/test_tern_known_origin_geographic_minrelax_v1.py) test full source/archive SHA checks, a real-source distant movement missed by near "any" source, future-index leakage protection, radius-order invariants, and source quality STOPs. The [GitHub Actions](../.github/workflows/eog-tern-known-origin-geography-v1.yml) produces only aggregate counts and median/mean distances; no original ID, location, date or event row is uploaded.

The original EOG-WF **3 scored / 31 scientific STOP / 3 administrative exclusions** remains unchanged. If the original source data/columns fail an invariant, the correct result is a **source quality STOP, not a negative/positive biological finding**.
