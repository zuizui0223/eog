# Field repeated-detection and BAM evidence gate

## Current evidence and the gap

The prior 12-landscape/768-world results are exact **synthetic**
BAM response-identification studies. They show that assumed detection
probability, prior weights and correlated site errors affect conclusions.
They do **not** estimate natural detection probability.

The one verified empirical source is the released Charaxes reduced
trap dataset, with 1544 unique trap_ID records, 167 detections and
1377 nondetections from 2018–2021. The released CSV has no
independently verified repeat-visit/effort history, coordinates or
independent A, B and M measurements. Therefore **neither its
nondetections nor its trap IDs alone establish occupancy histories**.
This gate must not relabel those records as repeated-visit data.

## Executable field-data requirements

The companion CSV gate requires one row per site × visit, with:
site_id, visit_id, survey_date, detected, effort_minutes, method_id,
observer_id, latitude, longitude, A_measure, B_measure, M_measure,
A_method, B_method, M_method.

Minimum structural requirements:
- at least two distinct geographic sites;
- at least two distinct visit IDs per site;
- all visits for a site within a 30-day *provisional* closure window;
- detection coded 0 or 1, positive finite effort, valid coordinates;
- nonmissing separate A/B/M measurement values and method identifiers;
- no duplicate site × visit key.

These are **minimum machine-checkable readiness conditions**.
Passing them is *not* evidence that visits are independent,
population closure is valid, methods are causally independent,
site detection p is estimable, or landscape sampling is
representative. The 30-day window is an operational gate, not a
species-specific closure theorem.

## Source-aware STOP versus PASS

Current Charaxes source: **STOP for field occupancy/BAM causal
validation**. It remains usable for the previously verified
capture-resource geometry association. Its 1377 nondetections
are **not** biological absences.

The synthetic 768 worlds: **PASS for deterministic method replay**,
**STOP for independent ecological validation**.

A new site-visit CSV can be checked with:

```bash
python benchmarks/field_detection_bam_gate_v1.py \
  --csv new_field_site_visits.csv --output field_gate_result.json
```

Nonzero exit code means STOP. A PASS_SCHEMA_ONLY is permission to
proceed to independent scientific checks, not a fitted occupancy
model or empirical positive result.

## Next data dependency

To estimate p and ecological occupancy rather than assuming them,
obtain independent site × visit detection histories, measured
effort, date, stable site coordinates, and separately justified
A/B/M proxies. Preserve all zero-detection sites, observation
methods, and any changes in closure or availability.
A real occupancy/BAM test must be designed and held out
independently of the previously exposed 768 model worlds.
