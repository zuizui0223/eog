# Known-truth EOG development mainline

## Current position

This programme is a **separate post-closure simulation line**. It does not reopen or alter the frozen EOG-WF empirical 3/31/3 denominator.

The scientific center is now:

> **EOG does not need to recover one “true” process from occurrence data. It should eliminate finite declared worlds only when the available evidence contains a valid witness against them, preserve observationally equivalent worlds as unresolved, and use the remaining ambiguity to design the next discriminating observation, calibration, or intervention.**

## 1. What was directly refuted

The first large known-truth factorial falsified the strong recovery idea.

Across 64 virtual truth cases, even complete positive-occurrence coverage uniquely recovered the generating process in **0/64** cases.

This was not a software failure. Every truth had at least one alternative world whose positive reachable state was equal to or a superset of the truth.

For truth-positive set (R_*), false-world set (R_w), and observed positives (O), a false world is eliminated only when

[
O\cap(R_*\setminus R_w)\neq\varnothing.
]

If (R_*\subseteq R_w), no amount of positive-only sampling can eliminate that world.

Therefore the claim

> enough occurrence records should eventually recover the generating process

is rejected for the frozen known-truth universe.

## 2. BAM was made explicit rather than used as a covariate bundle

The focal realised state is generated as

[
G=A\cap B\cap M.
]

- **A** — abiotic niche support.
- **B** — explicit biotic permissibility from independently generated partner and antagonist distributions.
- **M** — source-conditioned movement accessibility from distance, barrier permeability and finite horizon.

v2.1 passed preregistered activation gates for all axes:

- A-only witness pairs: 16
- partner-B-only: 11
- antagonist-B-only: 6
- M-distance-only: 7
- M-barrier-only: 12

Across all ordered world contrasts, A-only, B-only, M-only and all overlap categories were observed.

Yet unique truth recovery remained:

- complete positives: **0/64**
- + perfect surveyed negatives: **2/64**
- + exact occupied-node arrival times: **6/64**

So the non-identification is not a failure to include B or M.

## 3. Direct mechanism evidence still has a ceiling

v2.2 supplied idealized complete A, B and M state information.

Unique parameter-world recovery became:

- baseline: 6/64
- + A: 8/64
- + B: 7/64
- + M: 9/64
- + A+B: 9/64
- + A+M: 18/64
- + B+M: 16/64
- + A+B+M: **32/64**

The remaining 32 worlds belonged to duplicate complete-state classes.

The alias audit showed that all residual duplicates differed only in inactive M parameters:

- 8 duplicate classes varied only barrier permeability (P);
- 8 varied only movement horizon (H).

Thus state identification and parameter identification are distinct targets.

## 4. Targeted interventions activated dormant parameters

v2.3 preregistered two mechanism-specific challenges.

**Barrier-permeability challenge**:
standardized source immediately left of the barrier, one-step crossing outcome.

**Horizon challenge**:
standardized source at one end of a long barrier-free corridor, distal reachability outcome.

Results:

- P-only alias classes split: 8/8
- H-only alias classes split: 8/8
- axis-specificity violations: 0
- passive classes: 48
- intervention-augmented classes: **64 singletons**

Within the frozen finite parameter universe, intervention therefore changed non-identifiable passive parameters into identifiable active parameters.

## 5. Ambiguity became an experimental-design object

v2.4 represented the 16 remaining passive alias pairs explicitly.

A preregistered evidence library contained:

- P barrier challenge
- H long-corridor challenge
- repeated passive observation as a negative control

Pair discrimination:

- P challenge: 8/16
- H challenge: 8/16
- repeated passive state: 0/16

The exact minimum separating set was the two useful interventions.

v2.5 generalized this to a domain-agnostic API taking only:

- world IDs;
- current evidence signature by world;
- predicted outcome by evidence channel;
- optional active-world subset.

It reproduced the BAM result exactly, failed closed when an evidence library was insufficient, and reduced the required design from two interventions to one after the compatible world set contracted.

## 6. Observation process is part of the world universe

v2.6 showed that low probability is not impossibility.

For finite repeated surveys and detection probability (p<1),

[
P(0\text{ detections}\mid Z=1)=(1-p)^n>0.
]

For example, at (p=0.75,n=8), the value is (1.5259\times10^{-5}): very small, but not zero.

