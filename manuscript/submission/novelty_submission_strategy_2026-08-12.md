# EOG novelty audit and submission strategy

Audit date: **2026-08-12**

Status: **the original frozen manuscript is scientifically submission-worthy, but the project has deliberately selected a higher-novelty island-biogeography route. Submission and DOI release are therefore on HOLD until one prospectively frozen A-Islands isolation-adequacy test is executed and incorporated, regardless of its direction.**

This strategy distinguishes three things that must not be conflated:

1. the already-frozen A-Islands and Tanzania outcomes, which must never be retuned;
2. a single new island-isolation adequacy extension whose complete reference hierarchy was fixed before its species outcomes were inspected;
3. journal positioning, which is determined by that new test rather than by searching for a favourable result.

## 1. Existing scientific evidence remains valid and frozen

### A-Islands original authoritative benchmark

The existing positive benchmark remains unchanged:

- 842 model-linked surveyed islands;
- 886 frozen APC-native plant taxa;
- 845 taxa with an estimable primary species statistic;
- mean conditional connected-frequency concordance = **0.6177466**;
- species-bootstrap 95% interval = **0.6086806–0.6269445**;
- 672/845 estimable taxa above the 0.5 null, 42 equal, 131 below;
- pointwise climatic support and nearest outer-training source distance were controlled by the frozen conditioning design;
- non-estimable species/folds remain visible.

The original effect is therefore real within its declared estimand, but it is evidence beyond **local climate + nearest source**, not evidence beyond every established island-isolation representation.

### Tanzania strong-reference boundary benchmark

The existing adverse benchmark also remains unchanged:

- 60 eligible bird species across 14 fragments;
- matrix-aware current-flow resistance selected from 512 candidates using outer-training responses only;
- strong reference = patch area + selected current flow + area×current-flow interaction + nearest-training occurrence distance;
- candidate = the same reference + EOG connected frequency;
- 826 matched primary LOSO predictions;
- species-macro candidate-minus-reference log-loss difference = **+0.0321131**;
- 95% interval = **+0.0174580 to +0.0486750**;
- 17 species favourable to EOG and 43 adverse;
- inverse-area LOSO remains adverse;
- spatial-block sensitivity is smaller and uncertain.

Tanzania remains important because a structural adequacy diagnostic must be allowed to say that the reference already contains enough structural information. It is retained as a non-island strong-reference boundary, not repaired into a positive result.

## 2. Why the paper is now being sharpened around islands

The broad proposition that suitability, accessibility and connectivity should be combined is already mature. Occupied-neighbour predictors, incidence-function connectivity, habitat-network occurrence models, resistance/current-flow approaches, threshold sensitivity and multi-model connectivity uncertainty all have clear precedents. EOG cannot earn strong novelty merely by adding a graph to an SDM.

Island biogeography offers a more precise theoretical target: **the adequacy of the isolation term itself**.

That does not mean multidimensional island isolation is new. The closest island literature already includes:

- Long, Trussell & Elliman (2009), DOI `10.1890/08-1337.1`: explicit stepping-stone isolation;
- Weigelt & Kreft (2013), DOI `10.1111/j.1600-0587.2012.07669.x`: 17 island-isolation metrics in 68 variants across 453 islands, including surrounding land area and stepping-stone information;
- Sillero, Biaggini & Corti (2018), DOI `10.1093/biolinnean/bly033`: graph-theoretic structural connectivity among islands;
- Carter, Perry & Russell (2020), DOI `10.1111/jbi.13778`: 16 isolation measures across 890 New Zealand offshore islands reduced to three major axes—**mainland distance, stepping stones and insular network position**;
- Daniel et al. (2023), DOI `10.1111/cobi.14047`: graph-based connectivity validated using independent presence–absence and genetic evidence.

These papers remove several tempting novelty claims. EOG does not discover stepping stones, multidimensional isolation, network position, graph-based island connectivity, or the idea of validating graph connectivity with biological data.

## 3. Island-specific gap that remains worth testing

The higher-value question is:

> **After generic multidimensional island isolation and conventional source-pressure information are already represented, does the target island's position relative to the observed source network of the focal species retain held-out incidence information?**

