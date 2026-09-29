# BAM inverse-identifiability — literature positioning v2

## Purpose

This note separates the manuscript's defensible contribution from established BAM,
equifinality, identifiability and experimental-design literature.

The novelty claim must remain narrow.

## 1. BAM is established forward theory

### Soberón & Peterson 2005

Soberón & Peterson formalized the geographic relationship among biotic conditions,
abiotic conditions and accessible area. The realised distribution arises from their
intersection.

Reference:
Soberón, J. & Peterson, A.T. (2005). Interpretation of Models of Fundamental
Ecological Niches and Species' Distributional Areas. Biodiversity Informatics 2.
DOI: 10.17161/bi.v2i0.4.

Therefore do not claim novelty for:

- A/B/M decomposition;
- the intersection G=A∩B∩M;
- distinguishing potential and actual distribution;
- accessible area as a separate constraint.

### Saupe et al. 2012

Saupe et al. used virtual species with known causal abiotic/dispersal configurations
to test niche/distribution model behavior.

Reference:
Saupe, E.E. et al. (2012). Variation in niche and distribution model performance:
The need for a priori assessment of key causal factors. Ecological Modelling
237–238:11–22.
DOI: 10.1016/j.ecolmodel.2012.04.001.

Therefore do not claim novelty for:

- known-truth virtual species;
- testing SDM behavior under known A/M configuration;
- using BAM-like causal configuration as a simulation test bed.

### Soberón & Osorio-Olvera 2023

Dynamic BAM theory already represents movement, niche tolerance and biotic
interactions as interacting matrices and explicitly notes that movement and niche
effects can become extremely difficult to disentangle.

Reference:
Soberón, J. & Osorio-Olvera, L. (2023). A dynamic theory of the area of
distribution. Journal of Biogeography 50.
DOI: 10.1111/jbi.14587.

Therefore do not claim novelty for:

- dynamic BAM;
- movement matrices;
- biotic-interaction matrices;
- the observation that movement and niche effects may be confounded.

### Absence under BAM

Bariotakis & Pirintsos explicitly proposed absence mapping in the BAM framework.

Reference:
Bariotakis, M. & Pirintsos, S.A. (2018). Mapping absences within the BAM concept:
Towards a new generation of ecological and environmental indicators.
Ecological Indicators 90:564–568.
DOI: 10.1016/j.ecolind.2018.03.043.

Therefore "absence adds BAM information" is not itself a contribution.

## 2. Equifinality and pattern-to-process non-identification are established general problems

Ecology and environmental modelling already recognize that multiple processes or
parameterizations can produce the same observable pattern.

Relevant adjacent literature includes:

- general ecological equifinality / model non-identifiability;
- multiple-working-hypothesis approaches in which distinct processes can generate
  indistinguishable patterns;
- simulation-method literature explicitly warning that equifinality prevents
  inference of a unique process from a pattern;
- environmental model ensembles that retain multiple behaviorally equivalent models.

A particularly close conceptual statement is the "degenerate relationship" between
process and pattern: multiple mechanisms can generate an indistinguishable response
pattern.

Therefore do not claim:

> We discovered that multiple processes can generate the same ecological pattern.

That is general prior knowledge.

The BAM manuscript must instead show what the equivalence relation is **exactly**
for the BAM inverse problem under explicit evidence contracts.

## 3. Experimental design for model discrimination is established

Optimal and adaptive experiments for distinguishing competing models have a long
history in statistics and mathematical biology.

Examples include:

- Atkinson & Cox (1974), Planning Experiments for Discriminating between Models,
  JRSS B, DOI 10.1111/j.2517-6161.1974.tb01010.x;
- systems-biology methods that choose perturbations to maximize differences among
  rival mechanisms;
- adaptive ecological experiments for discriminating functional-response models;
- modern identifiability/model-discrimination optimal-design work.

Finite experiment selection can also be formulated generically as set-cover /
pair-separation problems in other fields.

Therefore do not claim novelty for:

- optimal experiment design generally;
- model discrimination generally;
- adaptive evidence acquisition generally;
- set cover / hitting set generally.

The manuscript contribution is the BAM-specific mapping from residual inverse
ambiguity to a finite diagnostic-measurement problem after deriving the exact
survivor fiber.

## 4. The narrower gap

The forward BAM literature asks:

(A,B,M,initial state) -> G.

The present paper asks:

evidence -> {BAM worlds compatible with that evidence}.

The key contribution is not the existence of non-identifiability but an exact
description of the inverse fibers under specific ecological evidence.

### Positive-only evidence

For complete positive support G*:

S0(w*) = {w : G* subseteq G_w}.

This makes the positive-superset ceiling exact.

### Complete perfect presence/absence

S1(w*) = {w : G_w = G*}.

This distinguishes identifying the realised distribution from identifying its
decomposition.

### Progressive mechanism evidence

Arrival, A, B and M evidence create nested equality fibers.

Complete state evidence terminates at the BAM-state equivalence class, not
necessarily one parameter label.

### Restrictiveness–ambiguity ordering

For complete positive supports R1 subset R2:

C(R1) supseteq C(R2).

Thus a more restrictive realised positive support can be less informative about the
generating mechanism.

The 304/304 stochastic inclusion audit is an empirical audit of this exact
set-theoretic ordering.

### Diagnostic evidence

Once a survivor fiber is explicit, candidate A/B/M measurements correspond to sets of
nuisance worlds they eliminate. Exact diagnostic measurement is therefore a finite
hitting-set problem over the current BAM survivor fiber.

The hitting-set algorithm is not itself novel; the contribution is deriving the
ecological survivor sets to which it applies and quantifying the resulting measurement
requirements in known-truth BAM systems.

## 5. Strongest defensible novelty statement

> BAM is usually used as a forward account of how abiotic, biotic and movement
> constraints generate distributions. We formulate the complementary inverse problem:
> for explicit evidence types, we derive the exact finite fiber of BAM worlds that
> remain compatible, show when occurrence evidence cannot distinguish them, and use
> the residual fiber to specify which mechanism measurements would be diagnostic.

## 6. Strongest counterintuitive result

The most distinctive result is not generic equifinality.

It is the exact inverse ordering:

> Under complete positive-only evidence, stronger ecological restriction can increase
> process ambiguity because a smaller truth support is contained in more permissive
> candidate supports.

This result is both:

- a direct theorem from positive-support inclusion;
- observed with zero violations across 304 strict nested-support pairs in the
  independent stochastic audit.

That result should be foregrounded in the abstract, Figure 2 and Discussion.

## 7. Search boundary

Targeted searches through September 2026 surfaced substantial prior work on:

- forward BAM theory;
- dynamic BAM simulation;
- known-truth virtual species;
- generic equifinality and non-identifiability;
- BAM absence information;
- general optimal/adaptive model-discrimination experiments.

The searches did not surface a BAM paper deriving the same sequence of exact inverse
survivor fibers, the positive-support inclusion ordering above, and its finite
diagnostic-measurement formulation as one framework.

This is a search-based novelty assessment, not a proof that no such paper exists.

## 8. Writing consequences

### Introduction

Lead from:

1. BAM forward theory;
2. general pattern-process equifinality;
3. the missing BAM-specific inverse characterization.

Do not write as if non-identifiability itself is newly discovered.

### Discussion

Acknowledge that experiment design and model discrimination are broad existing fields.

Frame EOG evidence design as the consequence of making the BAM survivor fiber
explicit, not as invention of experiment design.

### Title

"Distributions are lossy intersections" remains appropriate because it states the
BAM-specific inverse problem rather than a generic identifiability claim.