Therefore finite nondetection cannot be promoted to exact absence without an observation contract that makes it impossible under presence.

Similarly, if any admissible observation world allows false positives (q>0), one detection does not robustly falsify absence.

## 7. Ecological worlds and observation worlds must be audited jointly

v2.7 formed an explicit Cartesian product:

[
W_E\times W_O.
]

At the response-independent maximally discriminating BAM node `r1c3`:

- 16 ecological worlds predict presence;
- 48 predict absence.

After four nondetections:

- with perfect detection only, ecological projection = **48/64**;
- after admitting an imperfect (p=0.75) observation world, ecological projection = **64/64**.

All 16 presence worlds were “resurrected” because at least one admissible observation world could miss the species.

Even eight nondetections left all 16 presence worlds compatible.

Direct calibration to (p=1), without a new focal ecological observation, restored the 48-world strict projection.

Thus calibration of how data were observed can be more discriminating than collecting more of the same ecological observation.

## 8. Future observations can be stochastic

v2.8 extended evidence design from deterministic outcomes to finite sets of possible outcomes.

An action robustly separates two hypotheses only if their possible outcome sets are disjoint.

For the three active joint hypotheses:

- `absent::p1`
- `absent::p075`
- `present::p075`

the robust split counts were:

- repeat one survey: 0/3 pairs
- repeat four surveys: 0/3
- direct detection calibration: 2/3
- direct biological-state assay: 2/3

The minimum worst-case robust nonadaptive design was the two direct channels.

## 9. Evidence collection is naturally adaptive

v2.9 solved the finite decision tree exactly.

- minimum worst-case depth: **2**
- optimal first actions: detection calibration or state assay
- repeat-survey-first worst-case depth: **3**
- known truth `absent::p1`: calibration outcome (p=1) resolves in **1 action**
- remove calibration: worst-case exact resolution impossible
- remove state assay: worst-case exact resolution impossible

The first CI run failed because child-node replanning incorrectly required action mappings to contain *exactly* the reduced active hypothesis set. This was corrected to allow parent-universe mappings while reading only active hypotheses. The rerun passed the independent brute-force depth check.

## 10. Independent stochastic generator: restriction can increase ambiguity

The deterministic BAM results were then challenged with an **independent stochastic
metapopulation generator** implemented outside the EOG reconstruction modules.

Across 384/384 eligible stochastic runs:

- true-world retention failures: **0**;
- EOG API parity mismatches: **0**;
- positive-superset ceiling violations: **0**;
- omitted-truth witness-criterion mismatches: **0**;
- unique truth recovery at horizon 40: **0 in every truth scenario**.

Two stronger hypotheses were refuted.

First, the preregistered expectation that every structurally distinct truth would
realize a positive witness failed for the joint A+B+M truth. Its complete positive
support contained only 33 nodes and was a subset of every candidate reachable set, so
even complete positive observation eliminated **0/32** candidates.

Second, unordered accumulated positive history was never strictly more discriminating
than the final snapshot in any of the 384 runs.

This exposed an exact set-theoretic principle. If complete positive supports satisfy

[
R_1 subset R_2,
]

then the compatible-world sets obey

[
C(R_1) supseteq C(R_2).
]

The restrictiveness audit checked **304/304** strict support-inclusion pairs with zero
violations. The most jointly constrained A+B+M support was therefore also the most
ambiguous in the frozen universe.

So stronger ecological restriction does **not** imply easier mechanism identification
from positive occurrences. It can do the opposite.

## 11. Time-stamped occurrence history recovers information that unordered history loses

The failure of unordered accumulated history did not imply that temporal information
was useless.

When first-occurrence time was retained:

- static support classes: **8**;
- temporal signature classes: **20**;
- static M-equivalent pairs: **48**;
- pairs split by temporal signatures: **19**;
- stochastic runs with strict temporal contraction: **256/384**.

Truth retention remained exact, but unique truth recovery was still **0** in every
scenario.

Thus the relevant distinction is:

> unordered occurrence accumulation can be redundant, while time-stamped occurrence
> history is a genuinely different evidence class that can recover movement
> distinctions.

## 12. The stochastic principles generalize across preregistered landscapes

