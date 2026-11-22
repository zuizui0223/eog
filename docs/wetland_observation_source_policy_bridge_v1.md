# EOG bridge: a lost observation witness is NOT the same operation under fixed versus self-excluded sources

## Completed comparison and what is actually empirical

This audit connects two **distinct and explicitly separated layers**:

1. **Authenticated original wetland source records:** a species can have an acoustic/visual positive over all survey dates and a full-method positive in a specified calendar window, yet no acoustic/visual positive **in that same window**. This is exactly an observation-recording/provenance phenomenon. For example, `orditoi-zsilip|Hyla arborea` in the published 2024 Hungarian amphibian CSV.
2. **An abstract, completely declared three-node EOG finite-world example:** the existing `eog.v2.occurrence_constraints.evaluate_occurrence_rule_compatibility` and `eog.v2.world_reconstruction.reconstruct_compatible_worlds` functions can behave differently when observations are filtered out **depending on whether source identities remain fixed**. The graph nodes are `A`, `B`, `C`, and are **NOT** coordinates, habitats, observed animal pathways, species or the above Hungarian wetland sites.

This is a **post-exposure original-source witness check + synthetic native-EOG source-policy counterexample**, *not an empirical reconstruction of wetland movement worlds* and not another EOG-WF independent scored endpoint.

