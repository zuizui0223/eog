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


## Scored descriptive result (post-protocol; source worlds previously exposed)

The first scoring run **succeeded** for all 12 unchanged synthetic landscapes
and their 768 parameter worlds. Code head: `9e29bdcaabe3fa5d44072505151f187205af8bf4`;
[Actions run 40839251793](https://github.com/zuizui0223/eog/actions/runs/40839251793);
full result fingerprint `8c60d83820ae9693fa528791071d371748b032df65ca9cd62eb91d3103596d0c`.
The complete JSONs and hashes are pinned in
`validation/bam_geometry_768_v1/result_receipt_v1.json` and the
named Actions artifact (ID 12882430690).

| Descriptive quantity | Result |
| --- | ---: |
| Original synthetic systems / parameter worlds | **12 / 768** |
| G point clouds estimable (at least 2 nodes) | **768 / 768** |
| Distinct G sets (summed within system) | **129** |
| G families with more than one distinct A/B/M decomposition | **69 / 129** |
| Parameter worlds in those aliased G families | **632 / 768** |
| Same-G geometry invariance checks / violations | **639 / 0** |
| G versus U matched span smaller / larger / unchanged | **719 / 15 / 34** |
| G versus A matched span smaller / larger / unchanged | **666 / 17 / 85** |
| Geographic versus environmental MST-cut component-count disagreement | **241 / 768** |
| Geographically one component, environmentally 2+ MST-cut components | **205 / 768** |
| Geographically two components, environmentally one MST-cut component | **36 / 768** |

Median log(G/U) matched span ratio across 768 parameter rows is
`−0.282617`; median log(G/A) is `−0.217035`. These are **descriptive
within-generator summaries**, not ecological effect-size estimates.
All 12 within-landscape medians of log(G/U) were negative, but the 64
parameter worlds in a landscape are not independent samples.

**Interpretation:**

- Imposing a constructed set of A/B/M constraints often contracts the
  realized environmental span relative to equally sized draws from the
  unchanged environment. A minority of matched contrasts have the
  opposite direction; geometric summary changes are not a deterministic
  monotone function of set inclusion after sample-size matching.
- The same G can arise from multiple known A/B/M decompositions.
  A G-only geometric summary *cannot* resolve this ambiguity, so the
  result preserves rather than reverses the published inverse-BAM limit.
- Environmental MST cut components and geographic rook components measure
  different objects. Their disagreement in the defined synthetic worlds
  is a **diagnostic distinction under the fixed thresholds**, not a
  general field claim about fragmentation or mobility.
- Three axes are known by construction, and the reference contains the
  candidate environments. The result is *not* independent ecological
  identification of which factor produces a real species range.

These scored results do not create a new manuscript or affect the closed
EOG-WF predictive denominator. Any applied validation must acquire
independent abiotic, biotic, movement and observation-process information.