This makes the distinction between two kinds of island isolation explicit.

**Species-independent archipelago isolation** asks how an island is placed relative to continental mainland, surrounding islands, surrounding landmass, generic stepping-stone routes and the island network itself.

**Species-conditioned archipelago configuration** asks how the same target is placed relative to the **outer-training occupied source islands of the focal species** through the same declared archipelago graph.

The novelty target is therefore not continuity. It is a **leakage-safe empirical test of whether generic island isolation is structurally sufficient for species incidence**.

In the literature audited for this project, we did not identify a directly equivalent design that simultaneously fixes a strong multidimensional island-isolation reference, rebuilds all response-derived source features from outer-training occurrences only, and evaluates only the final species-conditioned structural increment on held-out data. This is an audit conclusion, not an exhaustive priority claim.

## 4. The new island test is prospectively frozen, not a reopened old outcome

The distinction is critical.

**Forbidden:** reopen or retune the original A-Islands/Tanzania analyses to manufacture a stronger story.

**Authorized exactly once:** execute the independently specified A-Islands island-isolation adequacy extension frozen in:

- `docs/aislands_isolation_adequacy_preoutcome_contract.md`;
- `validation/aislands_isolation_adequacy_20260812/preoutcome_contract.json`;
- `validation/aislands_isolation_adequacy_20260812/area_gate_expected.json`;
- `validation/aislands_isolation_adequacy_20260812/mainland_gate_expected.json`.

The extension was designed before its species outcomes were inspected. Its reference design is marked `final_before_extension_species_outcomes`; after execution, no reference variable, scale, class gate, taxon subset or interpretation rule may be changed in response to the direction of the result.

### Outcome-free geographic gates already passed

The same frozen A-Islands v1.0 polygon shapefile yielded finite positive area for all 842 surveyed/model-linked islands. Frozen area-table SHA-256:

`496789783a98e55e1b9552f6f6d28e7b4567ef0f52c795657c7e2fea9c60aae2`

Natural Earth 1:10m Admin-0 Countries v5.1.1 was frozen before species outcomes. The continental Australian mainland is the largest polygon ring in the unique country feature `ADMIN=Australia AND ADM0_A3=AUS`.

- Natural Earth archive SHA-256: `ce1ac7036499a0edd641fbc093cd209a98f96a49d2eca8480aaacad35138a7f6`;
- mainland ring SHA-256: `18d151bfe8aee727677ba8beca6f244f80a9a3cb3b616de534cf4ba331f042a4`;
- 842-row mainland-distance table SHA-256: `7d6f52f03702dd0cfae061023a1b2f405e39397de73eaad21b97d24176c4f869`.

The dedicated hard-match CI regenerated and matched all of these fingerprints before any new species outcome.

## 5. Final island reference hierarchy

The pre-outcome hierarchy is closed.

### R0 — local environment

Frozen CHELSA BIO1, BIO5, BIO6, BIO12 and BIO15.

### R1 — recipient size and direct isolation

R0 plus:

- log island area;
- distance to continental Australian mainland;
- nearest outer-training presence distance for the focal species.

### R2 — source quantity and source landmass

R1 plus:

- multi-source exponential pressure;
- island-area-weighted multi-source pressure.

Both are averaged over the already-frozen 25/50/125/250-km scale ensemble, and a training presence cannot contribute to its own source feature.

### R3 — strongest generic island-isolation reference

R2 plus:

- nearest-other-island distance;
- surrounding-island pressure;
- surrounding-landmass pressure;
- unanchored component exposure;
- species-independent mainland stepping-stone frequency.

Thus R3 explicitly represents Carter et al.'s generic mainland-distance / stepping-stone / network-position axes and adds recipient area, source pressure, source landmass and surrounding landmass.

### C — species-conditioned archipelago probe

C = R3 + geography-only EOG connected frequency.

The EOG term is the fraction of the four frozen geography-only graphs in which the target's component contains at least one **outer-training occurrence of the focal species**. Training rows use focal self-exclusion. Held-out outcomes never define anchors.

### Primary endpoint

Primary contrast:

`C − R3` matched held-out log loss.

