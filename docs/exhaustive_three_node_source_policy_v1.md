# Exhaustive three-node EOG source-policy monotonicity audit: all 64 directed graphs

## Result and scope

**The original three-selected-graph source-policy counterexample is a general finite-universe phenomenon, not an artifact of selecting one suggestive network.** We enumerated the **complete** set of (2^6 = 64) simple directed graphs on abstract nodes `A`, `B`, `C` (no self-edges), and evaluated all of them with the existing EOG v2 occurrence and finite-world APIs using the *same frozen transition operators*. Positive observation `C` was filtered out, changing the observed set from `{A,B,C}` to `{A,B}`.

Exactly the following source-policy differences arise within that entire, explicitly bounded synthetic universe:

| EOG source policy | Compatible with original `{A,B,C}` | Compatible after `C` filtered to `{A,B}` | Shared worlds | Lost on filtering | Gained on filtering |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Frozen declared source `A`** | **16** | **32** | 16 | **0** | **16** |
| **Self-excluded peers as sources** | **27** | **16** | 12 | **15** | **4** |

The fixed-source compatible set is **nested** under loss of a positive constraint. The self-excluded compatible sets are **not nested in either direction**: removing observed `C` simultaneously makes **15** previously compatible rule worlds incompatible and **4** previously incompatible rule worlds compatible. **Even the number of compatible rule worlds can shrink after a positive observation is removed**, and total count changes conceal identity changes.

These are exact finite synthetic **graph counts**, not probabilities, posterior odds, movement models calibrated on animal observations, geographic processes, real ecological EOG worlds, or the population size of possible biological histories.

## Frozen finite graph universe and native EOG contract

There are six possible directed non-self edges, in this exact frozen bit order:

`A>B`, `A>C`, `B>A`, `B>C`, `C>A`, `C>B`.

Each integer mask from 0 through 63 specifies whether each of the six directed edges is present, giving **all 64 possible simple directed three-node graphs**. For every present edge we instantiate the actual `DynamicReachabilityEdge(geographic_support=1)`, use EOG's `build_dynamic_transition_operator` with `loss_support=1`, and set `max_steps=1`. Every `FiniteWorld` declares the same `source_ids=('A',)`. The world graph operators and their fingerprints are **unchanged** between observed-node sets.

Two existing EOG v2 APIs are executed separately:
- **Fixed source:** `eog.v2.world_reconstruction.reconstruct_compatible_worlds`, then `compare_reconstructions` **only in the valid direction of adding positive C** (`{A,B}→{A,B,C}`). The declared source A stays fixed.
- **Self-excluded:** `eog.v2.occurrence_constraints.evaluate_occurrence_rule_compatibility(..., fixed_source_ids=None)` for every graph and observed-node set, so each target's source candidates are the other currently observed positive nodes.

Every one of the **64×2×2 = 256 source-policy/observation native EOG compatibility decisions** is cross-checked against a separate exact directed-edge predicate, without using the EOG numerical support outputs in those predicates. All original operators, threshold contracts, and world identities are retained.

### Independent combinatorial proof

A one-step positive first passage exists exactly when at least one declared positive-weight source has a directed edge into the target. No edge is inferred from missing source records.

**Frozen source A:**

- `{A,B,C}` requires `A>B` **and** `A>C`: two forced edges and four otherwise free ⇒ **(2^4=16)** compatible graphs.
- `{A,B}` requires only `A>B`: one forced edge and five free ⇒ **(2^5=32)** compatible graphs.
- All 16 originally compatible worlds remain compatible: the same declared source and operator cannot make a remaining target *less* reachable when an extra positive constraint is removed.

**Self-excluded peer sources:**

- `{A,B,C}` requires each target to have at least one incoming directed edge from the *other two* positive nodes. For each target, the pair of inbound edges has three valid states (first only, second only, both), and these incoming edge pairs are disjoint. Hence **(3^3=27)** compatible graphs.
- `{A,B}` requires **both** `A>B` and `B>A`: two forced edges, four free ⇒ **(2^4=16)** compatible graphs.
- To be compatible in both observations, `A>B` and `B>A` must exist and C must have `A>C` or `B>C`. The latter pair has three valid states, while edges `C>A` and `C>B` are arbitrary: **(3×4=12)** shared graphs.
- The set lost when removing C therefore contains **(27−12=15)**, and the set newly gained contains **(16−12=4)** graphs. The union has 31 graphs, leaving **33** incompatible in both observation sets.

