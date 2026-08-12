# A-Islands island-isolation adequacy extension — pre-outcome contract

Date frozen: 2026-08-12

Revision 1.1 was recorded after the outcome-free A-Islands polygon-area gate succeeded and **before any extension species outcome was computed**. It adds a fixed continental-mainland distance baseline so the island-biogeography reference cannot omit the classical mainland-isolation axis.

Revision 1.2 was recorded after the same outcome-free area gate and a closer island-biogeography prior-art audit, again **before any extension species outcome was computed**. Weigelt & Kreft (2013) showed that surrounding land area can outperform simple mainland distance as an isolation representation, and incidence-function/metapopulation work already weights source contributions by patch size. The reference was therefore strengthened prospectively with area-weighted occupied-source pressure and area-weighted surrounding-landmass pressure.

Revision 1.3 was recorded after identifying Carter, Perry & Russell (2020; DOI `10.1111/jbi.13778`) as the closest multidimensional island-isolation comparator, still **before any extension species outcome was computed**. Their 16 isolation measures reduced to three major axes—mainland distance, stepping stones and insular network position. R3 was therefore finalized with a species-independent mainland stepping-stone frequency so those generic axes are reference information rather than EOG novelty. **Revision 1.3 closes the pre-outcome reference design; no further reference variables may be added or removed in response to extension outcomes.**

## Scientific pivot

This extension treats islands as the primary biological domain. It does **not** claim that stepping stones, multiple source pools, graph connectivity, source-area effects, or multidimensional isolation are new. Those ideas are established in island biogeography and metapopulation ecology.

The new question is narrower and stronger:

> **After a reference model represents local climate, island area, continental-mainland distance, direct and area-weighted species-source pressure, surrounding landmass, generic mainland stepping-stone availability, and species-independent archipelago network position, does species-conditioned archipelago configuration retain held-out incidence information?**

Equivalently: **is the declared island-isolation reference structurally sufficient for a focal species?**

The target EOG term is therefore a *structural adequacy probe*, not a new generic connectivity index and not a colonisation probability.

## Prior-art boundary

The extension explicitly accepts the following as prior art:

- scalar mainland / nearest-island isolation in classical island biogeography;
- stepping-stone isolation (e.g. Long et al. 2009, DOI `10.1890/08-1337.1`);
- multiple-source-pool and dispersal-pathway indices in archipelagos (Yeakley & Weishampel 2000, *Ecology* 81:893–898);
- multidimensional isolation metrics including surrounding landmass and stepping stones (Weigelt & Kreft 2013, DOI `10.1111/j.1600-0587.2012.07669.x`);
- empirical reduction of 16 insular-isolation measures to mainland-distance, stepping-stone and insular-network axes (Carter, Perry & Russell 2020, DOI `10.1111/jbi.13778`);
- graph-theoretic structural connectivity among islands (Sillero et al. 2018, DOI `10.1093/biolinnean/bly033`);
- graph-connectivity validation with independent ecological/genetic evidence (Daniel et al. 2023, DOI `10.1111/cobi.14047`);
- source-patch size/quality weighting in incidence-function and metapopulation connectivity;
- species-specific dispersal ability modifying island occurrence and the meaning of isolation.

No novelty claim may be based on any item above by itself.

## Frozen upstream evidence that must not change

This extension does not supersede the authoritative A-Islands benchmark.

- source: A-Islands v1.0, immutable record 10775810;
- surveyed universe and graph node universe: the same 842 species-linked/model-linked islands used by the authoritative benchmark;
- shapefile-only records lacking frozen species-incidence rows are **not** added as neutral stepping-stone nodes in this confirmatory extension;
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

The geometry audit must record shapefile type, surveyed-island polygon coverage, per-island part/point counts, derived area, projection text, exact source SHA-256 values and the exact derived-area-table SHA-256.

### Hard stop

If the shapefile is not polygonal, if any surveyed island lacks a finite positive derived area, or if geometry identity cannot be verified against the existing frozen source manifest, **do not run the area-adjusted outcome analysis**. A coordinate-only sensitivity may be developed separately, but it cannot be relabelled as the primary island-biogeography test.

The accept/reject rule was fixed before derived areas were inspected. The successful geometry-only gate is recorded separately in `validation/aislands_isolation_adequacy_20260812/area_gate_expected.json`; it does not contain species outcomes.

## Gate 1b — freeze continental-mainland distance before species outcomes

A serious island-biogeography reference should not omit the classical mainland-isolation axis merely because A-Islands v1.0 lacks a downloadable mainland-distance column.

Use **Natural Earth 1:10m Admin-0 Countries, version 5.1.1**, acquired from the official Natural Earth CDN:

`https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip`

The acquisition workflow must record the exact archive and extracted-file SHA-256 values before any extension species outcome is computed.

### Deterministic mainland rule

1. select exactly one Admin-0 country feature with `ADMIN=Australia` and `ADM0_A3=AUS`; the broader `SOVEREIGNT=Australia` grouping is diagnostic only because it includes the country and five dependencies in the frozen Natural Earth file;
2. split the selected country's polygon geometry into rings;
3. calculate spherical absolute area for each ring without using A-Islands occurrences;
4. select the ring with the largest absolute area as the **continental Australian mainland**;
5. record its point count, area, bounding box and derived ring SHA-256;
6. for every frozen A-Islands centroid, calculate the minimum spherical point-to-minor-great-circle-segment distance to that fixed mainland coastline ring.

This rule deliberately excludes Tasmania and smaller Australian islands from the `mainland` baseline by geometry rather than by a hand-curated island-name list.

### Hard stop and frozen result

