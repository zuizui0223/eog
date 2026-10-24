# EOG development mainline

## Status

This file is the **single source of truth for the current scientific and release mainline**.

The fresh paired-complementarity validation line is now **closed**.

Frozen empirical boundary:

- fresh scored endpoints: **3**;
- endpoint pattern: **favorable / favorable / adverse**;
- scientific/protocol STOPs: **31**;
- administrative exclusions: **3**;
- fourth fresh endpoint allowed: **false**;
- candidate hunting hard stop: **true**.

Frozen product boundary:

> **Layer A remains an auditable structural compatibility / contraction / falsification framework. Layer B is a world-label-invariant, context-dependent predictive complement whose added value is not uniformly beneficial.**

Frozen submission boundary:

- primary route: **Methods in Ecology and Evolution**;
- Nature Ecology & Evolution escalation trigger: **closed**;
- primary aggregation: **endpoint-wise; no row-level pooling or common-effect claim**.

Canonical closure assets:

- [`../manuscript/paper_ready/submission_boundary.json`](../manuscript/paper_ready/submission_boundary.json)
- [`../manuscript/paper_ready/methods_results_core.md`](../manuscript/paper_ready/methods_results_core.md)
- [`../manuscript/paper_ready/fresh_endpoint_results.csv`](../manuscript/paper_ready/fresh_endpoint_results.csv)
- [`../manuscript/paper_ready/candidate_flow_table.csv`](../manuscript/paper_ready/candidate_flow_table.csv)
- [`../manuscript/paper_ready/generation_manifest.json`](../manuscript/paper_ready/generation_manifest.json)

The previous state in which no fresh post-Daphnia paired endpoint had completed is historical and must not be used to reopen candidate search.

## Current known-truth result (v39–v45, 2026-10-24)

**Active scientific status: origin-history information can survive an imperfect
observation channel, but the proposed static-confluence placement heuristic did
not pass a preregistered *materiality* criterion.** These are controlled
known-truth results, **not** field-calibrated genetic ancestry or colonisation.

- [v39 imperfect provenance](eog_imperfect_provenance_sampling_v39.md) reused
  the exact v23 **768 design worlds** (579 occupancy-identifiable; 189 occupancy-
  ambiguous). Perfect combined occupancy + all ideal earliest-source tags
  identifies 687. Under *assumed* tag coverage `q=0.60` / miscall `e=0.10`,
  three confluence sites supplied **0.655816 bit** of additional history
  information in the **88** equal-budget occupancy-aliased worlds; the single
  frozen response-blind random placement gave **0.648676 bit**.
- [v40 fixed 64-seed robustness](eog_provenance_placement_multiseed_v40.md)
  compared the **same 88 designs** to 64 deterministic, source-blind three-site
  random placements: random-ensemble mean **0.647256 bit**, fixed confluence
  **0.655816 bit**, difference **+0.008560 bit**, **below** the
  predeclared **+0.020-bit** materially useful threshold.
- All **64/64** random seed *world-mean* scores were below the fixed confluence
  score, but only **34/88** individual worlds strictly favored the targeted
  policy, **54/88** tied within 1e-9 and none disfavored it. **All 88**
  fair-world comparisons have **clustered**, not dispersed, source geometry.
  A seed-level win is therefore neither 64 independent ecological replicates
  nor broad landscape generality.
- v40 preregistered verdicts: **M1, M3, M5 REFUTED; M2, M4 SUPPORTED**.
  The entire independently inspected v40 result is frozen by SHA256
  `e366c4945e2110bd6359c3db1ae86e4e01bb6df8741fc4370af6ae54b5792f91`
  at `validation/eog_original_idea_provenance_placement_multiseed_v40/result_frozen_v40.json`.

### v41: value for a declared present ecological-state target

The new [v41 original-EOG target-specific benchmark](eog_provenance_ecological_state_value_v41.md)
reuses the **same 768 v23 latent histories** and the unchanged v39 synthetic
source-tag coverage q=0.60/miscall e=0.10; it uses the previously frozen
v25–v26 *lag2 persistent maturity*, *transient age 1–2* and *saturating age*
present-state targets at the same common structural T*. Nothing is calibrated
to actual animal or plant maturation.

