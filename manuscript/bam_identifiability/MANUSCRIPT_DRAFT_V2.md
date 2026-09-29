# Distributions are lossy intersections: exact identifiability limits for abiotic, biotic and movement mechanisms

## Abstract

Species distributions are often interpreted as evidence about the abiotic, biotic and movement processes that generated them, yet the inverse problem is not guaranteed to be identifiable. We formulate finite BAM inference as a partial-identification problem in which each candidate world has abiotic support A, biotic permissibility B, movement accessibility M and realised distribution G=A∩B∩M. Under complete positive occurrence evidence, the exact survivor set is the worlds satisfying G*⊆G; under complete perfect presence/absence it is the worlds satisfying G=G*. Thus even a complete realised distribution can fail to identify its BAM decomposition. More strongly, when one truth support is nested inside another, its compatible-world set is necessarily equal or larger, so stronger ecological restriction can increase ambiguity under positive-only inference.

We tested these results in preregistered known-truth simulations. Across 12 activation-qualified deterministic BAM systems and 768 truth cases, complete positive occurrence maps uniquely identified 0/768 BAM states. Progressive evidence increased unique recovery to 25/768 with complete realised distributions, 159/768 with occupied-node arrival times, 275/768 after direct abiotic evidence, 565/768 after direct biotic evidence and 768/768 after direct movement-accessibility evidence. An independent stochastic generator reproduced truth retention and positive-superset logic while refuting stronger expectations that every structural difference must realise a positive witness and that unordered accumulated occurrence history must outperform the final snapshot. Across 304/304 strict support-inclusion pairs, narrower positive support retained equal or more compatible worlds. First-occurrence timing nevertheless refined static support in 256/384 stochastic runs.

The resulting inferential object is therefore not a selected “true process” but an evidence-dependent fiber of compatible BAM worlds. We show that distinguishing the remaining alternatives is an exact finite hitting-set problem and that, within the frozen deterministic programme, at most one direct A measurement, two B measurements, three joint A+B measurements or two M-accessibility measurements were required. This reframes distribution-to-process inference from best-model selection toward explicit non-identification and targeted evidence design.

## 1. Introduction

Species distributions are often used to reason backward from pattern to process. An observed range can motivate claims about climatic tolerance, dependence on interacting species, dispersal limitation or barriers to movement. The Biotic–Abiotic–Movement (BAM) framework makes the forward logic explicit: a realised geographic distribution is shaped by abiotic conditions, biotic permissibility and accessibility. In its simplest set representation,

[
G = A cap B cap M.
]

BAM is therefore naturally generative. Given A, B, M and an initial state, one asks what distribution follows.

The inverse problem is different. Given an observed distribution, which combinations of A, B and M are actually identified? The same realised intersection can be produced by multiple decompositions. A missing site can arise because abiotic conditions are unsuitable, because a required partner is absent or an antagonist is present, because the site is inaccessible, or because several constraints overlap. Conversely, a positive site only shows that all necessary constraints were simultaneously satisfied there. It does not reveal which mechanism would have been limiting elsewhere.

This many-to-one structure creates a distinction between fitting a distribution and identifying the mechanisms that generated it. A model may reproduce G well while remaining unresolved about A, B or M. Selecting one best-fitting mechanism can therefore convert lack of information into apparent certainty.

Existing BAM work establishes the forward framework, dynamic process representations and the possibility of confounding among ecological components. Virtual-species studies likewise provide known causal systems for evaluating ecological models. Our goal is narrower: to characterize the inverse information content of occurrence evidence itself.

We treat inverse BAM inference as a finite partial-identification problem. Instead of asking which candidate world is best, we ask which declared worlds remain compatible with a specific evidence contract. This survivor set, or evidence fiber, is the primary inferential object. The formulation has three advantages. First, exact non-identification can be stated without relying on arbitrary score thresholds. Second, different evidence types can be compared by how they contract the same finite survivor set. Third, remaining ambiguity can be converted directly into a diagnostic-measurement problem: which additional observations would distinguish the surviving alternatives?

