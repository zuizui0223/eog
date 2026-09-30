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

## Next validation after this paper core is frozen

Do **not** add another arbitrary synthetic system to improve the counts.

The next independent extension should replace idealised release probes with
prospectively frozen ecological perturbations, for example:

- a defined abiotic/climate shift acting on A;
- a partner/antagonist perturbation acting on B;
- a corridor/barrier/translocation perturbation acting on M.

The key test is whether the target-specific identifiability hierarchy persists when the
counterfactual is biologically structured rather than an axis deletion.
