# Manuscript spine v1 — BAM counterfactual identifiability

## Working title

**From mechanism ambiguity to decision robustness: target sufficiency and universe fragility in finite BAM worlds**

## Separation from the first BAM paper

The first paper asks:

> Given occurrence and progressively richer evidence, which A/B/M worlds remain
> compatible and when is the BAM state identified?

This successor asks:

> When the BAM state remains unresolved, does that ambiguity actually change the
> counterfactual ecological conclusion that matters?

The first paper must remain frozen.  This manuscript uses its survivor-fiber framework
as the starting point but has a different estimand and result.

## One-sentence claim

> **Occurrence-equivalent BAM worlds can remain mechanistically unresolved while agreeing on a declared counterfactual target, but that agreement is conditional on the declared world family; exact target-specific evidence burdens and completion margins separate decision sufficiency from universe-boundary fragility.**

## Core questions

1. How often does current-distribution equivalence hide different counterfactual
   responses?
2. How often do exact counterfactual maps differ while a coarser ecological decision
   remains invariant?
3. How much direct evidence is needed to identify the decision compared with the exact
   map or full BAM state?
4. Can the evidence-burden hierarchy be proved rather than only observed in simulation?

## Formal structure

For survivor fiber (S) and target (T),

[
wsim_Tviff T(w)=T(v).
]

The target is identified when (S) lies inside one target-equivalence class.

For a refinement chain

[
	ext{BAM state}
ightarrow
	ext{exact counterfactual map}
ightarrow
	ext{binary decision},
]

the same evidence library implies

[
b_{m decision}
leq
b_{m map}
leq
b_{m BAM}.
]

This is the theoretical backbone, not an empirical pattern fitted after scoring.

## Preregistered known-truth experiment

Use the existing 12 activation-qualified finite BAM systems and 768 truth cases.

Current evidence is complete perfect current (G), so the survivor fiber is the exact
same-(G) class.

Frozen idealised probes:

- release A: (Bcap M);
- release B: (Acap M);
- release M: (Acap B).

For each probe score:

- exact counterfactual map identifiability;
- binary expansion/no-expansion identifiability;
- exact minimum truth-relative direct-measurement burden.

No new landscape, truth case or named taxon is added after observing the results.

## Headline results

Current (G) identified the BAM state in only **25/768 (3.3%)** truth cases.

Yet:

- joint exact three-probe counterfactual signature identified: **174/768 (22.7%)**;
- all three binary release decisions identified: **636/768 (82.8%)**;
- at least one binary release decision unresolved: **132/768 (17.2%)**.

Among the **743** BAM-state-nonidentified truths:

- **149 (20.1%)** — mechanism unresolved, but all three exact release maps invariant;
- **462 (62.2%)** — at least one exact map differs, but all three binary decisions
  remain invariant;
- **132 (17.8%)** — at least one binary decision differs.

Thus more than four fifths of the mechanism-nonidentified truth cases still support the
same three binary decisions across their surviving mechanism worlds.

## Evidence result

Full BAM-state identification required:

- 0 measurements: 25 truths;
- 1: 232;
- 2: 313;
- 3: 150;
- 4: 48.

Median = 2 direct measurements.

For binary decisions, most truth cases required none:

- release A: 652/768 already identified;
- release B: 705/768 already identified;
- release M: 732/768 already identified.

Strict binary-decision savings relative to full BAM-state identification occurred in:

- A: 730/768;
- B: 738/768;
- M: 741/768.

The preregistered target-coarsening inequality had **0/2304 probe-level violations**.

## Ecological meaning

The practical cost of nonidentification depends on what one wants to know.

A mechanism alias is consequential when the surviving alternatives imply different
outcomes under a declared ecological perturbation.  It is harmless for that target when
all alternatives imply the same outcome.

This creates a distinction between:

- **process uncertainty** — which A/B/M world generated current (G)?;
- **counterfactual uncertainty** — what exact distribution follows under a declared
  perturbation?;
- **decision uncertainty** — would the perturbation cross the decision threshold that
  matters?

The three need not coincide.

## What is surprising

The strongest result is not simply that the BAM mechanism is hard to identify.  That
was already established by the first paper.

The new result is that **severe mechanism nonidentification can coexist with strong
decision identification**.

Conversely, a minority of survivor fibers contain aliases that are indistinguishable
from current (G) but separate under perturbation.  Those are the cases where additional
mechanism-focused evidence is genuinely decision-relevant.

