# Positive-only field recovery protocol

This protocol applies when field discoveries are available but standardized non-detection, effort, and visited-area records are not.

## Inputs

`recommended_zones.csv` must contain `zone_id`, `island`, `latitude`, `longitude`, and `frozen_rank`. Optional `zone_radius_km` is interpreted as a documented claim radius, not an exact occupied boundary.

`field_discoveries.csv` must contain `discovery_id`, `island`, `latitude`, and `longitude`. Survey date may be retained as an additional audit field.

The recommendation table must have been frozen before the discovery outcomes were inspected. Neither table may contain duplicated IDs or invalid coordinates.

## Primary analysis

Discovery GPS records are clustered independently within each island using deterministic complete-link clustering at 0.5 km. This prevents many nearby observations of one population from being counted as independent successes. Clustering at 1 km and 2 km is reported as sensitivity analysis.

For each discovery cluster, distance to a zone equals the haversine distance to its representative point minus the documented zone radius, truncated at zero. The evaluator reports minimum distance to the selected zone set, recovery within 0.5, 1, 2, 5, and 10 km, and top-k recovery curves.

## Random comparison

Random selections preserve the exact number of recommended zones on each island. They are sampled without replacement from the archived eligible candidate-zone pool. This comparison is invalid if only the selected zones, rather than the full eligible pool, are supplied.

## Claims supported

- proximity of frozen recommendations to observed field discoveries;
- recovery of discovery clusters at predeclared distance thresholds;
- improvement over island-stratified random selections from the same candidate pool.

## Claims not supported

- occupancy or absence;
- detection probability;
- discoveries per unit effort;
- superiority at unsurveyed locations;
- adaptive learning from field outcomes.

Those claims require visited non-detection records, standardized effort, accessible-area documentation, and pre-survey candidate archives.
