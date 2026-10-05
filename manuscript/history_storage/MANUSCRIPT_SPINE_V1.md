# Assembly-history storage — manuscript spine v2

## Working title

**Assembly history is stored through contrasting structural channels in ecological communities**

Sharper alternative:

**The present can retain ecological history without retaining the same kind of information**

## One biological question

> **Where does assembly history remain encoded in the present community?**

The paper does **not** ask whether priority effects exist. Arrival-order effects on
community composition and ecosystem or host function are already established.

The paper asks a different question:

> When history remains detectable, which component of present organization carries it —
> ecological identity, unlabeled abundance architecture, spatial organization, or an
> aggregate state?

## One-sentence answer supported now

> **Assembly history is not stored in one universal feature of the present: the amount
> and structural location of historical information differ among ecological targets and
> among systems.**

The mechanism determining that storage channel remains unresolved.

That last sentence is important. v33 prospectively falsified the first mechanism proposed
after v31, so the manuscript must not present first-arriver-role symmetry as established.

## Why this is not an ordinary priority-effects paper

Established literature already shows that:

- arrival order can alter community composition and function;
- taxonomically divergent communities can converge functionally;
- priority-effect magnitude and direction vary among species and environments;
- composition and ecosystem function need not retain the same historical contingency.

The new object here is **historical storage in present state**.

The same manipulated history is projected onto several present-state descriptions. The
analysis then asks which descriptions retain distinguishable information about the
history.

The strongest empirical decomposition does not require a new statistic:

- matched experimental units;
- frozen history models;
- randomization-calibrated retained-history scores;
- transformations that selectively remove identity while preserving the same abundance
  values and dimensionality.

## Evidence chain

### 1. Known truth: present targets are projections of history

v26 established in a frozen virtual world that final occupancy, provenance and
colonization-age-derived state can preserve different parts of the same history.

The durable conceptual statement is:

> a present state does not simply remember or forget history; it retains a projection of
> history defined by the state variable being observed.

This motivates the empirical work but is not the biological headline.

### 2. Two independent experiments show strong target-specific retention

#### v28 — plant microbiome

Same **233 plants** and the same manipulated fungal arrival history:

- fungal community composition:
  - retained-history excess E = **+0.1467**;
  - permutation p = **0.0001**;
- aggregate rust lesion state:
  - E = **+0.0153**;
  - p = **0.3893**.

Thus arrival history is clearly visible in community state but close to its randomized
baseline in the aggregate host-state target.

#### v30 — grassland

Same **19 rhizoboxes** and the same manipulated plant-functional-group arrival history:

- shoot functional-group composition:
  - E = **+0.8034**;
  - p = **0.0001**;
- full six-layer root-biomass distribution:
  - E = **+0.0344**;
  - p = **0.3765**;
- total shoot biomass:
  - E = **+0.0948**;
  - p = **0.2562**.

An independent enumeration of all **31,104** within-block history labelings reproduced
the primary shoot-versus-root contrast.

Together v28 and v30 establish the core empirical phenomenon:

> **history is present-state-variable specific.**

### 3. Identity stripping shows that even the storage medium differs among systems

v31 prospectively tested the stronger hypothesis that compositional history is generally
stored in the mapping between ecological identities and abundance ranks.

For every experimental unit, it kept the same abundance values and the same number of
dimensions but sorted abundances from largest to smallest, deleting taxon or functional-
group labels.

That universal identity-storage hypothesis was **refuted**.

#### Microbiome

- labeled fungal composition E = **+0.1467**;
- identity-stripped rank-abundance E = **+0.1486**;
- identity-storage gap G = **−0.0019**;
- Shannon entropy E = **+0.2523**, p = **0.0001**.

Removing fungal names did not remove the history signal. History is strongly visible in
unlabeled abundance architecture itself.

#### Grassland

- labeled functional-group composition E = **+0.8034**;
- identity-stripped rank-abundance E = **+0.1949**;
- identity-storage gap G = **+0.6085**;
- Shannon entropy E = **+0.3800**, p = **0.0235**.

