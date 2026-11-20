# Alternative-source minimum required relaxation — known-truth v2

> **後続の合成ネットワーク一般性検証：** [v3：1,152条件・96組の起源ネットワーク比較](occurrence_conditioned_source_minrelax_v3.md)。主結果は一方向循環起源コアの方が完全相互接続コアより、source-robustとpossibleの許容閾値集合に大きな差を残す（平均+0.257378、92/96組）。凍結シミュレーションの結果で、実環境の頻度推定ではない。

**Scientific status:** frozen *synthetic* finite-world experiment. This is **not** a new EOG-WF predictive endpoint or empirical source-identification result. The pre-implementation hypothesis/STOP contract was committed first at `validation/occurrence_conditioned_source_minrelax_v2/protocol_v2.json`.

## Question

If several origins are plausible and none is independently confirmed, which geographic/environmental/barrier relaxations can explain the *same* positive observations under at least one source, and which require no assumption about which declared source is correct?

The v1 inverse formulation fixed one observed source. The v2 bench holds the candidate graph, node-positive set, baseline threshold units, time horizon and full threshold grid unchanged while swapping **three declared fixed singleton source hypotheses**. An observed positive is not an independently verified parent/source.

## Estimands: source-existential ≠ source-universal

Let `Θ` be one finite Cartesian threshold grid with coordinatewise order, `O` the same complete observed-positive roster, and `S={A,B,C}` the declared alternative singleton source hypotheses. For each source hypothesis `s`:

```text
F_s = { θ in Θ : O is reachable from fixed s under θ within H directed hops }
P_s = ParetoMin(F_s)

F_possible = union_{s in S} F_s
F_source_robust = intersection_{s in S} F_s

P_possible = ParetoMin(F_possible)
P_source_robust = ParetoMin(F_source_robust)
```

`P_possible` requires only **one hypothetical source to make the whole positive set feasible**. `P_source_robust` requires the **same relaxation threshold vector** to permit the whole positive set from **each** of the declared sources, potentially along different directed paths. It does **not** require the same physical path, actual multi-origin colonization or a probabilistic posterior.

A biological system needs only its actual source(s) to explain its history. Therefore an empty `F_source_robust` **does not mean** the observations are impossible, nor does it mean the true origin can be ruled out; source-robust is deliberately a stringent counterfactual robustness criterion.

## Exact antichain composition (known order-theory algebra, not novel mathematics)

For a fixed graph and horizon, increasing a threshold cannot remove a previously admitted directed edge, hence each nonempty `F_s` is an *upper set* of the same finite coordinatewise ordered grid `Θ`. Write `uparrow P_s` for the upward closure of its minimal frontier.

```text
F_s = upward_closure(P_s)

P_possible =
    ParetoMin( union_s P_s )

P_source_robust =
    ParetoMin( { coordinatewise_max(p_A, p_B, p_C)
                 : p_A in P_A, p_B in P_B, p_C in P_C } )
```

**Proof of source-robust rule:** A threshold `θ` lies in all three `F_s` if and only if, for each source, some `p_s in P_s` obeys `p_s <= θ`. This is equivalent to a componentwise join `p_A∨p_B∨p_C <= θ`. The joint feasible upper set is therefore the upper closure of all joins. Taking its minimal elements gives the stated frontier. The source-existential rule follows from union of upper closures. The proof requires a shared comparable threshold grid and fixed source definitions.

**Subtle consequence:** `P_source_robust` is *not* `ParetoMin(intersection_s P_s)`. Minimal frontiers can be pairwise disjoint while their feasible upper sets overlap. This is the central category error the synthetic fixture catches.

## Frozen source-uncertainty fixture and independently recomputed results

Graph: nodes `A,B,C,T`, all of `A,B,C,T` observed positive, the three hypothetical sources considered separately. All six directed source-to-source edges are admitted already at baseline; each source's direct edge to `T` crosses a **different threshold axis**. The threshold grid has two levels per axis: `geo=10 or 15 km`, `env=1 or 2 unit`, `barrier permission=0 or 1` → `2×2×2=8` worlds.

| Source with max H=1 | Individual Pareto minimum `(Δgeo km,Δenv,Δbarrier)` | Compatible threshold worlds |
| --- | --- | ---: |
| A | `(0,1,0)` | 4/8 |
| B | `(5,0,0)` | 4/8 |
| C | `(0,0,1)` | 4/8 |

| Condition | `F_possible` size | `F_source_robust` size | Minimum source-robust relaxation |
| --- | ---: | ---: | --- |
| **H=1** directed hop | **7/8** | **1/8** | **`(5,1,1)`** |
| **H=2** directed hops | **7/8** | **7/8** | Three distinct one-axis vectors `(0,1,0)`, `(5,0,0)`, `(0,0,1)` |
| **H=1; C→T hard-unavailable** | **3/4** | **0/4** | None within the declared graph |

