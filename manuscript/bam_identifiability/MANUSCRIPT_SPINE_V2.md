# BAM inverse identifiability — manuscript spine v2

## Working title

**Distributions are lossy intersections: exact identifiability limits for abiotic, biotic and movement mechanisms**

Alternative:

**Why complete species distributions need not identify the processes that generated them**

## One-sentence claim

A realised distribution is a many-to-one projection of abiotic, biotic and movement states, so even complete occurrence maps can leave the generating BAM mechanism non-identifiable; the correct inverse object is the finite evidence fiber of compatible worlds, whose size can be characterized exactly and reduced only by evidence that exposes disagreement among survivors.

## Paper identity

Theory + preregistered known-truth simulation + finite evidence-design method.

This paper is separate from:

- EOG-WF predictive complementarity;
- the inferential-accessibility paper;
- NEON continuity/world-survival papers.

Do not use EOG-WF predictive results as evidence for BAM inverse identifiability.

## Central questions

### Q1 — What exactly can positive occurrence data identify?

For truth world w* with realised distribution G* and candidate world w with G_w:

S0(w*) = {w : G* subseteq G_w}.

Therefore any positive-superset world survives complete positive observation.

### Q2 — Does complete presence/absence solve the inverse problem?

No in general.

With perfect complete presence/absence:

S1(w*) = {w : G_w = G*}.

This identifies the realised intersection G, not necessarily its A/B/M decomposition.

### Q3 — Does stronger ecological restriction make process identification easier?

Not necessarily.

If R1 subset R2 for complete positive supports, then:

C(R1) supseteq C(R2).

A more restrictive truth can have a smaller positive support and therefore leave more candidate supersets compatible.

### Q4 — What evidence actually breaks BAM ambiguity?

Progressively richer evidence defines nested fibers over:

- realised G;
- movement arrival on occupied nodes;
- direct A;
- direct B;
- direct M accessibility;
- full movement-arrival state.

The needed direct observations can be formulated as an exact finite hitting-set problem.

## Exact theory

Let X be a finite node universe and each candidate world be

w = (A_w, B_w, M_w, tau_w, theta_w)

with

G_w = A_w intersect B_w intersect M_w.

### T1 — positive-only fiber

S0 = {w : G* subseteq G_w}.

### T2 — complete-map fiber

S1 = {w : G_w = G*}.

### T3 — progressive evidence fibers

S2 = {w in S1 : tau_w restricted to G* equals tau* restricted to G*}

S3 = {w in S2 : A_w = A*}

S4 = {w in S3 : B_w = B*}

S5 = {w in S4 : M_w = M*}

S6 = {w in S5 : tau_w = tau*}.

Hence

S6 subseteq S5 subseteq ... subseteq S0.

### T4 — complete BAM-state fiber

S6 equals the BAM-state equivalence class of truth.

Parameter aliases can remain even when BAM state is fully identified.

### T5 — restrictiveness–ambiguity relation

For complete positive supports R1 subset R2:

C(R1) supseteq C(R2).

This is the exact reason stronger ecological restriction can produce greater positive-only ambiguity.

### T6 — targeted measurement

Given current survivor set S and target fiber T, every possible measurement m eliminates a finite subset D_m.

Finding the smallest set of measurements whose eliminated subsets cover S\T is an exact finite hitting-set problem.

## Simulation programme

## Stage 1 — canonical known truth

Confirm that the implementation can:

- retain truth;
- eliminate false worlds when positive witnesses exist;
- falsify an omitted-truth finite universe when every candidate has a witness;
- remain unresolved under observational equivalence.

Then deliberately test the stronger claim that complete positives recover truth.

### Result

Across 64 truth cases, complete positive observation uniquely identified:

0 / 64.

The strong recovery claim was rejected.

## Stage 2 — orthogonally activated BAM

Generate A, B and M separately.

Pre-outcome activation gates require:

- A-only contrasts;
- required-partner B contrasts;
- antagonist B contrasts;
- movement-distance contrasts;
- barrier contrasts.

The realised state is always

G = A intersect B intersect M.

### Result

All axes generated independent witnesses, yet truth uniqueness remained:

- positives: 0/64;
- + perfect negatives: 2/64;
- + occupied-node arrival time: 6/64.

Therefore the ambiguity is not an artefact of omitting B or M.

## Stage 3 — deterministic cross-system generality

Twelve heterogeneous activation-qualified systems; 768 truth cases.

Unique BAM-state recovery:

| Evidence | Unique truths |
|---|---:|
| E0 complete positives | 0 / 768 |
| E1 complete G | 25 / 768 |
| E2 + occupied arrival | 159 / 768 |
| E3 + direct A | 275 / 768 |
| E4 + direct B | 565 / 768 |
| E5 + direct M accessibility | 768 / 768 |
| E6 + full M arrival | 768 / 768 |

Predeclared claim that M is always the final bottleneck: REFUTED.

At least one system was already fully identified before direct M evidence.

## Stage 4 — independent stochastic challenge

Use an independently implemented stochastic BAM/metapopulation generator.

Primary integrity results:

- truth-retention failures: 0;
- EOG API parity mismatches: 0;
- positive-superset violations: 0;
- omitted-truth witness-rule mismatches: 0.

Stronger hypotheses refuted:

1. every structurally distinct BAM truth will realise a positive witness;
2. unordered accumulated positive history must be more discriminating than the final positive snapshot.