Here roughly three quarters of the labeled retained-history excess disappears when
functional-group identity is removed.

Therefore:

> **the storage medium of assembly history is itself system specific.**

### 4. A plausible first-arriver-role explanation fails a specificity audit

v32 prospectively aligned each community by assembly role:

- coordinate 1 = abundance of the experimentally first-arriving identity;
- remaining abundances sorted;
- absolute names otherwise removed.

The resulting role-aligned contrast appeared to support a biological explanation based
on how differently identities express the first-arriver role.

Numerically:

- microbiome role-aligned E = **+0.7313**, p = **0.0001**;
- grassland role-aligned E = **+0.1949**, p = **0.0769**.

However, the response transformation itself used the observed Treatment label to choose a
coordinate. v33 therefore froze a specificity audit before calculating any placebo
mapping.

#### v33 microbiome audit

All **120** one-to-one history-to-fungal-coordinate mappings were enumerated.

The biologically correct mapping:

- R² = **0.945878**;
- median incorrect-mapping R² = **0.945209**;
- rank = **53/120**;
- finite mapping-tail fraction = **0.4417**.

The correct mapping is not exceptional.

#### v33 grassland audit

All **6** history-to-functional-group mappings were enumerated.

The biologically correct mapping:

- R² = **0.337247**;
- median incorrect-mapping R² = **0.876815**;
- rank = **6/6**.

Thus arbitrary treatment-indexed coordinate transformations can produce stronger apparent
separation than the biologically correct first-arriver mapping.

### Consequence of v33

The numerical v32 transformations remain reproducible, and its first-arriver abundance
summaries remain descriptive observations.

But its proposed mechanism is not retained.

The manuscript must therefore say:

> **The storage channel differs among systems, but the mechanism determining that channel
> remains unresolved.**

This is stronger science than preserving a convenient explanation that fails its own
specificity audit.

## Current biological model

Use **storage channels** as descriptive states, not mechanistic categories.

### Architecture-rich storage

History remains visible after ecological identities are removed.

Observed in the v28 microbiome:

- labeled composition and rank-abundance retain similar history;
- entropy also retains history.

This means different histories leave different abundance architectures.

It does **not** yet say why.

### Identity-rich storage

Most labeled history disappears when ecological names are removed.

Observed in the v30 grassland:

- labeled functional-group composition retains very strong history;
- rank-abundance retains much less;
- aggregate total biomass retains little.

This means much of the final historical fingerprint lies in which functional group holds
which abundance position.

Again, this is a description of storage, not a mechanism.

## A new post-v33 clue

The v33 placebo ensemble contains one potentially useful lead.

In the microbiome, all five highest-scoring mappings preserve:

- **Alternaria -> Alternaria**

while freely reassigning the other four fungal histories.

This suggests that architecture-level memory may be disproportionately driven by one
highly distinctive history state rather than by a general first-arriver-role asymmetry.

This is **not yet a result**.

The next valid test is a prospectively frozen history-leverage analysis:

- remove each history level in turn;
- recompute rank-abundance retained-history excess under the same genotype/block
  contract;
- ask whether removing Alternaria causes a uniquely large collapse in architecture
  memory;
- use equivalent leave-one-history-out diagnostics in the grassland as a contrast.

No statement that Alternaria is the driver should appear before that test.

## Relation to established theory

The paper should connect to priority-effects theory conservatively.

Existing theory supplies candidate mechanisms:

- niche preemption;
- niche modification;
- species-specific interaction strength;
- environmental conditioning;
- differential persistence of early colonists;
- functional redundancy.

The current EOG evidence does **not** discriminate among them.

The contribution is instead to separate the phenomenon that theory must explain:

1. history can be strongly present in one current state and weak in another;
2. even within composition, history may be stored in different structural coordinates;
3. a biologically appealing role-based explanation can fail when tested against equally
   complex placebo mappings.

That decomposition makes subsequent mechanism tests sharper.

## Main hypotheses / tests in manuscript order

### H1 — present-state retention is target specific

