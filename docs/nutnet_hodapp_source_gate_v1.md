# NutNet herbivore-exclusion / fertilisation candidate — source-only gate

## Scientific status and separation

**This is a candidate for independent experimental-response validation, not a completed test.** The original EOG × BAM geometric response-direction results (PR #702, post-exposure reclassification of PR #677) are synthetic and conditional on a finite 12-landscape universe. This gate does not reopen the frozen three-endpoint EOG-WF programme.

The separate 2024 Hungarian wetland-amphibian source is structurally useful but cannot support a genuine before–after test: there is one sampled year, no coordinates in its two published CSVs, and no pre-restoration community map. Further examination of the pinned `frogcs` source (commit `5e2f0a87c639df373fa2700b29403d2ab417a1cc`) showed that the two duplicated survey identifiers carry conflicting species counts, while `num` is an exact date-order index within each site×method rather than measured effort. Thus neither duplicate can be silently deleted and `num` must not be used as effort time. The original paper reports variable survey duration and trap counts. These observations do not license EOG causal evaluation.

## New external candidate

Hodapp et al. (2019), *Data from: Spatial heterogeneity in species composition constrains plant community responses to herbivory and fertilization*, Dryad DOI [10.5061/dryad.8vs569h](https://doi.org/10.5061/dryad.8vs569h), supporting Hodapp et al. (2018), *Ecology Letters* [10.1111/ele.13102](https://doi.org/10.1111/ele.13102).

Source catalogue advertises two files:
- `composition-data.csv` (plot × taxon × year since treatment, with percent cover);
- `env-param-Y0.csv` (plot-level environment **before** treatment).

The declared randomized-factorial treatment labels are Control, NPK (nutrients), Fence (herbivore exclusion), and NPK+Fence. Year 0 is before the first treatment. The source is from a geographically distributed grassland network. The observed result in the publication (higher compositional turnover after fertilisation and herbivore exclusion driven by replacement) is already public background knowledge; no analysis of new EOG response signs has been conducted.

### Why this is closer to the EOG target

An actual Fence treatment experimentally modifies a biotic process, unlike static `G=A∩B∩M` mask deletion. NPK modifies nutrient availability (an abiotic process). Experimental replicate treatments and a pretreatment baseline offer a route to independently assess **whether the sign of a declared ecological summary is predictable despite uncertainty in the underlying process model**.

However, **Fence is not literal removal of all B mechanisms**; NPK is not literal removal of A; dispersal constraints M are not measured. Even a successful out-of-site test would validate a treatment-specific response-sign prediction, **not** the exact mask-release theorem or full BAM mechanism recovery.

## Source-access status

This change freezes the metadata-only protocol **before original experiment response values are read**. `benchmarks/nutnet_hodapp_source_gate_v1.py` fetches only bounded API metadata JSON and returns a reproducible `SOURCE_METADATA_COMPLETE_BYTES_NOT_VERIFIED`, `MIRROR_PROVENANCE_UNVERIFIED` or fail-closed STOP. The Zenodo record 5023851 is *only a candidate mirror* until byte-level identity and source attribution are proven. Metadata success is not scientific success.

The gate **does not download, parse, score or expose** the treatment-time composition table. If an endpoint is inaccessible, that fact is retained. No fabricated file checksum, file ID, sample size, result, fitted effect or success status is inferred.

## Binding successor design (must be frozen before treatment response access)

1. Acquire exact source files and verify published version, checksums, rights and plot IDs. Inspect **source structure only**; preserve any data incompatibility as a STOP.
2. Verify sufficient independent sites, complete year-0 baseline, stable site/block/plot treatment labels, shared plot-level reference features, and enough within-treatment replicate plots for an estimable span. Classify missing vs actual zero cover.
3. Freeze an **independent-site holdout** and specific target: candidate is the sign of the Fence-minus-Control change in 90th-percentile *plot community-state distance* relative to Y0, in one shared feature reference fit only to training Y0. This is deliberately **not** an environmental niche-span response unless the inputs really are environmental coordinates. Specify years, ordination/features, coverage threshold, no-change tolerance, size matching and missing-data rules before seeing the outcome.
4. Declare the model-universe family using training sites only; issue a nonzero sign only if all admitted models agree. Evaluate on held-out sites: wrong-sign rate, coverage/abstention, calibration and baselines with independent site as the inferential unit.
5. If enough sites/plots or independent feature support is missing, **STOP** rather than tune a denominator or switch outcomes after reading treatment effects.

No new predictive result is claimed in this document. The extant synthetic PR #702 and EOG-WF endpoint count remain unchanged.