Among **189** v23 four-snapshot **occupancy-aliased** source-history design
rows, the at-most-three-site confluence source-tag readout added information
about **exact history in 120** (mean **0.404169 bit**) but information about
the frozen **lag2 mature/not-yet-mature current state in only 48** (mean
**0.140648 bit**). Exactly **72** rows gained information about past history
while gaining **zero** about the declared maturity target. The same source-tag
observation had **0.177515 bit** of mean information about the transient
age-1-to-2 state and **0.208385 bit** about the saturating age class;
history-blind occupancy as target had exactly zero additional information.

Complete ideal source/occupancy observations left **81** exact-history
equivalences, including **12** whose histories differed on lag2 maturity
and **45** on transient/cap3 state. Even complete *perfect source identity*
does not identify those abstract present-state differences. Original v25/v26
counts and the v39 exact history Bayesian calculation were reproduced
independently. Five v41 hypotheses V1–V5 were SUPPORTED, but V4 (parent
count) and V5 (data-processing bound) are structural **integrity controls**,
not independent biological discoveries.

**Updated scientific decision:** `more information about a hidden
history` and `more information about the current ecological target` are
**different estimands**. Do not claim a biologically meaningful source assay
simply because it improves exact-history information in simulation.
The v41 entire result is frozen by canonical JSON SHA256
`34f6f2bd94b9b22854eb699c97607ec2b9408f0ea55bcd6d5103a4019581125d`
at `validation/eog_original_idea_provenance_ecological_state_v41/result_frozen_v41.json`.

**Decision:** source/provenance measurements may distinguish histories that
occupancy cannot, but **static confluence ranking should not be recommended as
a materially better field sampling design** based on these results. Actual
genetic assignment error, survey effort and location-to-source equivalence
remain unresolved. The attempted [original Helgeland 2021 public Dryad
README](eog_helgeland_saatoglu2021_original_data_access_gate_v1.md) returned
HTTP 403; no 2021 individual/genetic record was analyzed. Stop additional
same-archive proxy rescreens. This programme must **not** be appended as a
fourth EOG-WF predictive endpoint. The frozen 3 scored / 31 STOP / 3
administrative-exclusion denominator is unchanged.

## v42–v44: target uncertainty and as-of-time source evidence (2026-10-22)

The [v42 exact source-uncertainty decomposition](eog_provenance_uncertainty_v42.md)
corrected an important v41 denominator interpretation. Of the **189** synthetic
designs whose full historical activation schedule was not determined by the old
occupancy observations, the v26 binary present-maturity target was **already
known from occupancy alone in 141**. In the other **48**, perfect source
readouts from the already selected sites can resolve the target in **36**;
**12** remain ambiguous even with every ideal source tag. Among remaining
noisy-assay maturity uncertainty, **64.4%** of entropy was attributed to
synthetic missingness/miscall and **35.6%** to the remaining source-tag
measurement-class ceiling, with **zero** added distinguishability from *extra
perfect* source-site coverage. Zero such coverage information does **not**
mean extra redundant noisy observations could not improve precision.

