# Structural-reachability manuscript figure specification

## General rule

Every quantitative panel must be generated from a frozen machine-readable artifact by a committed script. No effect estimate, interval, sample size, failure count, or fingerprint may be typed directly into plotting code.

A figure build should fail when:

- an expected input fingerprint differs;
- the declared number of taxa, sites, folds, or contrasts differs;
- a plot excludes non-estimable groups without an explicit display or count;
- an effect direction is inconsistent with the frozen metric definition;
- a figure label calls connected frequency a probability of movement or colonisation.

Recommended directory layout:

```text
figures/
  build_figure_1_roles.py
  build_figure_2_aislands.py
  build_figure_3_tanzania.py
  build_figure_4_boundary.py
  build_figure_s1_audit.py
  figure_manifest.json
  source_tables/
  output/
```

The final scripts should write both the figure and the exact plotted table.

## Figure 1 — Different meanings of “spatial”

### Scientific purpose

Prevent readers from treating spatial cross-validation, spatial dependence, direct occurrence distance, matrix-aware connectivity, and EOG configuration as interchangeable.

### Panels

**A. Pointwise environmental support**

- show two candidate patches with equal local support;
- no statement about connection to known occurrences;
- label: “Where are local conditions supportive?”

**B. Spatial block cross-validation**

- training and held-out blocks separated geographically;
- label: “Does the model extrapolate to separated locations?”

**C. Direct source distance**

- two targets at equal nearest-anchor distance;
- one has intermediate stepping-stone nodes and one does not;
- label: “How far is the nearest training occurrence?”

**D. Matrix-aware current flow**

- multiple routes through cells with different resistance;
- label: “How conductive is the intervening matrix?”

**E. Occurrence-anchored EOG**

- scenario ensemble and connected frequency;
- label: “How robustly is the target embedded in an anchored patch configuration?”

### Input

Conceptual only. The panel semantics must match `docs/structural_competitor_matrix.md`. No empirical result is shown.

### Prohibited visual implication

Do not use animal/seed movement arrows that imply an observed route. Use graph edges, candidate routes, or structural links.

## Figure 2 — A-Islands confirmatory structural benchmark

### Scientific purpose

Show that island-chain structure retained incidence information after pointwise climatic support and nearest-training-occurrence distance were controlled.

### Panels

**A. Frozen design**

- 842 islands;
- five spatial folds;
- 886 declared taxa;
- five CHELSA predictors;
- 12 predeclared graph scenarios.

**B. Conditional comparison**

- diagram of 5 × 5 pointwise-support × nearest-distance strata;
- occupied and unoccupied held-out islands compared only within the same stratum;
- score direction defined before plotting.

**C. Species-level primary distribution**

- one point per estimable species;
- x-axis: conditional concordance;
- vertical reference at 0.5;
- show n above, equal to, and below 0.5;
- display all 845 estimable species or a density plus complete rug.

**D. Frozen structural quantities**

Forest plot with:

- combined connected frequency;
- geography-only connected frequency;
- environmentally constrained connected frequency;
- normalized geographic bottleneck secondary.

The first three use the same 0.5 null. The bottleneck direction must be labelled as smaller bottleneck being favourable and plotted using its frozen concordance score, not the raw bottleneck.

**E. Applicability**

- declared taxa;
- taxa with a primary species statistic;
- fold failure categories;
- comparable-pair absence must remain visible.

### Authoritative inputs

- `docs/aislands_authoritative_contracts.md`;
- `benchmarks/run_aislands_authoritative_benchmark.py` outputs;
- `benchmarks/run_aislands_predeclared_secondary.py` outputs;
- frozen bottleneck-secondary outputs from PR #92;
- input SHA values enforced by the authoritative runner.

### Required extraction step

The figure script must either rerun the authoritative workflow or consume an archived artifact whose hashes match the runner output. A manually transcribed PR description is not an acceptable plotting source.

## Figure 3 — Tanzania strong-competitor external benchmark

### Scientific purpose

Show the strict incremental comparison and the adverse LOSO result without obscuring the weaker spatial-block sensitivity.

### Panels

**A. Leakage-safe workflow**

For each species and outer fold:

1. use outer-training responses only;
2. select one of 512 current-flow candidates by the frozen source AIC rule;
3. construct nearest-anchor and EOG features from training occurrences only;
4. reuse the selected current-flow candidate in both probability tiers;
5. score the untouched held-out label.

**B. Reference versus candidate**

Reference:

`area + selected current flow + area × current flow + nearest occurrence`

Candidate:

`reference + EOG connected frequency`

Define candidate-minus-reference loss before displaying results. Positive values are worse.

**C. Species-level LOSO effects**

- one point per species with an estimable matched effect;
- x-axis: mean candidate-minus-reference log-loss difference;
- vertical reference at zero;
- retain species with few matched folds and expose their matched counts in the source table;
- optionally order by effect, but do not label selected favourable/adverse examples in the main panel unless the rule is frozen.

**D. Aggregate contrasts**

Forest plot with:

- primary weighting × LOSO;
- inverse-area weighting × LOSO;
- primary weighting × spatial MST blocks;
- inverse-area weighting × spatial MST blocks.

Plot the frozen species-macro effect and bootstrap interval. Use a zero reference line.

**E. Applicability and failures**

- 3,360 declared held-out prediction rows;
- 826 matched primary LOSO rows per weighting mode;
- 718 matched spatial-block rows per weighting mode;
- single-class and current-flow-selection failures shown explicitly.

### Authoritative inputs

- `benchmarks/tanzania_heldout_expected.json`;
- archived `predictions.jsonl`, `groups.jsonl`, and `species.jsonl` from the verified held-out workflow;
- `docs/tanzania_heldout_result.md` only for prose verification, not numeric plotting.

### Fingerprint gate

Before plotting, verify:

- result fingerprint: `6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4`;
- candidate-library fingerprint: `3cabff50f138f7ccfe77cdbe87aefe14d5ec4dd40db15f16fb7b072cd3d01026`;
- prediction/group/species cross-run hashes in `benchmarks/tanzania_heldout_expected.json`.

## Figure 4 — Cross-system evidence boundary

### Scientific purpose

Make the main conclusion understandable without comparing incompatible effect metrics directly.

### Recommended matrix

Rows:

- A-Islands plants;
- Tanzania forest birds.

Columns:

- local support in reference;
- nearest-source distance in reference;
- matrix-aware connectivity in reference;
- EOG structural addition;
- holdout design;
- endpoint;
- result direction;
- permitted conclusion.

### Visual encoding

- use symbols for whether a reference already contains a quantity;
- use text and interval marks for result direction;
- do **not** place concordance 0.618 and log-loss +0.032 on one common numerical axis;
- use “added information” and “no incremental benefit / adverse LOSO result”, not “win” and “loss”.

### Authoritative input

Generate from a machine-readable table derived from:

- `docs/structural_validation_synthesis.md`;
- A-Islands archived summaries;
- `benchmarks/tanzania_heldout_expected.json`.

The plotted table should become a supplementary data file.

## Supplementary Figure S1 — Audit and timing map

### Scientific purpose

Demonstrate that protocol corrections were separated from biological outcome inspection.

### Required timeline categories

- source identity freeze;
- cohort freeze;
- fold freeze;
- support/reference-model freeze;
- graph-scenario freeze;
- pre-outcome correction;
- first outcome execution;
- result fingerprint freeze;
- independent reproduction;
- post-result numerical fingerprint-policy correction that left raw values unchanged.

### Visual rule

Use different shapes for scientific-design changes and numerical/reproducibility changes. A post-result numerical change must not be drawn as if it preceded the result.

## Tables accompanying figures

Each figure build must produce:

- `figure_N_panel_data.csv` or `.json`;
- a metadata JSON containing source paths, input SHA values, script commit, package versions, and build timestamp;
- a caption draft defining every metric direction and uncertainty interval;
- an accessibility description for screen readers.

## Style rules

- Use one consistent font family and panel-label convention.
- Avoid red–green-only contrasts.
- Ensure point clouds remain legible when printed at journal column width.
- Intervals should be more visually prominent than p-values.
- Always display the null/reference line.
- Use identical wording for the same quantity across figures and text.
- Do not use “probability”, “colonisation”, “dispersal route”, or “connectivity truth” for EOG connected frequency.
- Put exact hashes and long failure tables in Supplementary Information, while keeping applicability counts in the main paper.

## Build-order recommendation

1. Implement the machine-readable cross-system evidence table.
2. Build Figure 4 first; it tests whether the paper's logic is coherent.
3. Build the aggregate forest plots for Figures 2D and 3D.
4. Add species-level distributions after artifact retrieval is automated.
5. Build Figure 1 last, once manuscript terminology is frozen.
6. Run a final consistency test comparing every caption number with the frozen JSON projections.