Negative values favour the EOG structural probe. Brier difference is secondary. Species are the replication unit; uncertainty uses 10,000 species bootstrap replicates and a 100,000-replicate two-sided sign-flip diagnostic with seed 20260812.

The outcome may be positive, null, adverse or too sparse to determine. All are acceptable results.

## 6. What a positive island result would mean

If `C−R3` is robustly negative with its uncertainty excluding zero, the permitted central claim is:

> **Across Australian continental-island plant incidences, species-conditioned archipelago configuration retained held-out information beyond climate, recipient island area, continental-mainland distance, direct and area-weighted species-source pressure, surrounding island number and landmass, generic mainland stepping-stone accessibility, and species-independent island-network position.**

That is substantially stronger than the original A-Islands claim. It would justify framing EOG as a test of whether a conventional multidimensional isolation description is structurally sufficient for the focal species.

It would still **not** establish historical colonisation routes, realised stepping-stone use, dispersal probabilities or causal movement mechanisms.

## 7. What a null or adverse island result would mean

If R3 absorbs the EOG increment, do not weaken R3.

That outcome would show that the original `0.6177466` signal beyond local climate + nearest source is explainable by a sufficiently rich combination of conventional multidimensional island-isolation and source/landmass information. That is a scientifically useful saturation result and an important boundary on the EOG claim.

The paper would then retain the broader structural-adequacy contribution: A-Islands demonstrates what appears missing under a weaker reference, the new island extension identifies whether conventional island-isolation information absorbs that signal, and Tanzania demonstrates an adverse increment beyond a strong matrix-aware connectivity reference.

## 8. Journal decision tree

### Route A — robust residual island increment: *Journal of Biogeography* first

If the frozen `C−R3` test is robustly favourable, **Journal of Biogeography becomes the preferred first target**, Research Article.

This route is justified only if the manuscript is rewritten around a broad biogeographic question rather than around the EOG acronym. The journal currently asks papers to articulate their theoretical foundations and conceptual advances, encourages precisely framed questions of broad biogeographic interest, and requires rigorous analysis and argument.

Editorial pitch:

> **Is multidimensional island isolation structurally sufficient for species occurrence?** Using 886 plant taxa across 842 Australian continental islands, we separate recipient environment and area, mainland isolation, source pressure, surrounding landmass, generic stepping-stone accessibility and generic network position from a final species-conditioned archipelago term, with every response-derived source feature reconstructed inside the outer-training boundary.

Tanzania remains a secondary non-island stress test showing that the generic structural term is not universally additive.

### Route B — no residual island increment: *Ecological Informatics* first

If R3 absorbs the species-conditioned EOG term or the extension is indeterminate, return to the broader **Ecological Informatics** Original Research Paper framing.

The central contribution then remains leakage-safe, reference-conditioned structural adequacy testing and transparent positive/adverse/indeterminate boundaries rather than a new island-isolation concept.

### *Methods in Ecology and Evolution*: NO-GO for this empirical paper

MEE remains a poor first target unless a separate prospective method-development layer adds known-truth simulations, calibration/error analysis and a generally reusable methodological advance beyond the present combination of established components.

### *Ecological Modelling*: conditional backup

Retain *Ecological Modelling* as a backup for the broader computational/model-assessment route if *Ecological Informatics* rejects on fit rather than a fatal validity issue.

## 9. Current stop/go rule

**GO for the one frozen island-isolation adequacy execution. HOLD manuscript release, DOI reservation and journal submission until that result is incorporated.**

The sequence is fixed:

1. merge the novelty/island pre-outcome strategy to `main`;
2. create a separate outcome branch from that immutable contract state;
3. reproduce all frozen A-Islands, area and mainland fingerprints;
4. execute the 886-taxon `C−R3` comparison exactly once;
5. freeze raw predictions, applicability accounting, species summaries, uncertainty and a result fingerprint;
6. report the result regardless of direction;
7. choose Route A or Route B using the decision rule above;
8. only then revise the manuscript, complete human/release gates and mint the final DOI/tag.

Do not reopen the frozen outcome analyses. Do not add a second positive dataset, species-specific radii, trait-informed edges or weaker references after seeing the island extension. The novelty-maximization strategy succeeds only if the stronger hypothesis is allowed to fail.