This independent combinatorial argument is not conditional on numerical coincidences, a fitted detection model, or selecting a favorable graph after observing results.

### Source-identity explanation

In the full observed set `{A,B,C}`, target A can be supported by B **or C**, target B by A **or C**, and target C by A **or B**. When positive C is removed, no remaining target C has to be supported (this **relaxes a constraint**), but C is also **no longer an eligible peer source** for A and B (this **tightens their support condition**). These opposing directions produce nonmonotone membership changes under self-exclusion.

They do **not** occur under the fixed source A rule: source A remains A, so removal of target C only relaxes constraints.

The earlier three selected-world example is embedded exactly in the 64 graphs:
- `hub` = mask **58** (A↔C, B↔C) — self-excluded compatible only with **{A,B,C}**.
- `isolated_C` = mask **05** (A↔B, C isolated) — self-excluded compatible only with **{A,B}**.
- `complete` = mask **63** (all six directed edges) — compatible with **both**.

Unlike the earlier three-world example (where both self-excluded compatible sets happened to contain two worlds), **the full synthetic 64-world universe makes the contraction and the gain/loss counts explicit**.

## Why this is relevant to authentic wetland observation records — and what is not established

The original Hungarian amphibian source has a concrete method×calendar split witness: the originally recorded source-positive `orditoi-zsilip|Hyla arborea` occurs as **visual on 2024-03-24 (original CSV line 6)** and as **dipnet on 2024-05-30 (line 368)**. In the source site's last-14-calendar-day window, a positive via *all* recorded methods still exists, while a positive via *acoustic+visual* does not. In the original Q1 full source, **16** site×species pairs display this split-witness structure; in intervention-only Q2 there are **9**.

Those **authentic** original row identities are verified from the immutable files [Wenner et al. 2025](https://doi.org/10.1016/j.gecco.2025.e03837), [Zenodo 10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115), original source mirror `frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc`, survey SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd`, sites SHA256 `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`.

**The real observations are not mapped onto the synthetic A/B/C nodes**. They establish the risk of losing a genuine *recorded* positive witness under observation gating. They do **not** establish any of the EOG synthetic transition edges, fixed ancestral sources, natural dispersal routes, true biological absence, biotic interactions or restoration effects. Accordingly, the **64-world count is not an empirical estimate of compatible Hungarian wetland ecological histories**.

In general, safe EOG inference requires distinguishing:
1. The *original observation grain* (site×species×date×method) and whether a positive witness survives a joint data gate.
2. The declared *source policy* for evaluation (fixed-source or evidence-dependent self-excluded peer-source).
3. The *finite-world universe* and whether its actual transition operators are independently specified/fixed.

An ordinary positive-only monotonicity conclusion **requires fixed sources**, not merely a positive-only input. EOG's `compare_reconstructions` has a fixed-world contract; it must **not** be applied to self-excluded diagnostic memberships.

## CI, artifacts and explicit STOPs

- Source- and graph-contract precommit: `validation/exhaustive_three_node_source_policy_v1/protocol.json` (posted **before** any new 64-world native EOG computation).
- Complete original EOG v2 executable: `benchmarks/exhaustive_three_node_source_policy_v1.py`; no changes to production EOG algorithms.
- Fail-closed regression tests: `tests/test_exhaustive_three_node_source_policy_v1.py` for the whole 64-world bit roster, fixed and self-excluded exact sets, 256 native EOG API vs independent bit-predicate agreements, original three example masks, malformed mask rejection, and explicit non-ecological scope.
- Full **64-row graph/source-policy output CSV**: `synthetic_64_eog_graph_source_policy_results.csv`, including each graph's exact directed-edge mask, graph/world fingerprints, four native compatibility flags, four independent graph-predicate flags and original unsupported target IDs.
- Result and archive fingerprints: `validation/exhaustive_three_node_source_policy_v1/result_receipt.json`.

**Scope STOP:** This complete enumeration is complete only for **abstract directed simple three-node, one-step** EOG graphs. There is no biologically established `max_steps=1`, no empirical graph or movement edge estimation, no actual wetland EOG inverse-world model, no occupancy likelihood, no true absence, no randomized restoration effect, and no extra EOG-WF prediction endpoint. The previous EOG-WF 3 scored /31 scientific STOP /3 administrative exclusions remain unchanged. PR #697 remains Draft/unmerged.
