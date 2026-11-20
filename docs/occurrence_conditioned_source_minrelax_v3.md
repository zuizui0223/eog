# Source-uncertain minimum relaxation: frozen paired random-graph generality v3

> **後続v4の確定結果：** [候補起源ごとの必要hop幅とsource-core有向直径による上限](occurrence_conditioned_source_minrelax_v4.md)。v3の1 horizon比較（循環 vs 完全相互接続）とは別に、v4で全horizon積分値（循環 vs 双方向スター）を独立新seed検証し、事前予測G5は**不支持**（平均循環−スター = −0.0390625 hops、13正・20同・31逆/64組）。上限定理は成立、直径による平均効果量の順位づけは不可。

## Status

Research-only **synthetic generality stress test**. The protocol was committed *before running the paired generator* at [v3 protocol](../validation/occurrence_conditioned_source_minrelax_v3/protocol_v3.json), commit `32626e5a5726d8f33083163c2e2dfc31b7eb2f46`. This successor to the [v2 three-source known-graph demonstration](occurrence_conditioned_source_minrelax_v2.md) holds EOG-WF's 3 scored / 31 scientific STOP / 3 administrative exclusion empirical closure unchanged.

This test checks a substantive concern: v2's convergence after two hops could be a property of its fully interconnected source triangle, not a generic property of origin uncertainty.

## Frozen design: graph pairing, not ecological replication

- **Source candidates:** 2, 3, or 4 frozen hypothetical singleton source nodes, all positive.
- **Positive targets:** 3 additional nodes, shared by every source hypothesis in the panel.
- **Source-core topology:** fully bidirectional baseline source core or a one-direction baseline source cycle. Both are **strongly connected** but may have different shortest-path lengths. For two sources the two regimes are exactly identical (frozen negative control).
- **Other edges:** Same random *optional* source-to-target / target-to-target edges under each paired source-core comparison. Optional source→target inclusion 0.25 or 0.65, target→target inclusion 0.30; hard-unavailable fraction and geographic/environment/barrier tiers were frozen, not fit.
- **Guaranteed anchor opportunities:** source S0 has three direct candidate edges to the targets, each requiring a different potential relaxation axis. They ensure possible high-threshold pathways and prevent every difficult cell from being a trivial unconnected graph.
- **Steps:** H=1, 2, 3, and H=n_nodes−1. H is **graph-hop budget**, not years or generations.
- **Pseudorandom coverage:** 24 deterministic seed indices, paired exactly between source-core treatments. Total **3 source counts × 2 densities × 24 seeds × 2 source cores × 4 horizons = 1,152 graph×horizon panels**. The primary directed source-core comparison is at H=n_sources−1 for source counts 3 or 4 (**96 matched graph pairs**).

The source-core manipulation is a *constructed graph property*. A matched source graph comparison is not a real population replication, nor a statistical p-value for natural systems.

## Quantified target

For each finite shared geographic/environment/barrier threshold grid `Θ`, compute the complete set `F_s(H)` of threshold vectors for which every positive node is reachable from singleton source s within H hops. Define

```text
F_possible(H) = union_s F_s(H)
F_source_robust(H) = intersection_s F_s(H)
g(H) = ( |F_possible(H)| - |F_source_robust(H)| ) / |Θ|
```

`g` is a **fraction of possible threshold worlds** for which a source-existential explanation exists but not every declared origin hypothesis works. It is *not* a probability of occurrence, failure, origin, migration, or biological reality.

Predeclared G1 directional hypothesis: under matched optional edges and n_sources in 3/4, the one-direction source cycle has a larger **mean g** at H=n_sources−1 than a fully bidirectional source core. The correct denominator is 96 matched graph draws. A nonpositive mean must be retained as a **refutation or unsupported directional prediction** without changing seed rosters.

## Necessary formal controls

- **G2, horizon monotonicity:** For fixed sources/graph and identical threshold grid, both `F_possible(H)` and `F_source_robust(H)` are nested upward as H grows. This **does not imply** that their *difference* `g(H)` is monotone.
- **G3, finite SCC terminal:** At H=n_nodes−1, baseline source-core connectivity ensures that if one declared source reaches every positive, then every declared source does (possibly along a different route). Possible and source-robust thus coincide at this declared horizon. A theorem/implementation-control, **not** a new discovery.
- **G4, identical two-source control:** A complete 2-node source core and a directed 2-cycle are exactly the same graph, so their outputs must match under identical optional edges.
- **G5, independent native-core bridge:** For seed index 0, all source counts, both densities, both source-core regimes and both critical/terminal horizons (**24 checks**), compare direct independent bounded BFS and finite threshold Pareto frontiers against existing production EOG v2 reconstruction. Original v2 code is **reused rather than modified**.
- **G6, roster fidelity:** No source is claimed as historical or genetically validated; all source hypotheses are held fixed across threshold worlds and compared graph regimes.

