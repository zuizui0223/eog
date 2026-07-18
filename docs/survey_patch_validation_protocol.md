# Survey-patch outcome validation protocol

## Goal

Evaluate whether a frozen pre-survey patch ranking increases observed detection yield under a limited survey budget. The evaluation unit is a surveyable geographic patch, not an isolated raster cell.

## Required separation

`candidate_patches.csv` must be frozen before `survey_outcomes.csv` is joined. Candidate data may contain spatial, environmental, accessibility, and ranking variables, but must not contain outcome-like columns such as `detected`, `surveyed`, `presence`, or `absence`.

Unsampled patches are not negatives. The primary retrospective comparison is restricted to accessible patches with recorded survey outcomes. This restriction must be stated because it does not remove all selection bias in where surveys were conducted.

## Required candidate columns

- `patch_id`
- `priority_score`: frozen ACSP/EOG survey priority; higher is better
- `nearest_occurrence_distance`: geographic distance to the nearest occurrence known before the survey; lower is better
- `environmental_similarity`: pre-survey similarity to known occupied environmental states; higher is better
- `travel_cost`: common positive cost proxy
- `accessible`: whether the patch belonged to the feasible survey set

Additional columns such as centroid, area, island, region, or score components may be retained for auditing.

## Required outcome columns

- `patch_id`
- `surveyed`
- `detected`
- `effort`

Recommended additions are survey date, number of detections, observer, detection method, and weather. Non-detections should never be interpreted without effort metadata.

## Frozen comparisons

The same eligible patch set is ranked by:

1. final frozen priority score;
2. nearest-known-occurrence distance;
3. environmental similarity alone;
4. repeated random accessible ordering.

No outcome-derived ensemble or threshold may be tuned.

## Primary summaries

- detections and detection yield among top-k patches;
- recall of observed detections among top-k patches;
- detections and recall after spending 50% of total observed travel cost;
- random-order median and 90th percentile references.

The first implementation uses `k = min(10, n eligible)` unless a different value was declared before outcomes were inspected.

## Decision rule

The frozen priority ranking passes the initial outcome gate only when its top-k detection yield is greater than both:

- the median random-accessible yield;
- the nearest-known-occurrence baseline yield.

This gate is deliberately simple. A pass does not establish species-distribution accuracy or biological absence. A fail must be retained and should trigger examination of patch construction, accessibility modelling, or ranking objectives rather than post-hoc score tuning.

## Extension after the first dataset

When multiple islands or regions are available, evaluate transfer with leave-one-region-out ranking rules. When repeated visits are available, add detection-process modelling without changing the descriptive geometry definitions.
