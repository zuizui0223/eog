# EOG v45 — observing a source label is not the same as learning about a future state

## Scientific question and status

**Post-exposure audit of the original, already scored v44 source-only finite-world results.** This is *not* an independent registered ecological prediction, a new virtual-world run, a new biological finding or new EOG-WF endpoint. The original v44 18,432 source-world×cutoff-panel×target×policy rows, controls, Bayesian likelihood, three histories and assumed observation costs remain unchanged. They are loaded only from the source-verified archived GitHub Actions artifact, with the original result and complete per-world CSV SHA256 verified before any classification.

The goal is to separate two necessary observational gates for source-tag information to help forecast a particular future synthetic state:

1. **Acquisition opportunity.** Can at least one chosen site be occupied at the observation cutoff under a history compatible with the *observed cutoff occupancy*? Numerically, the original v44 output's **expected** occupied selected-site count is positive. A value greater than zero means **potentially** available—not guaranteed to be occupied for every prior history, not proof that a source label was actually sampled under the q=0.6 missingness channel.
2. **Target diagnosticity conditional on cutoff occupancy.** Does the *original noisy tag likelihood* actually distinguish histories that imply different predeclared future target states? Numerically, \`I(future target; cutoff-available noisy source tags | exact cutoff occupancy)>1e-9 bit\` in the original verified v44 result.

These are conditions in an idealized known-candidate-history model. They are neither genotyping precision or true ecological colonization probabilities.

## Source identity and audit limits

The source is [v44 original mainline](./eog_original_idea_asof_time_provenance_v44.md), original successful CI [run 39452406392](https://github.com/zuizui0223/eog/actions/runs/39452406392), artifact ID \`12279172589\`.

- Original entire GitHub artifact ZIP SHA256: \`066d3d48a9ab06b6817680c447df3a416f15c8614e84bf9caf0cf9c790abbdbe\`.
- Original 18,432-row \`per_world_asof_v44.csv\` SHA256: \`5f7ca0e158f23cc9d479bdb51539458bf6ce4da3dced11a64bd310e80aee5b8e\`.
- Original full numerical result JSON canonical SHA256: \`38c30f7de94574b26b8a0170bb25880d8a75f88433277de4b82bfbe7788d43ed\`.

The v45 audit protocol was frozen in commit \`8f4f752ac87cf2bf8c28e37f70b36ff13ef679b4\` **after primary v44 outcomes and opportunity counts had already been inspected**. It fixes definitions and source checks, but it is **not** an independent prespecification of the findings.

Full source grain must remain unique by \`design_key × panel × target × policy\`, with all 768 original worlds, 4 fixed time panels, 2 target types and 3 policies. The audit refuses duplicate or missing rows, nonfinite metrics, future target dates at or before the cutoff, and positive information with no potentially available source measurement. It does not resimulate graph evolution, alter the source-tag error channel or read 2021 Dryad bird/genetic records.

## Primary v44 t=2 observation → t=5 maturity-state target

Among the **126** worlds where the fixed synthetic future lag-2 maturity map was still ambiguous after exact t=2 occupancy, the original v44 per-world data divide as follows:

| Source-tag site choice | At least one selected site potentially occupied by t=2 | Tags add positive conditional information about target | Potentially measurable but no target information |
| --- | ---: | ---: | ---: |
| **Occupied-confluence priority** | **8/126** | **8/126** | 0 |
| Static source-confluence priority | **8/126** | **8/126** | 0 |
| Fixed source-blind random site ranking | **105/126** | **6/126** | **99/126** |

The **99 cutoff-observable but target-uninformative** random-policy cases show only that the **selected tags' reports do not distinguish this particular future target after conditioning on cutoff occupancy**. The archived aggregate does **not** distinguish a history-invariant source label from a label that varies across histories but carries no information about this target; it must not be used to claim a specific biological mechanism for each case. The original mean **expected cutoff-occupied sites per ambiguous world** is approximately 0.4524 for random, versus **0.0635** for cutoff-occupied confluence, yet **mean target information remains smaller** (0.015121 vs 0.020563 bit). Counting potentially readable tags is therefore **not an estimator of their predictive value**.

This does not prove confluence priority is materially better in nature. The absolute confluence-vs-random source-information difference is only ~0.00544 bit in this particular fixed panel; the cutoff-aware versus static confluence difference is **0.00120 bit**. All policy comparisons use the same known model-world graph, prior, q/e channel, and *one* original SHA256 random seed. No field measurement costs or uncertainty in population/source locations are modeled.

Among the 126 target-uncertain worlds, 40 have clustered and 86 dispersed candidate sources. All 8 confluence-policy acquisition opportunities with target-information are in clustered layouts (8/40); dispersed worlds have no cutoff-occupied confluence opportunity under this policy (0/86). This is not a randomized geometry treatment comparison or a causal ecological statement.

## Why the cutoff matters

Under the **same already frozen** cutoff t=4 → future t=5 maturity panel, only 59 worlds remain target-uncertain, but the cutoff-occupied confluence policy has **51/59** with source-tag acquisition opportunity, and **51/59** with positive future-target information. The corresponding original mean is **0.409902 bit** among target-uncertain worlds, compared with **0.020563 bit** for the early t=2→t=5 panel.

The denominators, forecast horizons and the cutoff-available source sets differ. The difference cannot be assigned causally to the two-step time gap, habitat suitability or origin clustering; the finite v44 design restricts both which tags exist by cutoff and which future targets are still uncertain.

The separate t=4→t=6 lag-2 target is **already exactly known from t=4 occupancy** by the age-2 definition. It correctly has *zero uncertain-target worlds*. Classify it as \`target_known_from_cutoff\`, not as missing data or failure to observe tags.

## Strongest conclusion and STOP

> **Predictive information is gated both by whether source history can already be sampled at the cutoff and by whether the available measurement distinguishes the chosen future ecological state. More observable records can provide less target-relevant information.**

This is the clearest *mechanistic interpretation of already exposed v44 known-truth source outputs*, not an independent result about natural dispersal or an approved new field sampling strategy. It clarifies why advancing a temporal cutoff can change apparent value of source evidence, and why EOG needs explicit evidence availability and target identity to avoid retrospective selection bias.

Do not continue extracting ever more filters and “positive results” from the same 768 finite worlds. In particular the v44 and v45 assays remain *idealized earliest-source labels, not genetic ancestry*; actual original 2021 Dryad individual/genotype files were unavailable on the tested public route. The next genuine empirical step requires independent age/first-arrival observations, real survey effort and measured error, or a different independently sourced ecological system. Original EOG-WF **3 scored endpoints /31 scientific STOPs /3 administrative exclusions**, Methods in Ecology and Evolution submission and no-fourth-endpoint hard stop are unchanged.

## Reproduce from the original frozen source artifact

The dedicated GitHub Actions workflow obtains the **same original v44 run artifact** with read-only access and checks its CSV/JSON hashes before deriving any summary. Local reproduction using a legitimately obtained original GitHub Actions ZIP:

\`\`\`bash
python -m pytest -q tests/test_eog_source_opportunity_v45.py
python benchmarks/audit_eog_source_opportunity_v45.py \
  --source path/to/verified-original-v44-actions-artifact.zip \
  --output build/eog-v45-source-opportunity-audit.json
\`\`\`

After an independently inspected successful audit, freeze the **complete canonical audit result SHA256** and key category tables; subsequent CI runs must reproduce it exactly. No biological raw data are exported or accessed.