The H=1 three single-source minimal frontiers have *empty intersection*, yet all three sources can accommodate every positive when the **joint vector `(5,1,1)`** is admitted. When H rises from 1 to 2, each source can reach another source in one hop and continue through that source's direct T-edge in the second. Therefore the three separate feasible sets coincide in this fixture. This is **horizon-conditional**, not a universal prediction that two generations abolish origin uncertainty.

With H=1 and C→T physically marked unavailable, no threshold opens that edge. C has no route to T within H=1; its source-specific frontier becomes empty, and the shared robust frontier is empty. A/B still offer possible explanations. This is a deliberate *model-structure STOP*, not biological impossibility.

The exact expected class counts and hypotheses are declared in the frozen protocol. A separate **JavaScript graph enumeration** of every source×threshold combination reproduced the 8-world / 24 source-world-pair counts, `H1=7 possible/1 robust`, `H2=7/7`, hard-edge `3 possible/0 robust` under its four remaining non-hard breakpoints. The new Python benchmark reproduces these using the original `infer_required_relaxations` (which itself uses original EOG `reconstruct_compatible_worlds` and `minimum_relaxation_frontier`) and separately computes per-world feasibility with an independent set-BFS and checks the antichain composition identity. The distinct runtime statuses must be read from CI (do not equate any successful workflow with empirical science).

## Verification receipt (GitHub Actions)

The dedicated synthetic-only workflow [run #44729976721](https://github.com/zuizui0223/eog/actions/runs/44729976721) **completed successfully**, with native EOG regression, this v2 test suite, relaxation-family and temporal-relaxation regression, independent bounded BFS and frozen-frontier checks passing. Archive artifact ID `14626066741`, ZIP SHA-256 `351b9778c4c1faf508dc7231c0977acb81de16eeea758f8c35902e464299debb`.

The independently archived [synthetic result receipt](../validation/occurrence_conditioned_source_minrelax_v2/result_receipt_v2.json) binds the protocol-first commit, run, artifact and the **H1=7 possible/1 robust; H2=7/7; hard-edge=3/0** finite-world counts. It is **not** an external or heldout biological confirmation.

## Method and exactness boundary

- **Exactness:** all explicitly declared finite edge-breakpoint worlds on one fixed source/graph/positive/horizon contract. The effect of a source alternative is not inferred from real survey data.
- **Fixed analytical coordinates:** the three axes retain the same units. A different climate product, graph-resolution rule or source-detection model requires a new explicitly declared analyst/observation world layer. This v2 is **not** the full `natural × analyst` uncertainty universe.
- **What is not measured:** verified founder identity, genetic parentage, historical dispersal route, geographic barrier permeability, movement years or colonization success. The horizon H counts graph *hops* rather than calendar years.
- **Positive source policy:** only compared **fixed singleton sources** named before running the model. This is **not** the self-excluded peer-source mode studied separately in unmerged PR #697/#698, for which removing observations can change the source set itself and invalidate fixed-world monotonicity.
- **Novelty:** Pareto antichain upper-set joins and set-theoretic existential/universal quantifiers are existing mathematical ideas. The possible EOG contribution is the *explicit ecological source-hypothesis contract*, combining occurrence-conditioned reachability, bounded directed graph, separate relax axes and a certified source-sensitive inference output.

## Reproduce

```bash
python -m pip install -e ".[dev]"
python -m pytest -q tests/test_occurrence_conditioned_source_minrelax_v2.py tests/test_occurrence_conditioned_minrelax_v1.py
python -m benchmarks.occurrence_conditioned_source_minrelax_v2 \
  --protocol validation/occurrence_conditioned_source_minrelax_v2/protocol_v2.json \
  --output results/source_minrelax_v2.json
```

Canonical files:

- [Frozen pre-implementation contract](../validation/occurrence_conditioned_source_minrelax_v2/protocol_v2.json)
- [Known-truth benchmark](../benchmarks/occurrence_conditioned_source_minrelax_v2.py)
- [Frozen exact regression tests](../tests/test_occurrence_conditioned_source_minrelax_v2.py)
- [Parent fixed-source MRR benchmark](../docs/occurrence_conditioned_minrelax_v1.md)
- [Minimum required relaxation evidence inventory](../docs/result_inventory/MINIMUM_REQUIRED_RELAXATION_AUDIT_20261120.md)

## Next valid biological gate

To go beyond source-uncertainty mathematical robustness, a separate independent source study must declare the candidate source roster from data *not fitted to the same targets*, source-observation uncertainty (nondetection ≠ absence), time windows, biological movement evidence, and at least two defensible analytical graph representations. Exact finite `F_possible / F_source_robust` is a **scientific sensitivity** statement, not a source-identification method or EOG predictive superiority.
