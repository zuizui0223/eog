# Literature positioning v1 — BAM target identifiability and universe robustness

## Purpose

This note prevents the successor BAM manuscript from claiming novelty for ideas that are
already established in decision science, partial identification, systems biology or
ecological adaptive management.

It does not establish a priority claim.  It fixes the **claim boundary** that the
manuscript must respect.

## 1. BAM and functional habitat are prior art

The BAM framework itself is established:

- Soberón & Peterson (2005) and subsequent BAM literature;
- Barve et al. (2011), accessible area M in ecological niche modelling;
- Van Moorter et al. (2023), functional habitat as the integration of environmental and
  geographic space.

Therefore this manuscript does not claim novelty for

[
G=A\cap B\cap M,
]

for suitable-versus-accessible habitat, or for combining biotic, abiotic and movement
constraints.

Relevant sources:

- Barve et al. 2011, Ecological Modelling,
  https://doi.org/10.1016/j.ecolmodel.2011.02.011
- Van Moorter et al. 2023, Ecology,
  https://doi.org/10.1002/ecy.4105

## 2. Decision robustness under model uncertainty is prior art

Adaptive management has long represented structural uncertainty through alternative
models and asked whether uncertainty actually changes the management action.

Williams, Eaton & Breininger (2011) formalized Value of Information for adaptive
resource management under structural uncertainty.

- DOI: https://doi.org/10.1016/j.ecolmodel.2011.07.003

Adaptive-management applications explicitly note that when competing models agree on
the best action, resolving the model uncertainty may have little decision value.

A related intervention-focused exposition is:

- Metcalf et al. 2014, PLOS Biology,
  https://doi.org/10.1371/journal.pbio.1001970

Therefore the successor BAM paper must not claim as a general discovery that:

> mechanism uncertainty can exist without decision uncertainty.

That principle is already established.

## 3. Partial identification of counterfactuals is prior art

Partial-identification theory already distinguishes an incompletely identified
structural model from counterfactual quantities that may have narrower identified
sets.

Examples include:

- Manski 2007, partial identification of counterfactual choice probabilities,
  https://doi.org/10.1111/j.1468-2354.2007.00467.x
- Kalouptsidi, Kitamura, Lima & Souza-Rodrigues 2020/2022, *Partial Identification and
  Inference for Dynamic Models and Counterfactuals*, NBER Working Paper 26761,
  https://doi.org/10.3386/w26761

The latter explicitly derives identified sets for model parameters and counterfactual
outcomes of interest.

Therefore the BAM paper must not claim novelty for:

- target-specific partial identification in general;
- identified sets for counterfactuals in general;
- the proposition that a low-dimensional target can be identified more tightly than
  the full structural model.

## 4. Model-set expansion and structural uncertainty are prior art

Ecological decision frameworks already consider multiple ecological models and
robustness to structural uncertainty.

Examples:

- Williams et al. 2011, adaptive resource management and Value of Information;
- Fulton et al. / related multiple-model ecological decision frameworks summarized in
  Frontiers in Marine Science 2021, *Using Multiple Ecological Models to Inform
  Environmental Decision-Making*;
- Rozowski & Fackler 2025, *Adaptive management under structural uncertainty: A linear
  opinion pool approach to expanding the model set*, Methods in Ecology and Evolution,
  https://doi.org/10.1111/2041-210X.70137

The 2025 paper is especially important because it explicitly expands the effective model
space rather than assuming that one member of the original candidate set must be true.

Therefore the BAM successor must not claim generic novelty for:

- expanding a model set;
- robustness to omitted models;
- structural uncertainty;
- consensus across alternative models.

## 5. Prediction under non-identifiability is prior art

Outside ecology, systems-biology and mathematical-biology work has shown that
parameter non-identifiability does not automatically imply useless prediction and has
developed experimental-design methods aimed at prediction uncertainty.

Examples include work on:

- predictive power of non-identifiable models;
- prediction-profile / profile-likelihood uncertainty;
- selecting experimental readouts and intervention sites to reduce prediction
  uncertainty.

One accessible example is:

- Maiwald et al. 2015, *Rational selection of experimental readout and intervention
  sites for reducing uncertainties in computational model predictions*,
  Bioinformatics / PMC4310145.

Therefore the BAM successor must not present “prediction despite non-identifiable
parameters” as its general novelty.

## 6. What remains specific to the BAM programme

The candidate contribution must be stated narrowly.

The BAM programme begins with an **occurrence-conditioned inverse fiber** inside a
declared finite biogeographic world universe:

[
S(G)
=
\{w:G_w=G_{obs}\}
]

or the corresponding positive-evidence fiber.

For every surviving world it keeps A, B and M mechanistically explicit rather than
collapsing them into one fitted suitability score.

It then asks, for the **same current observed distribution**:

1. which BAM parameter worlds remain compatible?;
2. which current BAM states remain compatible?;
3. which exact future distributions remain possible under a declared ecological
   transformation?;
4. which decision classes remain possible?;
5. how much direct evidence is required for the declared target rather than for full
   mechanism recovery?;
6. whether the target certificate survives a prospectively declared expansion of the
   BAM world family?;
7. how far the declared family is from a same-G counterexample under either a logical
   completion metric or an ecological parameter-neighbourhood metric?

The specific finite-world structure is:

[
\text{occurrence evidence}
\rightarrow
\text{same-G BAM survivor fiber}
\rightarrow
\text{target equivalence}
\rightarrow
\text{target-specific evidence burden}
\rightarrow
\text{nested world-universe robustness}
\rightarrow
\text{structured counterfactual response}.
]

## 7. The most defensible novelty target

The strongest manuscript claim should be approximately:

> **We formulate the inverse BAM problem as an occurrence-conditioned finite survivor
> fiber and show how current mechanism identity, counterfactual distribution identity
> and decision identity can be separated exactly; we then audit those target
> certificates across nested, prospectively declared BAM world universes and structured
> ecological transformations.**

A still narrower version is:

> **The contribution is not that uncertain models can agree on decisions.  It is an
> exact BAM-specific accounting of which occurrence-compatible A/B/M explanations
> agree, which future ecological targets they agree on, what evidence separates only
> the target-relevant disagreements, and when that agreement fails as the admissible
> biogeographic world family expands.**

## 8. Priority claim boundary

Do not write:

- “the first framework to make decisions under model uncertainty”;
- “the first counterfactual partial-identification method”;
- “the first method showing predictions can be robust despite non-identifiability”;
- “the first method to expand model sets”;
- “the first method to combine A, B and M.”

A defensible wording is:

> **We are not aware of a prior BAM-focused framework that uses occurrence-conditioned
> exact survivor fibers to distinguish current-state, structured-counterfactual and
> decision equivalence while auditing those equivalence classes across nested declared
> BAM world universes.**

Even this sentence should remain a qualified literature-positioning statement rather
than an absolute priority claim unless a dedicated systematic review confirms it.
