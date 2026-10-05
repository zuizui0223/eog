# Assembly-history storage — manuscript spine v1

## Working title

**Assembly history is stored through contrasting structural channels in ecological communities**

Sharper alternative:

**Where ecological history is stored depends on how identities express the first-arriver role**

## One biological question

> **What determines where assembly history remains encoded in the present community?**

The paper does **not** ask whether priority effects exist. Arrival-order effects on
community composition and ecosystem/host function are already well established.

The paper asks what happens after a priority effect has occurred:

> When history remains detectable, is it stored in **who is abundant**, in the
> **unlabeled abundance architecture**, or in another present ecological state — and why
> does that storage channel differ among systems?

## One-sentence answer supported now

> **Assembly history is not stored in one universal feature of the present: the dominant
> storage channel differs among systems and, in the two completed experiments, that
> contrast tracks how identity-dependent the ecological effect of arriving first is.**

This is the manuscript-level claim boundary. It is intentionally narrower than a
universal law.

## Why this is not an ordinary priority-effects paper

Established literature already shows that:

- arrival order can alter community composition and function;
- taxonomically divergent communities can converge functionally;
- priority-effect magnitude and direction can vary among species identities;
- symmetric niche preemption is possible when different identities express a similar
  first-mover advantage.

The new object here is **historical storage**.

The same manipulated history is projected onto multiple present-state descriptions. By
holding experimental units, raw abundances and in v31-v32 even response dimensionality
fixed, the analysis asks which component of present organization actually carries the
historical signal.

## Evidence chain

### 1. Target-specific retention is real, not just a known-truth artifact

Known-truth v26 established that different present-state mappings can preserve different
parts of the same hidden colonization history.

This is conceptual support, not the empirical headline.

### 2. Two independent real experiments show strong target dependence

#### v28 — plant microbiome

Same 233 experimental plants and the same manipulated fungal arrival history:

- fungal community composition retained clear above-null history:
  E = **+0.1467**, p = **0.0001**;
- aggregate rust lesion state:
  E = **+0.0153**, p = **0.3893**.

Thus history was strongly visible in community state but close to the randomized baseline
in the downstream host-state target.

#### v30 — grassland

Same 19 rhizoboxes and the same manipulated plant-functional-group arrival history:

- shoot functional-group composition:
  E = **+0.8034**, p = **0.0001**;
- complete six-layer root-biomass distribution:
  E = **+0.0344**, p = **0.3765**;
- total shoot biomass also retained little history:
  E = **+0.0948**, p = **0.2562**.

An independent exact enumeration of all 31,104 within-block labelings reproduced the
primary contrast.

These two systems establish the empirical phenomenon: **history is present-state
variable specific**.

### 3. A universal identity-storage explanation fails

v31 prospectively predicted that compositional memory would generally reside in the
mapping between ecological identities and abundance ranks.

The prediction was refuted.

The identity-stripped target kept every abundance value and every response dimension but
sorted values within each experimental unit.

#### Microbiome

- labeled E = **+0.1467**;
- identity-stripped rank-abundance E = **+0.1486**;
- identity-storage gap = **−0.0019**;
- Shannon entropy E = **+0.2523**, p = **0.0001**.

Removing fungal names did not remove history.

#### Grassland

- labeled E = **+0.8034**;
- rank-abundance E = **+0.1949**;
- identity-storage gap = **+0.6085**;
- Shannon entropy E = **+0.3800**, p = **0.0235**.

Here most, but not all, historical memory depended on which functional-group identity
occupied each abundance rank.

Therefore the storage medium itself is system-specific.

### 4. Assembly-role alignment explains the contrast

v32 prospectively aligned communities by **assembly role** rather than identity:

- coordinate 1 = abundance of the experimentally first-arriving identity;
- all remaining abundances sorted;
- absolute identities removed.

The prospective prediction that the role-aligned fraction would be greater in the
microbiome than in the grassland was supported.

#### Microbiome

Role-aligned history retention:

- E = **+0.7313**, p = **0.0001**.

Mean final abundance share of the first arriver depended drastically on which fungus was
first:

- *Alternaria* = **0.778**;
- *Fusarium* = **0.179**;
- *Cladosporium* = **0.090**;
- *Dioszegia* = **0.047**;
- *Aureobasidium* = **0.031**.

The ecological role "arrive first" is therefore expressed very differently by different
fungal identities.

#### Grassland

Role-aligned retention:

- E = **+0.1949**, p = **0.0769**.

This is exactly identical to the fully rank-sorted target.

Mean final first-arriver biomass shares were all high:

- F-first = **0.716**;
- G-first = **0.672**;
- L-first = **0.817**.

Here different identities express a comparatively similar first-mover-dominance role.
Most history is consequently stored in **which identity occupies that role**, rather than
in a different unlabeled abundance architecture.

## Central biological model

The manuscript should use two descriptive storage modes, not assert two universal
mechanisms.

### Architecture-memory mode

Different possible first arrivers do not express the first-arriver role equivalently.

