# EOG cross-phase ecological synthesis v1 — source geometry, resilience, and historical observability

**Status:** post-result synthesis of already frozen known-truth programmes. **Not** a new preregistration, new independent replication, biological mechanism identification, or third manuscript.

**Authoritative machine ledger:** `validation/eog_virtual_world_ecology_synthesis_v1/claim_ledger_v1.json` (pins the Git blob SHA, result fingerprint, authoritative run, and audited JSON paths for every numerical claim).

## Decision: one ecological question, not another method or paper by default

> **How does the spatial arrangement of source populations trade off the geographic area a distribution can reach against its resilience to source loss, and what does the same arrangement do to how much of its history can be reconstructed?**

The strongest next contribution would be **an independent ecological validation of the joint source-layout trade-off**, *not* another graph metric, BAM decomposition, or fresh synthetic operator selected after seeing the existing results.

Three distinct outcomes must remain separate:

1. **Expansion:** union geographic area reachable from all declared sources, under the frozen transition world.
2. **Source-loss insurance:** fraction of that reachability retained after removal of the worst source. **This is a structural reachability ratio, not species persistence, extinction probability, or fitness.**
3. **Historical observability:** whether the declared library of transient occupancy/provenance observations distinguishes source-activation histories. **This is about evidence sufficiency, not an intrinsic adaptive property of the population.**

The existing v18–v26 panels are related and reuse constructed landscapes. Contrasts across these phases are **not a single preregistered three-way mediation test** and their sample sizes cannot be pooled as if independent.

## 1. Supported synthetic mechanism: source placement, coverage, and insurance (v18)

The same **384 directed synthetic landscapes** and the same number of source populations were compared under clustered versus spatially dispersed placement.

| Fixed two-source comparison | Clustered | Dispersed |
|---|---:|---:|
| Union reachable fraction | 0.4042 | **0.4454** |
| Worst-source-loss retention | **0.6933** | 0.2641 |
| Multi-source basin overlap | **0.6403** | 0.0779 |

Placement changed two-source coverage in **347/384** landscapes; the preregistered coverage–insurance trade-off occurred in **280/384**. In **225/384**, two dispersed sources reached more geographic area than three clustered sources.

**Interpretation:** source **number**, coverage, and worst-source-loss redundancy are not interchangeable landscape variables. It does *not* show that the clustered population survives disturbances better demographically.

Related turnover experiment **v20**, with the number of sources restored to three after a frozen worst-source loss, found:

- **718/768** design rows changed coverage with the replacement arrangement;
- **352/768** had below-original coverage under all three allowed replacement strategies;
- **407/2,304** strategy cases exceeded the original coverage.

Replacing a count need not restore a spatial function. Again, none of these are realized extinction/recolonization experiments.

## 2. A second dimension: confluence hides source origin, observation may recover it (v19, v21–v22)

In the v19 two-source networks, mean fraction of union-reachable nodes compatible with multiple sources:

- **Clustered 0.6403** versus **dispersed 0.0779**.

For the v21 source-activation-order experiment (three source identities held fixed, activation order changed), all **768** design rows converged to the same equilibrium occupied set across compared histories (**0** equality violations), while **507** rows retained an equilibrium provenance-map difference.

A complete post-activation transient occupancy library in v22 identified exact activation history in:

- clustered source layouts: **231/384**;
- dispersed source layouts: **348/384**.

**Important preregistered refutation:** v22 Q3 predicted a lower *conditional minimum number of snapshots* for dispersed layouts. This was **REFUTED**: it was exactly **one** for every identifiable row in either layout. Source placement changed the **fraction of histories observable**, not the minimum burden conditional on observability. Moreover, **428/768** design rows admitted an earlier single snapshot that identified full history when the later t8 snapshot alone did not.

**Interpretation:** basin overlap and observation timing alter what historical origin can be inferred; history observability must not be confused with colonization success or insurance. Do not claim a jointly identified pathway from source placement to memory from these separate frozen tests.

## 3. Static distributions can conceal a different intervention response (v10–v12)

The v10 hand-designed worlds were constructed with identical A, B, M masks, realised G and identical nodewise marginal support. They differed only in transition topology. At 14 nodes:

- chain topology: mean knockout retained fraction **0.5385**, mean critical nodes **12**;
- star topology: corresponding values **1.0000** and **0**.