A later frozen panel contained eight landscapes spanning open-smooth, barrier-gap,
environmental-bottleneck and joint-fragmented structures.

Two joint-fragmented landscapes failed response-free activation gates and remained
**DESIGN_STOP**. They were not repaired or replaced.

The remaining six landscapes contributed **1,152** eligible stochastic runs.

Across every eligible landscape:

- truth retention failures: **0**;
- restrictiveness-nesting violations: **0**;
- static compatible-set expansion violations: **0**;
- independent evaluator parity mismatches: **0/72 audits**;
- joint A+B+M limitation remained maximally ambiguous;
- temporal signatures refined static support classes;
- at least one realized temporal strict-gain run occurred;
- non-identification persisted at horizon 40.

All frozen U1-U8 claims were supported in the eligible panel.

The two DESIGN_STOP landscapes remain part of the denominator and are evidence that
the validation protocol can reject a virtual system before outcome scoring.

## 13. Deterministic BAM generality and exact evidence bounds

A separate deterministic panel used **12/12 activation-qualified systems** and
**768 truth cases**.

Unique BAM-state recovery across the frozen evidence ladder was:

| evidence level | unique truths |
|---|---:|
| complete positives | **0 / 768** |
| complete realized G | 25 / 768 |
| + occupied-node arrival | 159 / 768 |
| + direct A | 275 / 768 |
| + direct B | 565 / 768 |
| + direct M accessibility | **768 / 768** |
| + full M arrival | **768 / 768** |

The positive-only zero bound generalized to all 12 systems.

However, the predeclared claim that **M must always be the final bottleneck** was
refuted: at least one system already reached complete BAM-state identification before
direct M evidence was added.

Exact targeted-measurement audits across all 768 truths found maximum requirements of:

- direct A: **1 node**;
- direct B: **2 nodes**;
- joint A+B: **3 nodes**;
- direct M accessibility: **2 nodes**;
- additional full-arrival timing after M state: **0 nodes**.

These are finite-universe existence bounds, not claims that those measurements are
always feasible in real field systems.

## 14. Formal identifiability boundary

The simulation sequence is now accompanied by finite-set identities rather than only
empirical benchmark results.

For a declared truth world, the verified theory separates:

1. **positive-only compatibility** — the survivor fiber is exactly the set of worlds
   whose realized support contains the observed truth support;
2. **complete perfect presence/absence** — survivors are exactly the worlds with the
   same realized support;
3. **direct A/B/M evidence** — later evidence levels are successive state-equality
   fibers;
4. **complete BAM-state evidence** — survivors are the BAM-state equivalence class,
   which need not be a unique parameter label;
5. **targeted measurement design** — finding a minimal direct-measurement set is an
   exact finite hitting-set problem.

The exact hitting-set audit passed all **768** truth cases with zero failures.

This is the central conceptual correction to “recover the true process”: the inferential
object is a sequence of **evidence fibers over a declared finite universe**, and a
singleton is justified only when the relevant fiber is actually unique.

## 15. Computational language decision

The original witness factorial required **75.865 s** in the straightforward Python implementation, crossing the provisional 60 s threshold for considering C++.

A preregistered Python integer-bitset replay then reproduced the **exact same scientific fingerprint** in **1.437 s**, a **52.8× speedup**.

Therefore:

> **C++ is not currently needed.**

Python remains the scientific reference implementation. C++ should be reconsidered only if later finite-world universes exceed the optimized Python/bitset envelope.

## 16. EOG v3 public joint-world engine

The validated post-closure algorithms are now exposed through one domain-agnostic
public surface rather than as separate benchmark-only modules.

EOG v3 represents

[
W_J = W_E 	imes W_O,
]

where (W_E) is the declared finite ecological-world universe and (W_O) is the
declared finite observation-process universe.

An evidence event removes a joint world only when its observed outcome lies outside
that joint world's declared support. Ecological and observation conclusions are then
projections of the surviving joint set.

The integrated v3 regression reproduces the canonical frozen results:

- strict perfect-detection case: **48 joint / 48 ecological survivors**;
- broad perfect + imperfect case: **112 joint / 64 ecological survivors**;
- perfect-detection calibration: **48 joint / 48 ecological survivors**;
- robust split counts on the three active joint hypotheses: **0, 0, 2, 2**;
- exact minimum robust evidence set: **calibration + direct state assay**, size **2**;
- minimum adaptive worst-case depth: **2**;
- repeat-survey-first worst-case depth: **3**;
- removing either direct channel: exact worst-case resolution **unavailable**.