Across 384 eligible runs, unique truth recovery remained zero.

## Stage 5 — restrictiveness–ambiguity audit

Across 304/304 strict support-inclusion pairs:

narrower positive support produced an equal-or-larger compatible-world set.

The jointly constrained A+B+M truth was frequently maximally ambiguous because its positive support was contained in many more permissive candidate supports.

This is the most counterintuitive empirical/theoretical result and should be prominent.

## Stage 6 — temporal evidence

Retaining first-occurrence time rather than unordered accumulated occurrence history:

- static support classes: 8;
- temporal signature classes: 20;
- static M-equivalent pairs: 48;
- pairs split by temporal signature: 19;
- strict temporal contraction: 256 / 384 stochastic runs.

Unique truth recovery nevertheless remained zero.

Therefore temporal history contains genuinely new movement information but does not automatically solve the full inverse problem.

## Stage 7 — multilandscape stochastic generality

Eight preregistered landscapes:

- six activation-eligible;
- two DESIGN_STOP and retained as such;
- 1,152 eligible stochastic runs.

Across every eligible landscape:

- truth retention held;
- restrictiveness nesting held;
- temporal signatures refined static support classes;
- at least one strict temporal gain occurred;
- non-identification persisted.

The two DESIGN_STOP landscapes remain part of the denominator.

## Stage 8 — exact diagnostic measurement bounds

Across the 12 deterministic systems / 768 truths, exact targeted-measurement audit:

- direct A: maximum 1 node;
- direct B: maximum 2 nodes;
- joint A+B: maximum 3 nodes;
- direct M accessibility: maximum 2 nodes;
- full arrival after M accessibility: no additional node required in the frozen programme.

These are finite-programme bounds, not universal ecological constants.

## Main results to emphasize

### Result 1 — occurrence completeness does not imply mechanism identification

0/768 BAM states uniquely recovered from complete positives in the deterministic generality panel.

The same non-identification persisted under independent stochastic generation.

### Result 2 — stronger ecological restriction can increase inverse ambiguity

Because positive-only compatibility is based on set inclusion, smaller truth supports are compatible with more positive-superset worlds.

This is both exact theory and empirically audited across 304/304 nested-support pairs.

### Result 3 — richer evidence contracts fibers monotonically

Negatives, time, direct A/B/M observations and interventions reduce survivor fibers only when they expose differences among surviving worlds.

### Result 4 — time matters when order is retained

Unordered accumulated occurrence history was not strictly better than the final snapshot, but first-occurrence timing was informative in 256/384 stochastic runs.

### Result 5 — ambiguity can be converted into measurement design

Exact hitting-set analysis identifies small sets of direct A/B/M measurements sufficient to distinguish the current finite survivor fiber.

## Discussion structure

### 1. Forward BAM and inverse BAM are different problems

Forward:

(A,B,M,initial state) -> G.

Inverse:

evidence -> {BAM worlds compatible with evidence}.

A forward model can be biologically meaningful while the inverse map remains many-to-one.

### 2. Why a perfect distribution map can still be insufficient

G is an intersection. Knowing the intersection does not reveal which factor excluded which nodes.

### 3. The restrictiveness paradox

A strongly constrained organism may occupy fewer states, producing fewer positive witnesses.

Consequently stronger ecological restriction can increase ambiguity under positive-only inference.

### 4. Prediction is not process identification

Accurate prediction of G does not imply identification of A, B or M.

Do not compare methods by predictive accuracy in this paper.

### 5. Unresolved is a scientific result

The survivor fiber is the exact set of mechanisms not distinguished by the declared evidence.

Selecting one best-fitting mechanism can hide non-identification.

### 6. Evidence should target disagreements

More observations of the same type can be useless.

Useful data are observations, calibrations or interventions whose predicted outcomes differ among surviving worlds.

### 7. Connection to EOG v3

EOG v3 implements the general finite-world consequence:

declare worlds -> condition on evidence -> retain survivor fiber -> diagnose ambiguity -> design the next discriminating evidence.

The software is an implementation of the inverse-identifiability logic, not the primary novelty claim.

## Claim boundary

Do not claim:

- first BAM model;
- first virtual-species simulation;
- first recognition that niche and movement can be confounded;
- universal truth recovery by EOG;
- universal values for the 1/2/3-node measurement bounds;
- complete ecological identifiability in real systems;
- that a surviving world is historical truth.

Do claim:

- exact finite survivor fibers under explicit evidence contracts;
- exact positive-superset non-identification;
- exact complete-map equality fiber;
- exact monotone evidence contraction;
- exact restrictiveness–ambiguity ordering under positive-only support inclusion;
- exact finite hitting-set formulation for targeted diagnostic evidence;
- preregistered known-truth evidence showing these ambiguities are common across heterogeneous deterministic and stochastic systems.

## Paper boundary

Keep the following mostly outside the main paper:

- EOG-WF Layer-B predictive complementarity;
- MEE endpoint results;
- detailed public CLI engineering;
- broad software productization;
- inferential-accessibility paper.

Mention EOG v3 only as the implementation carrying the survivor-fiber and evidence-design logic.

## Provisional venue logic

The scientific center is biogeographic identifiability rather than software engineering.

Primary conceptual fit remains a biogeography/ecology theory venue.

A methods venue becomes stronger only if the evidence-design software and empirical illustration are made co-primary.