Independent *random topology fixtures* v12 retained the same static-map equivalence while varying 12 graph worlds per replicate across **144** panels; the pooled edge count versus knockout retention Spearman correlation was **+0.750**. For the **48** panels with 12 active nodes, all 12 pairwise-relation signature classes were distinguishable.

**Boundary:** this is a controlled *information insufficiency* demonstration, not a new network-robustness theorem, a real extinction result, or proof that EOG outperforms a graph-aware comparator. Network redundancy, graph/circuit connectivity and patch-removal robustness are all established ecological science (see prior art below).

## 4. Why identical current distributions can have different history-sensitive states (v26)

Under four preregistered maps from colonization age to current state, the v26 result was **target-dependent** rather than a universal history-storage mechanism.

- History-blind current occupancy: **0/768** rows showed history memory.
- Three different age-sensitive targets: each showed some memory in exactly **726/768** rows (**P5 REFUTED**), but differed in the fraction of affected nodes:
  - persistent lag-2 binary state: **0.2743**;
  - transient age-1-to-2 binary state: **0.4583**;
  - saturating four-class age state: **0.4918**.
- Among **45** residual cases whose colonization-age differences were hidden by equilibrium occupancy and source provenance, the persistent target distinguished **12**, but the transient and saturating targets each distinguished **45**.
- The preregistered claim that a richer process necessarily rescues hidden rows was also **REFUTED (P6)**.

The result depends on the *mapping of latent history to the declared observed state*. It establishes neither a universal biological memory law nor which natural process (competition, facilitation, resource conditioning, demography) generates memory.

**Link, not duplicate paper:** v26 motivates the separately developed `manuscript/history_storage/` work, where two manipulated real experiments show that contemporary ecological measurements retain different amounts or structural types of assembly history. Those experiments do **not** experimentally validate the source-placement mechanism of v18–v22.

## 5. What is actually new relative to ecology prior art?

Existing ecological network research already studies fragmentation, redundancy, connectivity, patch removal and the insurance value of network structures. Historical contingency and ecological memory, and the difference between transient and equilibrium assembly, are established too.

Directly relevant prior art:

- *Indicators for assessing the robustness of metapopulations against habitat loss*, **Ecological Indicators** (2021), DOI [10.1016/j.ecolind.2020.106809](https://doi.org/10.1016/j.ecolind.2020.106809).
- *A comprehensive framework to assess multi-species landscape connectivity*, **Methods in Ecology and Evolution** (2024), DOI [10.1111/2041-210X.14444](https://doi.org/10.1111/2041-210X.14444).
- *Community assembly: alternative stable states or alternative transient states?*, **Ecology Letters** (2011), DOI [10.1111/j.1461-0248.2011.01663.x](https://doi.org/10.1111/j.1461-0248.2011.01663.x).
- *Quantifying the impact of ecological memory on the dynamics of interacting communities* (2022), [open article](https://pmc.ncbi.nlm.nih.gov/articles/PMC9200327/).

Consequently, **neither "a graph contains more information than a map" nor "sources create insurance" is a sufficient novelty claim**. The still-unverified ecological hypothesis worth pursuing is that a *single independently observed source configuration* jointly determines (i) the area reached, (ii) the response to loss/turnover of a source, and (iii) the identifiability of its source history; importantly, these outcomes may order source placements differently.

That stronger joint claim is **NOT YET TESTED**. The source panels support different pieces of it, not their natural prevalence or a field-calibrated causal mechanism.

## 6. External validation contract — do not expose responses before design freeze

One target is enough; avoid a new arbitrary synthetic landscape sweep.

**Candidate system requirement:** independently published or prospectively registered patch/population network with georeferenced source events, at least one dated source loss/turnover or recolonization sequence, response-independent source/patch registry, declared survey opportunity, and detection semantics sufficient to separate true absence from nondetection. A candidate lacking these data should `STOP_NOT_IDENTIFIABLE` rather than be forced into a negative result.

**One primary ecological test:** conditioned on the same baseline source count and an independently frozen network, does source arrangement and source-basin overlap add held-out explanation of **post-source-loss reachable/recolonized coverage** beyond (a) source count, (b) initial occupied fraction, (c) nearest-source/geographic distance, and (d) established network robustness/connectivity measures? Do not substitute simulated structural retention for realized recolonization without an explicit observational link.

**Secondary test, only if time-resolved provenance exists:** are histories more frequently identifiable under dispersed than clustered source configurations **at matched timing, effort and source count**? The target is identification rate, **not** a predicted smaller number of observations conditional on identification (the latter failed in v22).

**Outcomes:** prospective paired heldout difference and uncertainty, comparator fidelity, observation-process calibration, and predeclared STOPs. No AUC-only promotion; an adverse or null result remains part of the denominator.

### Scope and paper decision

- v10–v12: static-map/topology failure modes → **background/diagnostic**, not a new main ecology result.
- v18–v22: spatial source geometry/insurance/history observability → **strongest candidate for an ecology-first external test**, presently synthetic only.
- v26: age-to-current-state storage → already linked to the separate **assembly-history** empirical manuscript.
- BAM inverse and future-target partial identification → already has its own **BAM identifiability** manuscript lane.
- **Decision: HOLD third paper.** The linked source-geometry story should not be promoted into a manuscript until an independent ecological endpoint, comparator baseline and observation contract exist.

### One metadata-only candidate; not a scored empirical validation

A public *Lepanthes rupestris* patch-occupancy archive is a plausible **candidate, not an approved confirmatory system**:

- Dryad [10.5061/dryad.9p8cz8wc6](https://doi.org/10.5061/dryad.9p8cz8wc6) advertises one `lepa_all.csv` file (~84.83 KB).
- The published study [Acevedo et al. (2020)](https://doi.org/10.1111/1365-2745.13361) describes **975 georeferenced phorophyte patches** monitored in **1999–2008**, with within-year repeated surveys used for a dynamic occupancy and detection model.
- The publication already showed an association between asymmetric connectivity and colonization. **That headline result is prior art, not new EOG support.** The EOG-added question would be *source-basin redundancy and observed post-turnover/recolonization* beyond this strong existing model, under a genuinely held-out temporal split.
- Archive metadata does **not** establish whether natural source-loss events, patchwise detection replicates and source attribution satisfy the new endpoint. Natural loss is not a randomized source-removal experiment.

The **metadata-only HOLD** with all pre-response gates is recorded at `validation/eog_virtual_world_ecology_synthesis_v1/metadata_candidate_v1.json`. **No focal CSV response rows were downloaded or opened in this EOG candidate audit**, and no predictor, fit, outcome, source-loss estimate or new scientific score is reported. Only a separately frozen response-blind acquisition and detection contract can authorize further testing.

### Follow-on pre-response qualification outcome (new, separately frozen audit)

The initial metadata candidate above was deliberately a HOLD, not an authorized empirical analysis. A separate response-blind catalogue comparison has now reached the **v1 protocol STOP** `STOP_REGISTRY_SCHEMA_AND_DETECTION_UNQUALIFIED`: the Dryad and derivative dictionaries disagree on four physical column names (three coordinates and the 2004 second visit); the archive advertises one combined patch/occupancy CSV but no independently verified separate opportunity registry; the physical header, checksum, missingness coding and proposed source-loss event remain unverified. The 2020 published model's estimated detection is not independent calibration.

- Full provenance and precise stopping conditions: [Lepanthes pre-response audit v1](eog_lepanthes_pre_response_metadata_audit_v1.md).
- Frozen source catalog: `validation/eog_virtual_world_ecology_synthesis_v1/lepanthes_pre_response_catalog_v1.json`.
- A versioned deterministic **metadata-only** test/CI emits a STOP receipt without opening `lepa_all.csv`.

This is the failure of **this stringent EOG qualification contract**, not a negative ecological result or a defect attributed to the original study. The original v1 metadata HOLD entry is retained as historical state; the subsequent STOP is not backdated to it. No biological outcome has been scored.

## 7. Validation and non-retroactivity

This is a post-result evidence synthesis, *not* a new independently randomized validation. `tests/test_eog_virtual_world_ecology_synthesis_v1.py` verifies all pinned Git source blobs, exact JSON fields, published result fingerprints, and the two preregistered **REFUTED** outcomes. It must not reopen or alter v10–v26 experimental results, the JBI BAM manuscript, the Ecology Letters history-storage manuscript, or the EOG-WF empirical 3/31/3 closure.