The public commands are:

```text
eog-v3-joint-evaluate
eog-v3-plan-evidence
eog-v3-plan-adaptive
```

Their JSON examples are executed inside CI after package installation.

Integrated v3 result fingerprint:

`073bcdf0e0e1761e6b5af077f9ffbfc79aeadb59b1c5aee4dd4ab6c4bbc23dab`

The v3 API is a product consolidation of frozen post-closure results. It is **not** a
new EOG-WF empirical endpoint and does not modify the MEE manuscript result.

## Current product definition

The post-closure known-truth line now supports the following workflow:

[
\text{declare ecological + observation worlds}
\rightarrow
\text{observe}
\rightarrow
\text{contract the joint world set}
\rightarrow
\text{project ecological / observation uncertainty}
\rightarrow
\text{retain unresolved equivalence}
\rightarrow
\text{diagnose why unresolved}
\rightarrow
\text{rank admissible next evidence}
\rightarrow
\text{choose exact or robust minimum design}
\rightarrow
\text{adapt after each outcome}.
]

The product is therefore better described as a **falsification-driven evidence and experiment design framework** than as a conventional distribution predictor or true-process selector.

## 17. BAM inverse-identifiability paper lane

The exact finite-set theory and frozen known-truth programme are now assembled as a
separate biogeographic inverse-identifiability manuscript and merged to `main` via
PR #518.

The paper's inferential object is not a recovered “true BAM process”. It is the exact
survivor fiber of declared BAM worlds still compatible with the available evidence.

Frozen submission-facing evidence includes:

- 12/12 deterministic activation-qualified systems / 768 truths;
- complete-positive unique BAM-state recovery: 0/768;
- complete realised-G recovery: 25/768;
- + occupied arrival: 159/768;
- + direct A: 275/768;
- + direct B: 565/768;
- + direct M accessibility: 768/768;
- 384 eligible runs from an independently implemented stochastic generator;
- 304/304 strict support-inclusion pairs obeying inverse survivor ordering;
- 8 preregistered stochastic landscapes, 6 eligible and 2 retained DESIGN_STOP;
- exact targeted-measurement bounds audited over all 768 deterministic truths.

The preregistered claim that M is always the final identifiability bottleneck was
refuted and remains refuted.

Canonical manuscript:
`manuscript/bam_identifiability/MANUSCRIPT_DRAFT_V4_JBI.md`.

Primary route:
**Journal of Biogeography — Research Article**.

Current readiness:
`manuscript/bam_identifiability/JBI_SUBMISSION_READINESS_V1.json` =
`READY_FOR_SUBMISSION_ADMIN`.

A named-species empirical illustration is not required for the current theory claim and
must not be added opportunistically.

## 18. Target-specific counterfactual identifiability

A separately preregistered successor then asked whether BAM-state nonidentification is
necessarily relevant to the ecological target being acted on.

The protocol was frozen at commit
`fad0a6e931bac9012fb978d293dadac4d041d012` before implementation/scoring and reused
the unchanged 12-system / 768-truth deterministic panel.

Current evidence was fixed at complete perfect current (G) (E1). Three idealised
counterfactual probes were declared:

- release A: (B\cap M);
- release B: (A\cap M);
- release M: (A\cap B).

The probes are mechanism thought experiments, not literal management interventions.

The result exposed a strong target-identifiability hierarchy:

- full BAM state identified: **25/768 (3.3%)**;
- joint exact three-probe counterfactual signature identified: **174/768 (22.7%)**;
- all three binary release decisions identified: **636/768 (82.8%)**.

Among the **743** truths whose BAM state remained unresolved after complete current
(G):

- **149** were invariant across all three exact counterfactual maps;
- **462** had at least one exact-map disagreement but no disagreement in any of the
  three binary release decisions;
- **132** retained at least one binary decision disagreement.

Thus mechanism ambiguity, exact counterfactual ambiguity and decision ambiguity are
different inferential states.

The same finite direct-measurement library established the exact target-coarsening
contract:

[
b(\text{binary decision})
\le
b(\text{exact counterfactual map})
\le
b(\text{full BAM state})
]

with **0/2304 probe-level violations**.

Strict binary-decision measurement savings relative to full BAM-state recovery occurred
for **730/768** A-release truths, **738/768** B-release truths and **741/768** M-release
truths.

The formal reason is target refinement. If (T=f\circ U), every world disagreeing
with truth on the coarser target (T) is also discordant on the finer target (U).
Therefore a measurement set that resolves (U) is automatically sufficient for (T),
while the converse need not hold.

This changes the development target again:

> **Do not automatically collect evidence until the BAM mechanism is uniquely
> recovered. Collect enough evidence to place the surviving world fiber inside one
> equivalence class of the ecological target that matters.**

Canonical successor assets:

- `validation/bam_counterfactual_identifiability_v1/protocol_v1.json`;
- `validation/bam_counterfactual_identifiability_v1/result_summary_v1.json`;
- `docs/bam_counterfactual_identifiability_v1_result.md`;
- `docs/bam_target_identifiability_theory_v1.md`;
- `manuscript/bam_counterfactual_identifiability/MANUSCRIPT_SPINE_V1.md`.

This programme is separate from the frozen JBI BAM inverse-identifiability manuscript
and does not alter its submission claims.

## 19. Decision certificates are conditional on the BAM world-family boundary

The target-specific Phase-II result was then stress-tested against unrestricted same-G
BAM decomposition completion.

For

[
\mathcal C(G)=\{(A,B,M):A\cap B\cap M=G\},
]

every proper current distribution (G\subset X) admits both binary outcomes under
each single-axis release.  Therefore a release decision can be identified from current
(G) only because the declared BAM family excludes some same-G decompositions.

The successor does not treat those omitted decompositions as biologically plausible.
Instead it measures their exact logical distance from the current survivor fiber.

Completion flip margin is Hamming distance across A/B/M node states to the nearest
same-G completion with the opposite binary decision.

The frozen 12-system / 768-truth audit found, among proper-G decisions already
identified in the declared universe:

- release A: 618 truths; median margin **1**, maximum **13**, margin 1 in **439**;
- release B: 671 truths; median margin **2**, maximum **29**, margin 1 in **263**;
- release M: 698 truths; median margin **2**, maximum **31**, margin 1 in **281**.

All exact theorem and benchmark checks passed with zero violations.

A directional asymmetry follows from the BAM set structure.

For an expansion decision, every node in the released support outside (G) is an
existing witness and all such witnesses must be destroyed to reverse the decision.

For a no-expansion decision, creating one new outside-(G) witness is enough.  In the
frozen panel, every finite no-expansion margin was 1 or 2.

The mainline claim is therefore now explicitly conditional:

> **target identification is certified inside a declared BAM world universe; the
> completion margin quantifies how much the same-G world-family boundary must be relaxed
> before that target certificate can fail.**

Canonical assets:

- `validation/bam_decision_robustness_margin_v1/protocol_v1.json`;
- `validation/bam_decision_robustness_margin_v1/result_summary_v1.json`;
- `docs/bam_decision_robustness_margin_v1.md`;
- `docs/bam_decision_robustness_margin_v1_result.md`.

## 20. Ecological parameter-neighbourhood robustness

The unrestricted same-(G) completion margin is a logical stress test.  Phase IV
therefore inserted a preregistered ecological parameter neighbourhood between the
original world family and complete decomposition closure.

Each of the 12 frozen systems was expanded from 64 to **2,592** BAM parameter worlds
using only pre-score rules:

- A niche-breadth extrapolation by one discrete level on either side;
- partner and antagonist one-shell erosion/base/dilation;
- one additional M dispersal-radius level;
- one extra-long M horizon.

All original worlds were required to embed exactly.  Counterexamples were required to
reproduce the exact current (G).

The preregistered results were:

- H1 one-step fragility: **SUPPORTED**;
- H2 nontrivial robustness: **SUPPORTED**;
- H3 irrelevant-axis invariance: **SUPPORTED** with zero violations;
- H4 directional margin asymmetry: **REFUTED**.

Identification across nested universes became:

| target | original | structured expansion | complete same-G closure |
|---|---:|---:|---:|
| release A | 652 | 646 | 34 |
| release B | 705 | 693 | 34 |
| release M | 732 | 691 | 34 |