The directional magnitude is a result of the *chosen generator*, not of theorems G2–G4. All outcomes, including negative and no-possible worlds, remain in the denominator.

## Frozen result — hypothesis G1 supported **within generator**, not ecological generality

Dedicated [GitHub Actions run 44743842920](https://github.com/zuizui0223/eog/actions/runs/44743842920) completed successfully. Full 1,152-panel JSON is preserved as artifact `14632595326` (ZIP SHA256 `2a0adab26a0ad3eea7bec3f084475584d34dd284f24f6df945ae391b1bfa9f54`; complete result self-excluded SHA256 `2d6008fcaf959fcf22d029eaf6a344ca1a21e8eb2ee0b6f390f4a1bdcc728611`). [Frozen aggregate receipt](../validation/occurrence_conditioned_source_minrelax_v3/frozen_aggregate_summary_v3.json).

**Preregistered primary result** (3 or 4 possible sources; critical H=n_sources−1; same optional graph/thresholds within each of 96 paired comparisons):

- Mean cycle-minus-complete uncertainty gap `g_cycle-g_complete`: **+0.2573784722** (**+25.74 percentage points of finite threshold worlds**, not percent change or biological probability).
- Per-pair directions: cycle larger **92/96**, tied **4/96**, complete larger **0/96**.
- Hence predeclared G1 **SUPPORTED within this synthetic graph generator**. No permutation p or ecological replication claim is attached.

| Source candidates | Optional source-target edge probability | Cycle mean `g` | Complete mean `g` | Cycle larger, out of 24 matched seeds |
| --- | ---: | ---: | ---: | ---: |
| 3 | 0.25 | 0.2587 | 0.0990 | 22 |
| 3 | 0.65 | 0.2674 | 0.0208 | 22 |
| 4 | 0.25 | 0.3090 | 0.0069 | 24 |
| 4 | 0.65 | 0.3212 | 0.0000 | 24 |

**Theorem/implementation controls** (distinct from G1's nontrivial generator-specific contrast):

- **0/864** horizon-set monotonicity violations across adjacent H levels.
- **0/288** full-terminal-source-SCC mismatch panels: at H=n_nodes−1, possible and universal sets coincide.
- **0/192** two-source complete-versus-cycle negative-control mismatches.
- **0/24** native EOG-v2 versus independent shortest-path/threshold/Pareto mismatches in prespecified seed-0 graphs.
- Breakpoint worlds among rows: **296 panels with 8 worlds**, **856 panels with 12 worlds**.

**Failure diagnosis retained:** first CI [run 44743714561](https://github.com/zuizui0223/eog/actions/runs/44743714561) stopped because the JavaScript xorshift32 reference value was compared to a Python float by literal string-rounding equality, differing only in the last IEEE754 bit of the *test literal*. Changed only the assertion to bounded tolerance; **no generator, protocol, threshold, outcome or observed G1 score was altered**. The second, successful run is authoritative.

**Interpretation:** On these matched finite synthetic graphs, a directed origin cycle creates a larger region where *some* origin hypothesis suffices but not *all* origin hypotheses suffice. Fully connected baseline source cores make sources more interchangeable under a finite hop budget. The vanishing gap at H=n_nodes−1 is a deterministic SCC reachability consequence, **not** independently observed dispersal homogenization.

## Results and reproducibility

The result is computed by the research-only [v3 benchmark](../benchmarks/occurrence_conditioned_source_minrelax_v3.py), with deterministic generator [regression tests](../tests/test_occurrence_conditioned_source_minrelax_v3.py), and synthetic-only [workflow](../.github/workflows/eog-source-minrelax-random-generality-v3.yml). CI must verify the frozen source-native crosschecks and denominators before the aggregate can be promoted from an independently computed estimate to a **CI-backed result**.

Run:

```bash
python -m pip install -e . pytest
python -m pytest -q \
  tests/test_occurrence_conditioned_minrelax_v1.py \
  tests/test_occurrence_conditioned_source_minrelax_v2.py \
  tests/test_occurrence_conditioned_source_minrelax_v3.py
python -m benchmarks.occurrence_conditioned_source_minrelax_v3 \
  --protocol validation/occurrence_conditioned_source_minrelax_v3/protocol_v3.json \
  --output results/source_minrelax_v3/result.json
```

## Claim boundaries and next biological stage

These are finite candidate graph diagrams of directional source access and threshold requirements. They do not estimate actual founding source(s), observed dispersal paths, colonization kernels, biological barriers, real elapsed time, nor a new predictive SDM endpoint.

Next ecological test cannot score already-exposed Åland/Glanville observations as an independent holdout. The current [Glanville audit](result_inventory/MINIMUM_REQUIRED_RELAXATION_AUDIT_20261120.md) and [genetic source assignment comparison](glanville_genetic_host_world_v2_result.md) can motivate source-roster eligibility criteria, but genetic *model-inferred* origin is not a guaranteed natal label. Future sampling and source evidence must be frozen independently before any new target predictions are inspected.
