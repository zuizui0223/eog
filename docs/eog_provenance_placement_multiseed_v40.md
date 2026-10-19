# EOG v40 — does confluence-targeting survive random placement seeds?

## Current boundary

**Post-v39-exposure sensitivity, not an independent new heldout biological experiment.** The pre-result v40 protocol was committed at \`ce72c8a258e3c3ddd8bd8c6e8b43e103501de745\`. v39's preregistered 2026-10-19 assay setting \`coverage=0.60\` and \`miscall=0.10\` was already exposed when this design was chosen.

Previous [v39](./eog_imperfect_provenance_sampling_v39.md) held three static potential-source confluence nodes up against **one** fixed response-blind SHA256-ranked random placement (same three selected nodes allowed). Among 88 fair occupancy-aliased scenarios, the conditional information mean was **0.655816 vs 0.648676 bit**, a tiny **+0.007140-bit** advantage. This is much smaller than the total value of a noisy source-tag readout. An apparent directional success under one seed does not establish a robust sampling principle.

## Key scientific distinction

**Potential source confluence** means more than one source could reach the same node under the static landscape. It does **not guarantee** that the *set of earliest-arriving sources* changes between different activation histories. A graph node can be a confluence under topology and yet have a history-invariant source label, adding no information about order.

The v40 experiment therefore separates:

- static graph-overlap heuristic chosen *before* seeing hidden history labels;
- information actually carried by those labels *after* the synthetic truth is inspected;
- variability due to a response-blind placement algorithm's random seed, not ecological process differences.

## Frozen design and controls

- **Same 768 v23 design rows** (384 landscapes × clustered/dispersed sources); v39 579 occupancy-identifiable, 189 occupancy-aliased, and 88 equal-budget fair alias rows must all reproduce exactly.
- **Same 88 fair three-site rows in every comparison**. No refitting, resampling of latent landscapes, dropping inconvenient outcomes, or outcome-conditioned eligibility.
- **Exactly 64 new deterministic random seeds** \`eog-v40-20261019-random-seed-000\` to \`063\`, with SHA256-based per-node ranking (seed, landscape key, node ID). Selection uses only eligible node identity, not history-specific provenance tags.
- Fixed comparator: v39's static potential-source-confluence top 3, chosen by possible-source count then node ID. Its original **0.655816 bits** must match anew from source. The prior one-random-seed **0.648676 bits** is an independent frozen regression target.
- Primary channel: **q=0.60, e=0.10** with v39's explicit synthetic missingness/label-confusion likelihood and exact finite Bayesian enumeration.
- Secondary perfect-tag q=1/e=0 upper comparison **cannot replace the primary setting**; site-to-site variation is summarized at both placements.
- No bird/genetic records, true ancestry, calibrated assay error, real-world sampling cost or new EOG-WF result.

Primary estimand: fixed confluence mean conditional information minus the mean of the **64 random-seed-specific mean conditional informations**, each computed on the identical 88 designs. Report seed spread and world-paired positive/tie/negative counts; do not treat the 64 seeds as 64 independent ecological samples.

### Five prespecified tests

**M1 meaningful gain:** require confluence > random-seed mean by **0.020 bit**, with tolerance 1e-9; an advantage of 0.001 bit is not treated as ecological materiality.

**M2 stability across placements:** require at least 48/64 separate random seeds to have an 88-world mean below the confluence mean.

**M3 consistency across worlds:** require confluence to exceed each world's **own** random-seed mean in more than half (44) of the 88 matched design rows.

**M4 placement-seed sensitivity:** require an observed spread of more than 1e-9 bit between random-seed mean informations. This is mainly an implementation/robustness diagnostic.

**M5 topology-versus-information gap:** require at least one confluence-targeted node whose tag is invariant across the three truth activation histories. This is a structural distinction, not evidence about actual genetic measurement.

Refutations remain refutations. Seed-level success rates, effect-size thresholds, and uncertainty cannot be redefined after the result.

## How to run

\`\`\`bash
python -m pytest -q tests/test_eog_provenance_placement_multiseed_v40.py
python benchmarks/run_eog_provenance_placement_multiseed_v40.py \
  --output build/eog-v40-provenance-placement-64seeds.json
\`\`\`

The dedicated CI will execute the original world generator with fixed parent fingerprints, test the synthetic controls, upload aggregate seed/world diagnostics and require exact full-result SHA256 after independent inspection. The output does not export latent individual bird/genetic records or historical source-route claims.

## Ecological interpretation constraint

A positive v40 result can mean that topology-selected assay locations are more informative *under the chosen synthetic likelihood and declared worlds*. A negative or non-material result is equally scientifically useful: it would show that the mere existence of possible source-basin overlap does not suffice as a practical rule for placing noisy ancestry measurements. Even a very large simulated gain would **not prove** genetic ancestry measures first arrival, nor that real island-year survey effort or genomic assignment behaves like independent symmetric q/e errors. EOG-WF science stays 3 scored /31 scientific STOP /3 administrative exclusions.


## Source-verified precommitted result (2026-10-19)

The full independent v40 original-source known-truth [Actions run 39240966984](https://github.com/zuizui0223/eog/actions/runs/39240966984) completed successfully after a **schema-identifier-only typo** in the initial test/runner was repaired. The original v23 stored schema uses \`eog.original_idea_provenance_observability.result_summary.v23\` with an underscore; no 2021 data or v23/v39 biological/numerical assumptions were changed. The authenticated aggregate artifact **12180579805** was downloaded independently and fully inspected. ZIP SHA256 \`6a0ff87ba9201fb471a6c4e9cf12b476b1584deb4711e62fce68058dfd5ff27a\`; **complete canonical original JSON SHA256** \`e366c4945e2110bd6359c3db1ae86e4e01bb6df8741fc4370af6ae54b5792f91\`. A frozen receipt pins those digests and all five outcomes at \`validation/eog_original_idea_provenance_placement_multiseed_v40/result_frozen_v40.json\`.

The 768/579/189/88 v23 and v39 denominators and the previous **0.65581640998 / 0.64867601835** selected-versus-one-random-seed mean information both reproduced exactly.

### Primary fixed noisy-assay result — materiality refuted

On the 88 matched equal-budget occupancy-aliased v23 designs, q=0.60, e=0.10, three measured sites:

| Placement | Additional conditional history information | Accuracy gain beyond complete occupancy |
| --- | ---: | ---: |
| Frozen potential-confluence heuristic | **0.655816 bit** | **0.333056** |
| Mean across all 64 SHA256-blind random site seeds | **0.647256 bit** | **0.329586** |
| Confluence−random ensemble difference | **+0.008560 bit** | **+0.003470 (0.347 percentage points)** |

The precommitted **+0.020 bit materiality requirement was NOT met**. Hypothesis M1 was **REFUTED**, not a newly promoted field recommendation.

The 64 random-seed-specific means ranged from **0.640300 to 0.653048 bit**, median **0.647128 bit**, with 10th/90th quantiles **0.644923 / 0.649890 bit**. All 64 random seed means fell below confluence: M2 **SUPPORTED**, and actual random seed variability M4 **SUPPORTED**. Thus the *direction* of the small average benefit is not explained by the one v39 seed alone, even though it is not of predeclared meaningful magnitude.

Critically, comparing each ecological design with its **own** mean across 64 random placements gave:

- **34/88** designs strictly favored confluence targeting;
- **54/88** were equal within 1e-9;
- **0/88** strictly favored the random-ensemble mean.

Median world-paired information advantage was **zero**. M3 (benefit in more than half the fair ecological worlds) was **REFUTED**.

### The important design limitation: no dispersed geometry in the fair stratum

**All 88 of the v39 fair three-confluence-site / occupancy-aliased worlds have clustered source geometry.** None of the dispersed-source scenarios supplied three eligible confluence assay sites under this fixed source-placement scheme. Thus the strict v40 88-world comparison **does not estimate the effectiveness of the topology heuristic in dispersed-source landscapes**.

The static-topology-versus-history-label structural control counted **264** fixed targeted confluence site selections (88×3) and **zero** whose source-of-first-arrival tag was history-invariant across the three activation schedules. M5's positive prediction was therefore **REFUTED within this very specific selected stratum**. It does not prove *all* possible topological confluences are informative: unselected, lower-ranked confluence sites and nonfair worlds were not the M5 testing population.

### All five predeclared hypotheses, including negative results

| Hypothesis | Verdict |
| --- | --- |
| M1: confluence selection beats 64-seed random by at least 0.020 bit | **REFUTED** |
| M2: confluence beats at least 48/64 seed-level averages | **SUPPORTED** (64/64) |
| M3: confluence improves more than half the 88 matched ecological worlds | **REFUTED** (34/88) |
| M4: independent deterministic SHA placements vary with seed | **SUPPORTED** |
| M5: some of the selected top-3 confluence tags remain history-invariant | **REFUTED** (0/264) |

M4 is a robustness test, not a novel biogeographical generalization. M1–M3 were evaluated post-v39 discovery of the tiny effect and therefore **do not add an independent field-data replication** even with a frozen v40 protocol.

**Scientific implication:** A source-provenance assay can add substantial information in a synthetic identifiable context even under missingness and miscalls, but static topological confluence ranking delivers only a **weak, conditional mean placement advantage** over properly matched response-blind random placement. Sampling-site design needs more than static overlap (e.g. actual diagnostic readout uniqueness, field feasibility, detection and misassignment calibration) and should not be marketed as already solved by EOG. None of these first-arrival-tag statements identify real genetic ancestry, true colonization, dispersal, island-year effort, or a fourth EOG-WF endpoint.
