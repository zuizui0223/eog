# A-Islands pre-outcome model contract

This document freezes the upstream pointwise support producer and the evaluation partition before any A-Islands SDM or EOG held-out result is inspected.

## The scientific distinction

The benchmark is not a contest in which EOG is trained to beat a weak SDM. The support model and EOG answer different questions and are frozen separately.

- **Pointwise support:** a fitted location-indexed quantity produced from island presence/absence and climate.
- **EOG reachability:** a later, separately frozen structural quantity relating unlabelled target islands to training-presence anchors under explicit graph assumptions.
- **Spatial holdout blocks:** evaluation partitions only. They are not dispersal barriers and do not model colonisation.
- **ACSP:** remains downstream if a finite survey set is needed.

The primary A-Islands empirical question will therefore be conditional: after accounting for the frozen pointwise support score, and separately for simple distance to the nearest training presence, does a predeclared reachability quantity contain additional held-out incidence information? A positive result would support added structural information, not universal superiority to species distribution models.

## Frozen model units

A-Islands version 1.0 provides 842 surveyed islands linked to at least one species-list row. All 842 have valid WGS84 centroid coordinates in the frozen shapefile. The shapefile contains 887 records in total and the DBF fields are exactly `island_ID`, `x_centroid`, and `y_centroid`.

The exact downloadable version-1.0 CSV/DBF files audited here do **not** contain the paper-described area or archipelago-level fields. Those attributes are therefore absent from the primary model contract rather than reconstructed from another source after outcomes are seen.

## Frozen evaluation partition

Centroids are assigned to a 5-degree longitude/latitude grid from a global origin. The 29 occupied blocks are assigned intact to five folds by a deterministic load-balancing rule. Fold sizes are 169, 169, 168, 168 and 168 islands.

The frozen assignment file has SHA-256:

`221a925e289347069c89354d26acfab83fa3d4bc130b56f0178b8db30ab427fa`

The same fold assignment is used for all species. Species labels played no role in making it.

## Frozen pointwise support producer

The primary support model is a deterministic L2-penalized logistic regression with no hyperparameter tuning. The five frozen climate predictors are CHELSA-bioclim version 2.1 variables for 1981–2010:

- `bio01`: mean annual temperature;
- `bio05`: maximum temperature of the warmest month;
- `bio06`: minimum temperature of the coldest month;
- `bio12`: annual precipitation;
- `bio15`: precipitation seasonality.

Each predictor is sampled at the frozen island centroid. Predictors are z-standardized using training islands only within each fold. The L2 penalty is fixed at 1.0 and the intercept is not penalized. The implementation is deterministic and uses no model-family selection, cross-validated hyperparameter search, predictor screening or importance-based feature removal.

A species-fold model is explicitly not evaluable if the training fold has fewer than five presences or five absences, contains a non-finite training predictor, or has a constant predictor. Failures are retained and reported rather than triggering a fallback model or a changed holdout.

The fitted value is interpreted as relative pointwise occurrence support for comparison and conditioning. It is not assumed to be a calibrated occupancy probability.

## Leakage boundary

Held-out species labels may not affect climate extraction, standardization, model fitting, predictor choice, graph construction, graph hyperparameters, EOG anchors or scenario choice. In the later reachability stage, only training-presence islands may serve as occurrence anchors. Held-out islands may be present as unlabelled nodes because their frozen geography and climate are known independently of the held-out incidence label.

## What is still intentionally unfrozen

The reachability graph is **not** defined in this contract. Geographic radii, k-nearest-neighbour rules, environmental-jump restrictions and scenario aggregation belong to the next independent freeze. Keeping them separate prevents joint tuning of the support model and the graph against the same held-out outcomes.

Likewise, this contract does not choose the final inferential statistic or a favorable complete-case denominator for EOG. The next contract must predeclare the support-only and distance baselines, reachability scenario family, failure handling and paired held-out comparison before results are inspected.