Thus the structured neighbourhood retained 99.1%, 98.3% and 94.4% of the respective
declared-universe certificates even though unrestricted same-(G) completion destroys
every nontrivial certificate.

Finite structured counterexamples occurred in only:

- A: 6 truth cases / 1 unique fiber, all distance 3;
- B: 12 truth cases / 3 unique fibers, distances 2–3;
- M: 41 truth cases / 5 unique fibers, distances 1–4.

The scientific output is therefore a **nested-universe robustness profile**:

> **identified in the original world family; retained or lost in a preregistered
> ecological neighbourhood; and eventually unresolved or retained under complete
> logical closure.**

Do not promote “no counterexample in the 2,592-world lattice” to universal ecological
robustness.  It is robustness only to the frozen expansion operators.

Canonical Phase-IV assets:

- `validation/bam_ecological_expansion_margin_v1/protocol_v1.json`;
- `validation/bam_ecological_expansion_margin_v1/result_summary_v1.json`;
- `docs/bam_ecological_expansion_margin_v1.md`;
- `docs/bam_ecological_expansion_margin_v1_result.md`;
- `docs/bam_nested_universe_target_identifiability_v1.md`.

## 21. Structured future targets and dormant parameter reactivation

The next preregistered phase replaced axis-release targets with three frozen ecological
transformations:

- climate shift: temperature +0.08, moisture -0.04;
- biotic stress: one additional partner erosion + antagonist dilation;
- barrier restoration: force movement barrier permeability true.

Before implementation, the protocol was amended to recognize that future targets need
not factor through current BAM-state equivalence.  A parameter alias can be dormant
today but activated by intervention.

The guaranteed hierarchy was therefore defined as:

[
\text{parameter identity}
\rightarrow
\text{exact counterfactual map}
\rightarrow
\text{binary decision}.
]

This hierarchy had zero violations.

### W0 — original 64-world universe

- parameter-world identified: **13/768**;
- current BAM state identified: **25/768**.

Target identification:

| transformation | exact map | binary decision |
|---|---:|---:|
| climate | 622 | 646 |
| biotic stress | 558 | 603 |
| barrier restoration | 604 | 744 |

### W1 — 2,592-world ecological universe

- parameter-world identified: **0/768**;
- current BAM state identified: **8/768**.

Target identification:

| transformation | exact map | binary decision |
|---|---:|---:|
| climate | 610 | 636 |
| biotic stress | 442 | 498 |
| barrier restoration | 604 | 700 |

W0 binary certificates lost after W1 expansion:

- climate: **10**;
- biotic stress: **105**;
- barrier restoration: **44**.

Yet large target-identified sets remained despite complete parameter-world
nonidentification in W1.

One W1 climate fiber in `S11_9x5_gap` demonstrated dormant alias reactivation:
36 same-G parameter worlds shared one complete current A/B/M/tau state but split into
two climate future maps and two net-loss decision classes.

The current mainline therefore distinguishes:

1. parameter-world identity;
2. current BAM-state identity;
3. exact future-map identity under a declared transformation;
4. decision identity under that transformation.

These are not interchangeable inferential targets.

Canonical Phase-V assets:

- `validation/bam_structured_counterfactuals_v1/protocol_v1.json`;
- `validation/bam_structured_counterfactuals_v1/result_summary_v1.json`;
- `docs/bam_structured_counterfactuals_v1.md`;
- `docs/bam_structured_counterfactuals_v1_result.md`;
- `docs/bam_current_vs_future_identifiability_v1.md`.

### Development stop for synthetic operator proliferation

The synthetic mainline has now answered the planned target-identifiability questions.
Do not add further climate deltas, interaction shells or movement operators merely to
generate more favorable examples.

The next substantive validation requires an independently fixed ecological
transformation contract rather than another outcome-chosen synthetic operator.

## 22. Future-target evidence routing

Phase VI asked what should be measured **now** when the scientific target is a future
structured decision rather than complete recovery of the present BAM mechanism or W1
parameter world.

The frozen W1 evidence libraries were separated into:

- present-state channels: node-level A, B, M and movement-arrival tau;
- latent-parameter channels: the eight W1 ecological coordinates.

