# Community spatial continuity is species-redundant rather than turnover-generated in small-mammal metacommunities

## Provisional title

Community spatial continuity is species-redundant rather than turnover-generated in small-mammal metacommunities

## Alternative titles

1. Individual species, not turnover, account for spatial continuity in small-mammal metacommunities
2. Spatial continuity in small-mammal assemblages is inherited from species-level ranges
3. Pooling species does not create emergent spatial continuity across NEON small-mammal metacommunities

## One-sentence ecological claim

Across 16 fresh NEON small-mammal sites, pooling target species never increased finite-world spatial continuity beyond the best individual species; community-scale continuity was therefore redundant across species rather than emergent from species turnover.

## Abstract

Species turnover can stabilize aggregate ecological properties when different species compensate for one another across heterogeneous environments. Whether such complementarity can also create spatial continuity at the metacommunity scale is less clear. We tested the prospective hypothesis that pooling small-mammal species would connect spatial occurrence patterns that no single species could connect alone. Using 16 response-naive sites from the NSF NEON small-mammal trapping programme, we froze site selection, trap-node geometry, finite one-step spatial world sets, target taxa, a community-minus-best-species connectivity contrast, and a row-permutation null before biological response access. All 16 sites were estimable. Contrary to the hypothesis, the pooled target-species community never survived more spatial worlds than the best individual species. Median emergent connectivity gain was zero, no site showed a positive gain, and the preregistered null-adjusted sign test returned p = 1.0. At every site, at least one individual target species survived every distinct canonical world; no strict emergent world occurred in which the guild survived but all individual species failed. Cross-species-only local support was rare (median 0.0027; maximum 0.066), whereas one species occupied at least 80% of guild-positive nodes at 10 of 16 sites. At ORNL, pooling species reduced world survival from 1.0 for the best individual species to 0.25 for the guild, showing that adding spatially restricted taxa can weaken an all-occurrences connectivity criterion. These results reject a turnover-generated connectivity hypothesis for this programme and instead indicate species-level redundancy: community spatial continuity was already contained within one or more individual species' distributions. This contrasts with spatial-insurance expectations based on compensatory aggregate function and suggests that cross-species complementarity need not translate into emergent spatial connectivity.

## 1. Introduction

Metacommunity ecology asks how local community composition, dispersal and environmental heterogeneity combine to generate regional biodiversity patterns. A central idea is that compositional turnover can produce aggregate properties that are not evident at the level of individual species. Spatial insurance theory, for example, predicts that different species or local communities can compensate for one another across heterogeneous environments, stabilizing regional biomass or ecosystem function.

But an aggregate property can also be redundant rather than complementary. A community may appear spatially continuous simply because one or more individual species are already continuous across the relevant landscape. In that case, pooling taxa does not create a new regional property; it inherits a property already present in its component species.

This distinction is rarely asked for spatial occupancy itself. If local assemblages turn over across space, does the union of species occurrences bridge gaps that remain in every individual species distribution? Or is community-level continuity mostly carried by spatially widespread or individually self-connected species?

We tested this question prospectively in NEON small-mammal metacommunities. The analysis used a finite set of response-blind spatial worlds at each site. A world survives an occurrence set only if every positive trap has at least one positive peer connected by an admitted one-step edge. We applied the same rule to the pooled target-species guild and separately to every target species.

Our primary effect was stringent:

community survival fraction minus the maximum survival fraction of any individual species.

A positive value requires the community to survive spatial worlds that no individual species can survive alone. We further distinguished strict emergent worlds, cross-species-only local rescue, and dominance coverage, and used a preregistered assemblage-row permutation to test whether any observed gain depended on the spatial arrangement of local assemblages rather than only on species frequencies and local richness.

The prospective hypothesis was that species turnover would generate positive emergent connectivity. It was rejected. Instead, the results reveal a contrasting ecological organization: spatial continuity was species-redundant, and in one case pooling taxa reduced connectivity.

## 2. Methods

### 2.1 Fresh confirmatory site set

We excluded all 16 NEON sites consumed by the preceding EOG world-survival programme and three tutorial sites whose response summaries had been viewed during design. From the remaining RELEASE-2026 small-mammal sites, we scanned site codes in ascending order and froze the first 16 sites meeting response-blind geometry and structural-adequacy requirements.

The fixed sites were JORN, KONA, LAJA, LENO, MLBS, MOAB, NIWO, NOGP, OAES, ONAQ, ORNL, OSBS, RMNP, SERC, SJER and SOAP.

No biological response was opened during site selection.

### 2.2 Nodes and structural worlds

Individual geolocatable mammal traps were graph nodes. Trap coordinates containing X were excluded prospectively because the official NEON small-mammal geolocation implementation treats such trap locations as spatially uncertain.

For each site we generated an adequacy-complete Haversine distance ladder, deduplicated exact adjacency operators, and retained three or four distinct canonical one-step worlds. All 16 fresh sites passed the frozen structural gate.

### 2.3 Target community

