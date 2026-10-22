# EOG v44 — genuinely time-censored synthetic source-tag information about *future* ecological states

## Problem fixed, before scoring

The previous [v43 analysis](./eog_minimal_temporal_evidence_v43.md) showed that 12 previously source-aliased synthetic maturity targets could be distinguished by one additional ideal site×time occupancy report. **However all 12 maturity targets were at t=3 or 4, whereas the original input observation library already included t=8.** That was a retrospective reconstruction, **not** an as-of-date forecast test.

This v44 experiment explicitly repairs that information leak for a **new known-truth estimand**. The contract in \`validation/eog_original_idea_asof_time_source_v44/protocol_v44.json\` was committed at \`cbf852c9cd1aab7b36609ffca960da2325decadf\`, before any new cutoff-time target or observation metric was scored. The original v43 result is an external consistency boundary, **not** reused as a prospective test or as the v44 denominator.

## Scientific question

*Given all synthetic spatial observations actually available at time t, do imperfect source-of-earliest-arrival labels from sites already occupied by t improve the prediction of a predefined age-dependent state at time t+h?*

The benchmark is a fully specified finite-world Bayesian information test, **not real out-of-time field model validation**. The graph, potential source locations and propagation law are taken as ideally known at the cutoff; only the actual source activation order (among the same three v21 alternatives) is unknown. A particular hidden activation history is never revealed to the forecaster.

## Frozen independent clock convention

Instead of the old history-dependent \`Tstar\` (which can be selected using future arrivals from all possible histories), all forecast endpoints are fixed *before scoring*:

| Panel | Input cutoff t | Future target time | Meaning |
| --- | ---: | ---: | --- |
| **Primary early** | 2 | 5 | Source history can include a source activation at t=4, **after** the observation cutoff |
| Secondary near | 4 | 5 | One-step-ahead latent maturity-state value |
| **Identity negative control** | 4 | 6 | Lag-2 maturity at 6 is **definitionally equal** to cutoff occupancy at 4 |
| Secondary late | 4 | 7 | Three-step-ahead state, potentially reflecting arrivals after cutoff |

For each panel, the only baseline observation is a **complete perfect non-source-node occupancy census at the cutoff t**, plus assumed externally known graph and candidate source coordinates. Previously used perfect t=4, 5, 6 and 8 snapshots **are not combined into the observation** unless they happen at the cutoff. No future occupancy snapshot, future literal source tag, target-state readout or history-specific first-arrival time is admitted as an observed predictor.

**Target maps** reuse the unchanged v26 process functions evaluated at the fixed future target date: lag-2 binary mature state (age since first arrival ≥2) and transient age1-to-2 binary state. Non-source nodes that have not yet been reached have age less than zero, hence both binary states are false. These are not real breeding, survival or reproduction states.

## Cutoff-available source tags and fair placement

A source-of-earliest-arrival tag can be measured **only if the sampled non-source site is already occupied at the cutoff**. An empty site has a deterministically missing tag, even if a future source would arrive there later in the simulator.

The original v39 synthetic miscall channel is reused with assumed q=0.6 availability at occupied sites, e=0.1 categorical source-tag misassignment, and exact finite enumeration of possible missing/wrong labels. A q=1/e=0 measurement is a within-cutoff perfect-tag upper limit, never a future complete provenance library. No error, coverage or site cost is estimated from the 2021 inaccessible genetic archive.

Compare up to three sites under:

- **Static confluence:** same v39 static potential-source overlap ranking, fixed before seeing any cutoff observation.
- **Static random:** same v39 history-blind SHA256 seed and per-node ranking.
- **Cutoff-occupied confluence:** among potential confluence sites, preferentially sample sites already *observed occupied* at the cutoff, then order by static potential-source count and ID. The availability decision can use observed cutoff occupancy; it cannot inspect any future events or which activation history is true.

All three policies get the same **nominal budget** of at most three sites, but the *number actually occupied by the cutoff* is separately reported. Selection costs and observability/field feasibility are not equated.

## Exactly computed estimands

Across all **768 original v23 worlds**, retain all three candidate activation orders with uniform prior. Condition on cutoff-time occupancy to form observational equivalence classes. Each class has its own permitted cutoff-occupied measurements. Exactly enumerate all noisy reports under the known synthetic likelihood and compute:

- \(I(T_{t+h}; \text{source-tag reports up to }t \mid O_t)\) in bits;
- expected Bayes-optimal correct **future target-state** probability gain beyond cutoff occupancy alone;
- number of worlds where the target is still uncertain after observing the cutoff census;
- number of actually observable source-tag sites, as opposed to sites only reachable in the future;
- q=1/e=0 same-cutoff upper bound and zero-coverage control.

Report all 768 per policy/target/panel and the **cutoff-ambiguous-target** subset separately. Do not re-use v41's \`189\` histories conditional on multiple observations at future dates as the denominator.

## Precommitted falsifiable tests

1. **A1:** at t=2, future t=5 lag-2 maturity is uncertain for at least one original world under its own cutoff-time occupancy.
2. **A2:** genuinely cutoff-available imperfect source tags from observed occupied confluences add some future maturity information in at least one such world. May be refuted.
3. **A3:** sites still empty at the cutoff never provide future origin labels (mandatory leakage negative control).
4. **A4:** future lag-2 maturity at t=6 is already identical to the t=4 complete census, so source tags **must add zero** (mandatory target-definition negative control).
5. **A5:** occupied-at-cutoff confluence selection has higher mean maturity information than unchanged static confluence under primary cutoff t=2→5, among target-ambiguous worlds. May be refuted.
6. **A6:** with a correctly specified synthetic channel, perfect source tags *available by the same cutoff* cannot be less informative or reduce expected Bayes accuracy compared with noisy available tags (information-theory integrity control).

These decisions will be frozen even if the main positive target claim is refuted. **A3, A4 and A6 are structural/mathematical checks, not independent discoveries of real ecology.**

## Inference restrictions

Although the target time is strictly after the input date and the observation model rejects future label access, the forecaster is granted **the exact candidate source network, source positions, simulator and prior**, which are not available with comparable certainty in nature. This is therefore an *as-of-time-valid controlled model-world experiment*, **not a newly scored empirical held-out test of EOG**. The source tags in the simulator are first-arrival-source labels, **not genotyped ancestry, parentage or measured natal dispersal**. Perfect occupancy at the cutoff and independent missingness/misclassification are optimistic assumptions. All original 2021 Dryad genetic/individual data remain unavailable via the tested public source, and no new real demographic field observations are included.

The frozen original EOG-WF manuscript retains **3 scored endpoints /31 scientific STOPs /3 administrative exclusions** and the existing Methods in Ecology and Evolution submission boundary unchanged.

### Reproduce

\`\`\`bash
python -m pytest -q tests/test_eog_asof_time_provenance_v44.py
python benchmarks/run_eog_asof_time_provenance_v44.py \
  --output-dir build/eog-v44-asof-time
\`\`\`

The dedicated CI first checks the entire original v41 canonical 768-world result, then runs the strict cutoff-only report. An independently downloaded aggregate-only CSV plus full JSON will be frozen by exact SHA256 and reproduced in CI before merge.


## Source-verified first cutoff-only result (2026-10-20)

The original dedicated [Actions run 39452406392](https://github.com/zuizui0223/eog/actions/runs/39452406392) was independently inspected from its complete artifact **12279172589** (name \`EOG-V44-CUTOFF-ONLY-FUTURE-STATE-AGGREGATES\`). The 84,426-byte ZIP's SHA256 is \`066d3d48a9ab06b6817680c447df3a416f15c8614e84bf9caf0cf9c790abbdbe\`; the **complete original numerical JSON** canonical SHA256 is \`38c30f7de94574b26b8a0170bb25880d8a75f88433277de4b82bfbe7788d43ed\`, and the **entire 18,432-row per-world CSV** SHA256 is \`5f7ca0e158f23cc9d479bdb51539458bf6ce4da3dced11a64bd310e80aee5b8e\`. All three were independently verified. The fixed receipt at \`validation/eog_original_idea_asof_time_source_v44/result_frozen_v44.json\` requires future dedicated CI to match both original JSON and CSV exactly.

Original source integrity and completeness checks passed: 768 initial synthetic world designs × four cutoff/forecast panels × two v26 future target states × three predeclared site policies = **18,432 unique** keyed scenario rows. The original complete v41 768-world canonical result SHA256 was independently reproduced before any new future-state scoring. There were **zero future unoccupied-site source-tag exposures**, zero noisy-vs-perfect tag information bound violations and no use of old post-target v23 snapshots as predictors.

### Primary: as-of cutoff t=2 to synthetic maturity at t=5

At this early clock, **126/768 designs** had different possible future lag-2 maturity maps among activation histories compatible with the *same full observed cutoff occupancy*. Thus 642 designs already had their maturity map identified at cutoff under the assumed candidate-history model and cannot gain additional target-specific information.

The following refers to the **same 126 target-uncertain designs**. All site policies have **at most three nominal measurement locations**, but many are unoccupied, hence no source label can be read.

| Policy | Mean conditional future-maturity information gain | Expected correct future-target accuracy gain | Number of 126 designs with positive information | Mean actually occupied assay sites |
| --- | ---: | ---: | ---: | ---: |
| **Cutoff-occupied confluence** | **0.020563 bit** | **+0.012534** absolute probability | **8** | **0.0635** |
| Static confluence (v39) | 0.019359 bit | +0.011954 | 8 | 0.0582 |
| Static SHA256 random (v39) | 0.015121 bit | +0.009256 | 6 | 0.4524 |

Baseline Bayes correct-target probability across these 126 uncertain designs is **2/3** under the three equiprobable source activation orders. Under the cutoff-occupied confluence source-tag policy, the expected Bayes accuracy increases by **1.253 percentage points** to approximately **67.92%**. This is conditional on the defined synthetic world and known candidate histories, not observed holdout field accuracy.

The **advantage of cutoff-occupied selection over static confluence was only +0.001204 bit**. A1, A2 and the directional A5 hypotheses were supported, but the A5 criterion required *any positive mean gain*, not a materiality threshold. It would be misleading to promote a +0.001204-bit difference to an empirically superior or cost-effective field sampling method.

Using the exact per-world CSV, the 126 maturity-uncertain primary worlds comprise:

| Frozen source geometry | All worlds | Cutoff maturity-uncertain | Noisy source tags provide some information |
| --- | ---: | ---: | ---: |
| Clustered potential sources | 384 | 40 | **8** |
| Dispersed potential sources | 384 | 86 | **0** |

The geometry-conditioned candidate sets differ and are not matched experimental treatment pairs; do not claim clustered geometry causally increases predictability. They illustrate that observation *availability* and the specific future target matter.

### Horizon dependence and a target-definition negative control

The predeclared **cutoff t=4, target t=5** maturity panel retains **59** designs with unknown maturity from cutoff occupancy. Cutoff-available source-tag information is positive in **51/59**, with mean information **0.409902 bit**; this is far larger than the primary t=2→t=5 panel. The other same-t4 transient-state panel has **124** uncertain designs and **91** with positive information (mean **0.391593 bit**).

In the separately frozen **t=4→t=6** lag-2-maturity negative control, and across all **768** worlds, \`mature_at_6(node)\` is *definitionally identical* to \`occupied_at_4(node)\`, so source tags cannot add anything. There were **zero** ambiguous future target designs and exactly zero tag information for this target. In the t=4→t=7 panel, both original declared future state targets were already determined by cutoff occupancy within the restricted three-history world family; their uncertain-target denominators are **zero**, not 768 or 189. A result with zero ambiguity cannot validate a new predictive benefit.

### Six preregistered outcomes and the hard scientific boundary

All predeclared A1–A6 were **SUPPORTED** under the declared finite world ensemble. A3 (no future tags), A4 (lag-2 state identity) and A6 (perfect-current-tag upper bound) are **observation-leakage and mathematical controls**, not independent ecological discoveries. A1 confirms an eligible denominator, A2 confirms a **small, limited** positive model-world forecasting information value, and A5 confirms merely a tiny directional gain for a cutoff-aware policy.

This is the first version of this particular *synthetic source-tag/value-of-information experiment* that genuinely imposes a strict historical observation cutoff. It is **not** a prospective field trial or independent biological heldout forecast: propagation, potential source coordinates, complete cutoff census and correct likelihood are assumed known, the hidden activation order comes from only three original schedules and the abstract v26 maturity mapping is not measured animal or plant reproduction.

No actual Helgeland source/genetic data or island-year survey effort have been acquired. Do not add this as an EOG-WF fourth endpoint. The original Methods in Ecology and Evolution three scored /31 scientific STOP /3 administrative exclusions remain unchanged.
