# Genetic specific-origin versus EOG existential worlds: two-host + radius audit (v2)

**Status:** Frozen post-outcome same-archipelago *source-conditioned* exploratory analysis; direct genetic assignment is model-inferred, not tracked natal movement. The earlier EOG-WF prospective validation stays closed (3 scored / 31 scientific STOP / 3 administrative exclusions).

## Exactly what changed since PR #707

PR #707 joined 799 publisher-identical full-sib-family/destination rows against authenticated 2019 Åland patch/year survey data. Among 498 off-patch inferred assignments, 163 assignment rows (157 distinct families) with **100 distinct recorded-zero → recorded-positive target patch-years** had both (i) EOG-eligible prior-year recorded-positive assigned source and (ii) original EOG eligible target. Those remain the **identical and selected** units in the current analysis. Total eligible EOG targets for 2008–2012 remain 1,465; do not interpret 100 as a representative sample.

The previous comparison of assigned-source distances (target-equal median **1.211 km**) versus nearest-any-source distances (median **0.284 km**) did **not** require environmental matching to the assigned source. This v2 uses the exact EOG two-host *ordinal* gate, based on **Plantago and Veronica from the 2019 survey**, measured at `t−1` for both candidate source and destination. It must not substitute the separate `host.x/host.y` variables from the genetic family table.

## Source and reproducibility

The user-supplied DiLeo Dryad 2022 `fullsibfamLevelData.csv` is SHA256 `140e5361f9bced20a434bfee01bae6ce7c925e028718cdb9c6fd8aa635cc912a`. The 2019 Schulz Zenodo original survey archive is SHA256 `c70f43544f61e7273afebfa42ed1d488c3b945efe4d5c68e6557030087ee7fd9`.

A **new ephemeral RSA key** was generated locally, private key never sent to GitHub. One-shot [GitHub Actions 44655571491](https://github.com/zuizui0223/eog/actions/runs/44655571491) verified the original 2019 source bytes and emitted AES-256-GCM ciphertext only. Its published encrypted artifact has one-day retention; no identifiers were logged, and the locally decrypted source never entered the repository. The resulting local science JSON fingerprint without self-hash is `94ebcf0582361901a8aa847affad52beb42d68cb03ffeca9509e3891395d5f3a`. The original strict 2008–2012 source and target roster counts, 163/100 join units and prior target-equal medians were rechecked. An independent separate raw-data implementation reproduced **all eight** main EOG/assigned coverage combinations.

Artifacts:
- `validation/glanville_genetic_host_world_v2/protocol_v2.json` — frozen before source reacquisition;
- `validation/glanville_genetic_host_world_v2/frozen_aggregate_summary_v2.json` — durable counts, year tables and source fingerprints;
- `scripts/glanville_genetic_host_world_local_audit_v2.py` — local-only audit for original user file and locally decrypted source snapshot;
- `scripts/glanville_encrypt_survey_source_v2.py` — encrypted-only survey source reacquisition, with locked original archive identity.

## Two distinct questions, same 100 selected target patch-years

`EOG` asks whether **at least one** recorded-positive source in `t−1` lies within radius r and has max two-host score difference ≤δ. The source can be any of the eligible patches; this is a compatibility/existence witness, not an inferred historical source.

`Genetically assigned source` asks whether **at least one of the specific genetically inferred** earlier source assignments for each target patch-year meets exactly that same δ and r. All assigned sources used in the primary subset have recorded-positive source eligibility. Some destinations have multiple full-sib-family assignments, so **at-least-one** and **all** assigned origins are both reported; assignment rows are not treated as independent target-year replicates.

| Host gap δ | Maximum 1-hop radius | EOG any eligible source / 100 targets | ≥1 genetically assigned source / 100 | Every genetically assigned source / 100 |
|---|---:|---:|---:|---:|
| 0 | 2 km | 68 | 17 | 11 |
| 0 | 5 km | 83 | 21 | 15 |
| 1 | 2 km | 91 | 50 | 37 |
| 1 | 5 km | 98 | 65 | 46 |
| 2 | 2 km | 94 | 69 | 53 |
| 2 | 5 km | 100 | 87 | 77 |
| 3 | 2 km | 97 | 72 | 56 |
| 3 | 5 km | 100 | 93 | 86 |

Those counts are **conditional logical coverage**, not holdout predictive accuracy or a biological detection/dispersal-rate estimator. Monotonic increase when δ or r is relaxed is by construction. The source-specific/existential gap is partly mathematical: when multiple potential sources exist, the genetically assigned one need not be the nearest or satisfy the strictest environment gate.

## Host-score difference for the 163 selected assignment rows

The exact original two-host maximum ordinal gap at t−1 was:
- gap 0: 29 rows
- gap 1: 67 rows
- gap 2: 52 rows
- gap 3: 15 rows

At δ≤1, **96/163** original inferred source assignments are compatible in host scores regardless of radius; allowing r=2 km reduces to **75/163** assignments. EOG existential at the same δ=1 and r=2 km covers **91/100** targets, but only **50/100** have an eligible, genetically assigned source meeting both conditions. This is a measurable *difference in estimands* and source roster choice, not evidence that EOG “predicted a wrong dispersal”.

Across selected genetic records, there are 157 distinct family IDs in 163 destination rows. Across **all 799 original rows**, there are 760 families, 39 split across two destination patches; 21 split families show one same-patch and one off-patch assignment, 18 show two distinct off-patch destinations. In one split family the separately assigned portions have different inferred source labels. This is *possible under the paper's explicit method of assigning portions of one full-sib family sampled in different patches separately*, not proof of two actual natal populations or sample mislabeling. No per-assignment score is present in the uploaded table.

## Interpretation and next falsifiable step

DiLeo et al. (2022), DOI `10.1098/rspb.2022.0322`, reported GENECLASS2 Rannala–Mountain assignments to prior-year **sampled** reference patches; they applied an assignment score=100 filter and split multi-patch full-sib families before assignment. This reference-sampling restriction is not independent of the detection/availability problem. All real individuals were sampled from a selected subset of patches, with genetically inferred origin—not directly followed flight or natal proof.

To test a **nontrivial** mechanism, a future comparison should first freeze an explicit *opportunity-weighted source choice null*, not just EOG's existential minimum, and then ask whether assigned sources are closer or more host-similar than source opportunities at the same target-year. It must control for source sampling coverage, repeated families, geography, natal genetic assignment uncertainty and sampling-year state. Without that, `EOG any > assigned source` is conceptually expected and does not demonstrate selection or new predictive skill.

**EOG-WF prospective denominator unchanged: 3 / 31 / 3.**