For truth \(\theta_*\), current-state alias class

[
A_C(\theta_*)
=
\{\theta\in S:C(\theta)=C(\theta_*)\},
]

and future target \(T\), complete present-state evidence is sufficient if and only if

[
|T(A_C(\theta_*))|=1.
]

If target values differ inside the complete current-state class, no amount of additional
evidence of the same A/B/M/tau state type can resolve the future target.  The evidence
class itself is insufficient.

The preregistered 768-truth W1 audit found:

### Climate shift

- binary target already identified from G: **636**;
- unresolved: **132**;
- state-resolvable: **122**;
- state-only impossible: **10**;
- every unresolved decision resolved by exactly **one A-level assay**.

### Biotic stress

- binary target already identified from G: **498**;
- unresolved: **270**;
- state-resolvable: **270/270**;
- state-only impossible: **0**;
- parameter-only designs required two assays in 110 truths, but the combined library
  resolved all 270 with one channel.

### Barrier restoration

- binary target already identified from G: **700**;
- unresolved: **68**;
- state-resolvable: **58**;
- state-only impossible: **10**;
- parameter designs required one assay in 61 truths and two in 7.

For exact future maps, state-only impossibility occurred in 10 climate truths,
0 biotic-stress truths and **88 barrier-restoration truths**.

Full W1 parameter-world identification required a median of **5** exact parameter
assays and up to 7.  In contrast, every frozen binary target required at most two
parameter assays, and every truth under all three transformations showed a strict
parameter-assay saving relative to full world identification.

The preregistered S11 climate dormant-alias fiber supplied the clean impossibility case:
36 same-G W1 worlds share one complete current A/B/M/tau state, but the climate
decision splits in two.  Present-state evidence is therefore insufficient by theorem;
one **A-level** parameter assay resolves the decision for both original truth worlds.

The evidence-design rule is now:

> **Before ranking more measurements, test whether the proposed evidence class can
> separate the future-target disagreement at all.  If target-discordant worlds are
> current-state aliases, route evidence collection to a parameter-sensitive or
> transformation-sensitive channel rather than collecting more present-state data.**

Canonical Phase-VI assets:

- `validation/bam_future_target_evidence_v1/protocol_v1.json`;
- `validation/bam_future_target_evidence_v1/result_summary_v1.json`;
- `docs/bam_future_target_evidence_v1.md`;
- `docs/bam_future_target_evidence_v1_result.md`;
- `docs/bam_future_target_evidence_theory_v1.md`.

Evidence-channel cardinalities remain synthetic information counts, not field-cost
estimates.

## 23. Assay-process uncertainty and target self-calibration

Phase VI assumed exact parameter assays.  Phase VII crossed each W1 ecological survivor
fiber with two frozen assay-observation worlds:

- calibrated coding;
- systematic deterministic miscoding.

The future ecological decision depends on the ecological world only; assay-world
identity is nuisance uncertainty.

The frozen action library contained one assay for each of the eight W1 parameter
coordinates, a same-assay repeated action, and one idealized assay-process calibration.

Across **67** future-target-unresolved W1 fibers:

- repeat-same-assay robust pair-coverage violations: **0**;
- assay-only robust impossibility occurred in **2 climate**, **2 biotic-stress**, and
  **3 barrier-restoration** fibers;
- every assay-only impossible fiber became solvable when calibration was admitted;
- complete calibrated-library failures: **0/67**.

Thus repeated observation of the same deterministically biased channel does not replace
observation-process calibration.

However, the preregistered S11 climate prediction was **refuted**.

The expected exact minimum was

`{assay_process_calibration, assay:A_level}`.

The actual exact minimum was

`{assay:A_level, assay:antagonist_excluded}`.

It remained sufficient even when the calibration action was unavailable.

Therefore explicit observation-world identification is not always necessary.  Multiple
assay channels can be **target-self-calibrating**: their joint observed signature can
separate every target-discordant ecological/observation joint hypothesis while the
assay-process world itself remains unresolved.

This creates a second evidence-routing layer:

1. determine whether the future target is unresolved ecologically;
2. determine which ecological evidence class can separate the target;
3. audit whether the chosen evidence is interpretable across the admitted observation
   worlds;
