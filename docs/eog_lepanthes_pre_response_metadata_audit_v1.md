# EOG *Lepanthes rupestris* external validation — pre-response metadata audit v1

**Decision: `STOP_REGISTRY_SCHEMA_AND_DETECTION_UNQUALIFIED`, within this declared evidence contract.**

**Stage:** descriptive source/publication metadata only. We have **not** downloaded `lepa_all.csv`, opened any plant occurrence row, fit a model, computed any source-loss event, or scored an ecological hypothesis in this audit. This is **not** a finding that the Dryad dataset is defective, that the published conclusions are false, or that the species lacks metapopulation structure.

**Canonical frozen description:** `validation/eog_virtual_world_ecology_synthesis_v1/lepanthes_pre_response_catalog_v1.json`

**Deterministic gate:** `scripts/audit_lepanthes_pre_response_metadata_v1.py`. The script accepts a local metadata JSON only, validates both public dictionaries and the frozen STOP, and writes a machine-readable receipt; it has no download or focal response-reading interface.

## 1. Verifiable source metadata

- [Dryad deposit](https://datadryad.org/dataset/doi%3A10.5061/dryad.9p8cz8wc6), **DOI 10.5061/dryad.9p8cz8wc6**, publication dated 21 January 2020. The landing page advertises one file, `lepa_all.csv`, approximately 84.83 KB, and describes a permanent **975-phorophyte** survey in Puerto Rico over **1999–2008**.
- [Public derivative R documentation](https://rdrr.io/github/andrewmarx/ecodata/man/lepanthes_rupestris.html) describes a **975-row, 23-variable** data frame derived from the same deposit; this is a *separate descriptive dictionary*, not verification of the Dryad CSV's physical header.
- [Acevedo et al. (2020), *Journal of Ecology*, DOI 10.1111/1365-2745.13361](https://doi.org/10.1111/1365-2745.13361) compares **290 dynamic occupancy models** with asymmetric wind-dependent connectivity, habitat/climate covariates and detection probability. The article estimates detection probabilities of approximately **0.85–0.99**, but these are **model-based estimates**, not independent known-state detection calibration.
- [Previous asymmetric-connectivity analysis](https://pubmed.ncbi.nlm.nih.gov/26054613/) had already shown the value of accounting for directional dispersal in this same metapopulation. EOG cannot relabel asymmetric connectivity itself as a new biological finding.

## 2. The published schema is not a verified physical schema

Two public dictionaries refer to the same resource but have **four exact-name disagreements**:

| Semantic coordinate / visit | Dryad usage note | Derivative R dictionary |
|---|---|---|
| horizontal X | `x.coord.` | `x.coord` |
| horizontal Y | `y.coord.` | `y.coord` |
| vertical Z | `z.coordinate` | `z.coord` |
| second survey of 2004 | `X7104` | `X71704` |

These differences may result from import-time name transformations, a typo, or another representation step; **the physical CSV header was not read**, so the cause is unknown. Automatically treating either dictionary as ground truth would be post hoc schema repair. The source file's immutable version identifier and physical checksum were also not independently obtained.

The metadata list **17 survey columns in 10 years**, not an independent two-visit register for every year:

| Year | Published visit columns |
|---|---|
| 1999 | `X70199` |
| 2000 | `X20100`, `X80100` |
| 2001 | `X10101`, `X60101` |
| 2002 | `X10102`, `X60102`, `X120202` |
| 2003 | `X61003` |
| 2004 | `X12404`, `X7104` (Dryad label) |
| 2005 | `X12205`, `X91705` |
| 2006 | `X72406` |
| 2007 | `X20307`, `X61507` |
| 2008 | `X10208` |

This is **a column inventory, not an empirical completeness audit**. Four years (1999, 2003, 2006, 2008) have one advertised survey column. No occupancy value, missing-data code or patch-level opportunity/effort status was examined.

## 3. Why the v1 gate stops

| Gate | Current metadata-level result |
|---|---|
| Dataset DOI, species, advertised file, prior publication | **Identified** |
| Immutable Dryad file/version ID plus independent file checksum | **Unverified** |
| Actual CSV header independent of biological rows | **Unverified** |
| Four dictionary inconsistencies reconciled from independently observed header | **Unverified** |
| Separate response-independent patch registry and physical coordinate orientation/units | **Unverified** |
| Patch-specific visit opportunities, missingness and surveyed-negative semantics | **Unverified** |
| Detection model/independent calibration adequate for the proposed future negative-state inference | **Unverified** |
| Dated source removal / turnover event distinguishable from simple nondetection | **Unverified** |

The Dryad landing page advertises a **single combined CSV** with patch attributes and survey outcomes. This does **not** demonstrate that an independently versioned patch/opportunity registry is publicly available. It also does not prove such a register could never be obtained from the original investigators or another permitted release.

**The v1 protocol therefore stops before exposing the response file.** A future attempt must declare a newly frozen source/registry/observation process contract, rather than silently changing these gates after looking at responses.

## 4. What a valid future external test would require

A true test of the virtual source-layout hypothesis must measure *ecological outcomes*, not only graph reachability:

1. **Source and opportunity qualification.** Independently verify source/version and physical header; obtain a response-independent patch registry, physical coordinate orientation/unit contract and independent list of offered visits.
2. **Observation process.** Define patch-level missing survey versus observed nondetection, and estimate or otherwise qualify detection from admissible repeated visits. A one-visit year must not become perfect observed absence.
3. **Temporal leakage firewall.** Freeze training/heldout years before reading response rows. Wind years **1999, 2000 and 2005** were imputed using a whole-period average in the source study; any truly heldout design must avoid leaking future wind values into predictors. Connectivity constructed with source-patch occupancy must use only the permitted *past* occupation state.
4. **Strong baseline.** Explicitly compare with the published-style dynamic occupancy model using wind/asymmetric connectivity, moss area, phorophyte type, temperature, rainfall, and detection, as well as established network-redundancy measures. Do not compete only against Euclidean distance or an SDM raster.
5. **New EOG claim only after passage.** Ask whether frozen source overlap/redundancy predicts *heldout observed recolonization following identifiable local source loss* beyond the baseline. Natural turnover is observational; do not infer randomized removal or fitness benefit from it. Use the published result as prior art, not independent new confirmation.

**Status:** `STOP_WITHIN_DECLARED_PRE_RESPONSE_GATE`. No third paper is promoted, and none of the frozen v10–v26 results or the closed EOG-WF empirical denominator is reclassified.

## 5. Reproduction

```bash
python scripts/audit_lepanthes_pre_response_metadata_v1.py \
  --output build/lepanthes_metadata_gate_v1.json

python -m pytest -q tests/test_lepanthes_pre_response_metadata_v1.py
```

The JSON receipt reports the declared STOP and seven unmet source/observation gates. This test does **not** download, decode, query, or access any response-bearing `lepa_all.csv` payload.
