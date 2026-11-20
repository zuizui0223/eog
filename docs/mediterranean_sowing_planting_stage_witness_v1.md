# Mediterranean forest seed introduction × sapling transplantation: stage-specific viability witnesses

## Scope and pre-response chronology

**Post-exposure exploratory cross-stage audit — NOT a new EOG-WF endpoint or an independently blinded replication.** The original published result and the 61,000 sowing-seed rows had already been examined in [PR #709](https://github.com/zuizui0223/eog/pull/709). A separate, narrower contract was committed at `fee2041b2ef9aa09449b1c8538251ef5c92ca716` **before examining individual outcomes in the separate 299-row planting table**. Source: Acevedo-Limón et al., [Dryad 10.5061/dryad.t1g1jwtg3](https://doi.org/10.5061/dryad.t1g1jwtg3), author README and six original R analysis scripts.

**Question:** For a naturally absent species at a forest patch, does experimental introduction reveal survival after bypassing (i) natural propagule arrival with *seeds*, and (ii) both natural arrival and the initial seed-to-sapling stages with *transplanted saplings*? A positive observation is a stage-specific viability witness. An absence of positive records is **not** a certificate of impossibility or an identified historical dispersal mechanism.

## Reverified data / immutable parent quality boundary

- Exact original 2025-10-16 Dryad ZIP SHA-256: `e05646c628caed63c7f169a53c52e3977f5c11dff3f5d1b1d7e7e32bcd871e26`. Every one of 12 file hashes and sizes matches the independent authoritative provider manifest checked in by PR #709.
- Sowing experiment: 61,000 seed records, 40 species × patch combinations (20 naturally absent, 20 naturally present), 10 plant species and 10 forest patches. The **five ambiguous duplicated seed IDs** and entire 50-row paired station are quarantined exactly as in PR #709. The preregistered *complete* sowing-treatment analysis remains a source-quality **STOP**.
- Independent planting experiment: **299 planted saplings, four species, ten forest patches, 16 species × patch combinations**, including eight naturally absent and eight naturally present. `species × site × station × id` keys are distinct; all planting source `site_type` labels agree with the seed source. The 299 planting survival statuses are 0/1, with no missing values. **The planting table has no protected/unprotected treatment column.** It is not a second experimental estimate of the cage effect.

## Stage-specific direct evidence

Every count below is **species × patch**, not seeds or independent geographic replicates. Planting was only carried out for 4 of 10 species and 16 of 40 species × patch combinations, so 8/8 may not be generalized to 20/20. These outcomes have already been published by the data originators in their broader scientific interpretation.

| Witness in naturally absent species × patch | Observed positive / eligible |
|---|---:|
| At least one *unprotected sown seed* germinated | **20/20** |
| At least one unprotected sown seedling survived its first summer | **17/20** |
| At least one unprotected sown individual survived its second summer | **11/20** |
| At least one *transplanted sapling* survived its first summer | **8/8 planted combinations** |

Those eight naturally absent planted combinations span **7 forest patches**. At individual level, **97/152** planted saplings at naturally absent species × patch combinations had recorded first-summer survival. This is an observation, **not** a 152-independent-replicate inferential test. For natural-present planting combinations, 7/8 showed a survival witness, with 56/147 individual survivors. The two site-status classes differ in which patches and species they include; percentages must not be treated as a causal experiment of natural occupancy status.

Among the eight naturally absent species × patch combinations with both experiments:

- **7** have first-summer survival witnesses in both unprotected seed-sowing and planted-sapling experiments.
- **1** has a witness only after planting an already-developed sapling.
- **0** have a sowing-first-summer witness without a planting witness, and **0** lack both kinds of witness.

**Direct exception:** `myrtus_communis` in `algaida`. In the unprotected seed-sowing source, **51/500** seeds were recorded as germinated, but **0/51** of those germinants were recorded as surviving the first summer. In the separate transplant experiment, **1/14** planted saplings survived that summer. This contrast establishes survival after bypassing the initial seedling stage in at least one planted microsite; it does **not** explain the zero observed sown-seedling survival, establish a treatment effect between experiments, or imply natural recruitment/long-term population viability. The experiments differ in entry stage and potentially in conditions; `planting_experiment.csv` does not record fencing status.

## Mechanism versus response — defensible inference

An experimentally planted individual surviving at a naturally absent patch refutes an **absolute** claim that *no individual at the supplied life stage can survive in any tested planted microsite*. It does not tell us whether natural absence reflects dispersal/arrival history, seed fate, seasonal phenology, herbivory, soils, a rare demographic bottleneck, sampling/detection error, or lack of population-level persistence. A positive response establishes a **one-sided viability witness** despite unresolved mechanisms; absence of a positive does not establish the opposite.

Therefore this result is a stronger **life-stage resolution** of the previously observed presence/establishment mismatch, rather than a prospective demonstration that finite-world BAM target-sign certificates are general ecological predictions. It does **not** repair the original source anomaly or increase the EOG-WF frozen three-endpoint count. The NutNet out-of-site result (2 correct, 1 wrong, 5 abstain among eight) remains unchanged.

## Reproduce / integrity checks

```bash
python benchmarks/mediterranean_sowing_planting_stage_witness_v1.py \
  --source-zip doi_10_5061_dryad_t1g1jwtg3__v20251016.zip \
  --official-manifest validation/mediterranean_sowing_uploaded_archive_v1/official_manifest.json \
  --parent-receipt validation/mediterranean_sowing_uploaded_archive_v1/result_receipt.json \
  --output-dir /tmp/eog_stage_witness_v1
python -m pytest -q tests/test_mediterranean_sowing_planting_stage_witness_v1.py
```

The script fails closed on changed ZIP digest, any mismatch to all 12 official file checksums, changes to the parent PR #709 sowing witness result, missing/duplicate planting IDs, unexpected survival codes or species/site-status inconsistency. It quarantines the unchanged anomalous seed station before computing sowing witnesses. A separately written pandas group-by audit matched **40/40** species × patch stage cells, all 16 planted-combination survival flags, and all individual transplant counts. CI on GitHub can test synthetic fixtures and byte-preserved **derived** results; it cannot re-download the original 9.4 MB raw dataset without working provider credentials or a supplied archive. Thus green CI is not misrepresented as an independent re-download or field validation.