We address four questions.

1. What does complete positive occurrence evidence identify?
2. Does complete presence/absence recover the BAM decomposition?
3. Can stronger ecological restriction paradoxically make inverse identification harder?
4. Which additional evidence is sufficient to break the remaining ambiguity?

We answer these questions with exact finite-set identities and a preregistered known-truth simulation programme. The deterministic programme contains 12 activation-qualified heterogeneous BAM systems and 768 truth worlds. We then challenge the results with an independently implemented stochastic BAM generator, a temporal-evidence analysis and an eight-landscape stochastic panel that retains preregistered design stops rather than repairing them after outcome inspection.

## 2. Theory

### 2.1 Finite BAM worlds

Let X be a finite node universe. Each candidate world (win W) has:

- abiotic support (A_wsubseteq X);
- biotic permissibility (B_wsubseteq X);
- movement accessibility (M_wsubseteq X);
- movement first-arrival state (	au_w);
- optional parameter labels (	heta_w).

The realised distribution is

[
G_w=A_wcap B_wcap M_w.
]

Let (w_*) be the generating truth.

The inverse problem is evaluated relative to the declared finite candidate universe W. Surviving worlds are evidence-compatible explanations inside W; survival does not establish historical truth.

### 2.2 Complete positive occurrence evidence

Suppose every truly occupied node is observed and no absence information is available. A candidate survives iff it contains every observed positive:

[
S_0(w_*)=
{win W:G_*subseteq G_w}.
]

This immediately gives the positive-superset ceiling. If

[
G_*subseteq G_w,
]

then no valid positive occurrence sampled from (G_*) can eliminate w. This is not a finite-sample limitation. It remains true under complete positive observation.

### 2.3 Complete perfect presence/absence

If every node in X is surveyed perfectly, positives imply

[
G_*subseteq G_w
]

and negatives imply

[
G_wsubseteq G_*.
]

Therefore

[
S_1(w_*)=
{win W:G_w=G_*}.
]

A complete distribution map identifies the realised G inside the candidate universe. It does not necessarily identify its A/B/M decomposition.

### 2.4 Progressive evidence fibers

We condition the same survivor set on increasingly direct evidence.

Occupied-node movement timing:

[
S_2=
{win S_1:
	au_w|_{G_*}=	au_*|_{G_*}}.
]

Direct abiotic state:

[
S_3=
{win S_2:A_w=A_*}.
]

Direct biotic state:

[
S_4=
{win S_3:B_w=B_*}.
]

Direct movement accessibility:

[
S_5=
{win S_4:M_w=M_*}.
]

Complete movement-arrival state:

[
S_6=
{win S_5:	au_w=	au_*}.
]

Hence

[
S_6subseteq S_5subseteq S_4subseteq
S_3subseteq S_2subseteq S_1subseteq S_0.
]

Valid additional evidence can contract or preserve the survivor fiber, but cannot restore a contradicted world.

### 2.5 BAM-state equivalence and parameter aliases

Two parameter worlds are BAM-state equivalent when

[
A_w=A_*,
quad B_w=B_*,
quad M_w=M_*,
quad 	au_w=	au_*.
]

At E6, the survivor set is exactly the BAM-state equivalence class of truth. Multiple parameter labels can therefore remain even after the complete finite BAM state is identified.

This distinction separates:

- distribution identification;
- BAM-state identification;
- parameter identification.

### 2.6 Restrictiveness and ambiguity

Let R denote complete positive support and define the compatible set

[
C(R)={w:Rsubseteq G_w}.
]

If

[
R_1subset R_2,
]

then any world containing (R_2) also contains (R_1). Therefore

[
C(R_1)supseteq C(R_2).
]

A narrower positive support cannot have fewer compatible positive-superset worlds. Stronger ecological restriction can therefore increase, rather than decrease, ambiguity under positive-only inference.

### 2.7 Targeted measurements as a finite hitting-set problem

