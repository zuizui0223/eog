# EOG × BAM: 768-world shared-reference geometry readout (exploratory v1)

## Scientific question

Under the **same known-truth** A/B/M model rosters already used by the
BAM-identifiability project, how does the *realized* environmental point-cloud
geometry of `G=A∩B∩M` differ from the known constraint supports `U/A/B/M/AB/AM/BM`?

This is an **additive diagnostic** integrating the original EOG operators with
BAM. It is neither a source of independent ecological evidence nor a new
generative theorem. The 12 heterogeneous synthetic systems / 64 worlds each
were already constructed and previously examined; their true mechanisms are
**known by construction**.

## Source and protocol boundary

- Original unmodified generator:
  `src/eog/v2/known_truth_bam_generality.py`, `SYSTEM_SPECS`,
  `build_generality_system`, `audit_system_activation`.
- Frozen before new geometry scoring:
  `validation/bam_geometry_768_v1/protocol_v1.json`
  (protocol commit `cd7a9222bb8512713a47e26f96d4411229736329`).
- Any original `DESIGN_STOP` invalidates the present fixed roster; no
  replacement systems and no cherry-picking valid worlds.
- Authoritative run entry point:
  `benchmarks/run_bam_geometry_768_v1.py`.
- Published programmatic source remains the original package API.
  Do not retune the initial EOG or BAM theory manuscripts on this data.

## Measurements

### Environmental point cloud — original EOG

One pooled-descriptive median/MAD reference is fit using **all candidate
nodes of each individual system**; every A/B/M/G set is transformed using
that reference. Two environmental features and their order are frozen.

The EOG 90th-percentile pairwise `span` is the primary geometry readout.
The original `MST compactness`, `gap_strength` and `MST-cut components`
are explicitly descriptive, not dispersal routes or niche-population counts.

For a world with at least two realized G nodes, its G span is compared
to a median from 16 *matched-sized* uniform without-replacement draws
within each parent/superset constraint set. Differences are
`log(span_G / median(span_superset))`. Every draw is deterministic from
the frozen seed, system ID, group bitmask and matched size. A mean distance
from each sampled point to that sample's centroid supplies a **basic
dispersion comparator**; it is not a full PERMDISP significance test.

The q05/q95 of matched draws are sensitivity summaries, **not confidence
intervals or general population uncertainty**. No G geometry is reported
for 0 or 1 nodes, and no log ratio is reported for zero spans.

### Geographic support topology — original EOG, kept distinct

The same finite landscape is re-expressed on its fixed row-major grid
only after its node IDs and Cartesian coordinates have been checked
one-to-one. The declared frozen support field equals 1 for all candidate
nodes (a **binary structural input**, not an SDM). A/B/M failures lower
that field to zero. A single positive threshold 0.5 and rook adjacency
give fixed **binary connected components**, with all G-positive nodes
declared as ideal positive anchors. There is *no* multi-threshold
persistence test in this readout; despite the older API's lineage-class
names, single-threshold classes must not be advertised as evidence of
threshold robustness.

We explicitly compare geographic G component counts to environmental
point-cloud MST-cut component counts. The latter use feature-space
distances, not geographic edges, and their equality is not guaranteed.

### Inverse-BAM information boundary

For each system we group the 64 known worlds by their exact realized
G bitmask. The readout reports the number of G-equivalence classes
containing more than one **different A/B/M decomposition**. Every world
with identical G must have identical G-only environmental geometry and
geographic G structure. Those checks confirm the logical inference
boundary; geometry computed from G cannot identify its unknown
generating decomposition when G is unchanged.

## Denominators and interpretive limits

Each 64-world group reuses the **same synthetic environment**; its
worlds are not independent ecological replicates. Report 12 systems
separately and descriptive pooled counts, without species-level
p-values, bootstrap confidence intervals, or ecological prevalence.

A different G-versus-A matched span is not the causal effect of A.
These constraint sets overlap, and the geometry metrics are nonlinear
and nonadditive. Positive/negative ratio counts are exploratory
descriptive contrasts, not directional hypothesis tests.

The fixed EOG-WF three scored endpoints, 31 scientific-protocol STOPs
and three administrative exclusions remain closed. Existing JBI BAM
inference and early EOG results are never rewritten as confirmation
by this same-source readout.

## Reproduction

```bash
python -m pytest -q tests/test_bam_geometry_768_v1.py
python benchmarks/run_bam_geometry_768_v1.py --smoke
python benchmarks/run_bam_geometry_768_v1.py --output-dir /tmp/eog_bam_geometry_768
```

The dedicated `bam-geometry-768-audit.yml` CI checks the bridge
modules and this readout, then stores `result_summary_v1.json`
and `world_rows_v1.json` as one auditable workflow artifact.
The full-output SHA/fingerprint is pinned in a separate **post-scoring
receipt**. Any bug repair after the first scoring must be made and
labelled explicitly; the prior receipt remains part of the audit trail.

## Beyond this readout

The next real ecological comparison would require independent A
environment observations, B interaction support, M mobility/barrier
information and an observation/detection model. One should only
attribute constraints after those independent channels are present,
and benchmark against PERMDISP, hypervolume and landscape connectivity
methods without treating original EOG diagnostics as causal operators.