## Proposed figures

### Figure 1 — Three nested identifiability targets

One same-(G) survivor fiber, colored first by BAM state, then exact counterfactual
map, then binary decision.  Show how several mechanism classes collapse into one
decision class.

### Figure 2 — Identifiability hierarchy across 768 truths

Three bars or nested counts:

- BAM state: 25;
- exact three-probe signature: 174;
- all binary decisions: 636.

### Figure 3 — Anatomy of the 743 mechanism-nonidentified truths

Three classes:

- 149 exact-map invariant;
- 462 map-divergent / decision-invariant;
- 132 decision-divergent.

### Figure 4 — Evidence burden

Distribution of minimum direct measurement count for BAM state, exact maps and binary
decisions.

### Figure 5 — Worked survivor-fiber examples

One example for each of the three nonidentification classes, using the exact frozen
finite worlds.

## Universe-boundary stress test

The Phase-II decision result is conditional on the declared finite BAM universe.

Define the complete same-current-distribution completion set

[
\mathcal C(G)=\{(A,B,M):A\cap B\cap M=G\}.
]

For every proper (G\subset X), this complete decomposition set contains both binary
outcomes for each single-axis release.  Therefore no nontrivial binary release decision
is identified by current (G) **without restrictions on the admissible A/B/M family**.

To quantify that dependence rather than hide it, define the completion flip margin

[
\rho_T(S)
=
\min_{w\in S,\,v\in\mathcal C(G):T(v)\neq T(w)}
d_H(w,v),
]

for a target-identified survivor fiber (S), where (d_H) counts A/B/M node-state
changes.

The preregistered Phase-III audit found:

| release | proper-G identified truths | margin 1 | median | maximum |
|---|---:|---:|---:|---:|
| A | 618 | 439 | 1 | 13 |
| B | 671 | 263 | 2 | 29 |
| M | 698 | 281 | 2 | 31 |

Thus some declared-universe decisions are extremely close to an omitted counterexample,
while others require many coordinated axis-state changes to reverse.

### Witness asymmetry

For a current expansion decision, every outside-(G) node in the released map is a
witness. Reversing the decision requires eliminating all such witnesses, so the exact
margin is the number of existing witnesses.

For a current no-expansion decision, only one new outside-(G) witness is required.
The nearest reversal is therefore local and, in the frozen panel, every finite
no-expansion margin was 1 or 2.

This asymmetry is a more specific result than generic decision robustness: the geometry
of the BAM intersection determines how a release claim can fail under same-G universe
completion.

## Prior-art correction

The paper must **not** claim as a general discovery that poorly identified mechanisms
can still yield useful predictions or decisions.

That principle is established outside biogeography.  Examples include work on
prediction uncertainty in sloppy/non-identifiable biological models and explicit
methods for making predictions with poorly identified models:

- Brown et al. (2014), prediction uncertainty under parameter uncertainty;
- Simpson & Maclaren (2024), *Making Predictions Using Poorly Identified Mathematical
  Models*, Bulletin of Mathematical Biology, DOI 10.1007/s11538-024-01294-0;
- Grabowski et al. (2023), *Predictive power of non-identifiable models*.

Likewise, target-aware information collection and robust decisions under structural
uncertainty are established in conservation/adaptive-management literature:

- Bolam et al. (2019), Value of Information for conservation decisions,
  DOI 10.1111/brv.12471;
- Raymond et al. (2020), SDM + Value of Information,
  DOI 10.1111/1365-2664.13580;
- Rozowski & Fackler (2025), adaptive management under structural uncertainty,
  DOI 10.1111/2041-210X.70137;
- Liu, Maini & Baker (2026), optimal experiment design for parameter identifiability
  and model discrimination, DOI 10.1016/j.mbs.2026.109710.

The candidate contribution must therefore remain BAM-specific:

> **start from an occurrence-conditioned same-(G) survivor fiber; distinguish BAM
> mechanism, exact counterfactual and decision equivalence; compute the exact evidence
> burden for the target; then quantify how far that target certificate is from an
> undeclared same-(G) decomposition that reverses it.**

This combination, rather than generic prediction-under-nonidentifiability or generic
robust decision theory, is the novelty target.

## Structured ecological universe expansion

Phase III used complete same-(G) decomposition closure as a worst-case logical
envelope.  Phase IV inserts a prospectively frozen ecological parameter neighbourhood
between the original 64-world universe and that complete closure.

