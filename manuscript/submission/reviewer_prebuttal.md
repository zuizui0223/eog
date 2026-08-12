# Reviewer prebuttal: structural-reachability manuscript

This document is an internal submission aid, not manuscript text.

## “Suitability and connectivity have already been integrated.”

Agreed. The revision will cite Berlow 2013, Ortiz-Rodríguez 2019, Van Moorter 2023, Riva 2024, Kim 2024 and Felin 2025 explicitly. The paper's claim is not priority for integration. It tests whether a structural term earns an **incremental held-out claim conditional on a declared reference**, with occurrence-conditioned features constructed without held-out labels.

## “Occupied-neighbour or nearest-occupied-patch information is not new.”

Agreed. Berlow 2013 explicitly discusses distance to the nearest occupied patch and density of occupied patches. EOG's distinction is the leakage boundary: occurrence anchors for a held-out prediction are outer-training presences only, and the structural term is evaluated after nearest-training-source distance is controlled separately.

## “Sensitivity to dispersal thresholds is not new.”

Agreed. Ortiz-Rodríguez 2023 directly tested habitat-network occurrence models across dispersal distances; Prima 2024 and Cushman 2026 address uncertainty/model-choice variation in connectivity analyses. EOG's connected frequency is not claimed as the first sensitivity analysis. It is a predeclared ensemble-defined estimand whose incremental incidence information is tested rather than choosing a favourable threshold after observing held-out outcomes.

## “A-Islands only proves value relative to a weak reference.”

The reference is intentionally limited to frozen climatic support and nearest-source distance, so the supported claim is limited accordingly. The paper does not claim superiority over current flow or other landscape-specific connectivity models. The Tanzania benchmark supplies that stronger falsification test and is adverse.

## “Why keep a method that worsens prediction in Tanzania?”

Because the paper is about when a generic structural term earns an incremental claim. A method framework that only reports favourable datasets cannot define its scope. Tanzania shows that EOG is not automatically beneficial once a strong matrix-aware connectivity predictor is already present.

## “The two systems are not directly comparable.”

Correct. Their metrics and reference hierarchies differ and the manuscript explicitly prohibits cross-metric magnitude comparisons. The cross-system inference is logical rather than meta-analytic: incremental structural value is reference- and representation-dependent.

## “Connected frequency has no direct biological calibration.”

Correct. It is defined as robustness of target-to-training-anchor connection across a frozen scenario ensemble. It is never called dispersal, colonisation or movement probability. Direct process inference would require temporal occupancy, telemetry, genetics or other movement/process data.

## “Why no new trait-informed or directional tuning after Tanzania?”

Because those choices would be motivated after seeing the adverse result. They are listed only as prospective variants. The frozen Tanzania result remains visible under any future development.

## “Why should this be in Ecological Informatics?”

The manuscript is a computational ecology/data-science paper about estimand separation, leakage-safe feature construction, reference-conditioned held-out testing, uncertainty/applicability accounting, and source-to-manuscript reproducibility. The biological benchmarks are used to establish an applicability boundary for the computational framework rather than to propose a new movement mechanism.