[v43 exact source-aliased timing](eog_minimal_temporal_evidence_v43.md)
showed that a model-aided single site×time binary occupancy readout can
distinguish the target in **12/12** previously source-aliased worlds without
simply reading the maturity definition at \`Tstar−2\`. Its essential
post-exposure chronology audit also showed **all 12 target times are only
t=3 or 4, while the baseline included a later t=8 census**. Thus this is
**retrospective smoothing/reconstruction, NOT any prospective forecast**.
The twelve worlds are already exposed and tiny (1–4 non-source nodes),
all clustered-source/rook. This 12/12 result must not be reused as an EOG
predictive validation.

[v44 strict as-of-time source evidence](eog_original_idea_asof_time_provenance_v44.md)
therefore fixed four new observation cutoffs and strictly later target
times *before scoring*, with **only cutoff-time occupancy and
source-of-earliest-arrival tags from nodes already occupied by cutoff**
available to the latent-history forecaster. It retained the original
768 synthetic worlds, uniform three-history prior, original v26 target maps
and an assumed q=0.60/e=0.10 source-tag channel.

- **Primary t=2→t=5 lag2 maturity:** **126/768** worlds have remaining
  future-target uncertainty after a complete cutoff occupancy census. Tags
  available at occupied potential confluences add nonzero conditional
  information in **8/126**, with mean **0.020563 bit** and **+0.012534**
  expected correct-target probability (1.25 percentage points). Static
  confluence yields **0.019359 bit**, the one fixed response-blind random
  seed **0.015121 bit**; the cutoff-aware minus static advantage is
  **+0.001204 bit**, not material evidence for a better field sampling policy.
- **Horizon matters:** t=4→t=5 maturity has **59** uncertain worlds; tags
  provide some additional information in **51/59**, mean **0.409902 bit**.
  At t=4→t=6 the lag2 maturity target is by definition *identical* to
  cutoff occupancy at t=4, so **0** target-uncertain worlds and no positive
  information can occur. The t=4→t=7 future states are similarly already
  determined by cutoff occupancy in the fixed three-history model.
- In the t=2→t=5 panel, all **8** positive-information worlds came from
  clustered-source conditions (8/40 eligible clustered vs 0/86 dispersed).
  This is conditional to candidate worlds, not a causal field inference.
  All six preregistered v44 tests were supported, but A3/A4/A6 principally
  enforce **time-leakage and mathematical integrity**, not independent
  biological discoveries.

The authentic v44 source-only CI result, exactly **18,432** synthetic
world×panel×target×policy rows, is frozen by canonical JSON SHA256
\`38c30f7de94574b26b8a0170bb25880d8a75f88433277de4b82bfbe7788d43ed\`
and CSV SHA256
\`5f7ca0e158f23cc9d479bdb51539458bf6ce4da3dced11a64bd310e80aee5b8e\`
in \`validation/eog_original_idea_asof_time_source_v44/result_frozen_v44.json\`.

**Current decision:** Declared future endpoints must be tested with an
explicit information cutoff. Even when a synthetic, strictly time-valid
source-tag readout carries additional information, the value is strongly
cutoff-, horizon- and target-dependent. The graph, propagation law, potential
source sites and exact cutoff occupancy were granted as known; the
source tags are NOT measured ancestry or natal dispersal. **No real
heldout ecological forecast or fourth EOG-WF endpoint was added**.
The empirically frozen 3 scored /31 scientific STOP /3 administrative
exclusions and Methods in Ecology and Evolution submission route remain
unchanged.

### v45: potential availability is not target-diagnostic evidence

The [v45 post-exposure original-output audit](eog_source_opportunity_vs_target_diagnosticity_v45.md) replayed the **same complete 18,432 v44 scenario rows** from the original SHA256-verified Actions archive, with no additional histories, likelihood fit or field source. It distinguishes two gates: a selected site is potentially occupied **at the observation cutoff**, and its available source label actually distinguishes the **declared future maturity target** after conditioning on cutoff occupancy.

In the **126** future-maturity-uncertain designs for t=2→t=5, cutoff-occupied confluence tags have potential observation opportunity in only **8** designs, and all 8 have target information. A fixed response-blind random site policy has observation opportunity in **105/126**, but only **6** have target information; **99** have possible source-tag measurements but **zero extra target information**. For t=4→t=5, occupied confluence tags are potentially measurable and informative in **51/59** uncertain designs. The first gate controls whether evidence can exist by cutoff; the second controls whether that evidence answers this particular future-state question.

These are previously exposed **synthetic** world outputs, not a new preregistered experiment, a biological source of dispersal, a causal comparison of source geometry or a field genetic sampling recommendation. The v45 audit independently verified original CSV/JSON source hashes and makes this interpretation a **STOP on further v44 same-source proxy mining**. Original three scored EOG-WF endpoints, 31 scientific STOPs, three administrative exclusions and submission route remain unchanged.

## Post-closure active method architecture

The frozen three-endpoint EOG-WF manuscript line remains closed and unchanged.

**Active method development now uses BAM and related finite virtual worlds as an
experimental laboratory for the original EOG ideas.**

The question is not BAM combinatorics for its own sake.  The virtual-world programme
tests, under known truth, whether the original EOG distinctions actually hold:

- local viability versus reachability;
- endpoint environmental similarity versus pathwise environmental continuity;
- stepping-stone dependence;
- bottleneck versus redundant routes;
- multiple source/branching histories producing the same observed distribution;
- static occurrence equivalence versus temporal-history discrimination;
- robust impossibility under expansion of the declared world universe.

Canonical active protocol:

- `validation/eog_original_idea_virtual_worlds_v1/protocol_v1.json`

Canonical benchmark:

- `benchmarks/run_eog_original_idea_virtual_worlds_v1.py`

BAM remains central as the A/B/M mechanism coordinate system used to build controlled
known-truth worlds, but the outputs may include route, source, first passage, stepping
stones, bottlenecks and temporal order whenever those are the original EOG quantity
being tested.

The relational-history API remains available as one measurement surface for these
virtual-world experiments.  It is **not** the active programme by itself.

Empirical bridge hunting is paused while this known-truth programme is the scientific
mainline.  Existing empirical stops remain frozen audit evidence and are not repaired.

## Scientific center

EOG keeps four objects separate:

1. **local possibility**;
2. **reachability from declared current sources**;
3. **distributional realizability under declared worlds**;
4. **historical truth**.

For a finite declared universe `W` and evidence `O`:

```text
W(O) = {w in W : w is compatible with O}
```

Observed positives constrain worlds but do not identify one true route or history.

For exact finite worlds, EOG exposes:

- `possible` — reachable in at least one declared world;
- `robust` — reachable in every declared world;
- `unresolved` — possible but not robust;
- `robustly_unreachable` — unreachable in every declared world.

These statements are conditional on the declared universe. Expanding a fixed survivor
universe cannot manufacture a new universal certificate; it can only preserve or erode
one.  The v6-v8 known-truth programme further shows that certificate persistence depends
on **expansion direction**: restrictive same-source additions protect robust
impossibility, permissive same-source additions protect robust reachability, while
mixed/incomparable/new-source additions can erode either class.

## Final two-layer architecture

### Layer A — exact scientific state

Retain exact world/rule identity for:

- compatibility;
- per-world support;
- evidence-driven rule elimination;
- possible / robust / unresolved / excluded interpretation;
- sequential contraction;
- finite-universe falsification;
- deterministic provenance and fingerprints.

Exact identity is required to say which declared rule was eliminated. It is **not** historical truth and is **not** the default supervised prediction representation.

### Layer B — label-invariant predictive projection

Production interface:

`src/eog/v2/world_predictive_summary.py`

Frozen `symmetric_world_support_summary_v1` features per node/horizon:

- surviving-world fraction;
- support mean / SD / min / max;
- q25 / q50 / q75;
- positive-support fraction;
- support range.

World IDs remain in Layer A and are not exposed as default supervised columns.

### Predictive endpoint — paired complementarity

Production evaluator:

`src/eog/v2/predictive_complementarity.py`

For each frozen heldout outer unit compare:

```text
strong learner + frozen conventional features
```

with:

```text
same learner + same conventional features + frozen Layer B
```

Learner family, preprocessing, hyperparameters, external features, Layer B, response endpoint, split, metric and favorable/adverse rules are frozen before response access.

The product question is deliberately narrow:

> **Does the frozen Layer-B representation add heldout information beyond the unchanged strong conventional learner in this endpoint?**

It is not a claim that EOG universally improves prediction.

## Closed fresh endpoint evidence

### Azores yellow eel telemetry

- baseline macro log loss: `0.1422727`;
- augmented macro log loss: `0.1322871`;
- paired difference: `-0.0099856` (`-7.0%`);
- augmented wins: `5/5` heldout blocks;
- terminal class: **favorable**.

### Southwest Louisiana King Rail passive acoustics

- baseline macro log loss: `0.2463173`;
- augmented macro log loss: `0.2453455`;
- paired difference: `-0.0009718` (`-0.39%`);
- augmented wins: `7/8` heldout occasions;
- terminal class: **favorable**.

Independently, all six frozen local Layer-A worlds were eventually falsified and only `external_open` survived. This is the key decoupling example: a small predictive complement can coexist with strong structural falsification without identifying a local movement mechanism.

### Tampa Bay seagrass monitoring

- baseline macro log loss: `0.3377354`;
- augmented macro log loss: `0.4387640`;
- paired difference: `+0.1010287` (`+29.9%`);
- augmented wins: `1/5` folds;
- terminal class: **adverse**.

Secondary feature-count placebo:

- 20 replicates × 10 features;
- placebo median macro log loss: `0.3361758`;
- real Layer-B augmentation beat `0%` of placebo replicates.

The placebo does not rescue the adverse primary result.

## Final interpretation

The three fresh endpoints are heterogeneous rather than uniformly favorable.

Supported:

> **Layer A is an auditable structural compatibility / falsification state, and Layer B can contain non-redundant predictive information in some systems.**

Not supported:

- universal predictive superiority;
- a standalone Layer-B predictor;
- causal identification;
- recovery of a unique dispersal history;
- truth of an exact surviving Layer-A world;
- continued candidate hunting to improve the endpoint pattern.

The final product boundary is:

`structural_diagnostic_plus_context_dependent_predictive_complement`

## Validation integrity boundary

The final denominator is part of the method result:

- **3** scored fresh endpoints;
- **31** scientific/protocol STOPs;
- **3** administrative exclusions.

Pre-response and pre-model STOPs remain integrity evidence. They are not converted into favorable, null or adverse predictive results, and opened endpoints are not repaired and rerun as independent confirmation.

Physical response-header identity, categorical response-token semantics, registry identity, source/process closure, structural adequacy, exact runtime identity and the once-only outcome-access contract remain part of the reusable validation machinery.

## Post-closure Layer-B v2 real-translation programme

A separate post-closure experiment asked whether the synthetic known-truth support for calibration-only selective promotion could translate into a genuinely fresh real ecological system. This programme is **not part of the three-endpoint EOG-WF denominator**.

Frozen synthetic result:

- `selective_promotion_known_truth_result_v1.json`: **known-truth support for calibration-only selective promotion**;
- this remains synthetic mechanism evidence only, not real-system predictive evidence.

Fresh-real attempts under unchanged `qualification v2`:

- **India tiger** — terminal pre-response transport STOP; response unopened; no model fit or outer score;
- **Illinois coyote** — terminal pre-response transport STOP; response unopened; no model fit or outer score;
- **NCRN Red-bellied Woodpecker** — passed the complete response-blind qualification path and one-shot authorization, then terminated after the single response fetch because `PointCode="2550"` was absent from the frozen points registry.

NCRN response consumption was exactly one request / `91,825,004` bytes. Site-year response construction did not complete; model fits = `0`; inner-selection decisions = `0`; outer-scoring runs = `0`; `counts_as_predictive_evidence = false`.

Therefore the post-closure real-translation programme ends with:

- scored fresh-real predictive endpoints: **0**;
- Layer-B real selective-promotion benefit / protection / harm: **unanswered**;
- known-truth selector support: **unchanged**;
- closed EOG-WF synthesis: **unchanged**;
- registry repair, alias discovery, rerun and replacement-candidate rescue: **forbidden**.

Canonical closure assets:

- [`../validation/layer_b_mechanism_v2/ncrn_final_terminal_result_v1.json`](../validation/layer_b_mechanism_v2/ncrn_final_terminal_result_v1.json)
- [`../validation/layer_b_mechanism_v2/real_translation_programme_closure_v1.json`](../validation/layer_b_mechanism_v2/real_translation_programme_closure_v1.json)

Any future real-system Layer-B translation test must be a **new separately preregistered protocol/version**. It cannot be represented as rescue or continuation of this closed programme.

## EOG-WF submission lane — frozen science, parallel administration only

The EOG-WF scientific manuscript is closed and the deterministic submission-package builder is on `main`. Remaining EOG-WF work is limited to author/admin completion:

1. final title page / author metadata;
2. author-approved AI/LLM disclosure.

The review-ready repository gate is resolved by the immutable public snapshot at commit `91125ae68004f298fcd45027566506772a3688d5`.

These items may proceed in parallel, but **they do not reopen scientific development, endpoint search, model fitting or claim expansion**.

## Structural paper moved to standalone repository

The Structural/reference-adequacy paper now has a separate canonical repository:

- `https://github.com/zuizui0223/Structural`

