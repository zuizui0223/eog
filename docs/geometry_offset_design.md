# Geometry-derived offset comparison: fixed development design

This extends the offset experiment without altering its earlier results. It is a
new synthetic development check, not ecological confirmation. Freeze this design
before scoring; do not tune after seeing results.

- Seeds: 801, 809, 811, 821. Each has 120 independent eight-node graphs.
- Two sources (indices 0,1) and six target nodes per graph. All coordinates are
  uniform in the unit square. The reference is the initial geometry; current
  geometry adds independent Gaussian displacement, SD 0.12, with no clipping.
- EOG worlds have radius thresholds 0.45 and 0.65. Directed edges in both
  directions use exp(-Euclidean distance/0.4), loss support 0.3. Compute existing
  first-passage support from each source to each target, depth four, separately
  for reference and current. Existing source-symmetric summary and innovation
  modules then yield the ten prediction features. No new operator is introduced.
- Independent synthetic response mechanism uses shortest distances in a separate
  radius-0.55 undirected graph, computed with SciPy shortest_path, nearest of the
  two sources, capped at four (including unreachable). Route signal is
  2*tanh(2*(reference_distance-current_distance)). It is not an EOG support output.
- Conventional inputs: current target x/y, reference target x/y, current and
  reference nearest-source straight-line distance. Baseline logit is
  0.8*(current_x-0.5)-0.4*(current_y-0.5).
- Regimes: route signal, environment only, route signal reversed only on outer
  graphs. Common random uniforms across regimes. All regimes are retained.
- Graphs 0:60 fit, 60:90 calibration, 90:120 outer. OOF folds use graph index
  modulo three, never target-row random splits. Identical response budget.
- Same RF settings as the original comparison (64 trees, leaf 10, sqrt, seed91),
  ridge0.1, and scoring clip. No search and no post-selection refit.
- Compare RF+absolute EOG, RF+innovation, offset with ten EOG innovations,
  offset with only mean/std innovations, offset with shortest-distance change,
  and offset with permuted innovations independently within each split.
- Report always-on and calibration-selected paired log loss, per seed and regime,
  using the baseline on selection ties. Selection sees no outer outcomes.

The distance comparator is intentionally aligned with the known response process:
it is a transparent simple comparator, not hidden ground truth available only to
EOG. If it suffices or dominates, report that and do not claim that the ten-feature
representation is necessary. Four seeds are not enough for a methods superiority
claim. There is no biological data, occupancy calibration, source inference,
topology parameter estimation, or empirical input admission in this experiment.