Each deterministic system is expanded to **2,592** parameter worlds using only levels
frozen before scoring:

- A: one niche-breadth level beyond each side of the narrow/broad pair;
- B: partner and antagonist one-shell erosion/base/dilation while retaining the four
  original interaction modes;
- M: one additional dispersal-radius level and one extra-long movement horizon.

The original 64 worlds must embed exactly.  For each E1 survivor fiber, only expanded
worlds with exactly the same current (G) may challenge the binary release decision.

Distance is unit-weight Manhattan distance in the frozen ecological parameter
coordinates, not cell-level Hamming distance.

### Phase-IV preregistered result

H1 one-step fragility: **SUPPORTED**.  
H2 nontrivial robustness: **SUPPORTED**.  
H3 irrelevant-axis invariance: **SUPPORTED**, zero violations.  
H4 directional median asymmetry: **REFUTED**.

No operator was added after H4 failed.

### Nested-universe erosion

The same binary target is now evaluated over three nested universe levels:

[
W_0(G)
subset
W_1(G)
subset
mathcal C(G),
]

where (W_0) is the original 64-world family, (W_1) is the same-(G) subset of the
2,592-world ecological expansion lattice, and (mathcal C(G)) is unrestricted
same-(G) binary decomposition closure.

Identification counts were:

| target | (W_0) original | (W_1) ecological expansion | (mathcal C(G)) complete closure |
|---|---:|---:|---:|
| release A | **652** | **646** | **34** |
| release B | **705** | **693** | **34** |
| release M | **732** | **691** | **34** |

Thus the structured expansion retained:

- **99.1%** of A-release certificates;
- **98.3%** of B-release certificates;
- **94.4%** of M-release certificates.

The complete closure retains only the 34 full-(G) truth cases, where there is no
outside node to become newly occupied.

This gives the paper a stronger and safer result:

> **logical same-(G) counterexamples can be ubiquitous even when counterexamples are
> rare inside the first preregistered ecological parameter neighbourhood.  A BAM
> decision certificate therefore needs a world-universe robustness profile, not merely
> an identified/unidentified label.**

### Structured counterexamples

Within (W_1):

- A release: only **6/652** identified truth cases acquired a counterexample, all at
  ecological distance 3;
- B release: **12/705**, at distances 2–3;
- M release: **41/732**, at distances 1–4.

At unique-fiber level the corresponding counterexample counts were only **1/119**,
**3/124** and **5/126** identified fibers.

The one-step fragility signal occurred only for M release.

### H4 refutation is informative

The predeclared directional-asymmetry hypothesis was not supported.

Finite ecological counterexamples were instead segregated by target:

- A: all finite flips started from no-expansion;
- B: all finite flips started from no-expansion;
- M: all finite flips started from expansion.

Therefore the bit-level witness asymmetry from unrestricted completion does not dictate
the direction of fragility under a restricted ecological operator family.

This result must remain a refutation rather than being repaired with additional
post-score operators.

## Exact nested-universe theorem

For fixed evidence (e), target (T), and nested universes (W_0subseteq W_1),

[
S(e;W_0)subseteq S(e;W_1)
]

and therefore

[
T(S(e;W_0))subseteq T(S(e;W_1)).
]

Universe expansion can preserve or destroy target identification, but cannot resolve
existing target disagreement by itself.

The 64 → 2,592 → complete-closure sequence is the frozen BAM demonstration of this
elementary exact rule.

## Structured ecological counterfactuals

Phase V replaced the idealised axis-release target with three transformations frozen
before implementation:

1. **climate shift** — temperature +0.08 and moisture -0.04, recomputing A under each
   world's niche parameters;
2. **biotic stress** — one additional partner-range erosion and antagonist-range
   dilation under the world's existing interaction mode;
3. **barrier restoration** — recompute M with the same dispersal radius and horizon but
   barrier permeability forced true.

These remain synthetic fixtures, but they test whether the target-identifiability result
depends on using axis deletion as the counterfactual.

### Pre-implementation correction

Before implementation, the protocol was amended because a structured transformation
can reactivate **parameter aliases** that have the same current A/B/M/tau state.

Therefore two different maps must be kept distinct:

[
\theta\rightarrow C_{current}(\theta)
]

and

[
\theta\rightarrow F_{counterfactual}(\theta)\rightarrow D(\theta).
]

The future transformation need not factor through current BAM state.

The guaranteed target hierarchy is therefore