Let S be the current survivor set and T the target fiber to retain. Each possible direct measurement m eliminates a finite subset (D_msubseteq S).

A measurement set Q reproduces T exactly when no measurement contradicts T and the eliminated subsets cover every nuisance world:

[
Ssetminus T
subseteq
igcup_{min Q}D_m.
]

The smallest such Q is an exact finite hitting-set problem. This converts residual non-identification into a diagnostic design problem.

## 3. Known-truth simulation programme

### 3.1 Design principle

All simulation stages were evaluated with known generating truth. Primary hypotheses, activation conditions and terminal rules were frozen before scoring within each stage. Failed activation systems were retained as design stops rather than repaired after results were known.

The simulations were not intended to estimate real ecological parameter distributions. Their purpose was to test identifiability logic under controlled finite worlds.

### 3.2 Canonical finite-world falsification

The initial virtual-biogeography benchmark established four basic behaviors:

1. retain the exact truth under valid positive evidence;
2. eliminate false worlds when positive witnesses exist;
3. falsify an omitted-truth finite universe when each candidate is contradicted by at least one positive witness;
4. remain unresolved when multiple candidate worlds are observationally equivalent.

A larger factorial then tested the stronger claim that complete positive occurrence coverage should identify the generating process.

### 3.3 Orthogonal BAM activation

The focal realised state was generated as

[
G=Acap Bcap M.
]

A was an explicit virtual abiotic niche. B was derived from independently generated partner and antagonist distributions. M was source-conditioned accessibility under distance, barriers and finite movement horizon.

Before scoring, activation gates required at least one:

- A-only witness contrast;
- required-partner B-only contrast;
- antagonist B-only contrast;
- movement-distance-only contrast;
- movement-barrier-only contrast.

The orthogonal factorial contained 64 candidate/truth BAM worlds.

### 3.4 Deterministic generality panel

The deterministic generality panel contained 12 heterogeneous virtual systems. All 12 passed activation requirements, yielding 768 truth cases.

For every truth, survivor sets were evaluated under the frozen evidence ladder:

- E0: complete positive occurrences;
- E1: complete realised G;
- E2: occupied-node movement arrival;
- E3: direct A;
- E4: direct B;
- E5: direct M accessibility;
- E6: complete movement-arrival state.

BAM-state uniqueness, rather than parameter-label uniqueness, was the primary identification target.

### 3.5 Independent stochastic BAM challenge

A separate stochastic metapopulation/BAM generator was implemented independently from the EOG reconstruction code. This reduced the risk that agreement simply reflected reuse of the same deterministic machinery.

The frozen workload contained 384 eligible stochastic runs spanning six truth scenarios and 32 candidate worlds. We audited:

- truth retention;
- EOG/evaluator parity;
- positive-superset ceiling;
- omitted-truth witness logic;
- realised positive witnesses;
- final-snapshot versus accumulated-history discrimination.

### 3.6 Restrictiveness–ambiguity audit

For every strict nested positive-support pair in the stochastic programme, we compared support inclusion with compatible-world inclusion. The audit contained 304 strict support-inclusion pairs.

### 3.7 Temporal evidence

Static positive support was compared with a signature retaining first-occurrence time. We measured:

- number of static support classes;
- number of temporal classes;
- static M-equivalent pairs split by temporal signatures;
- run-level strict contraction of the compatible set.

### 3.8 Multilandscape stochastic panel

A later preregistered panel contained eight landscapes spanning open-smooth, barrier-gap, environmental-bottleneck and joint-fragmented structures.

Two joint-fragmented systems failed response-free activation gates and remained DESIGN_STOP. The remaining six landscapes contributed 1,152 eligible stochastic runs.

### 3.9 Exact targeted-measurement audit

For the 12 deterministic systems and 768 truths, we solved exact finite hitting-set problems for direct measurements of:

- A;
- B;
- joint A+B;
- M accessibility;
- complete M arrival after accessibility.

The reported values are maximum exact requirements inside the frozen programme.

