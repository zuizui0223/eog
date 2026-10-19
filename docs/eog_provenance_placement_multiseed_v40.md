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
