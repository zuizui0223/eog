# BAM inverse identifiability — manuscript spine v1

## Working title

**Distributions are lossy intersections: exact identifiability limits for abiotic, biotic and movement mechanisms**

Alternative:

**From BAM forward models to BAM inverse inference: what species distributions can and cannot identify**

## One-sentence claim

A realised distribution (G=A\cap B\cap M) is a many-to-one projection of ecological mechanism states, so even complete occurrence maps need not identify the abiotic, biotic and movement processes that generated them; the compatible mechanism set can instead be characterized exactly and reduced only by evidence that distinguishes its surviving worlds.

## Paper type

Theory + preregistered known-truth simulation.

This is a separate paper line from EOG-WF predictive complementarity.

## Introduction logic

1. BAM provides a powerful forward conceptualization of geographic distributions.
2. Dynamic BAM models and virtual-species studies already examine how A/B/M configurations generate distributions and affect model performance.
3. The inverse problem is different: given a realised distribution, which BAM mechanisms are actually identified?
4. Multiple A/B/M states may map to the same realised G.
5. Selecting one best-fitting process hides this non-identifiability.
6. We derive exact survivor fibers under progressively richer evidence and test their practical size in known-truth virtual biogeographies.

## Theory

Define finite world universe (W).

For world (w):

[
G_w=A_w\cap B_w\cap M_w.
]

Truth is (w_*).

Derive:

[
S_0=\{w:G_*\subseteq G_w\}
]

for complete positive occurrence evidence.

Derive:

[
S_1=\{w:G_w=G_*\}
]

for complete perfect presence/absence.

Then condition sequentially on:

- movement arrival over occupied nodes;
- A;
- B;
- M accessibility;
- full movement-arrival state.

Prove nested contraction and BAM-state equivalence-class endpoint.

Derive direct-measurement design as a hitting-set problem.

## Known-truth simulation programme

### Stage 1 — canonical falsification

Demonstrate:

- truth retention;
- false-world elimination with positive witnesses;
- finite-universe falsification when truth is omitted and every candidate has a witness;
- honest non-identification under observational equivalence;
- false-positive observation boundary.

### Stage 2 — orthogonal BAM

Construct explicit independent:

- focal A;
- required-partner / antagonist B;
- source-conditioned M.

Activation gates guarantee A-only, B-only and M-only witness contrasts before scoring.

### Stage 3 — evidence ladder

Measure survivor-set contraction under:

E0 positive occurrence  
E1 + complete negatives  
E2 + occupied-node movement timing  
E3 + direct A  
E4 + direct B  
E5 + direct M accessibility  
E6 + full M arrival

### Stage 4 — cross-landscape generality

12 frozen heterogeneous virtual systems.

No replacement after activation.

768 eligible truth worlds.

## Core results

### Result 1 — positive occurrence is structurally insufficient

Across all 12 scored systems:

[
0/768
]

truth BAM states were uniquely identified from complete positive occurrence data.

This supports the positive-superset theorem in a heterogeneous simulation ensemble.

### Result 2 — richer observations contract but do not immediately identify mechanism

Pooled unique BAM states:

- E0: 0 / 768
- E1: 25 / 768
- E2: 159 / 768
- E3: 275 / 768
- E4: 565 / 768
- E5: 768 / 768
- E6: 768 / 768

### Result 3 — movement is important but not universally the last bottleneck

The preregistered claim that E4<1 and E5=1 in every system was **refuted**.

At least one system reached complete state identification by E4.

Therefore direct M is a common, not universal, final information requirement.

### Result 4 — targeted evidence can be small

Exact finite hitting-set audit over all 768 truths:

- A: max 1 node;
- B: max 2;
- joint A+B: max 3;
- M accessibility: max 2.

These are finite-programme results, not universal constants.

## Discussion

### Main interpretation

Occurrence patterns are observations of the **intersection**, not direct observations of the factors composing it.

This makes BAM inversion partially identified unless the evidence exposes disagreement among candidate factors.

### Why prediction is not process identification

A model can predict G well while being wrong or unresolved about A, B or M.

The paper therefore complements predictive SDM evaluation rather than competing on predictive accuracy.

### Why unresolved is a scientific result

An equivalence class describes the mechanisms the current evidence genuinely cannot distinguish.

Forcing a single winner converts information absence into false certainty.

### Evidence design implication

The inverse framework points directly to the next measurement.

If surviving worlds differ in A, measure A.

If they differ in B, measure interactions.

If they differ in M outside realised occupancy, collect movement/accessibility evidence there.

## Claim boundary

- finite declared world universe;
- perfect-negative and direct-state layers are idealized known-truth evidence contracts;
- no claim that real BAM components are perfectly measurable;
- survivor world is not historical truth;
- numerical measurement bounds are not universal.

## Provisional journal fit

Closest conceptual venue: **Journal of Biogeography**, because the nearest forward-theory paper is Soberón & Osorio-Olvera (2023) and the contribution is a complementary inverse-identifiability theory.

A methods venue remains possible if the diagnostic-design algorithm, real-data illustration and software interface become more central.
