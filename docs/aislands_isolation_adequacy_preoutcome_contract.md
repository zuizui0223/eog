# A-Islands island-isolation adequacy extension — pre-outcome contract

Date frozen: 2026-08-12

Revision 1.1 was recorded after the outcome-free A-Islands polygon-area gate succeeded and **before any extension species outcome was computed**. It adds a fixed continental-mainland distance baseline so the island-biogeography reference cannot omit the classical mainland-isolation axis.

Revision 1.2 was recorded after the same outcome-free area gate and a closer island-biogeography prior-art audit, again **before any extension species outcome was computed**. Weigelt & Kreft (2013) showed that surrounding land area can outperform simple mainland distance as an isolation representation, and incidence-function/metapopulation work already weights source contributions by patch size. The reference was therefore strengthened prospectively with area-weighted occupied-source pressure and area-weighted surrounding-landmass pressure.

## Scientific pivot

This extension treats islands as the primary biological domain. It does **not** claim that stepping stones, multiple source pools, graph connectivity, source-area effects, or multidimensional isolation are new. Those ideas are established in island biogeography and metapopulation ecology.

The new question is narrower and stronger:

> **After a reference model represents local climate, island area, continental-mainland distance, direct and area-weighted species-source pressure, and species-independent archipelago geometry and surrounding landmass, does species-conditioned archipelago configuration retain held-out incidence information?**

Equivalently: **is the declared island-isolation reference structurally sufficient for a focal species?**

The target EOG term is therefore a *structural adequacy probe*, not a new generic connectivity index and not a colonisation probability.

## Prior-art boundary

The extension explicitly accepts the following as prior art:

- scalar mainland / nearest-island isolation in classical island biogeography;
- stepping-stone isolation (e.g. Long et al. 2009, DOI `10.1890/08-1337.1`);
- multiple-source-pool and dispersal-pathway indices in archipelagos (Yeakley & Weishampel 2000, *Ecology* 81:893–898);
- multidimensional isolation metrics including surrounding landmass and stepping stones (Weigelt & Kreft 2013, DOI `10.1111/j.1600-0587.2012.07669.x`);
- graph-theoretic structural connectivity among islands (Sillero et al. 2018, DOI `10.1093/biolinnean/bly033`);
- graph-connectivity validation with independent ecological/genetic evidence (Daniel et al. 2023, DOI `10.1111/cobi.14047`);
- source-patch size/quality weighting in incidence-function and metapopulation connectivity;
- species-specific dispersal ability modifying island occurrence and the meaning of isolation.

No novelty claim may be based on any item above by itself.

## Frozen upstream evidence that must not change

This extension does not supersede the authoritative A-Islands benchmark.

- source: A-Islands v1.0, immutable record 10775810;
- surveyed universe: 842 species-linked islands;
- cohort: 886 APC-native taxa;
- folds: frozen five-fold 5-degree spatial partition;
- climate: CHELSA BIO1/BIO5/BIO6/BIO12/BIO15;
- original authoritative conditional concordance: `0.6177465917820878`;
- original bootstrap 95% interval: `0.6086806094469824–0.626944450492123`;
- original estimable taxa: 845.

No original source byte, cohort member, fold, climate value, graph radius, result, interval, applicability count, or fingerprint may be edited by this extension.

## Gate 1 — recover island area only from the already-frozen A-Islands shapefile

The peer-reviewed A-Islands data paper states that the shapefile contains island polygons, while the version-1.0 DBF audited by EOG contains only `island_ID`, `x_centroid`, and `y_centroid`. Before any new species outcome is computed, a geometry-only workflow must establish whether the **same frozen shapefile bytes** contain usable polygon geometry.

### Allowed area source

Only `A-Island_shape.shp/.shx/.dbf/.prj` fetched by the existing A-Islands v1.0 acquisition workflow may be used.

No external island-area database, manual lookup, Google Maps/Google Earth measurement, or outcome-informed correction is allowed for the primary extension.

### Area recovery rule

If and only if all 842 surveyed islands have finite polygon geometry, derive spherical polygon area in km² from those polygons using the committed equal-area spherical projection routine. Multipart polygons and interior rings must be handled by signed ring area.

