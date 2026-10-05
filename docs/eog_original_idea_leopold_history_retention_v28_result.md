# Original EOG external target-specific history retention — v28 result

## Result

The frozen external benchmark completed successfully.

Authoritative execution:

- workflow run: `37276170197`;
- artifact: `11330736048`;
- artifact digest:
  `sha256:3a9e989e79d72428b00b1ca45583e893a584fad56c992e618ed6ced739f9c38c`;
- result fingerprint:
  `60d32bf5daf49cb33f6c6989fd64ee7f0b74d544d0b3441e99d8605ba0b9b302`.

All four pinned source blobs reproduced their declared Git blob SHAs before scoring.

The common panel contained:

- **233 plants**;
- **12 host genotypes**;
- **5 manipulated arrival-order treatments**;
- all **60 genotype × treatment cells** represented.

The generic nested-model implementation and the independent fast cell-means
implementation agreed for both primary targets before the permutation distribution was
scored.

## Primary target-specific retention profile

The frozen history estimand compared:

[
M_0 = 1 + mathrm{Genotype}
]

against:

[
M_1 = 1 + mathrm{Genotype}
+ mathrm{Treatment}
+ mathrm{Genotype}	imesmathrm{Treatment}.
]

Thus the added history subspace includes both the average arrival-order contribution and
its genotype-dependent expression.

### Fungal community composition

Bias-corrected five-taxon Bray–Curtis composition:

- observed partial (R_H^2): **0.3697**;
- permutation-null mean: **0.2242**;
- permutation-null median: **0.2230**;
- null 95% interval: **0.1726–0.2801**;
- excess above null median: **+0.1467**;
- genotype-stratified permutation value: **0.0001** from 9,999 permutations.

The manipulated arrival history therefore left a community-composition signal well beyond
what is expected from fitting the same high-dimensional genotype × treatment structure to
randomized treatment labels.

### Host rust lesion fraction

Plant-level rust lesion fraction:

- observed partial (R_H^2): **0.2300**;
- permutation-null mean: **0.2188**;
- permutation-null median: **0.2147**;
- null 95% interval: **0.1238–0.3353**;
- excess above null median: **+0.0153**;
- genotype-stratified permutation value: **0.3893**.

Therefore the raw (R^2) value of 0.23 must **not** be read as strong history retention.
With 48 identifiable history dimensions added to the model, a substantial apparent
fraction is expected under randomized treatment labels.

Under the frozen v28 target and common-panel representation, the host disease state lies
close to its permutation baseline.

## Main ecological result

Within the same manipulated plants, the same arrival history was retained very differently
by two present ecological targets.

> **Assembly history remained strongly encoded in the fungal community state but was
> largely attenuated in the aggregate host disease state under the declared
> genotype-aware retention metric.**

This is not evidence that history has no effect on disease.

The original Leopold & Busby study already showed genotype-dependent disease modification
by arrival order and explicitly argued that composition and function can decouple.
v28 asks a different question: how much of the manipulated history remains visible when
each endpoint is treated as a target state under one common retention contract.

The correct interpretation is therefore:

> **historical information need not be conserved as ecological state is transformed
> across levels of organization.**

In this experiment, a strong community-level history signal does not translate into an
equally strong global history-retention signal in the host disease target.

## Why null calibration mattered

The initial observed values alone were:

- composition: 0.370;
- rust lesion: 0.230.

Those numbers could misleadingly suggest that both targets retain substantial history.

The permutation calibration shows why that conclusion would be wrong:

- composition exceeds its null median by **0.147**;
- rust exceeds its null median by only **0.015**.

The null calibration is not a new post hoc endpoint. It summarizes the
prospectively frozen 9,999-permutation diagnostic.

This is an important practical consequence for EOG: when the declared history model has
many context-dependent degrees of freedom, raw explained variance is not itself a measure
of retained ecological memory.

## Positive-control target

The secondary first-colonist proportional-abundance target had:

- partial (R_H^2): **0.9694**.

No permutation p-value is attached because the target definition itself selects the taxon
named by the treatment and therefore is not label-exchangeable in the same sense as the
two primary targets.

Its role is only to verify that the manipulated arrival identity is strongly reflected in
the expected local community coordinate.

## Frozen sensitivities

### Raw counts instead of taxon-bias correction

Five-taxon raw-count composition:

- partial (R_H^2): **0.3104**;
- null median: **0.2215**;
- excess above null median: **+0.0890**;
- permutation value: **0.0121**.

Thus the community-history result is weaker without the frozen bias correction but remains
above the genotype-stratified permutation baseline.

### Published outlier exclusion

After removing `G4.T2.R5.TP1`:

- n = **232**;
- corrected composition (R_H^2 = 0.3716);
- raw composition (R_H^2 = 0.3155);
- rust lesion (R_H^2 = 0.2323);
- first-colonist proportion (R_H^2 = 0.9695).

The headline profile is effectively unchanged.

### Composition-only structurally eligible panel

Using all TP1 community samples with structurally valid OTU data, without requiring rust
measurement:

- n = **248**;
- corrected composition (R_H^2 = 0.3364).

The strong community history signal is therefore not an artifact of restricting to the
233 plants with both targets.

### Region descriptives

East, n = 99:

- corrected composition (R_H^2 = 0.4387);
- rust lesion (R_H^2 = 0.2579).

West, n = 134:

- corrected composition (R_H^2 = 0.3213);
- rust lesion (R_H^2 = 0.0863).

These are descriptive sensitivities only. v28 did not preregister region-specific
permutation inference.

## Relation to the original paper

The original study already established that:

- arrival order changes fungal community composition;
- the effect varies among host genotypes;
- arrival order can alter disease susceptibility;
- composition and host function can be decoupled.

v28 does not claim any of those as new biological discoveries.

The added EOG result is the **common-unit retention profile**:

> the same manipulated history, evaluated with the same 233 plants and the same
> genotype-aware model expansion, is strongly above null in community composition but
> near null in the aggregate disease target.

## Claim boundary

Do not claim:

- that priority effects were discovered by EOG;
- that arrival order has no effect on rust disease;
- that community composition causally mediates the disease result;
- that the community-to-disease attenuation is universal across systems;
- that raw partial (R^2) values are directly comparable without their null calibration;
- that first-colonist proportional abundance is an independent inferential endpoint.

Do claim:

> **In one independently published, randomized assembly-history experiment, EOG's
> target-specific retention framing reveals that manipulated history can remain strongly
> detectable in community composition while being almost indistinguishable from the
> permutation baseline in a downstream host-state target.**

## Next question

The result is now ecological rather than only methodological.

The next question is whether this attenuation is general:

> **Does ecological history systematically lose, retain, or sometimes regain information
> as it propagates from community composition into ecosystem or host-level functions?**

One system cannot establish that principle.

The correct next move is therefore a second independently licensed assembly-history
experiment in which community composition and a functional endpoint are measured on the
same experimental units. The pre-screen must occur before a new benchmark is frozen.
