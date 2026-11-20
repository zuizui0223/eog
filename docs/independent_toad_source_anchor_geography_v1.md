# Independent toad translocation: capture-versus-release source-anchor geography (v1)

> **結果状態（2026-11-20）：`STOP_GEO_UNIT_CONCORDANCE`、事前H1は未評価。** 原データ165行の検査で `release-final` 距離列が幾何学的座標と一致せず、試験は科学的STOPで終了。後続の[事後source-QC v2](independent_toad_geocoordinate_diagnostic_v2.md)でも `capture-final` 163/163一致に対し `release-final` は77/163一致のみ。18種の事前明示的比較は元STOPの再解釈・結果修理・独立field confirmationではない。 [凍結した診断集計](../validation/independent_toad_geocoordinate_diagnostic_v2/frozen_aggregate_summary_v2.json)。


**Status at protocol freeze: research-only, one external experimental movement dataset; event response not yet opened.** [Pre-outcome frozen protocol](../validation/independent_toad_source_anchor_geography_v1/protocol_v1.json) was committed as the first branch commit (`d6e67a56d85bc6cf05b784d2f52b4914508c19f0`) before the toad individual's displacement/re-encounter values were read. This test is **not** natural founder/colonization, not geographical×environment×barrier Pareto mechanism identification, and not a new EOG-WF scored endpoint.

## Why this is an independent data source

The previous [Glanville MRR analysis](result_inventory/MINIMUM_REQUIRED_RELAXATION_AUDIT_20261120.md) used hypothetical compatible neighboring source patches. Even genetically **inferred** origins were not actual tracked movement. Here the [published Jreidini & Green toad experiment](https://doi.org/10.5061/dryad.x3ffbg7ms) measured explicit initial capture coordinates `I`, experimental release coordinates `R`, and later re-encounter coordinates `F`. The experimental release site is a *known observation anchor*, not a natural founder.

The source-only [publisher SHA check](independent_movement_source_gate_v2.md) qualified official Dryad version `198534`, 18,702-byte comma-delimited CSV with 165 rows, verified SHA256 `c8ee049eb807af31660ffa28e11f6a66b07a85a5dda4e756bb1b06610edb3f17`. Only original headers and row counts were accessed in that gate, **not** movement outcomes.

## Frozen estimand and comparators

For a single toad's experimental recapture:

```text
d_IR = sqrt((I_E-R_E)^2+(I_N-R_N)^2)   # experimental displacement
d_RF = sqrt((R_E-F_E)^2+(R_N-F_N)^2)   # known recent release -> recapture
d_IF = sqrt((I_E-F_E)^2+(I_N-F_N)^2)   # earlier capture -> recapture

r_release = d_RF
r_historical_capture = d_IF
r_possible = min(r_release,r_historical_capture)
r_source_robust = max(r_release,r_historical_capture)
anchor_uncertainty_width = |r_release-r_historical_capture|

Delta = d_RF-d_IF.
```

The **primary predeclared biological direction H1** is mean individual-weighted `Delta>0` for **toads relocated at least 90 m** with both location triples and a recapture date. Positive means the recaptured animal lies farther from the actual release site than from its earlier capture site—consistent with post-release return/home-oriented displacement. If mean Delta≤0, report a refutation/non-support. This directional biological behavior is already discussed by the original publication and should **not** be presented as a new behavior discovery or causal effect of EOG.

The **MRR consequence** of either sign is exact geometry: assuming the *wrong* source changes the minimum necessary one-hop geographical radius. For declared radii **100, 250, 500m**, group by distinct `Toad ID`, average every eligible observation for that ID, and report counts where release-source/historical-capture-source/possible/robust are within radius; also the two mutually exclusive false-assurance directions. The *mathematical* inequality `r_possible ≤ r_robust` and `|d_RF-d_IF| ≤ d_IR` are triangle/set definitions, not new ecology.

## Frozen quality and eligibility

- **Original record denominator:** exactly 165 publisher CSV data rows; SHA256 and bytes must match before analyzing.
- **Physical coordinates:** `Initial Easting/Northing`, `Released Easting/Northing`, `Final Easting/Northing`. Compute planar distances; check archived `Distance release-final (m)` and `Distance capture-final (m)` columns under predeclared tolerance max(2 m, 5% of recomputed distance). If either channel has less than 95% match, **STOP_GEO_UNIT_CONCORDANCE**—no result-dependent unit repair.
- **Observation grain:** require `Date of re-encounter` nonempty, nonmissing complete coordinate triple and Toad ID. Remove only **byte-identical** duplicated source CSV lines. All other recurring individual IDs are clustered; each ID receives one equal weight after its eligible events are averaged.
- **Fixed displacement groups:** relocated `d_IR≥90m`, sham `d_IR≤5m`, intermediate `5<d_IR<90m` retained descriptively. Require ≥20 unique relocated IDs for H1 scoring or stop.
- **No event selection by outcome:** directions, position relative to prior home, release-recapture distance and recapture success are not selection criteria beyond original eligibility. The dataset includes *recorded re-encounters only*; missing recaptures cannot be interpreted as absence, failure or emigration.
- **No private records in output:** aggregate counts, mean/median effect summaries, declared radius table and numeric quality diagnostics only. No original Toad ID, coordinates, dates, event-level values or published ZIP uploaded/committed.

## Evidence interpretation and hard boundary

This experiment answers **whether swapping the source anchor between a known experimental release location and a historical capture location can reverse geometric distance feasibility for a directly observed individual recapture**.

It cannot establish natural metapopulation colonization, real founder ancestry, how environmental/biotic/barrier constraints were crossed, time-varying SDM prediction, or the scientific novelty of this species' known homing behavior. A test failure in source verification, coordinate unit adequacy or sample size is a **STOP**, not evidence against EOG or the published biology. The apparent source-robust/possible difference is a deterministic comparison of two predeclared *spatial anchors*, not a posterior probability of either source.

In particular, **three-axis EOG minimum-constraint-relaxation remains untested** in this independent experiment; the study has no independently qualified habitat-edge environmental/barrier transition graph. The experiment tests only a **geographical source declaration** and the consequences of interpreting the wrong anchor.

## Reproduce without storing biological original records

```bash
python -m pip install -e . pytest
python -m pytest -q tests/test_independent_toad_source_anchor_geography_v1.py
python -m benchmarks.independent_toad_source_anchor_geography_v1 \
  --protocol validation/independent_toad_source_anchor_geography_v1/protocol_v1.json \
  --output results/independent_toad_source_anchor_geography_v1/result.json
```

The dedicated [GitHub Actions source-gated workflow](../.github/workflows/eog-independent-toad-source-anchor-v1.yml) intentionally only triggers on the frozen protocol, implementation, test and workflow, *not* on this narrative or future aggregate receipt. The EOG-WF empirical denominator remains **3 scored / 31 scientific STOP / 3 administrative exclusions**.
