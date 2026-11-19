# Glanville genetic assignment → EOG observed-transition crosswalk (exploratory)

## Outcome and source identity

**Source-qualified matching succeeded.** The user-uploaded `fullsibfamLevelData.csv` is byte-identical to Dryad published version ID 181375 (SHA-256 `140e5361f9bced20a434bfee01bae6ce7c925e028718cdb9c6fd8aa635cc912a`, 137,353 bytes). Its 799 family-patch assignment rows span five 2007→2008 through 2011→2012 year transitions and include exact `YearFrom`, `YearTo`, `PatchFrom`, `PatchTo`, `fullsibfam`, `dispersalBin`, `dispersalDistance` columns. All rows obey `YearTo=YearFrom+1`, zero distance only for same-patch assignments and the `dispersalBin` coding. There are **498 off-patch assignments, 301 same-patch assignments, 760 distinct full-sib-family IDs and 39 families split into two destination-patch rows**.

The original 2019 Schulz survey archive (Zenodo 4987060, SHA-256 `c70f43544f61e7273afebfa42ed1d488c3b945efe4d5c68e6557030087ee7fd9`) was reacquired and authenticated **once** on GitHub Actions [run 44547980619](https://github.com/zuizui0223/eog/actions/runs/44547980619). It contains **22,406** 2007–2012 patch×year survey observations and **4,656** patch coordinates. To protect site-level evidence, the runner published **only an AES-256-GCM ciphertext** encrypted under an ephemeral local-only RSA public key; private key never entered GitHub. No raw rows or patch IDs appear in Git or the Actions artifact.

The user file and encrypted source were decrypted/joined **locally only** on exact integer patch/year keys; no fuzzy matching. Full aggregate-only result is independently fingerprinted:
- `d8e70dc87e3ce6728827823bc28106757b6fcae3327727e72f92ed30e2d7be2e` (SHA-256 of canonical JSON excluding its self-hash).
- SHA-256 of full local audit JSON `79d61462336e6a5ccccc6c958fcf5c415f2fc790d44d224caf4895ff6c807fce`.
- Public subset retained here: `validation/glanville_uploaded_origin_crosswalk_v1/frozen_aggregate_summary_v1.json`.

An independent vectorized pandas left-join independently reproduced key counts, target overlap and network-distance discrepancy; this secondary check did not reuse the local EOG candidate-roster helper. The original EOG 2008–2012 source/target eligibility counts were also reproduced **exactly** on the re-acquired 2019 patch/year survey.

## Key result: exact origin/destination time joins

Among all 799 published family-patch assignment rows:

| Survey match / transition | Assigned rows |
|---|---:|
| Source `(YearFrom, PatchFrom)` survey record present | 793 |
| Target `(YearFrom, PatchTo)` prior-year survey record present | 791 |
| Target `(YearTo, PatchTo)` arrival-year survey record present | 797 |
| **All three exact patch×year records present** | **783** |

Among the **498 off-patch genetic assignments**:
- **475** assigned source patches were eligible previous-year *recorded-positive* EOG sources (with complete host information and spatial centroid).
- **17** assigned sources were **recorded zero** in the Schulz survey at `YearFrom`; **6** had no corresponding survey patch×year row. The genetic origin in those 23 is not independently established as true occupancy; differences may reflect survey detection, reference sampling, year/visit definitions or genetically assigned source uncertainty.
- **172** assignment rows landed on EOG's complete eligible *recorded-zero at t−1 → recorded-positive at t* destination transitions, representing only **103 distinct destination patch×year targets**.
- **163** assigned movement rows both reached EOG-eligible targets and had EOG-eligible previous-year positive assigned sources; they represent **100 distinct destination patch×year targets**.
- The complete original EOG eligible destination denominator for 2008–2012 is **1,465 patch×year targets**. This genetically assigned subset is **selected and sparse**; 103/1,465, not a representative independent panel.

### Original EOG target and source rosters re-established from source bytes

| Target year | EOG eligible recorded 0→positive patch-years | EOG previous-year eligible recorded-positive sources | Distinct eligible targets receiving a genetic assignment |
|---|---:|---:|---:|
| 2008 | 157 | 695 | 5 |
| 2009 | 285 | 508 | 16 |
| 2010 | 102 | 587 | 9 |
| 2011 | 521 | 298 | 50 |
| 2012 | 400 | 764 | 23 |

All five EOG source/target roster pairs match the previously frozen EOG empirical v2 result. The genetic assignment counts must **not** replace EOG's full observation denominator or be treated as 1,814 independent assignment tests.

## Geographical cross-check and distinct estimands

All **498 off-patch** genetic assignments have both site centroids in the earlier 2019 mapped network. The absolute difference between the genetic CSV's assigned `dispersalDistance` and an independent Euclidean distance using published 2019 patch x/y coordinates (original README units: kilometers) is:

- median **0.0000378 km** (0.038 m)
- q95 **0.001259 km** (1.26 m)
- maximum **0.04337 km** (43.37 m).

This is strong evidence that the patch identifiers refer to the same mapped system, **not** proof that an individual butterfly flew the assigned straight-line route.

On the 163 genetic assignments with an EOG-eligible source **and** target, the median genetically **assigned-source** distance is **1.177 km**, versus median distance to the **nearest eligible observed-positive EOG source** of **0.284 km**, on precisely that same selected subset. In **66/163** rows the assigned distance exceeds the minimum by more than 1 km.

These different measures should not be substituted for each other:
- EOG `min_source_distance` is an **existential lower bound** over a wide candidate source roster: at least one source could explain a target.
- The genetically assigned origin is **one inferred source** selected from previous-year sampled reference patches; it can be farther away than the nearest potentially compatible source, **without contradicting EOG**.
- We did NOT reconstruct a new movement kernel, fit a false-negative model, estimate true natal origins or certify barrier crossings.

## Source ascertainment / observation limits

DiLeo et al. (2022; DOI `10.1098/rspb.2022.0322`) used a GENECLASS2 assignment test conditioned on prior-year reference sampling and reported only treating score-100 assignments as true. The uploaded CSV does **not** contain an assignment-score column, so that confidence filter cannot be independently evaluated per row. Assigned families were not an unbiased random sample of all EOG patch transitions, and 39 family IDs occur in two destination-patch rows.

The 2019 source reports annual patch observations, **not** patch-specific repeated-visit detection histories. A `YearFrom` recorded zero does not establish that a candidate source was truly empty; nor does a genetic model-assigned source establish true earlier occupancy, natal location or direction beyond its model assumptions. Both alternatives remain unresolved.

## Scientific contribution and next independent gate

The previous EOG conditionally minimal radius and source roster can now be compared to **authenticated genetic-origin assignments at exact patch-year grain**, a first concrete cross-source agreement test. The robust new finding is **model identifiability and source ascertainment**: 475/498 assigned off-patch origins are within the old observed-positive source roster; 23/498 are not documented positive there; multiple genetically assigned origins are farther than the nearest allowed EOG candidate.

Future confirmation needs individually verified GENECLASS2 origin assignment quality / reference-sample calibration and repeated visit detection or direct direction-resolving mark-recapture. Do not report the 17 recorded-zero origins as confirmed false negatives, do not claim 498 observed dispersal events, and do not call this historical source overlap a new EOG-WF prospective endpoint.

Original frozen EOG-WF denominator remains **3 scored / 31 scientific STOP / 3 administrative exclusions**.
