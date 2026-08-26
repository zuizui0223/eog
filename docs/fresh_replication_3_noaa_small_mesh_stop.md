# Fresh paired-complementarity replication 3: NOAA small-mesh STOP

## Current decision

The NOAA Gulf of Alaska Small-Mesh Survey candidate is terminally stopped at
response-blind Gate 0 with `stop_analysis_registry_not_closed`. It contributes no
paired-complementarity result and does not change Layer B. Layer B therefore remains a
replicated candidate supported only by the completed Azores and Louisiana endpoints;
it is not a standalone theorem, universal ecological law, or stable public API.

## Prospectively frozen attempt

- Source: NOAA InPort item 22010, physically separate Haul (registry/effort) and Catch
  (response) CSV objects.
- Focal response: exact `Pandalus borealis` recorded station-year detection; no fuzzy
  match or species substitution.
- Initialization: 1973; calibration: 1974-1994; held out: 1995-2004.
- Node: exact non-empty `STATIONID`; Catch could not repair identity, geometry, effort,
  or years.
- Eligibility: GOA, standard station haul, performance 0, gear 508, predeclared
  quantitative catch-sampling methods, positive effort/net dimensions, and valid start
  coordinates.

## Gate 0 evidence

- Catch transport remained read-free: exact `206` and
  `Content-Range: bytes 0-0/11881418`; no returned byte, CSV header, row, or value was
  opened.
- The Haul object matched generation `1638988158418559`, MD5
  `7c4b107b815b00a1a7788498e5ab8710`, and contained 9,354 rows.
- The prospective four-column Haul key had 61 duplicate groups.
- All 196 GOA rows in the held-out decade lacked `STATIONID`, `NET_WIDTH`, and
  `NET_HEIGHT`. The closed station-year registry therefore contained zero nodes and
  zero held-out years.
- Replacing `STATIONID` with `BAYCODE` or relaxing the effort fields after observing
  Haul would be an undeclared node/eligibility switch, so it was not attempted.

The first allowed Haul opening exposed a documented schema mismatch between the InPort
entity display and distributed CSV. A response-blind v1.1 amendment froze the actual
CSV header without changing focal taxon, years, gear, node identity, thresholds, or any
response rule. The complete three-attempt ledger records three transport probes and
zero cumulative Catch bytes opened.

## Mainline consequence

The attempted third fresh endpoint remains unresolved. Northern New England stopped at
bounded archive transport, UKCEH PoMS stopped for both transport failure and response
contamination, and NOAA Small-Mesh stopped because the prospective analysis registry
could not be closed. None of these STOPs is favorable, adverse, null, or non-estimable
paired evidence.

## Transport-first replacement pass

A subsequent bounded search found no admitted replacement:

- NOAA West Coast Groundfish Bottom Trawl Survey (InPort 18418) stopped because the
  official Catch and Haul URLs both resolve to the same generic HTML object, destroying
  exact role identity. No body was opened.
- NOAA ACES-SHELFZ (InPort 23736) stopped from metadata because its 2013-2014 extent
  cannot supply six held-out outer units. Catch transport was not probed.
- NOAA RACEBASE (InPort 22008) passed physical separation and read-free Range transport.
  After freezing EBS, `STATIONID`, `HAULJOIN`, `ABUNDANCE_HAUL`, Pacific cod code 21720,
  initialization 2008, calibration 2009-2013, and heldout 2014-2019, Haul-only audit
  found 6,305 unique joins, 2,575 standardized EBS hauls, and 376 repeated nodes. The
  static object nevertheless contains only 2013-2018, leaving five held-out years and
  incomplete calibration. It is therefore a terminal outer-unit STOP; Catch remained
  unopened.

The candidate queue has no response-blind admissible endpoint after this bounded pass.
Further work requires a genuinely new source with at least six prospectively fixed
outer units, not a year-window repair of RACEBASE or a node repair of Small-Mesh.