A manipulated history can remain strongly above null in one present-state target while
being close to null in another target measured on the same experimental units.

**Supported independently by v28 and v30.**

### H2 — persistent compositional memory is universally identity based

If true, removing ecological labels while retaining the same abundance values should
erase most history.

**Refuted prospectively by v31.**

### H3 — first-arriver-role alignment explains the storage-channel contrast

v32 produced an apparently supportive cross-system contrast.

v33 then applied the required mapping-specificity control.

**Not supported.**

This failed mechanism test should remain explicit in the paper because it prevents the
story from becoming an after-the-fact narrative.

## Figure architecture

### Figure 1 — The storage problem

One manipulated assembly history branches into different descriptions of the present.

Show:

1. identity structure;
2. unlabeled abundance architecture;
3. downstream aggregate or spatial state.

The question is: which branch still distinguishes histories?

### Figure 2 — Target-specific retention in two independent experiments

Side-by-side:

- v28 fungal composition versus rust state;
- v30 shoot composition versus root distribution and total biomass.

Use null-calibrated E and show the relevant permutation-null context.

### Figure 3 — Identity stripping

For each system:

labeled composition -> same values, sorted, labels removed.

Plot:

- E_labeled;
- E_rank;
- Shannon sensitivity.

This is the manuscript's cleanest decomposition because response dimensionality and raw
abundances are held fixed.

### Figure 4 — A mechanism test that fails

Panel A: v32 role-alignment construction and apparent role-aligned result.

Panel B: v33 complete placebo-mapping ensemble.

Show the biologically correct mapping inside the ensemble:

- microbiome: 53/120;
- grassland: 6/6.

This figure demonstrates why treatment-dependent response transformations require
specificity controls and why the paper stops short of a mechanistic claim.

## Abstract spine

### Background

Priority effects are usually evaluated by asking whether arrival history changes final
composition or function. That does not reveal **where historical information remains
encoded in the present state**.

### Approach

Reanalyse two independently published randomized arrival-order experiments on matched
experimental units using null-calibrated history retention. Then prospectively remove
ecological identity while retaining the same abundance values and dimensions. Finally,
test a candidate first-arriver-role explanation against all equally complex placebo
mappings.

### Results

In both systems, assembly history remained strongly visible in community composition but
much less visible in another present ecological target. Identity removal had contrasting
effects: fungal history survived essentially intact in unlabeled abundance architecture,
whereas most grassland history depended on functional-group identity. A subsequent
role-alignment explanation failed a complete mapping-specificity audit.

### Conclusion

> **Historical contingency is not simply stronger or weaker across endpoints. Different
> communities retain the same kind of past perturbation in different structural
> components of the present, and identifying the storage channel is logically prior to
> assigning a mechanism.**

## What must not be claimed

Do not claim:

- that priority effects are new;
- that functional convergence is new;
- a universal information-loss law;
- a universal architecture-memory versus identity-memory dichotomy;
- that v32 identified assembly-role symmetry as the mechanism;
- direct evidence for niche preemption versus niche modification;
- causal mediation from composition to rust or root state;
- that Alternaria is already proven to drive the microbiome result;
- generality beyond the two completed empirical systems.

## Current novelty assessment

The strongest novelty is not the EOG statistic.

It is the **experimental decomposition of historical storage**:

> the historical signal in a final community can be localized to different components of
> present organization while the underlying abundance values are held fixed.

v31 is the key novelty-bearing test because it separates ecological identity from
abundance architecture without changing dimensionality.

v33 strengthens the paper by showing that a plausible biological explanation does not
survive an equally complex placebo-mapping control.

That negative result protects the central claim from becoming a just-so story.

## Decisive next evidence

Do not add an arbitrary third case yet.

The next analysis should test the post-v33 leverage clue prospectively:

> **Is the microbiome architecture-memory result distributed across fungal histories, or
> is it dominated by one exceptional arrival history such as Alternaria?**

A frozen leave-one-history-out test can answer this using the existing randomized
experiment without redefining the response after seeing the outcome.

Only after that should the project decide whether a third system is needed for
mechanistic generalization.
