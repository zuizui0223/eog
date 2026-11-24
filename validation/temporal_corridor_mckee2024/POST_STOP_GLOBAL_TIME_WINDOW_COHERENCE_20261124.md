# McKee 2024: full sparse-sequence time-window coherence (2026-11-24)

## Main result and status

**Source/input-level method diagnostic only; original time and CRS STOPs retained.** The prior [three-record audit](POST_STOP_TIME_INTERVAL_COHERENCE_20261124.md) identified 64 three-record windows where each adjacent 12.5-hour gap was separately possible but **no single assignment** to the shared middle timestamp satisfied both gaps, given the full-day T0 uncertainty model.

The present extension asks how that quantifier problem accumulates over **longer chains and entire individual-season observation sequences**, without opening the withheld dense 2-hour reference and without inferring biological connectivity.

The [full-window protocol](post_stop_global_time_window_coherence_protocol_v1.json) was committed at 82d3be54e7f4689cbda60a43ab15827532b740b8, **before the new 4/6/12/24-record and full-group audit**. It pins the six window lengths (2,3,4,6,12,24), source version/SHA, individual-season group key, 12.5-hour maximum gap, integer 1-second forward ordering, and two time-precision worlds T0 and T1.

## Exact, reusable logic

For a frozen ordered sequence of intervals [L_i,U_i] in integer local civil-clock seconds, require each adjacent gap to lie in [1,45000] seconds.

Naive pair aggregation only checks, for every consecutive pair separately, whether:
- U_(i+1) >= L_i + 1, and
- L_(i+1) <= U_i + 45000.

It can choose a different value of the shared record time for each pair. The correct **whole-window** test propagates a single reachable time interval:

1. Start with [a,b] = [L_0,U_0].
2. At next record i, replace it by [max(L_i,a+1), min(U_i,b+45000)].
3. If that interval becomes empty, the entire *fixed-order* record chain is infeasible; otherwise continue to the last record.

This is an elementary exact time-window constraint propagation, **not a newly invented temporal-graph theorem or a new GPS movement model**. It is an analogue of EOG's no-splicing finite-world distinction: a possible pair of edges in alternative time assignments is not necessarily a possible path under one shared assignment.

The local original 12-hour GPS ZIP was checked against publisher file size 1,539,661 and SHA-256 556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4. Only five already approved DBF columns (Herd, AID, SeasnYr, Season, Timstmp) were used ephemerally. The 28,953 fixes form 421 dependent animal-season groups, containing 3–304 records (median group size 46). **Individual fixes are not independent ecological replicates.**

T0 sets date-only entries to the *uncertain* range 00:00:00–23:59:59 in local naive seconds. T1 narrows them to 00:00:00–01:00:00 as an unverified publication-inspired alternative. Complete timestamps remain fixed; no DST correction or UTC alignment is inferred.

## Result: 2–24-record windows

| Fixed window length | Number of pairwise-possible T0 windows | No coherent whole-window assignment | False-chain fraction | T1 false chains |
|---|---:|---:|---:|---:|
| 2 records | 27,739 | 0 | 0% | 0 |
| 3 records | 26,764 | 64 | 0.24% | 0 |
| 4 records | 25,861 | 123 | 0.48% | 0 |
| 6 records | 24,275 | 217 | 0.89% | 0 |
| 12 records | 20,543 | 390 | 1.90% | 0 |
| 24 records | 15,789 | **590** | **3.74%** | 0 |

Windows overlap and are **not independent replicates**. The increasing ratio does not prove a general biological scaling law; it is a descriptive consequence of uncertainty accumulation in this exact source under the frozen T0 clock model. Different window lengths also have different eligibility denominators. The [aggregate receipt](post_stop_global_time_window_coherence_receipt_v1.json) preserves **all** denominators, T0/T1 scenario comparisons and affected-group counts.

The original PR #748 triple result is recovered exactly as a positive regression control: T0 **26,764 pairwise, 26,700 coherent, 64 false chains**; T1 **26,637 pairwise, 26,637 coherent, zero false chains**.

## Entire individual-season sequences

Among **421** source-defined animal-season groups:

| Status | Full-day T0 | Near-midnight T1 |
|---|---:|---:|
| All adjacent pairs separately pass the possibility rule | 230 | 216 |
| A single globally coherent assignment across every record | 216 | 216 |
| **Every pair possible yet full sequence impossible** | **14** | **0** |
| At least one adjacent pair already impossible | 191 | 205 |

It would be incorrect to call these 14 groups observed failed migration routes: a source time interval is not a space-time trajectory, and the two valid-input assumptions are not known true clock histories. A group with an excluded 12.5-hour link also need not represent failed animal movement; the paper's own Brownian-bridge *data interval rule* is not a physical barrier.

**Independent mathematical control:** 2,500 small 2–5-record integer-window worlds were checked against explicit enumeration of all clock assignments and a discrete-state DP, agreeing with the propagated interval result in every case. A synthetic 4-record counterexample also verifies that even every contiguous **triple** may be feasible while the full 4-record sequence is not.

## Biological and methodological boundary

- This test uses a deterministic **source-blind T0 lower-bound ordering**, frozen in PR #748. Because date-only record order is uncertain, its sequence-level feasibility is conditional on that order. The earlier all-six-permutations analysis showed the 64 3-record false chains were ordering-invariant under T0 but **does not certify full-group order invariance**.
- The 10,835 date-only records still have unverified actual hours, Mountain Time daylight-saving transitions and no independently certified physical elapsed times. T1's zero false chains are **conditional**, not evidence that it is true.
- The original Dryad .prj and README declare EPSG:3742 although coordinates fit Albers-family EPSG:5070/5071; the actual author CRS and best NAD83-HARN transformation grid remain unresolved. No coordinates were needed for this *time-only* audit.
- No 2-hour withheld GPS, SHP point geometry, independent animal outcomes, EOG prediction score, or new empirical method-validation endpoint was used. Source QC remains on HOLD and EOG-WF remains exactly **3 scored (2 favorable, 1 adverse), 31 scientific STOPs, 3 administrative exclusions**.
- The analysis does **not** test ecological resistance, stepping-stone choice, real migration route, connectivity, BBMM prediction accuracy, model skill or out-of-sample generality.

## Reproduction

The [SHA-frozen local producer](replay_post_stop_global_time_windows.py) reads the exact original 12h ZIP in memory without exporting raw identifiers, timestamps or coordinates; it refuses different source bytes. The [offline tests](../../tests/test_mckee2024_global_time_window_coherence.py) lock source identity, record/window denominators, complete-sequence counts, the triple historical regression and the independent exact mathematical oracle. No raw GPS archive or individual-level table is stored in GitHub.
