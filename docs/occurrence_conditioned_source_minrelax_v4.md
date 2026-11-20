# EOG source-horizon identifiability: exact hop-gap bound and independent topology stress test (v4)

**Scientific status:** preregistered *synthetic* experiment. No new field data, true founder, measured dispersal event, or EOG-WF endpoint. This continuation targets a specific weakness in [v3](occurrence_conditioned_source_minrelax_v3.md): source-existential versus source-universal differences were measured as threshold-world frequencies, but the **mathematical quantity explaining their onset and disappearance across horizons** was not yet isolated.

**Protocol frozen before execution:** [v4 declaration](../validation/occurrence_conditioned_source_minrelax_v4/protocol_v4.json) initially committed at `2828c38d1db8ef9f69b25e5fe5d69ac39983a0be`; a pre-score wording amendment at `0dca8a6f01c5ec060bbe30cf52edb8bc1b5cbf6e` defines zero contribution for all-source-infeasible threshold worlds. This amendment occurred before any generator result was scored; no data, source design, success metric, or threshold choice changed.

## 1. Target-specific hop-depth equivalence: an exact theorem, not a claimed new mathematical discovery

For a fixed directed graph world at geographic/environmental/barrier thresholds `theta`, an **unchanged set of positive observations** `O`, and fixed alternative singleton source hypotheses `S`, let

```text
d_theta(s,x) = shortest number of directed hops from s to positive node x
               (infinity if unreachable)
h_s(theta)   = max_{x in O} d_theta(s,x)
h_possible(theta) = min_{s in S} h_s(theta)
h_robust(theta)   = max_{s in S} h_s(theta)
```

For any finite hop budget `H`:

```text
some-source feasibility       iff h_possible(theta) <= H
all-declared-source feasibility iff h_robust(theta) <= H

source-unresolved at H iff h_possible(theta) <= H < h_robust(theta)
```

A threshold world with all sources unable to reach some positive target has `h_possible=∞` and contributes **zero** ambiguous hop budgets. When a baseline source core is strongly connected, either all candidate sources can eventually explain `O` or none can, so there is no source-specific mixture of infinite and finite `h_s` inside that world.

Let `N=|Theta|` be the count of declared threshold worlds, and

```text
g(H) = (# worlds possible at H but not source-robust at H) / N
K(theta) = h_robust(theta)-h_possible(theta) if finite,
           0 if h_possible(theta)=infinity
```

The integrated ambiguity area over all meaningful graph horizons is exactly

```text
sum_{H=0}^{|V|-2} g(H) = (1/N) sum_{theta in Theta} K(theta).
```

**Proof:** Each finite world contributes indicator 1 to `g(H)` exactly for integer `H=h_possible,…,h_robust-1`, which contains `K(theta)` hop budgets. When the baseline source core is strongly connected, all finite shortest paths can be made simple and have at most `|V|-1` hops. All-infeasible worlds contribute 0 on both sides. Summation over worlds and hop budgets commutes.

This is a general directed shortest-path and indicator-counting identity. It does not imply that `g(H)` itself is monotonic in H; both possible and robust sets grow with H, while the set difference can grow *or* shrink.

## 2. Source-core diameter gives an exact upper bound

Suppose all candidate source nodes form a strongly connected **baseline** directed core, with directed core diameter

```text
D_C = max_{s,s' in S} d_core(s,s')
```

and all core edges remain admitted at every examined threshold. Pick a source `s*` achieving `h_possible(theta)`. Any other `s` can reach `s*` within `D_C` hops and follow a finite path from `s*` to every observed positive. Hence

```text
h_s(theta) <= d_core(s,s*) + h_possible(theta)
             <= D_C + h_possible(theta).

Therefore    0 <= K(theta) <= D_C
and          0 <= integrated ambiguity area <= D_C.
```

This upper bound depends on the **source-to-source directed distances**, not simply the number of source populations or how many sites are occupied. Complete bidirectional source core has `D_C=1`, a bidirectional star centered at `S0` has `D_C=2`, a one-way directed source cycle of n sources has `D_C=n-1`.

**Critical qualifier:** If a proposed source is not reachable from another source within the baseline core, `D_C` can be infinite. A source hypothesis may be able to explain all positives while another cannot at **any** finite H. No universal finite bound is claimed for disconnected source hypotheses. The preregistered negative control explicitly deletes a cycle edge and keeps that contradiction in the result.

