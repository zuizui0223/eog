# Editorial positioning for the structural-reachability paper

Target: **Ecological Informatics — Original Research Paper**

## One-sentence problem

Existing ecological models already combine habitat suitability, occupied-neighbour information, patch structure and landscape connectivity, but the incremental value of a generic occurrence-conditioned structural term depends on what the reference model already contains and should be established with leakage-safe held-out evidence rather than assumed.

## One-sentence contribution

EOG provides an auditable, reference-conditioned validation design that separates local support, direct source proximity, generic graph configuration and landscape-specific connectivity, constructs occurrence-conditioned structural features from outer-training data only, and tests whether the structural addition earns an incremental held-out claim.

## One-sentence empirical boundary

Across 845 estimable A-Islands plant taxa, connected frequency retained conditional incidence information beyond frozen climate support and nearest source (mean concordance 0.618), whereas across 60 Tanzanian forest birds it worsened primary LOSO prediction after matrix-aware current flow and nearest source were already represented (+0.032 log loss), with spatial-block sensitivity uncertain.

## What the editor should not have to infer

The manuscript should explicitly acknowledge before introducing EOG that:

- accessibility/M in ENM/SDM is established;
- environmental-quality + network/occupied-neighbour occupancy models are established;
- habitat suitability + network topology models are established;
- functional-habitat frameworks already integrate E-space, G-space and topological space;
- connectivity terms have already been added to SDMs and metapopulation models;
- dispersal-threshold sensitivity and connectivity-model uncertainty have already been studied.

The editorial novelty case therefore rests on **reference-conditioned incremental validation, held-out-safe occurrence conditioning, falsifiability against a strong connectivity reference, explicit failure accounting, and preservation of a positive/adverse empirical scope boundary**, not on graph connectivity itself.

## Cover-letter opening direction

Lead with the scientific question and falsifiable result boundary, not the acronym:

> When does landscape configuration add information beyond local environmental support and simple source proximity, and when is that information already captured by a stronger landscape-connectivity model? We answer this with two leakage-controlled empirical benchmarks that were designed to permit opposite outcomes: a broad positive result across Australian island plants and an adverse strong-reference result across Tanzanian forest birds.

## Desk-reject defense

If the editor sees EOG as another suitability-connectivity integration, the manuscript has failed to communicate its actual contribution. The first two Introduction pages must make the closest precedents visible and then state that the paper tests the **incremental estimand relative to reference content**.

Do not respond to that risk by adding post-outcome favourable analyses. Respond by improving positioning, or retarget if the journal does not value validation/informatics contributions.