Its A-Islands and Tanzania empirical denominator, manuscript, figures, submission assets, release administration and Structural↔EGWE methodological framing are maintained there.

The Structural files retained in this EOG repository are **historical migration provenance only**, pinned by the standalone migration record to EOG commit `d7d18be0d34ba28065a947df59338e4d660a4b4c`. Do not continue Structural analysis, figure development, release preparation, author administration or journal submission from this repository.

The scientific separation remains strict:

- EOG-WF uses its frozen three-endpoint denominator: Azores / Louisiana / Tampa;
- Structural uses A-Islands original + A-Islands strong-reference + Tanzania;
- neither programme supplies extra replications for the other.

## Post-closure BAM inverse-identifiability paper lane — merged 2026-09-30

PR #518 was merged to `main` at commit `560c4e0054a3c9331dff1ea8267b8c559451c9aa`.

This is a **separate post-closure theory/simulation paper lane**. It does not reopen the
frozen EOG-WF empirical denominator, does not add a fourth predictive endpoint, and does
not change the favorable / favorable / adverse synthesis.

Canonical scientific state:

- inverse target: the exact finite survivor fiber of BAM worlds compatible with the declared evidence;
- complete positive distributions do not uniquely identify the generating BAM state in the frozen known-truth panels;
- direct and temporal evidence contract survivor fibers monotonically;
- complete BAM-state evidence terminates at the BAM-state equivalence class rather than automatically at a unique parameter label;
- exact targeted diagnostic measurement is represented as a finite hitting-set problem over the residual fiber.

