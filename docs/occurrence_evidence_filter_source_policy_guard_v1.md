# Safely comparing EOG occurrence compatibility after filtering positive observations

## Why this API exists

EOG previously had two well-defined but easily conflated source policies. `reconstruct_compatible_worlds` uses fixed declared source nodes and has a positive-evidence monotonicity contract. `evaluate_occurrence_rule_compatibility` alternatively permits **self-excluded observed peers as sources**: every occurrence node is evaluated using the other currently observed nodes as possible sources. Removing a recorded positive then changes **both** the tested targets and the eligible sources for retained targets.

Draft [wetland source audit PR #697](https://github.com/zuizui0223/eog/pull/697) established the concrete *observation problem*: original wetland site×species positives can disappear when the method and calendar windows are jointly restricted. Separately, it exhaustively enumerated the **64** simple three-node directed EOG graphs and found that self-excluded membership can lose and gain compatible rules as a positive node is removed.

The problem is a **software contract**: applying fixed-source inverse-world monotonicity or comparing only compatible **counts** to self-excluded results can conceal changes in rule identity. The original code could evaluate each policy separately, but had no explicit **safe paired-evaluation API**.

## Opt-in prospective EOG v2 interface

The new, non-breaking API is:

`eog.v2.traversability.audit_occurrence_evidence_filter`

It also remains importable through the historical lazy `eog.v2` root. The implementation resides at `src/eog/v2/occurrence_evidence_filter.py`.

The call accepts one immutable-by-contract mapping of named `DynamicTransitionOperator` candidates, a full observed positive-node set, a filtered proper subset, the same maximum reachability steps and numerical thresholds, and either explicit `fixed_source_ids` or omitted fixed sources (self-excluded peers).

Example:

```python
result = audit_occurrence_evidence_filter(
    frozen_candidate_operators,
    ("A", "B", "C"),
    ("A", "B"),
    source_policy="self_excluded",  # MUST be explicit; never auto-inferred
    max_steps=1,
    fixed_source_ids=None,  # explicit self-excluded peers
)
print(result.source_policy)
print(result.lost_compatible_rule_ids)
print(result.gained_compatible_rule_ids)
print(result.changed_retained_target_sources)
```

**Explicit source-policy declaration (pre-merge hardening):** The new API now **requires** `source_policy="fixed"` together with explicit `fixed_source_ids`, or `source_policy="self_excluded"` with **no fixed source IDs**. It refuses an omitted policy, a mismatched combination, and a mistaken `"current_state"` or `"historical_auto_detect"` selector. This prevents a caller from silently falling back to self-exclusion when a historical/fixed-source declaration was missing. These constraints are extra guards on this new opt-in API; the preexisting EOG APIs retain their original signatures.

**Source evidence is NOT proven by selection:** Even `source_policy="fixed", fixed_source_ids=(...)` only declares a source condition *for the chosen comparison*. The audit does **not** inspect historical genealogy, source population existence, temporal precedence, baseline trap occupancy, or independent archival provenance. Its `historical_origin_evidence_evaluated=False` and `source_state_scope="single_declared_static_observation_filter_not_temporal_sequence"` fields make this explicit. There is no auto-detection or certification of actual historical ancestors.

**Time-varying sources are an existing different API:** `eog.v2.sequential_world_forecast` allows the **realized current source state** to be updated once per transition while the candidate transition *rule* identity stays frozen. The already completed [Åland Glanville fritillary EOG-WF validation](../validation/glanville_eogwf/README.md) did exactly that for annual patch-state prediction, and returned adverse predictive added value for the exact-world-label head. That is not evidence that source patches were historical founders. A single static observation-filter audit must not be substituted for sequential, time-cutoff-locked updating.

**Response-blind source qualification is also different from historical source proof:** The existing [Algar v3 pre-response result](../validation/algar_restoration_v3_preresponse/authoritative_result.json) records a qualified 38-node / 114-deployment, three-context data design, yet `focal_species_selected=false` and `predictive_outcome_access_allowed=false`. Its candidate/transport adequacy does **not** establish ancestral origins or license outcome access. The archived [wetland source qualification](../docs/wetland_amphibian_source_qualification_v1.md) is `SOURCE_STRUCTURE_ONLY_NOT_OCCUPANCY_READY` and supplies no independently authenticated historical source. No search for another fresh EOG-WF endpoint follows from these checks.

The result is a frozen `OccurrenceEvidenceFilterAudit` dataclass containing **rule identity lists**, not only totals: compatible before, compatible after, retained, lost, gained, their membership-change label, rule/operator fingerprints, removed observed nodes, numeric settings, both EOG native comparison fingerprints and every retained target whose source peers changed (with source IDs and original/comparison first-passage support).

The following protections fail closed:

- **Source policy must be explicitly named**; fixed IDs are mandatory only with `"fixed"`, and forbidden with `"self_excluded"`. One-off fixed sources are declarations, not automatic validation of historical ancestry. Dynamic current sources belong to sequential forecasting.

- The filtered set must be a **proper subset** of full positive observations; both must contain at least two distinct valid node IDs. No unknown or repeated source nodes.
- Candidate operators must share the same complete node universe/order, and the **same mapping of operator objects** is used to compute before and after. The source policy, numerical threshold, floor and maximum steps are also reused from **one call**, not independently supplied precomputed results.
- A fixed-source filter may not remove any declared source, nor eliminate all non-source targets. If any compatible fixed-source rule disappears after *removing* a positive observation, the API throws rather than claiming a valid monotone result.
- In self-excluded mode, retained target source IDs and their support changes are preserved; **no monotonicity is asserted** and no call is made to EOG's `compare_reconstructions` fixed-world comparator.

This design leaves the existing `OccurrenceRuleCompatibility`, `OccurrenceRuleComparison`, and `FiniteWorldReconstruction` dataclasses and their result fingerprints unchanged. Production existing uses are not silently reinterpreted. The API reports compatibility of a **frozen finite candidate rule universe**; it is **not** a newly fitted biological-world likelihood.

## Exact synthetic regression results

Native EOG evaluation with fixed one-step operators on abstract `A,B,C` (loss channel support 1, raw positive edges support 1) yields:

| Test universe | Compatible before positive C removed | Compatible after positive C removed | Lost | Gained |
| --- | ---: | ---: | ---: | ---: |
| Three hand-audited worlds, fixed source A | `complete` | `complete, isolated_C` | 0 | 1 |
| Three worlds, self-excluded peers | `complete, hub` | `complete, isolated_C` | 1 | 1 |
| **All 64 directed three-node graphs, fixed source A** | **16** | **32** | **0** | **16** |
| **All 64 graphs, self-excluded peers** | **27** | **16** | **15** | **4** |

The 64-graph self-excluded overlap has **12** rule IDs. Source-peer changes are explicitly tracked for **both retained targets on every one of the 64 rules**, totaling **128** target×rule source-identity changes. In the fixed-source condition there are **zero** changed retained target source lists.

The 64 graphs are a complete finite **synthetic test universe**, not 64 environmental histories of Hungary, and the EOG numerical operators are not calibrated from wetland ecology. A separate, original, pinned wetland method/date dataset provides *why* real observation positivity may be lost — not real A/B/C node mappings or transition operators.

## Scientific and operational limits

This is a defensive API change, not an ecological discovery. No missing recorded positive can be upgraded to true absence, and no added positive can be assumed to be a biological movement event. The API computes *relative rule support* with the existing first-passage semantics, not an estimated detection probability, colonization rate, habitat selection, restoration causal effect or actual ecological world count.

The original EOG-WF 3 scored endpoints / 31 scientific STOPs / 3 administrative exclusions remain frozen. This new change lives in a **separate, small Draft PR based on main**, independent of the many source-validation files in Draft PR #697. Neither PR is automatically merged.

## Files and validation

- Core implementation: `src/eog/v2/occurrence_evidence_filter.py`.
- Public exports: `src/eog/v2/traversability.py` and historical root `src/eog/v2/__init__.py`.
- Exact 3-world and 64-world tests, export checks, malformed input controls: `tests/test_occurrence_evidence_filter_audit.py`.
- Frozen input/expectation contract: `validation/occurrence_source_policy_guard_v1/protocol.json`.
- CI: standard `.github/workflows/tests.yml` package checks including Python 3.10, 3.11 and 3.12, plus repository topology benchmark.

As with the prior wetland data, fail-closed checks and synthetic proofs cannot replace independent biological observation, calibrated movement operators or detection effort measurements.