Source: Wenner et al. (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, *Global Ecology and Conservation* 62 e03837 ([DOI 10.1016/j.gecco.2025.e03837](https://doi.org/10.1016/j.gecco.2025.e03837)); original CC BY 4.0 data/code archived at [Zenodo 10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115). Exact source CSVs were pinned to `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc` with source SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd` (survey) and `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319` (sites).

## The real original-source observation that motivates the distinction

One fixed source site/species combination `orditoi-zsilip|Hyla arborea` is positive in both of the following independent **original source CSV rows**:

| Original recorded date | Original method | Original CSV line | Relation to site's last 14 recorded calendar days |
| --- | --- | ---: | --- |
| **2024-03-24** | **visual** | **6** | Outside |
| **2024-05-30** | **dipnet** | **368** | Inside |

Thus the **same** site×species has `AV_all_dates=True` and `full_methods_last14=True` but `AV_last14=False` because no source-positive original acoustic/visual row occurs inside the last 14 calendar days. Source row filters are deterministic and commute; a pre-aggregated Boolean site×species occurrence label loses the method/date co-occurrence information needed to apply both filters at once.

This particular native witness remains independently source-authenticated by its original CSV SHA256 and line identities. The full Q1 original 27-site evidence has **16/144** such split-method×time positive pairs under last14, and Q2 intervention-only source subset has **9/77**. These are **original recorded positive pairs**, not biological state transitions or verified absences.

**What we cannot do:** use these source row dates to infer wetland transport edges, geographic sources, movement parameters, real occupancy histories or environmental suitability. None are provided or calibrated for EOG transition-world reconstruction.

## The EOG finite-world counterexample: same rules, different source policy

Freeze an abstract node universe `('A','B','C')`, one-step first-passage support (`max_steps=1`), directed geographic raw support of 1 per defined edge, and explicit EOG loss support of 1. All three worlds keep **exactly the same transition operators and source `A`** between observed-node sets.

| Frozen synthetic world | Directed edges in that world | Graph meaning within the declared abstraction |
| --- | --- | --- |
| `hub` | A↔C; B↔C; no direct A↔B | C can support both peers in one step; without C, A and B do not support one another within one step |
| `isolated_C` | A↔B; C disconnected | A/B peer reachable, C unavailable |
| `complete` | A↔B, A↔C, B↔C | Every node can support every other node in one step |

We compare `O_full={A,B,C}` and a filtered `O_gated={A,B}`, a hypothetical example of observation-positive `C` being dropped. **C is not the Hungarian wetland positive taxon or a geographic site**, and the graph is a strict theorem/counterexample witness, not a fitted biological model.

### Policy 1: EOG fixed-source world reconstruction

Call `reconstruct_compatible_worlds` with each `FiniteWorld` declaring the same source `('A',)` and `max_steps=1`. The rule is compatible when its frozen source can support *all remaining non-source positive targets*.

| Fixed source A held in both observed sets | hub | isolated_C | complete | Compatible world set |
| --- | --- | --- | --- | --- |
| `O_full={A,B,C}` | No: A cannot reach B directly | No: A cannot reach C | Yes | **{complete}** |
| `O_gated={A,B}` | No: A cannot reach B | Yes | Yes | **{complete, isolated_C}** |

The EOG native `compare_reconstructions` function, applied **in the valid direction** `O_gated → O_full` (adding positive C), reports one eliminated world, `isolated_C`, and a contraction fraction of **1/2**. In the reverse direction of *dropping* C, the compatible set **expands** or stays constant. This follows from frozen source and fixed support operators, NOT from an ecological probability of the worlds.

### Policy 2: EOG self-excluded peer-source diagnostics

Now call EOG's **different native API**, `evaluate_occurrence_rule_compatibility`, without `fixed_source_ids` for each of the **unchanged** frozen operators. For each observed node as target, **all other currently observed nodes** become peer sources; filtering a node changes not only the targets but also **who supplies their support**.

| Self-excluded peer sources change with observed set | hub | isolated_C | complete | Compatible rule/world labels |
| --- | --- | --- | --- | --- |
| `O_full={A,B,C}` | Yes: C supports A/B | No: C cannot be reached | Yes | **{complete, hub}** |
| `O_gated={A,B}` | No: A/B cannot support one another | Yes: A↔B | Yes | **{complete, isolated_C}** |

**After dropping positive C, `hub` becomes incompatible, while `isolated_C` becomes compatible.** Both sets contain **two** rules, but their **membership differs**. They are **not nested** in either direction.

One exact diagnostic target: under `hub`, the target `A` has peer source IDs `(B,C)` in the full set and one-step positive support thanks to C. In the gated set it only has peer source `B`, and its one-step support becomes **zero**. This is not a numerical artifact or a new movement rule: the target's peer-source set changed by the observation filter.

Therefore the positive-only compatible-world set monotonicity theorem of **fixed-source reconstruction cannot be silently transported to self-excluded policy diagnostics**. This also explains why EOG's existing fixed-world comparison API requires matching world fingerprints and declared fixed sources. The benchmark **does not invoke** `compare_reconstructions` on self-excluded result rows, and records this safety boundary explicitly.

## Technical and ecological scope

The example proves an exact fact **within its declared three-world synthetic finite universe**, using the real EOG v2 algorithms and the immutable graph/step definitions. It does **not** mean that dropping a recorded wetland observation would actually make a particular dispersal mechanism more plausible. No wetland site was mapped to A/B/C, and the original amphibian survey cannot establish movement edges, mechanism weights, natural barriers, source assignments or the field observation likelihood.

The real source-record result and theoretical policy comparison are **two distinct evidential layers**:
- Authentic wetland CSV: method×calendar gate can drop previously recorded positive witnesses when aggregated incorrectly;
- Native EOG synthetic proof: if such evidence loss is used to *redefine peer source identity*, the self-excluded compatibility result may be nonmonotone even though frozen-source compatibility is monotone.

This remains a **methodological warning about source provenance and inverse-world logic**, not an independent prediction of amphibian colonization, restoration success, ecological A/B/M partition or a new EOG-WF test. No original `unmarked` likelihood, true negatives, sampling effort, biological closure or real EOG finite-world graph was fitted.

## Reproduction, tests and immutable sources

- Fixed post-exposure protocol: `validation/wetland_observation_source_policy_bridge_v1/protocol.json`; committed **before** computation with frozen nodes, three graphs and expected compatible sets.
- Executable: `benchmarks/wetland_observation_source_policy_bridge_v1.py`; invokes actual EOG v2 fixed source reconstruction and occurrence self-exclusion, and source-authenticates the Hungarian positive pair.
- Unit tests: `tests/test_wetland_observation_source_policy_bridge_v1.py`; positive source subset monotonicity, exact self-excluded membership swap, peer-source identity change, source-A deletion rejection under frozen-world reconstruction, original unmodified row witness and altered-source SHA gate.
- Result receipt: `validation/wetland_observation_source_policy_bridge_v1/result_receipt.json`; CI run and fingerprints.
- GitHub Actions artifact: `observation_source_policy_bridge.json`, containing per-world/per-target first-passage support, frozen operator fingerprints, original source-dated witness rows and compatible world sets for both policies.

The production engine is not modified, and the example is intentionally isolated in `benchmarks/` and `tests/` until a separately justified biological source-policy application exists. PR #697 remains **Draft/unmerged**; EOG-WF's frozen three scored endpoints, 31 scientific STOPs and three administrative exclusions remain unchanged.