The response was the NEON target-small-mammal species guild. The target set was frozen from the SMALL_MAMMAL taxonomy endpoint at species rank with taxonProtocolCategory equal to target. Two species whose public response summaries had been exposed during prior design work were excluded prospectively.

A species-by-trap incidence matrix recorded whether each retained target species was ever captured at each frozen non-X trap across RELEASE-2026.

### 2.4 Spatial world survival

For any species or pooled guild, a canonical world survived if every positive trap had at least one other positive trap joined by an admitted one-step edge.

The pooled community survival fraction was the fraction of canonical worlds surviving the union of all target-species positive traps.

Species survival fractions were calculated independently. Species with fewer than two positive retained traps could not survive a world.

### 2.5 Primary emergent-connectivity effect

At each site:

Emergent connectivity gain =
community survival fraction
minus maximum individual-species survival fraction.

A positive gain therefore means that pooling species preserves at least one spatial world beyond what the best single species can preserve.

The preregistered primary hypothesis predicted positive gains across sites.

### 2.6 Strict emergence, local cross-species rescue and dominance

A strict emergent world was a canonical world in which the pooled guild survived but no individual species with at least two positive nodes survived.

Cross-species-only local rescue was measured across guild-positive target nodes within guild-surviving worlds. A target counted as cross-species-only supported when it had at least one positive neighbouring trap, but none of its positive neighbours shared any species with the target trap.

Dominance coverage was the largest number of guild-positive nodes occupied by any one target species divided by the total number of guild-positive nodes.

### 2.7 Assemblage-row spatial null

For each site, 999 null assemblages were generated by permuting complete observed species-incidence row vectors among the fixed guild-positive trap coordinates.

This preserves:
- the guild-positive node set;
- every species' node occupancy count;
- the multiset of local species-richness values;
- the complete within-node co-occurrence vectors.

It destroys only the spatial assignment of those local assemblages.

For each permutation, species-level world survival and the best-species survival fraction were recomputed. The community survival fraction stayed fixed because the guild-positive node set did not change.

The null-adjusted site effect was the observed emergent gain minus the median permuted gain.

### 2.8 Aggregate preregistered test

The consumed preregistered analysis counted a site as positive when its null-adjusted effect was greater than zero; exact zero counted as non-positive. The primary aggregate was a one-sided exact sign test against probability 0.5.

Support required at least eight scored sites, a positive median observed emergent gain, and sign-test p < 0.05.

This exact consumed rule is retained even though a later non-authoritative draft considered an alternative tie treatment.

## 3. Results

### 3.1 All fresh sites were estimable

All 16 fixed sites completed the once-only response programme. There were no response-consumed site stops.

The number of observed target species ranged from 2 to 16, with a median of 7. Species with at least two positive nodes had a median count of 6 per site.

### 3.2 Species pooling never created additional world survival

The primary hypothesis was rejected.

Median emergent connectivity gain was 0. No site had a positive emergent connectivity gain. The null-adjusted positive-site count was 0 of 16, and the preregistered one-sided sign-test p-value was 1.0.

Fifteen of 16 pooled communities survived every distinct canonical world. Yet at all 16 sites, at least one individual target species also survived every canonical world.

Thus pooling target species never increased the surviving-world fraction above the best individual species.

### 3.3 No strict emergent spatial world occurred

The strict emergent world fraction was zero at every site.

There was therefore no site-world combination in which the target-species guild remained spatially supported while every individual eligible species failed.

This is the strongest direct rejection of the turnover-generated connectivity hypothesis.

### 3.4 Cross-species-only local rescue was rare

Cross-species-only local support did occur, but it was uncommon and did not scale into additional system-level world survival.

Across sites, the median cross-species rescue fraction was 0.00269, the mean was 0.0103, and the maximum was 0.0661.

Thus species replacement occasionally supplied a local neighbouring occurrence where no conspecific neighbour was present, but these events were too sparse to create canonical worlds unavailable to individual species.

### 3.5 Community continuity was highly redundant across individual species

The number of species tied for best world survival had a median of two and ranged from one to eight.

Several taxa appeared as best-survival species at multiple sites, including Reithrodontomys megalotis, Sigmodon hispidus, Mus musculus and Peromyscus boylii, each appearing among the best species at three sites.

This recurrence did not reduce to one continent-wide dominant species. Instead, different sites were supported by different members of the regional species pool.

Dominance coverage nevertheless tended to be high: median 0.835, range 0.501-0.982, with 10 of 16 sites having at least one species occupying 80% or more of guild-positive nodes.

The identity of the species with highest node coverage was not preregistered as equivalent to the best world-survival species, so no such identity claim is made.

### 3.6 Pooling species can reduce spatial world survival

ORNL was the only site with a non-zero emergent gain, and it was negative.

The pooled community survived 0.25 of canonical worlds, whereas the best individual species survived 1.0, yielding an emergent gain of -0.75.

Ochrotomys nuttalli, Oryzomys palustris and Reithrodontomys humulis were tied as best-survival species at ORNL.