Canonical manuscript:

- `manuscript/bam_identifiability/MANUSCRIPT_DRAFT_V4_JBI.md`
- primary route: **Journal of Biogeography — Research Article**
- readiness: `READY_FOR_SUBMISSION_ADMIN`
- validated anonymous review bundle: isolated install PASS, focused tests PASS, Figure 1–6 rebuild PASS, privacy findings 0.

No named-species illustration is required for the current theory claim. Do not add one
opportunistically. Remaining work is submission administration, not new scientific
endpoint search.

## Open PR lane map — 2026-09-30

Open pull requests are **not** additional EOG-WF replication unless explicitly stated. The current map is:

- **PR #486 — inferential accessibility**: separate ecological-informatics paper using the frozen EOG STOP denominator plus the separate 284b Level-C ledger. It does not reopen EOG-WF outcomes.
- **PR #482 — NEON small-mammal continuity**: separate ecological paper. Its metacommunity endpoint and manuscript are outside the EOG-WF 3/31/3 denominator.
- **PR #479 — NEON metacommunity connectivity**: underlying prospective empirical branch for the #482 paper lane; keep as branch-level scientific provenance.
- **PR #478 — world-survival identifiability**: separate methods paper built from the closed NEON world-survival programme; not an EOG-WF endpoint extension.
- **PR #475 — NEON regime candidate funnel**: historical response-blind roster/geometry provenance from the earlier regime programme. It is not the active EOG-WF lane.
- **PR #473 — Layer-B v3 representation contract**: post-closure outcome-free mechanism experiment. It cannot reinterpret Azores, Louisiana, or Tampa and cannot count as endpoint 4.
- **PR #445 — separate fresh-real v2 protocol**: preserved as a draft, separately preregistered future protocol. It is not authorized as continuation of the closed EOG-WF series.
- **PRs #432–#434 — deferred experiments**: post-closure theory/safety/offset work; none is required for EOG-WF submission or current release readiness.