Do not run the species outcome extension unless the Natural Earth source resolves to the frozen version/hash, exactly one country feature satisfies `ADMIN=Australia` and `ADM0_A3=AUS`, a unique largest mainland ring is obtained, all 842 island centroids receive finite non-negative mainland distances, and the 842-row mainland-distance table is fingerprinted and reproduced exactly.

The outcome-free gate succeeded before any extension species outcome. The fixed mainland ring contains 9,462 vertices and has SHA-256 `18d151bfe8aee727677ba8beca6f244f80a9a3cb3b616de534cf4ba331f042a4`; the 842-row mainland-distance table has SHA-256 `7d6f52f03702dd0cfae061023a1b2f405e39397de73eaad21b97d24176c4f869`. Exact source, geometry and distance fingerprints are stored in `validation/aislands_isolation_adequacy_20260812/mainland_gate_expected.json`.

Natural Earth is used only for this fixed species-independent geographic baseline. It does not define EOG occurrence anchors.

## Gate 2 — final frozen reference hierarchy

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

### R3 — multidimensional species-independent island isolation

R2 plus all of:

1. nearest-other-island distance;
2. surrounding-island pressure, defined like unweighted source pressure but summing over all other surveyed islands;
3. surrounding-landmass pressure, defined as `log(1 + sum area_j * exp(-d(i,j)/s))`, averaged over the same four scales and summing over all other surveyed islands;
4. unanchored component exposure across the four frozen geography-only radii, defined as the mean over scales of `(component_size(i,s)-1)/(N-1)`;
5. **species-independent mainland stepping-stone frequency**: for each frozen radius `s`, islands with fixed centroid-to-mainland coastline distance `<= s` are generic mainland-entry nodes; the focal island scores 1 when its geography-only component contains at least one such node, and the predictor is the fraction of the four radii with a connection.

Together, fixed mainland distance, mainland stepping-stone frequency, and unanchored component exposure explicitly address the generic distance / stepping-stone / insular-network axes identified by Carter et al. (2020). Surrounding island number/landmass and source-pressure controls make R3 stronger than those three axes alone.

### Candidate C — species-conditioned archipelago configuration

C = R3 plus **geography-only EOG connected frequency** across the four frozen `25/50/125/250 km` scenarios.

For held-out islands, connected frequency is the fraction of those four graphs in which the target component contains at least one outer-training presence.

For outer-training rows used to fit the comparison model, the focal row is excluded as an anchor. A training presence therefore counts as connected only if its component contains at least one *other* training presence.

The contrast between `mainland_stepping_stone_frequency` and EOG is deliberate: the former asks whether the island is generically embedded in a stepping-stone route from continental Australia; EOG asks whether the same island network connects the target to **observed outer-training sources of the focal species**.

Environmental-edge EOG scenarios are not part of this new primary island-isolation test. They remain archived secondaries from the original authoritative benchmark. This makes the candidate strictly geographic/species-conditioned and prevents local environmental filtering from being silently folded into the new isolation probe.

## Model and held-out scoring contract

For each taxon × frozen outer fold:

1. build all response-derived spatial features from outer-training labels only;
2. construct training-row source/EOG features with focal-row self exclusion;
3. require at least five outer-training presences and five outer-training absences, matching the original A-Islands class gate;
4. within each probability tier, remove only predictors whose outer-training standard deviation is `<= 1e-12`, record every removed column, and apply the same retained column indices unchanged to held-out rows;
5. fit each tier using the same deterministic L2-penalized logistic engine, `lambda = 1`, intercept unpenalized, training-only z-standardisation, no class weighting and no hyperparameter tuning;
6. score the identical held-out rows for all tiers;
7. retain a row for a contrast only when both compared tiers produce finite probabilities;
8. calculate candidate-minus-reference log loss on matched held-out rows.

The constant-predictor rule mirrors the already-audited reduced-tier policy used by the Tanzania benchmark: a constant EOG or reference column becomes neutral rather than causing an artificial whole-fold failure.

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

1. **Residual species-conditioned archipelago structure** — `C-R3 < 0` with uncertainty excluding zero: the species-conditioned EOG term adds held-out information beyond the final multidimensional island-isolation reference.
2. **Structural saturation / no increment** — interval includes zero or the effect is adverse: the strong reference already captures the tested signal, or EOG adds noise.
3. **Indeterminate applicability** — data/folds are too sparse for a stable test.

A non-positive result is not grounds for retuning radii, source-pressure scales, topology metrics, species subsets, area handling, mainland-distance definition, landmass weighting, generic stepping-stone definitions, the 5/5 class gate, or the constant-predictor policy.

## Claim boundary if the primary extension is positive

Permitted:

> Across Australian continental-island plant incidences, species-conditioned archipelago configuration retained held-out information beyond climate, recipient island area, continental-mainland distance, direct and area-weighted species-source pressure, surrounding island number/landmass, generic mainland stepping-stone accessibility, and species-independent island-network position under the frozen reference hierarchy.

Not permitted:

- EOG discovers that island isolation is multidimensional;
- EOG discovers stepping stones;
- EOG invents surrounding-land-area, source-area or generic island-network isolation metrics;
- connected frequency is a dispersal, migration, immigration, occupancy, or colonisation probability;
- the graph reconstructs historical colonisation routes;
- unoccupied intermediate islands were actually used as stepping stones;
- the extension proves a causal mechanism.

## Journal-positioning decision rule

If both geographic gates succeed and `C-R3` retains a robust held-out increment, the manuscript may be repositioned primarily as an **island-biogeography isolation-adequacy** paper and *Journal of Biogeography* becomes a serious first-target candidate.

If a gate fails or R3 absorbs the EOG increment, retain the broader *Ecological Informatics* structural-adequacy framing rather than weakening the area/isolation standard for an island-biogeography claim.