The geometry audit must record:

- shapefile type;
- surveyed-island polygon coverage;
- per-island part and point counts;
- derived area;
- projection text;
- exact source SHA-256 values;
- exact derived-area-table SHA-256.

### Hard stop

If the shapefile is not polygonal, if any surveyed island lacks a finite positive derived area, or if geometry identity cannot be verified against the existing frozen source manifest, **do not run the area-adjusted outcome analysis**. A coordinate-only sensitivity may be developed separately, but it cannot be relabelled as the primary island-biogeography test.

The accept/reject rule was fixed before derived areas were inspected. The successful geometry-only gate is recorded separately in `validation/aislands_isolation_adequacy_20260812/area_gate_expected.json`; it does not contain species outcomes.

## Gate 1b — freeze continental-mainland distance before species outcomes

A serious island-biogeography reference should not omit the classical mainland-isolation axis merely because A-Islands v1.0 lacks a downloadable mainland-distance column.

### Mainland geometry source

Use **Natural Earth 1:10m Admin-0 Countries, version 5.1.1**, acquired from the official Natural Earth CDN:

`https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip`

The acquisition workflow must record the exact archive and extracted-file SHA-256 values before any extension species outcome is computed.

### Deterministic mainland rule

1. select exactly one Admin-0 country feature with `ADMIN=Australia` and `ADM0_A3=AUS`; sovereignty identifiers such as `SOV_A3=AUS` are diagnostic only because they also include Australian dependencies;
2. split the selected country's polygon geometry into rings;
3. calculate spherical absolute area for each ring without using A-Islands occurrences;
4. select the ring with the largest absolute area as the **continental Australian mainland**;
5. record its point count, area, bounding box and derived ring SHA-256;
6. for every frozen A-Islands centroid, calculate the minimum spherical point-to-minor-great-circle-segment distance to that fixed mainland coastline ring.

This rule deliberately excludes Tasmania and smaller Australian islands from the `mainland` baseline by geometry rather than by a hand-curated island-name list.

### Hard stop

Do not run the species outcome extension unless:

- the Natural Earth source resolves to the frozen version/hash;
- exactly one country feature satisfies `ADMIN=Australia` and `ADM0_A3=AUS`;
- a unique largest mainland ring is obtained;
- all 842 island centroids receive finite non-negative mainland distances;
- the 842-row mainland-distance table is fingerprinted and reproduced exactly.

Natural Earth is used only for this fixed species-independent geographic baseline. It does not define EOG edges or occurrence anchors.

## Gate 2 — frozen reference hierarchy

All features below must be calculated without held-out response labels.

### R0 — local environment

Five CHELSA predictors: BIO1, BIO5, BIO6, BIO12, BIO15.

### R1 — classical recipient-size, mainland-isolation and direct-source terms

R0 plus:

- `log_area_km2 = log(area_km2)` from Gate 1;
- fixed distance to the continental Australian mainland from Gate 1b;
- nearest outer-training-presence geographic distance.

The fixed mainland-distance term and the species-conditioned nearest-source term are intentionally separate. The former represents a classical island-geography baseline; the latter represents the nearest observed source available for the focal species under the outer-training boundary.

### R2 — multiple occupied sources and source landmass

R1 plus two source-pressure ensembles over the already-frozen geographic scales `25, 50, 125, 250 km`.

For focal island `i`, outer-training presence anchor set `A`, scale `s`, and source-island area `A_a`:

`P_s(i) = log(1 + sum_{a in A, a != i} exp(-d(i,a)/s))`

`P_area,s(i) = log(1 + sum_{a in A, a != i} A_a * exp(-d(i,a)/s))`.

Each predeclared predictor is the arithmetic mean of its four scale-specific values. The first controls the number/proximity of observed sources; the second also controls source-island landmass without treating area weighting as EOG novelty.

For an outer-training row, the focal row is excluded from the anchor set even if it is observed present. For a held-out row, all anchors are outer-training presences. This prevents a training presence from creating its own source-proximity or source-landmass signal.

### R3 — species-independent archipelago geometry and surrounding landmass

R2 plus all of:

1. nearest-other-island distance;
2. surrounding-island pressure, defined like unweighted source pressure but summing over all other surveyed islands;
3. surrounding-landmass pressure, defined as `log(1 + sum area_j * exp(-d(i,j)/s))`, averaged over the same four scales and summing over all other surveyed islands;
4. unanchored component exposure across the four frozen geography-only radii, defined as the mean over scales of `(component_size(i,s)-1)/(N-1)`.

These terms ask whether any apparent EOG benefit is merely local island density, surrounding landmass, or generic network embedding. They intentionally make the primary comparator stronger than a simple area-plus-mainland-distance ETIB baseline.

### Candidate C — species-conditioned archipelago configuration

C = R3 plus **geography-only EOG connected frequency** across the four frozen `25/50/125/250 km` scenarios.

For held-out islands, connected frequency is the fraction of those four graphs in which the target component contains at least one outer-training presence.

For outer-training rows used to fit the comparison model, the focal row is excluded as an anchor. A training presence therefore counts as connected only if its component contains at least one *other* training presence.

Environmental-edge EOG scenarios are not part of this new primary island-isolation test. They remain archived secondaries from the original authoritative benchmark. This choice removes environmental-edge construction from the new isolation estimand and makes the candidate strictly geographic/species-conditioned.

## Model and held-out scoring contract

For each taxon × frozen outer fold:

1. build all response-derived spatial features from outer-training labels only;
2. construct training-row source/EOG features with focal-row self exclusion;
3. fit each reference/candidate tier using the same deterministic L2-penalized logistic engine, `lambda = 1`, intercept unpenalized, training-only z-standardisation, no class weighting;
4. score the identical held-out rows for all tiers;
5. retain a row only when all compared tiers produce finite probabilities;
6. calculate candidate-minus-reference log loss on matched held-out rows.

The **primary extension contrast** is `C - R3` log loss. Negative values favour the EOG structural probe. The prespecified secondary is the matched Brier-score difference.

Intermediate contrasts (`R2-R1`, `R3-R2`, `C-R1`, `C-R2`) are explanatory only and may not replace `C-R3` as primary after outcomes are seen.

## Species-level inference

- replication unit: species;
- fold rows are averaged equally within species;
- species are averaged equally across estimable taxa;
- uncertainty: 10,000 species bootstrap replicates;
- two-sided sign-flip diagnostic: 100,000 replicates;
- seed: `20260812`;
- non-estimable folds/species remain explicit and are never converted to zero effect.

No significance filter is used to select species.

## Interpretation states

The extension allows all three outcomes:

1. **Residual archipelago structure** — `C-R3 < 0` with uncertainty excluding zero: species-conditioned configuration adds held-out information beyond the strong island reference.
2. **Structural saturation / no increment** — interval includes zero or the effect is adverse: the strong reference already captures the tested signal, or EOG adds noise.
3. **Indeterminate applicability** — data/folds are too sparse for a stable test.

A non-positive result is not grounds for retuning radii, source-pressure scales, topology metrics, species subsets, area handling, mainland-distance definition, or area-weighted pressure definitions.

## Claim boundary if the primary extension is positive

Permitted:

> Across Australian continental-island plant incidences, species-conditioned archipelago configuration retained held-out information beyond climate, recipient island area, continental-mainland distance, direct and area-weighted species-source pressure, surrounding island number/landmass, and species-independent island-network geometry under the frozen reference hierarchy.

Not permitted:

- EOG discovers that island isolation is multidimensional;
- EOG discovers stepping stones;
- EOG invents surrounding-land-area or source-area isolation metrics;
- connected frequency is a dispersal, migration, immigration, occupancy, or colonisation probability;
- the graph reconstructs historical colonisation routes;
- unoccupied intermediate islands were actually used as stepping stones;
- the extension proves a causal mechanism.

## Journal-positioning decision rule

If both geographic gates succeed and `C-R3` retains a robust held-out increment, the manuscript may be repositioned primarily as an **island-biogeography isolation-adequacy** paper and *Journal of Biogeography* becomes a serious first-target candidate.

If a gate fails or R3 absorbs the EOG increment, retain the broader *Ecological Informatics* structural-adequacy framing rather than weakening the area/isolation standard for an island-biogeography claim.