History therefore changes:

- dominance/evenness;
- rank-abundance architecture;
- and potentially which identity is abundant.

The v28 microbiome is the empirical example.

### Identity-assignment mode

Different possible first arrivers express a more interchangeable first-mover role.

History therefore changes mainly:

- which identity occupies the dominant position,

while unlabeled rank structure changes much less.

The v30 grassland is the empirical example.

These labels describe the **observed storage channel**. They are not synonyms for niche
preemption or niche modification.

## Relation to priority-effects theory

The natural theoretical bridge is Fukami's priority-effects framework.

Symmetric niche preemption provides a biological limiting case in which different
identities can obtain a similar advantage from arriving first. Species-specific
differences in fitness, interaction strength or niche modification can instead make the
magnitude and direction of priority effects identity dependent.

v32 is consistent with that distinction, but it does not directly measure the underlying
interaction coefficients or discriminate preemption from modification.

Therefore use:

> "consistent with differences in assembly-role symmetry"

not:

> "proves symmetric versus asymmetric niche preemption."

## Main hypotheses / tests in manuscript order

### H1 — present-state retention is target specific

A manipulated history can remain above null in one present-state target while being close
to null in another target measured on the same experimental units.

Supported independently by v28 and v30.

### H2 — persistent compositional memory is universally identity based

Refuted prospectively by v31.

This refutation is scientifically useful and should remain explicit.

### H3 — contrasting storage channels correspond to contrasting expression of the
first-arriver role

Prediction frozen before v32 scoring:

role_fraction(v28) > role_fraction(v30).

Supported.

## Figure architecture

### Figure 1 — Concept, not method

One arrival history branches into alternative present-state descriptions.

Show three possible storage locations:

1. identity assignment;
2. abundance architecture;
3. downstream collective/spatial state.

The figure should make the biological question visible without EOG jargon.

### Figure 2 — Two independent target-specific retention profiles

Side-by-side:

- v28 composition versus rust;
- v30 shoot composition versus root distribution / total biomass.

Plot null-calibrated E with permutation null context, not raw R² alone.

### Figure 3 — Identity-stripping experiment

For each system show:

labeled composition -> rank-sorted same values.

Then plot:

- E_labeled;
- E_rank;
- Shannon sensitivity.

This figure carries the v31 refutation.

### Figure 4 — Assembly-role alignment

Show the transformation:

named identities -> first_arriver + ranked later identities.

Then show:

- role-aligned E;
- history-specific first-arriver shares.

This is the mechanistic bridge to priority-effect symmetry.

## Abstract spine

### Background

Priority effects are usually described by whether arrival history changes community
composition or function, but this does not identify **where the resulting historical
information is retained in the present community**.

### Approach

Reanalyse two independently published randomized arrival-order experiments using matched
experimental units and null-calibrated history retention. Then prospectively remove
identity information while preserving raw abundances and dimensionality, followed by an
assembly-role alignment test.

### Results

History was strongly retained in community composition but much less in a downstream
host/spatial target in both systems. However, identity stripping had opposite
consequences: fungal historical memory survived without taxon labels, whereas most
grassland memory disappeared. Aligning communities by the first-arriver role exposed
strong colonist-specific variation in fungal first-arriver effectiveness but a
comparatively interchangeable first-mover-dominance pattern among grassland functional
groups.

### Conclusion

Historical contingency is not merely stronger or weaker across endpoints. **Different
communities can store the consequences of assembly history in different components of
present organization.**

## What must not be claimed

Do not claim:

- that priority effects are new;
- that functional convergence is new;
- a universal information-loss law;
- that history always moves composition -> function in one direction;
- a universal architecture-memory versus identity-memory dichotomy;
- direct evidence for niche preemption rather than niche modification;
- causal mediation from composition to rust/root state;
- generality beyond the two completed empirical systems.

## Current novelty assessment

The strongest novelty is **not** the EOG statistic.

The strongest novelty is the biological decomposition:

> **the historical signal in a final community can be localized to different components
> of community organization while holding the underlying abundances fixed.**

The v31 identity-stripping comparison is especially important because it prevents the
result from collapsing into the familiar statement that "composition contains more
information than function."

v32 then gives the result a biological interpretation by tying the storage contrast to
how differently candidate identities express the same first-arriver role.

## Decisive next evidence — not another arbitrary example

The next evidence should test a cross-system prediction, not merely add a third case.

For each fully reusable arrival-order experiment with matched final composition:

1. quantify **storage architecture** using labeled, rank-sorted and role-aligned targets;
2. quantify **first-arriver asymmetry** from variation in the final share/effect of the
   first-arriving identity;
3. test whether greater first-arriver asymmetry predicts a larger fraction of history
   retained in identity-free abundance architecture.

That would turn the current two-system mechanism into a general comparative prediction.

Until such a cross-system panel exists, the manuscript must present v28/v30 as two
independent demonstrations and v31/v32 as prospective mechanism-facing tests within those
systems.
