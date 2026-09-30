# Manuscript spine v1 — BAM counterfactual identifiability

## Working title

**Mechanism identifiability is not decision identifiability: counterfactual sufficiency in finite BAM worlds**

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

> **A current distribution can leave its generating BAM mechanism strongly
> nonidentified while still identifying a declared counterfactual decision; evidence
> should therefore be collected until the decision target is identified, not
> automatically until the entire mechanism is recovered.**

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
