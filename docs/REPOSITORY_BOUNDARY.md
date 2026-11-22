# EOG repository scope and study handoffs — 2026-11-22

**Owner:** EOG is a *mathematical inference / methods / benchmarking* repository. Biological results belong to a biological project repository; do not keep a separate EOG biology paper as the active source of truth.

## Ownership and provenance

| Line | Canonical owner | EOG retained role | Strong claims disallowed |
|---|---|---|---|
| Fungal/grassland experimental history v27–v38 | [KNK](https://github.com/zuizui0223/knk) | Reusable `src/eog/history_retention.py` statistical formulas/tests | Treating v31–v38 as independent experiments, restoring refuted v32 mechanism |
| NEON small mammals / old 16-site continuity study | [neon](https://github.com/zuizui0223/neon) | Generic metacommunity graph/frozen audit and historical null-ceiling *method* diagnosis | Promoting old 13/16 as established robust biological redundancy, or submitting obsolete Oikos paper |
| A-Islands, Tanzania, other structural comparators | [Structural](https://github.com/zuizui0223/Structural) for structural programme; original frozen EOG results remain method evidence | Benchmarking added value vs strong baseline and source history | Universal superior reachability or ecological colonization inference |
| EOG-WF Azores eel, Louisiana rail, Tampa seagrass | EOG method programme (3 prospective endpoints) | Real-data methodological performance, including negative control | Pooling 2 favorable + 1 adverse into universal predictor superiority |
| Known-truth BAM, world sets, MRR Pareto | EOG | Exact estimands, finite-world proofs, synthetic identification and comparator tests | Extrapolating simulated fractions as field population rates |

## NEON provenance and no-promotion

Original EOG source SHA: `91240104f9816459cd9555a63555664aff60760b`. The canonical NEON archive copied **80/80 Git blobs and exact byte sizes** under `archive/eog_legacy_neon_20261122` and has a source manifest with integrity workflow. The original 48 biological manuscript files, paper-specific CI and tests are removed from EOG's active tree; old Markdown links are redirected to their original archive paths.

**Why not a biological positive?** The historical observed best-species survival was saturated at all 16 sites. Independently, the current NEON mammal-ecology audit reports 93/94 adjacency worlds connecting all same-grid trap pairs, 26/27 sites saturated already at the smallest threshold, and carrier turnover not exceeding the species-pool-conditioned null (p=0.7568). NEON is now at `SUBMISSION HOLD`, redesigning individual-based space use with capture–recapture and sampling effort. The old endpoint is retained for mathematical ceiling tests only.

## Change rule

1. Never modify original frozen protocols/result fingerprints just to make a favourable new conclusion.
2. Preserve source Git blob SHA receipts and old workflow logs before cleanup.
3. Place biological manuscripts and interpretive updates in their canonical biological repository, not EOG.
4. Keep generic method implementation and reproducible method examples in EOG if required for checks.
5. An original study's methodological diagnostic result is **not** a new EOG-WF prospective scored endpoint; its denominator remains **3 scored / 31 scientific STOPs / 3 administrative exclusions**.

**Remaining legacy evidence in EOG:** biological source-specific stress data and *structural method benchmark* scripts/receipts remain where required to regenerate benchmark provenance. Stand-alone Structural manuscript/figure/test assets are no longer EOG authoring assets and are archived or canonical in Structural. [External NEON archive](https://github.com/zuizui0223/neon/tree/main/archive/eog_legacy_neon_20261122) and [KNK](https://github.com/zuizui0223/knk) contain their respective biological-study sources of truth.

## Automated scope regression (2026-11-22)

The package test suite now runs `tests/test_repository_scope.py` using
`docs/REPOSITORY_SCOPE_POLICY_V1.json`. This checks that EOG keeps the
generic mathematical core, retains the frozen 3-endpoint method evidence,
and does **not** silently restore KNK's or neon's migrated biological
manuscript/protocol lanes. The legacy neon manuscript paths may contain
link-only archival stubs, never new biology findings or active Oikos assets.

The check does not validate biological inference, run external scores,
or change the original frozen result fingerprints. Any new methodological
manuscript directory requires an explicit policy update and review.

## Structural paper provenance and retirement (2026-11-22)

Structural standalone paper assets were inventoried from EOG source tree `c9ba38785e42ecfdcae9256e5792fb8b32ea2b77` and matched against [Structural's 89-file handoff](https://github.com/zuizui0223/Structural/blob/main/archive/eog_structural_legacy_20261122/SOURCE_MANIFEST.json): **70 preexisting exact Git blob matches** plus **19 historically divergent/missing assets archived unchanged** in Structural. No active Structural files were overwritten. EOG's duplicate paper manuscript (40 files), paper-only figures (33), and paper-specific tests (16) are retired from its active tree, with Markdown path redirects for external links.

**Scientific boundary:** A-Islands original constrained graph concordance was 0.6177466, but an adequately strong reference gave an **adverse** added log-loss difference `C-R3=+0.0034852` (95% CI +0.0024664 to +0.0045082); Tanzania's strong-reference heldout result was adverse as well. EOG retains these as *method sensitivity/benchmark controls*; scientific ecological interpretation and new work belong to Structural. Do not count A-Islands/Tanzania as fourth and fifth independent EOG-WF endpoints.