This result demonstrates a weakest-link property of an all-positive spatial support rule: adding occurrences from additional, spatially restricted taxa can introduce unsupported peripheral nodes and reduce the set of worlds compatible with the pooled community.

## 4. Discussion

The expected ecological pattern did not occur. Species turnover did not create emergent community-level spatial continuity across the 16 fresh small-mammal metacommunities.

Instead, community continuity was species-redundant. Every site contained at least one individual species whose occurrences were sufficient to survive all canonical worlds, and no pooled community survived a world that all individual species failed.

This result distinguishes spatial continuity from classic insurance effects. Spatial and species insurance describe how aggregation across heterogeneous populations or communities can stabilize biomass or ecosystem function when components respond asynchronously. Our result shows that such a complementarity logic need not extend to an all-occurrences spatial-connectivity property. A regional community can be taxonomically heterogeneous yet spatially redundant because one or more constituent species already span the relevant graph.

The very low cross-species rescue fractions sharpen this distinction. Species replacement was present locally, but local replacement rarely provided support that was unavailable through shared-species neighbours, and it never generated additional canonical world survival.

The pattern also cannot be summarized as a single dominant-species effect. Dominance coverage was high at many sites, but not all. At OSBS, for example, the most widespread single species covered only about half of guild-positive nodes, yet individual species still matched the pooled community's complete world survival. The broader result is therefore redundancy among species-level spatial patterns, not merely numerical dominance by one species.

ORNL shows the opposite possibility. Pooling taxa can make a spatial criterion stricter because the guild union includes every positive node from every included species. If additional taxa occur at isolated or peripheral traps, the pooled community can fail worlds that a more spatially coherent species survives. This is not a statistical anomaly: it follows directly from asking every pooled positive occurrence to have peer support.

The ecological implication is that biodiversity aggregation does not necessarily add spatial connectivity. Depending on how the aggregate property is defined, species pooling may be neutral because component species are redundant, beneficial if different species truly bridge spatial gaps, or detrimental if additional restricted occurrences create new unsupported constraints.

For the NEON small-mammal systems studied here, the first process dominated and the third occurred once. The hypothesized second process was absent.

## 5. Relation to metacommunity and insurance theory

Metacommunity theory emphasizes local environmental filtering, dispersal and species sorting as joint determinants of regional composition. Spatial-insurance and cross-community asynchrony frameworks further show how different species or communities can compensate for one another when aggregate biomass or function is considered.

The present result concerns a different aggregate property: topological continuity of observed occurrences under a finite set of spatial worlds.

The comparison suggests a general distinction:

- functional or temporal aggregation can benefit from compensatory turnover;
- spatial all-occurrence continuity can instead be redundant across species;
- adding species can even reduce continuity when aggregation adds spatially unsupported occurrences.

This does not contradict spatial insurance theory. It identifies a property for which the expected insurance mechanism did not transfer.

## 6. Claim boundary

Supported:
- pooling target small-mammal species did not increase world survival beyond the best species at any of 16 fresh sites;
- no strict emergent world was observed;
- cross-species-only local support was rare;
- at every site, at least one individual species survived every distinct canonical world;
- dominance coverage was often high but varied strongly among sites;
- pooling taxa reduced world survival at ORNL.

Not supported:
- species turnover creates emergent connectivity in this programme;
- the best world-survival species is necessarily the numerically or spatially dominant species;
- high richness causes connectivity;
- observed redundancy identifies dispersal mechanism, habitat filtering or mass effects;
- the result generalizes automatically beyond NEON target small mammals;
- the one-step finite-world metric is the only meaningful definition of metacommunity connectivity.

## 7. Figure plan

Figure 1 — Redundancy versus complementarity.
Conceptual contrast among three cases: best species equals community, community exceeds every species, and pooling reduces continuity.

Figure 2 — Fresh-site empirical result.
For all 16 sites, pair community survival fraction with maximum single-species survival fraction. Fifteen sites are 1 versus 1; ORNL is 0.25 versus 1.0.

Figure 3 — Local mechanism diagnostics.
Site-level dominance coverage and cross-species rescue fractions, highlighting high redundancy and low cross-species-only support.

Figure 4 — ORNL weakest-link illustration.
Show a best species occupying a self-supported subset while pooling adds restricted positive nodes that eliminate three of four worlds.

## 8. Reproducibility anchors

Authoritative response closure:
validation/neon_metacommunity_connectivity_v1/response_lock_v1.json

Authoritative pre-response analysis:
validation/neon_metacommunity_connectivity_v1/analysis_implementation_v1.json

Response-locked analysis module blob:
a09ecd84d965ab4d2d0161f0567a8367ec7fec21

Fresh roster:
validation/neon_metacommunity_connectivity_v1/fresh_roster_lock_v1.json

Primary protocol:
validation/neon_metacommunity_connectivity_v1/protocol_v1.json

Response protocol:
validation/neon_metacommunity_connectivity_v1/response_protocol_v1.json
