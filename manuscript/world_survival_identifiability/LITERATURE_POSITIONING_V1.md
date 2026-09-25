# Literature positioning — world-survival identifiability

## Purpose

This note fixes what the manuscript may and may not claim as its contribution.

The paper must not present established ingredients as novel. Its contribution is the
specific separation, prospective test, and boundary result assembled inside EOG.

## 1. Accessibility and dispersal are established SDM concerns

Species-distribution modelling has long distinguished environmental suitability from
geographic accessibility and dispersal. Reviews and applied studies explicitly note that
species need not occupy all environmentally suitable regions and that dispersal,
barriers, accessible areas and movement assumptions can materially alter projected
ranges.

Relevant anchors include:

- Elith & Leathwick (2009), Species Distribution Models: Ecological Explanation and
  Prediction Across Space and Time, Annual Review of Ecology, Evolution, and Systematics.
- Barve and related accessible-area work in ecological niche modelling.
- Later habitat-suitability/accessibility reviews and dispersal-constrained SDM studies.

Therefore the manuscript must not claim novelty for:
- adding accessibility to suitability;
- using distance or dispersal constraints;
- comparing limited- and unlimited-dispersal scenarios;
- representing several dispersal assumptions.

## 2. Ruling out models with observations is established

History matching and related ensemble-calibration methods define a candidate input or
model space and use observations to rule out implausible regions while retaining a
not-ruled-out-yet set. Empty retained sets are interpretable as incompatibility between
the declared model family and observations under the stated tolerances.

Relevant anchors include:

- Williamson et al. (2013), history matching of climate-model parameter space,
  Climate Dynamics, DOI 10.1007/s00382-013-1896-4.
- Subsequent history-matching applications in environmental and land-surface models.

Therefore the manuscript must not claim novelty for:
- defining a finite candidate set;
- eliminating incompatible candidates;
- retaining an unresolved set rather than one winner;
- interpreting an empty retained set as failure of the declared universe.

EOG differs in object and contract, not in the generic logic of ruling out alternatives.

## 3. Multiple working hypotheses and pre-data identifiability are established in ecology

Ecological methodology already advocates formalizing multiple candidate hypotheses before
data collection and asking whether their predicted observation patterns are sufficiently
distinct to support inference. Yanco et al. (2020) explicitly frame pre-data modelling
as a way to diagnose degeneracy and identifiability among ecological hypotheses.

Therefore the manuscript must not claim novelty for:
- considering multiple working hypotheses;
- asking before data collection whether hypotheses are distinguishable;
- using simulation or formal reasoning to identify degeneracy;
- treating non-identifiability as an inferential problem.

## 4. Observation design for model discrimination is established

Optimal experimental-design and observation-network literatures ask where or how to
measure in order to discriminate competing models. Model-discrimination design is
therefore established outside ecology and appears in environmental modelling.

Relevant anchors include:
- Box-Hill style model-discrimination design;
- Pham & Tsai (2016), Water Resources Research, DOI 10.1002/2015WR017474;
- broader optimal experimental design for model discrimination.

This matters because the present EOG result naturally points toward N4-style observation
placement. That handoff is conceptually compatible with existing optimal-design theory
and must not be presented as a new general idea.

## 5. The graph witness is a proof device, not a graph-theory novelty claim

Under the declared one-step positive rule, survival depends on the induced positive
subgraph. The adjacent-pair/non-adjacent-pair witness is mathematically elementary.

The manuscript should not claim a novel graph theorem.

Its role is to prove an inferential statement about the EOG contract:

> If response-blind structure is fixed but positive-node placement is not, later
> world survival is not universally determined by global graph structure alone.

The ecological/methodological contribution is the boundary this establishes for the EOG
workflow, not the combinatorial fact itself.

## 6. Candidate contribution that remains defensible

The strongest contribution is the combination of four elements:

1. A strict distinction between response-blind structural adequacy of a declared finite
   biogeographic world universe and response-conditioned survival of those worlds.
2. A prospectively frozen empirical attempt to predict the later survival regime before
   response access, with pre-response method failures retained rather than repaired.
3. A once-only multi-site ecological validation in which the structure-only rule failed
   and systematically underpredicted world survival, while genuine intermediate
   contractions nevertheless occurred.
4. A formal witness showing why a universal graph-only survival predictor cannot exist
   under the stated positive-evidence rule without additional assumptions about positive
   placement.

A safe contribution sentence is:

> We show that structural testability of a finite biogeographic world set can be audited
> before biological response access, but that later evidence-driven contraction is a
> response-conditioned quantity that is not generally identifiable from global graph
> structure alone.

## 7. Relation to history matching

The closest conceptual analogy is history matching:

- declare alternatives;
- confront them with observations;
- eliminate incompatible alternatives;
- retain an unresolved set.

The manuscript should acknowledge that analogy directly.

The EOG-specific difference is that candidate worlds are explicit accessibility
operators over ecological nodes, positive occurrences act as reachability constraints,
and the paper asks whether the future contraction state of that world set is itself
predictable from response-blind topology.

The answer from the present programme is negative.

## 8. Relation to multiple-working-hypothesis ecology

The result is consistent with the pre-data identifiability logic emphasized in multiple
working hypothesis frameworks. The new EOG programme operationalizes that logic for
finite accessibility worlds and reveals a further distinction:

- hypotheses may be structurally admissible and testable;
- yet the amount of evidence-driven elimination cannot be known before the response
  pattern is placed.

This is the conceptual bridge between the empirical NEON failure and the identifiability
witness.

## 9. Claims to avoid in title, abstract and cover letter

Avoid:
- first framework to incorporate dispersal or accessibility;
- first ecological model-set falsification method;
- first use of multiple working hypotheses before data collection;
- novel graph-theoretic identifiability theorem;
- universal impossibility of predicting contraction;
- no response-blind predictor can ever work.

The last two are too broad. A response-location distribution or other probabilistic model
can support probabilistic forecasts. The supported boundary is narrower: global
response-blind graph structure alone does not universally determine later survival under
the declared observation rule.

## 10. References to verify in the final bibliography

- Elith J, Leathwick JR. 2009. Species Distribution Models: Ecological Explanation and
  Prediction Across Space and Time. Annual Review of Ecology, Evolution, and Systematics.
  DOI 10.1146/annurev.ecolsys.110308.120159.
- Barve N et al. 2011. The crucial role of the accessible area in ecological niche
  modeling and species distribution modeling. Ecological Modelling 222:1810-1819.
  DOI 10.1016/j.ecolmodel.2011.02.011.
- Williamson D, Goldstein M, Allison L, et al. 2013. History matching for exploring and
  reducing climate model parameter space using observations and a large perturbed
  physics ensemble. Climate Dynamics. DOI 10.1007/s00382-013-1896-4.
- Yanco SW, McDevitt A, Trueman CN, Hartley L, Wunder MB. 2020. A modern method of
  multiple working hypotheses to improve inference in ecology. Royal Society Open Science
  7:200231. DOI 10.1098/rsos.200231.
- Pham HV, Tsai FTC. 2016. Optimal observation network design for conceptual model
  discrimination and uncertainty reduction. Water Resources Research 52:1245-1264.
  DOI 10.1002/2015WR017474.

Final reference metadata should be verified before submission.
