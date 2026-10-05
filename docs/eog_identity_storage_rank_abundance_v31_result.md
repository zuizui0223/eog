# EOG v31 result — where is assembly history stored?

## Verdict

The preregistered identity-storage hypothesis was **refuted**.

v31 held the experimental units, abundance values, response dimensionality and history
model fixed, then removed only the mapping between abundance values and ecological
identities by sorting each community vector from largest to smallest.

If assembly history were generally stored in "who occupies which abundance rank", the
null-calibrated history signal should have fallen in both systems.

It did not.

Authoritative execution:

- workflow run: `37296204849`;
- artifact: `11339351017`;
- artifact digest:
  `sha256:7b13fb6cf3090eb26fa6f9d01f343571112345e7e3d49dafd201658ff8761adb`;
- result fingerprint:
  `82a84ac84133f3a7eb45e29acb276ae64bc61f520ec5682fd56cf8c2a4a8f9ee`.

Both authoritative labeled-composition results from v28 and v30 were exactly reproduced
before the identity-stripped targets were accepted.

## v28 microbiome: history survives without taxon identity

Five-dimensional labeled fungal composition:

- retained-history excess E = **+0.1467**;
- p = **0.0001**.

The same five values sorted within each plant, with fungal identities removed:

- E = **+0.1486**;
- p = **0.0001**.

Identity-storage gap:

- G = E(labeled) - E(rank) = **−0.0019**.

The rank-abundance target retained **101.3%** of the labeled target's excess.

The label-invariant Shannon sensitivity was stronger still:

- E = **+0.2523**;
- p = **0.0001**.

Thus the v28 historical signal is not mainly a record of which named fungal taxon occupies
which abundance rank. Arrival history strongly changes the **shape of the abundance
distribution itself** — dominance/evenness structure remains diagnostic even after taxon
names are erased.

## v30 grassland: identity carries most, but not all, memory

Three-dimensional labeled functional-group shoot composition:

- E = **+0.8034**;
- p = **0.0001**.

The same three biomass values sorted within each rhizobox:

- E = **+0.1949**;
- p = **0.0769**.

Identity-storage gap:

- G = **+0.6085**.

The rank-abundance target retained only **24.3%** of the labeled target's excess.

Here most persistent assembly history is therefore associated with **which functional
group occupies an abundance rank**, not merely the unlabeled dominance profile.

However identity is not the whole story. Shannon entropy still retained:

- E = **+0.3800**;
- p = **0.0235**.

So grassland arrival history also changes abundance inequality/evenness, just far less
than it changes functional-group identity structure.

## Main ecological result

The cross-system result is not a universal attenuation law and not a universal
identity-storage law.

It is more specific:

> **Ecological systems can store assembly history in different components of present
> community structure. In one system, history is encoded strongly in unlabeled abundance
> architecture; in another, most of the historical signal resides in which ecological
> identities occupy those abundance ranks.**

This explains why v28 and v30 both showed strong compositional memory while weaker
downstream-state memory, yet need not share the same internal storage mechanism.

## Why this is not just composition versus function

Functional convergence without taxonomic convergence is already well established in the
historical-contingency literature.

v31 asks a different question. The labeled and identity-stripped targets:

- use the same raw abundance values;
- have the same dimensionality;
- use the same experimental units;
- use the same distance metric;
- use the same history model;
- use the same paired permutation stream.

Only ecological identity labels are removed.

Therefore the divergent v28/v30 outcomes cannot be explained by a generic
"multivariate composition has more information than a scalar function" argument.

## Updated mainline

v26: present states retain target-specific projections of history.

v28 and v30: those projections differ strongly among real ecological targets.

v31: **the internal carrier of that retained history is itself system-specific**.

The current biological question is therefore no longer:

> does history persist?

or even:

> which target remembers history?

It is:

> **which component of present community organization — identity, abundance architecture,
> spatial structure or collective function — acts as the storage medium of assembly
> history in a given ecological system?**

## Claim boundary

Do not claim:

- a universal identity-storage principle;
- that taxon identity is unimportant in v28;
- that grassland history is purely identity-based;
- first discovery of compositional contingency or functional convergence;
- a mechanistic cause for the different storage channels without further tests.

Do claim:

> **The same priority-effect concept can leave fundamentally different statistical and
> biological fingerprints across systems: historical memory may reside in abundance
> architecture itself or primarily in the identity-to-abundance mapping.**