Recently closed as superseded/redundant:

- **PR #518** — BAM inverse-identifiability paper lane; merged after all manuscript, figure, review-package and package checks passed. Separate JBI route; does not alter EOG-WF.

- **PR #398** — old MEE manuscript shell; replaced by the current frozen manuscript, paper-ready bundle, live-policy check and submission builder on `main`.
- **PR #474** — v1 survival-regime protocol; superseded by v2.
- **PR #476** and **#477** — v2 intermediate protocol/empirical branches fully carried forward into #478.
- **PR #485** — inferential-openness draft superseded by the more explicit #486 inferential-accessibility lane.

Therefore an open PR must not be interpreted as permission to reopen EOG-WF science. The only active EOG-WF submission task remains author/admin completion.

## Hard stop rules

1. **Do not select a fourth EOG-WF fresh endpoint.**
2. Do not rerun opened/stopped EOG-WF systems and relabel them independent confirmation.
3. Do not add a favorable case to change the EOG-WF `favorable / favorable / adverse` pattern.
4. Do not expose arbitrary exact world labels as default supervised EOG-WF features.
5. Do not change learner family, hyperparameters or conventional features between paired EOG-WF fits.
6. Do not identify a surviving world as historical truth.
7. Do not claim universal robustness outside the declared finite-world certificate.
8. Do not pool EOG-WF endpoint rows to manufacture a common-effect predictive claim.
9. New response-independent synthetic exposition may clarify an already-frozen method property but cannot reopen or alter an empirical endpoint decision.
10. Do not repair or rerun the consumed NCRN attempt; any future Layer-B real translation requires a new protocol version.

The repository therefore has two non-competing active lanes:

1. **EOG-WF submission lane** — scientifically frozen; complete author/admin/release
   gates and submit without reopening endpoint search.
2. **post-closure known-truth method-development lane** — test the original EOG ideas
   in preregistered BAM/reachability virtual worlds.  The current result is the
   direction-conditioned certificate / world-growth survival principle from v6-v8.

Structural work remains exclusively in the standalone Structural repository.