[
\text{parameter world}
\rightarrow
\text{exact future map}
\rightarrow
\text{binary decision},
]

not parameter world → current BAM state → future decision.

### W0 results

In the original 64-world universe:

- parameter world identified: **13/768**;
- current BAM state identified: **25/768**.

Yet target identification was:

| transformation | exact future map | binary decision |
|---|---:|---:|
| climate shift | **622** | **646** |
| biotic stress | **558** | **603** |
| barrier restoration | **604** | **744** |

Thus parameter-world nonidentification coexisted with binary decision identification in
633, 590 and 731 truth cases respectively.

### W1 results

After expansion to the 2,592-world ecological lattice:

- parameter-world identified: **0/768**;
- current BAM-state identified: **8/768**.

Yet binary decisions remained identified in:

- climate: **636/768**;
- biotic stress: **498/768**;
- barrier restoration: **700/768**.

This is a direct structured-counterfactual replication of the target-specific
identifiability result.

### Universe expansion removes real target certificates

W0 → W1 binary certificate erosion was:

| transformation | W0 identified | retained W1 | lost |
|---|---:|---:|---:|
| climate | 646 | **636** | **10** |
| biotic stress | 603 | **498** | **105** |
| barrier restoration | 744 | **700** | **44** |

The biotic-stress target was most sensitive in this frozen synthetic design.  This is
not a universal A/B/M ranking.

### Dormant parameter reactivation

One W1 climate fiber gives a concrete counterexample to “identify current mechanism
state, then forecast.”

System `S11_9x5_gap`:

- current (G): 29 nodes;
- truth multiplicity: 2;
- same-G W1 parameter worlds: 36;
- current A/B/M/tau classes: **1**;
- climate-shift exact-map classes: **2**;
- climate net-loss decision classes: **2**.

Thus current BAM-state identity can be insufficient for a future target when parameter
differences are dormant under present conditions but active under intervention.

### New stopping rule

For a declared decision target (D), the relevant stopping condition remains

[
|D(S)|=1.
]

Current-state identity can be unnecessary if (D) is already invariant, or
insufficient if dormant parameter aliases split under the transformation.

This makes target-specific survivor-fiber analysis more than a rephrasing of current
mechanism identification.

## Updated figure plan

### Figure 6 — Universe erosion under structured transformations

For climate, biotic stress and barrier restoration, show W0 versus W1 exact-map and
binary-decision identification counts.

### Figure 7 — Dormant alias reactivation

Show the S11 same-current-state fiber splitting into two climate future maps and two
binary loss classes.

## Evidence routing for structured future targets

Phase V showed that current BAM-state identity need not determine a future response.
Phase VI turns that observation into an evidence-design problem.

Two evidence classes are kept distinct:

1. **present-state evidence** — node-level A/B/M/tau;
2. **latent-parameter evidence** — exact W1 ecological coordinates.

For a truth parameter world \(\theta_*\), present-state evidence can resolve a future
target \(T\) exactly if and only if target values are constant inside the truth's
complete current-state alias class.

This produces an evidence-routing gate before ordinary measurement ranking:

[
\text{future target unresolved}
\rightarrow
\begin{cases}
\text{state-resolvable}, & |T(A_C)|=1,\\
\text{parameter/challenge evidence required}, & |T(A_C)|>1.
\end{cases}
]

### Frozen Phase-VI result

| target | E1 unresolved | state-resolvable | state-impossible |
|---|---:|---:|---:|
| climate binary | 132 | 122 | **10** |
| biotic-stress binary | 270 | **270** | 0 |
| barrier-restoration binary | 68 | 58 | **10** |

For exact future maps the state-impossible counts were 10, 0 and **88** respectively.

The complete parameter library resolved every frozen target.

Full W1 parameter-world identity required a median of **5** parameter assays
(maximum 7), while binary decisions required:

- climate: at most 1;
- biotic stress: at most 2 parameter assays, or one channel with the combined library;
- barrier restoration: at most 2.

Strict parameter-assay savings versus full parameter-world recovery occurred for
**768/768 truths under every transformation**.

### Dormant-alias evidence routing

The S11 climate fiber makes the logic concrete.

All 36 same-G worlds share one complete present A/B/M/tau state.  Nevertheless climate
net-loss has two values.  Therefore no present-state measurement can solve the target.

For both original truth worlds, the canonical minimum parameter design is:

`A_level`

alone.

This is stronger than saying “parameter uncertainty matters.”  It identifies the
failure mode of the evidence class and gives an exact alternate channel.