## 3. Independent, preregistered synthetic topology comparison (outcome not assumed)

To distinguish this exact theorem from quantitative graph-generator effects, v4 freezes **fresh seed indices 24–39 not evaluated in v3**. It reuses v3's source-to-target optional-edge distribution and S0 target anchor, while varying only the source core.

| Axis | Frozen design |
| --- | --- |
| Candidate source count | 3, 4 |
| Non-source positives | 3, all held positive |
| Source-core networks | Complete bidirectional, bidirectional star (S0 center), directed one-way cycle |
| Optional source-target edge inclusion | 0.25, 0.65 |
| New paired random seeds | 16 per source count/density |
| Total independently newly generated topology graphs | **192** (= 64 matched triples) |
| Frozen primary comparison | Mean ambiguity area `A_cycle - A_star` over **64 matched triples**; predeclared direction `>0` |

Each source-core treatment in a triple preserves **exactly** the same optional directed edges, baseline geographic/environment/barrier threshold worlds, target observations and source eligibility. The source-center anchor S0 is deliberately preserved; it makes this a generator-specific comparison rather than a general theorem that every ecological cycle necessarily creates more source ambiguity than every star.

The benchmark uses one independent directed BFS over all candidate sources for each threshold world and checks all hop intervals. It also reuses [v2 original EOG reconstruction](../benchmarks/occurrence_conditioned_source_minrelax_v2.py) for predeclared seed24 and 36 graph×hop cases to test whether the interval-based fast calculation matches the native EOG finite-world compatibility and Pareto frontiers.

**Prespecified outcomes:** zero diameter-bound violations; zero identity failures; zero native-v2 inconsistencies; a disconnected negative control; plus the G5 star/cycle quantitative directional contrast, **recorded as supported or refuted without tuning**. Interior increases in `g(H)` are descriptive rather than a new hypothesis.

## 4. Claim boundary and relevance

- **Theorem:** For the declared fixed network, source roster and positive observations, the interval `[h_possible,h_robust)` **exactly** characterizes source disagreement and its finite upper bound under a strongly connected source core.
- **Synthetic result:** How frequently different source cores create nontrivial ambiguity intervals, and their average hop widths, is a fact about the frozen generator alone.
- **Not established:** actual island sources, genotype-based natal origins, biological travel time, calibrated natural dispersal kernels, or improved held-out SDM loss. A hop is an **edge transition**, not a year or generation.
- **Interpretive use:** The v3 result can be decomposed into a measurable *source-hop ambiguity duration* for each declared threshold world, rather than attributing a large mean gap simply to “more isolated sources.”
- **Prior art boundary:** Directed graph diameter, shortest path, strong connectedness, Pareto minimality, and counting indicators are standard results. Novelty—if established externally—would lie in source-uncertain **occurrence-conditioned biogeographic inference** and calibrated biological predictions.

## 5. Sources and reproduction

- [Frozen v4 protocol](../validation/occurrence_conditioned_source_minrelax_v4/protocol_v4.json)
- [v4 source-hop and topology benchmark](../benchmarks/occurrence_conditioned_source_minrelax_v4.py)
- [v4 theorem and negative-control tests](../tests/test_occurrence_conditioned_source_minrelax_v4.py)
- [Dedicated synthetic-only Actions workflow](../.github/workflows/eog-source-horizon-identifiability-v4.yml)
- [v3 source-uncertain MRR parent result](occurrence_conditioned_source_minrelax_v3.md)
- [Glanville empirical minrelax limitations](result_inventory/MINIMUM_REQUIRED_RELAXATION_AUDIT_20261120.md)

```bash
python -m pip install -e . pytest
python -m pytest -q tests/test_occurrence_conditioned_source_minrelax_v4.py
python -m benchmarks.occurrence_conditioned_source_minrelax_v4 \
  --protocol validation/occurrence_conditioned_source_minrelax_v4/protocol_v4.json \
  --output results/source_minrelax_v4/result.json
```

The original frozen EOG-WF **3 scored / 31 scientific STOP / 3 administrative exclusions** remains closed. This new experiment does not touch the earlier Glanville genetic assignments, or release any original source/target observations.