4. if a multichannel target-self-calibrating design exists, explicit calibration is
   unnecessary for that target;
5. otherwise observation-process calibration is required.

Canonical assets:

- `validation/bam_future_assay_observation_v1/protocol_v1.json`;
- `validation/bam_future_assay_observation_v1/result_summary_v1.json`;
- `docs/bam_future_assay_observation_v1.md`;
- `docs/bam_future_assay_observation_v1_result.md`;
- `docs/bam_future_assay_observation_theory_v1.md`.

The observation worlds are synthetic deterministic coding processes.  No claim is made
about independent random measurement error or real assay cost.

## 24. Stochastic assay error separates exact robustness from risk reduction

Phase VII studied fixed systematic miscoding.  Phase VIII froze a different
observation process: iid full-support categorical assay error under two global quality
worlds, with `p_correct=0.7` or `0.9`.

The ecological W1 fibers, three structured future targets and Phase-VII canonical
assay fields were left unchanged.

Two inferential claims were deliberately separated.

### Exact finite-world robustness

Because every stochastic assay code has positive probability under every true code,
same-quality target-discordant hypotheses retain overlapping support after any finite
number of iid repeats.

The audit found:

- scored future-target-unresolved fibers: **67**;
- finite-repeat exact robust separation: **0/67**.

Thus repetition does not turn full-support random error into hard falsification.

### Risk-bounded distinguishability

The stochastic endpoint was instead the worst target-discordant pair Bhattacharyya
upper bound

[
P_e^* \le BC/2.
]

The preregistered threshold was `BC/2 <= 0.05`, with repeat depth capped at 30.

Every frozen fiber crossed the bound:

- climate: **8 repeats** in 18/18 fibers;
- biotic stress: **27 repeats** in 43/43;
- barrier restoration: **11 repeats** in 1/6 and **27 repeats** in 5/6.

For S11 climate, the two Phase-VII fields
`A_level + antagonist_excluded` moved from a one-read worst bound of **0.3646** to
**0.03995** after eight repeats per field.

### Quality calibration hypothesis refuted

H4 predicted that idealized assay-quality calibration would strictly reduce total
synthetic action count for at least one fiber.

It did not.

- strict calibration cost savings: **0/67**;
- repeat depth with and without quality calibration was identical in every fiber;
- the limiting pair at the stopping depth was same-quality in **67/67** fibers.

Therefore quality calibration could not improve the worst-pair criterion: it removes
cross-quality ambiguity, while the active bottleneck was already ecological
target disagreement inside one quality world.

The preregistered H4 is **REFUTED** and remains refuted.

### Observation-process contrast

The mainline now distinguishes:

1. **fixed systematic miscoding** — repetition can be exactly redundant and explicit
   calibration can be structurally necessary;
2. **iid full-support random error** — repetition can reduce stochastic overlap
   exponentially but cannot restore exact support-disjoint robustness;
3. **quality calibration** — useful for the chosen worst-pair target only when
   cross-quality ambiguity is actually limiting.

Canonical Phase-VIII assets:

- `validation/bam_stochastic_assay_risk_v1/protocol_v1.json`;
- `validation/bam_stochastic_assay_risk_v1/result_summary_v1.json`;
- `docs/bam_stochastic_assay_risk_v1.md`;
- `docs/bam_stochastic_assay_risk_v1_result.md`;
- `docs/bam_stochastic_assay_risk_theory_v1.md`.

The 5% value is a preregistered pairwise sufficient error bound, not a statement of
95% posterior certainty or a universal ecological decision threshold.

## Hard claim boundary

Do not claim:

- a surviving world is historical truth;
- positive occurrences generally identify the generating process;
- complete realised distributions identify BAM decomposition;
- complete A/B/M state maps necessarily identify generating parameters;
- finite nondetections are hard absences under imperfect detection;
- more data of the same observational type necessarily resolve ambiguity;
- the current finite-world results imply universal ecological identifiability.

Do claim, conditionally on the declared finite universes:

- exact world elimination when valid witnesses exist;
- explicit non-identification when worlds remain observationally equivalent;
- monotone weakening of robust exclusion when ecological or observation universes expand;
- exact finite evidence-library sufficiency/insufficiency;
- exact or robust minimum evidence designs;
- adaptive replanning after evidence outcomes.