### Interpretation

The field-design implication is not “measure parameters instead of states.”

The three transformations show all three possibilities:

- present-state evidence can be enough;
- parameter evidence can be necessary;
- mixing evidence classes can reduce the number of required channels.

The correct order is therefore:

1. declare the future target;
2. inspect target disagreement inside the current survivor fiber;
3. test whether the intended evidence class can separate that disagreement;
4. only then optimize the smallest admissible design.

### Figure 8 — Evidence routing

Show the three transformations with:

- E1-unresolved decision count;
- state-resolvable versus state-impossible split;
- minimum parameter/combined assay burden;
- S11 dormant climate alias as a worked impossibility example.

## Observation-process uncertainty in target-aware evidence

Phase VI treated parameter assays as exact.  Phase VII adds a finite assay-observation
world axis and asks whether the target-specific evidence certificate survives uncertain
measurement semantics.

The joint hypotheses are

[
W_J = W_E \times W_O,
]

with the future decision depending only on (W_E).

Two observation worlds were frozen:

- calibrated;
- systematically miscalibrated.

The systematic world adds +1 to ordinal codes and flips binary codes.

This is a deterministic stress test, not a laboratory error model.

### Repetition is not calibration

For a fixed systematic observation world,

[
y=g_o(x)
]

and a repeated same assay returns

[
(y,y).
]

The second representation is one-to-one with the first, so it cannot add robust pair
separation.  The audit found **0 violations** across all scored field/fiber checks.

### Calibration necessity exists

Among future-target-unresolved unique fibers, assay-only robust separation was
impossible in:

- climate: **2/18**;
- biotic stress: **2/43**;
- barrier restoration: **3/6**.

All seven were restored by admitting assay-process calibration.  The complete
calibrated action library resolved **67/67** scored fibers.

### The S11 prediction was refuted

The preregistered S11 climate prediction expected the exact minimum robust design

[
\{\text{calibration},A\_level\}.
]

Instead the exact minimum was

[
\{A\_level, antagonist\_excluded\}.
]

Size remained 2, but calibration was unnecessary.

The pair remains sufficient across both observation worlds because its **joint assay
signature** never collides across opposite climate-decision classes.

This yields an important refinement:

> **future-target identification need not identify either the ecological parameter
> world or the observation-process world.**

A multivariate assay pattern can be target-self-calibrating even when assay-world
identity remains unresolved.

### Three observation regimes

The frozen panel contains:

1. assay-only robust separation;
2. calibration useful but not strictly required for solvability;
3. calibration-required robust separation.

The relevant field-design question is therefore not simply “how many replicates?” but

> which evidence channels jointly separate target-discordant ecological × observation
> worlds?

### Figure 9 — Observation-process routing

Show:

- the two assay worlds;
- repeat-same-assay as a no-gain negative control;
- calibration-required fibers by transformation;
- the S11 refutation, contrasting the preregistered calibration+A-level expectation
  with the observed A-level+antagonist-excluded self-calibrating minimum.

## Strong claim boundary

Do not claim:

- that the axis-release probes are literal management interventions;
- that 82.8% is a universal ecological frequency;
- that decision identification establishes the true mechanism;
- that full mechanism information is generally unnecessary for every future question;
- generic novelty for model discrimination, value of information, optimal experiment
  design or set-cover algorithms.

Do claim, conditional on the frozen universe:

- mechanism, counterfactual-map and decision identifiability are distinct;
- target coarsening cannot increase exact truth-relative evidence burden under the same
  evidence library;
- full mechanism recovery can require strictly more evidence than a declared
  counterfactual decision;
- unresolved BAM worlds should be retained until they become irrelevant to the target
  or are separated by target-discriminating evidence.

## Next validation after assay-process routing

Do **not** add another deterministic coding rule to make Phase VII look more or less
favorable.

The remaining abstraction is that the assay observation worlds are deterministic.
A genuinely new successor should freeze a **stochastic observation-process universe**
before scoring—for example finite misclassification/detection kernels—and ask whether:

- repeated independent measurements can now add robust or probabilistic information;
- target-self-calibrating multichannel designs survive stochastic overlap;
- calibration remains necessary in the fibers that required it under systematic bias;
- adaptive evidence selection can stop once the future target, rather than the assay
  world or parameter world, is sufficiently resolved.

That is a separate programme.  It must not reinterpret the frozen Phase-VII
systematic-bias result.