## 4. Results

### 4.1 Complete positive occurrence did not recover generating BAM states

In the initial 64-case factorial, complete positive occurrence coverage uniquely identified the generating process in 0/64 cases.

The same result generalized across the 12 deterministic systems:

[
0/768
]

truth BAM states were uniquely identified at E0.

This failure occurred despite complete positive observation and known truth. It therefore cannot be attributed to insufficient positive sampling.

### 4.2 A, B and M were all independently informative, but their intersection remained non-identifying

In the orthogonal BAM experiment, all preregistered activation gates passed.

Observed independent witness contrasts included:

- A-only;
- B-only;
- M-only;
- A+B;
- A+M;
- B+M;
- A+B+M.

Nevertheless, unique recovery was:

- complete positives: 0/64;
- + perfect negatives: 2/64;
- + occupied-node arrival: 6/64.

Thus the ambiguity did not arise because B or M was absent from the generative system.

### 4.3 The deterministic evidence ladder contracted ambiguity monotonically

Across 768 deterministic truths, the number of uniquely identified BAM states was:

| Evidence stage | Unique BAM states |
|---|---:|
| E0 complete positives | 0 |
| E1 complete G | 25 |
| E2 + occupied arrival | 159 |
| E3 + direct A | 275 |
| E4 + direct B | 565 |
| E5 + direct M accessibility | 768 |
| E6 + full M arrival | 768 |

The survivor fibers contracted monotonically by construction and by audit.

The preregistered claim that movement would always be the final identification bottleneck was refuted: at least one system had already reached complete BAM-state identification before direct M evidence was added.

### 4.4 Stronger ecological restriction increased positive-only ambiguity

The independent stochastic audit contained 304 strict positive-support inclusions. All 304/304 obeyed the exact inverse ordering:

[
R_1subset R_2
Rightarrow
C(R_1)supseteq C(R_2).
]

The most jointly constrained A+B+M support was also among the most ambiguous because its small realised support was contained in many more permissive candidate worlds.

This result reverses a common intuition that a more strongly constrained organism should necessarily reveal its mechanism more clearly from occurrence pattern alone.

### 4.5 Independent stochastic generation reproduced the core logic and refuted stronger expectations

Across 384 eligible stochastic runs:

- truth-retention failures: 0;
- EOG/evaluator parity mismatches: 0;
- positive-superset ceiling violations: 0;
- omitted-truth witness-criterion mismatches: 0.

Unique truth recovery remained zero in every truth scenario at the terminal horizon.

Two stronger preregistered expectations failed.

First, structural differences did not guarantee a realised positive witness. A jointly constrained A+B+M truth produced a complete positive support contained in every candidate reachable set, so complete positive observation eliminated no candidate.

Second, unordered accumulated positive history was never strictly more discriminating than the final positive snapshot in the frozen stochastic runs.

### 4.6 First-occurrence timing recovered information that unordered history lost

Retaining first-occurrence time refined:

- 8 static support classes into 20 temporal signature classes;
- 48 static M-equivalent pairs, of which 19 were split by temporal signature.

Temporal information strictly contracted the compatible set in 256/384 stochastic runs.

However, unique truth recovery remained zero. Time therefore supplied genuinely new movement information without guaranteeing complete inverse identification.

### 4.7 The stochastic principles generalized across landscapes

Of eight preregistered landscapes, six passed activation gates and two remained DESIGN_STOP.

The six eligible landscapes contributed 1,152 stochastic runs.

Across every eligible landscape:

- truth retention held;
- support nesting implied the predicted ambiguity ordering;
- joint A+B+M limitation remained highly ambiguous;
- temporal signatures refined static support;
- at least one strict temporal-gain run occurred;
- non-identification persisted.

The two failed landscapes were not repaired or replaced.

### 4.8 Exact diagnostic measurements were small in the frozen deterministic programme

Across the 768 deterministic truths, the maximum exact number of targeted measurements needed to reproduce the relevant target fiber was:

- direct A: 1 node;
- direct B: 2 nodes;
- joint A+B: 3 nodes;
- direct M accessibility: 2 nodes;
- additional full-arrival timing after M state: 0 nodes.

These values are programme-specific existence bounds. They do not imply that equivalent measurements are always feasible in real field systems.

## 5. Discussion

### 5.1 BAM is generative, but its inverse is partially identified

The BAM intersection explains how ecological factors combine to generate a realised distribution. The inverse map is different because intersections lose information about which factor excluded which nodes.

This creates evidence fibers rather than automatic point identification.

### 5.2 Complete occurrence data are not complete process data

The result 0/768 under complete positive observation is not a failure of sampling effort. Positive observations constrain candidate worlds by inclusion. Any more permissive world containing all truth positives remains compatible.

Complete presence/absence improves the situation by identifying G, but still does not generally reveal how G decomposes into A, B and M.

### 5.3 Strong ecological restriction can make the inverse problem harder

The support-inclusion result is particularly important because it contradicts an intuitive expectation.

A restrictive mechanism can shrink the realised distribution. But under positive-only inference, a smaller support has fewer opportunities to contradict permissive alternatives. The same biological restriction that makes the realised range narrow can therefore make the inverse mechanism less identifiable.

This is an exact set-theoretic property, not a peculiarity of one fitted model.

### 5.4 Temporal ordering is evidence, not just more occurrence

The stochastic analysis separates two ideas that are often conflated.

Adding more unordered occurrences of the same realised support did not improve discrimination. Retaining first-occurrence time did, because time creates a different evidence signature capable of distinguishing movement histories that share the same final support.

The relevant question is therefore not only how much data are collected, but which disagreements among candidate mechanisms the data expose.

### 5.5 Non-identification should be reported rather than optimized away

If multiple BAM worlds occupy the same evidence fiber, choosing a single best world does not create information. The scientifically faithful output is the unresolved fiber itself.

This is especially important when downstream ecological interpretation is mechanistic. Prediction of G and identification of A/B/M are different inferential targets.

### 5.6 Ambiguity can guide evidence collection

The hitting-set formulation gives non-identification an operational consequence.

Once the current survivor fiber is known, the next useful measurement is one that eliminates one or more surviving alternatives while retaining the target state. The exact finite design asks for the smallest set of measurements whose disagreement patterns cover all nuisance worlds.

The small exact bounds observed in the frozen deterministic programme show that substantial global ambiguity can sometimes be broken by a small number of strategically chosen mechanism measurements.

### 5.7 EOG v3 as an implementation

The EOG v3 joint-world engine implements the same logic in a more general form.

It keeps ecological worlds and observation-process worlds separate, conditions their Cartesian product on evidence, projects the surviving uncertainty onto ecological and observation axes, and supports robust/adaptive evidence design over a declared finite action library.

The software is an implementation of the survivor-fiber logic. It is not the primary novelty claim of this paper.

### 5.8 Limits

All exact statements are conditional on declared finite world and evidence universes.

The simulations do not imply that real A, B, M or movement states are directly observable without error. Perfect negatives and direct mechanism measurements are idealized evidence contracts used to establish identifiability boundaries.

The numerical targeted-measurement bounds are properties of the frozen simulation programme, not universal constants.

Finally, a surviving world is evidence-compatible. It is not thereby established as historical truth.

## 6. Conclusion

A species distribution is a compressed outcome of multiple ecological processes. Treating it as if it uniquely records those processes confuses the forward and inverse problems.

In finite BAM worlds, complete positive occurrence evidence identifies exactly a positive-support fiber, not necessarily the generating mechanism. Complete presence/absence identifies the realised intersection G, not necessarily its decomposition. Stronger ecological restriction can increase positive-only ambiguity, while temporal and direct mechanism evidence can contract the survivor fiber when they expose differences among surviving worlds.

The practical consequence is a shift from selecting the most plausible single process to characterizing what the current evidence actually distinguishes and designing the next observation around what remains unresolved.
