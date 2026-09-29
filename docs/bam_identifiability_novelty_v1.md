# BAM inverse identifiability — novelty positioning v1

## What is established prior art

### BAM itself is not new

Soberón & Peterson (2005) formalized the core heuristic that a realised distribution is shaped by Biotic, Abiotic and Movement constraints.

The central intersection idea

[
G_0 = A \cap B \cap M
]

is therefore prior art and must not be presented as an EOG innovation.

### Known-truth virtual BAM experiments are not new

Saupe et al. (2012, Ecological Modelling, DOI 10.1016/j.ecolmodel.2012.04.001) used virtual species with known causal BAM configurations to test how SDM/ENM algorithms recover occupied and potential distributional areas.

Therefore the following are not novelty claims:

- virtual species;
- known truth;
- varying abiotic/dispersal configurations;
- comparing model output against a known distribution.

### Dynamic BAM simulation is not new

Soberón & Osorio-Olvera (2023, Journal of Biogeography, DOI 10.1111/jbi.14587) developed a dynamic process-oriented theory of distributional area using movement, niche-tolerance and biotic-interaction matrices with cellular-automaton simulation.

Their paper explicitly reports that movement and niche effects can be mixed in ways that are extremely difficult to disentangle, linked to matrix singularity.

The current `bamm` R package implements BAM elements and dynamic simulation.

Therefore:

- matrix/cellular-automaton BAM dynamics;
- explicit movement;
- explicit biotic interaction matrices;
- mathematical analysis of forward BAM dynamics

are not EOG novelty.

### Absence information in BAM is not new

Bariotakis & Pirintsos (2018, Ecological Indicators, DOI 10.1016/j.ecolind.2018.03.043) explicitly introduced absence mapping under BAM and noted that an absence can arise from A, B, M or combinations thereof.

Therefore “absence adds information” is not a novelty claim.

### Simultaneous empirical A/B/M tests are not new

Empirical frameworks have already combined climate, biotic proxies and dispersal constraints to test distributional drivers, including North American wood-warblers.

Therefore “test A, B and M simultaneously” is not sufficient novelty.

---

# The narrower gap

The closest prior literature is primarily **forward**:

[
(A,B,M,\text{initial state})
\longrightarrow
G.
]

The present line asks the inverse question:

[
\text{observed evidence}
\longrightarrow
\{\text{BAM worlds still compatible}\}.
]

The central object is not a predicted distribution and not a selected best process.

It is the **survivor fiber** under a declared evidence contract.

## Exact inverse statements

The current theory establishes:

### Positive-only evidence

[
S_0(w_*)=
\{w:G_*\subseteq G_w\}.
]

Hence a positive-superset world is not merely hard to reject; it is **not rejectable by positive occurrences alone**.

### Complete perfect presence/absence

[
S_1(w_*)=
\{w:G_w=G_*\}.
]

Thus a complete distribution map identifies the realised (G), not necessarily its A/B/M decomposition.

### Progressive direct evidence

Arrival, A, B and M evidence produce nested fibers:

[
S_6\subseteq S_5\subseteq ...\subseteq S_0.
]

With complete A/B/M/full-arrival state:

[
S_6=[w_*]_{\mathrm{BAM}},
]

the exact BAM-state equivalence class.

### Measurement design

Distinguishing the target fiber from surviving alternatives is a finite hitting-set problem.

This converts “collect more ecological data” into:

> Which specific A, B or M measurements hit every remaining alternative explanation?

---

# Empirical/simulation contribution beyond the theorem

The theorem says what is possible in principle.

The preregistered known-truth programme measures how often each ambiguity occurs.

Across 12 independently generated, activation-qualified BAM systems and 768 truths:

- complete positive occurrence maps: 0/768 BAM states uniquely identified;
- + complete negatives: 25/768;
- + occupied-node movement timing: 159/768;
- + direct A: 275/768;
- + direct B: 565/768;
- + direct M accessibility: 768/768.

The universal claim that M is always the final bottleneck was explicitly **refuted**: one system reached full state identification before direct M evidence.

Exact targeted-measurement auditing showed, inside this finite programme:

- exact direct A minimum: at most 1 node;
- exact direct B minimum: at most 2 nodes;
- exact joint A+B minimum: at most 3 nodes;
- exact direct M accessibility minimum: at most 2 nodes.

These counts are programme-specific, not universal constants.

---

# Strongest defensible novelty sentence

> **We formulate BAM as an inverse partial-identification problem: rather than selecting a single mechanism from an observed distribution, we derive the exact finite set of abiotic–biotic–movement worlds that remain compatible under each evidence type, prove when occurrence data cannot distinguish them, and convert the remaining ambiguity into an explicit diagnostic-measurement problem.**

## Shorter version

> **BAM describes how processes generate distributions; this work characterizes when distributions can—and cannot—identify those processes.**

---

# What must not be claimed

Do not claim:

- first use of BAM;
- first BAM simulation;
- first virtual-species BAM test;
- first integration of A, B and M;
- first use of absences under BAM;
- first recognition that dispersal and niche effects can be difficult to disentangle;
- universal numerical measurement bounds from the current 12-system simulation.

The contribution is the exact inverse-world/fiber formalization, falsification boundary, equivalence-class output, evidence ladder and diagnostic measurement formulation.
