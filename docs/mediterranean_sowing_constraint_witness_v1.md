# Mediterranean forest sowing: independent A/B/M-analogue source qualification

## Independent source and intended task

Acevedo-Limón, L., Rumeu, B., Linares, M. & González-Varo, J. P. (2026), *Uncovering biodiversity deficits: Experimental evidence for dispersal limitation of woody species in Mediterranean forest patches*, *Journal of Applied Ecology*, DOI https://doi.org/10.1111/1365-2664.70207; original Dryad DOI https://doi.org/10.5061/dryad.t1g1jwtg3, published 2025-10-16.

The published design uses ten woody species, ten forest patches, 61,000 introduced seeds in 1,108 sowing stations (554 protected and 554 unprotected), across two sowing years for a subset of species. The authors already reported similar mean establishment in naturally occupied and unoccupied forest patches. That known paper result is **not** a novel EOG prediction.

## Why this experiment follows the existing EOG result

The synthetic EOG × BAM study identified signs within a finite artificial model universe. The independent NutNet Y3 heldout analogue found 2 correct, 1 wrong and 5 abstentions (8 holdout sites); it did not beat a simple training-mean baseline. Its result stays frozen and will not be tuned.

Experimentally sown seeds bypass *natural arrival* for those seeds. Physical protection alters vertebrate granivore/herbivore exposure. Abiotic soil and moisture variables are measured. This supports testing **stage-specific actual response constraints**, not labeling fitted model agreement as ecological mechanism identification.

## Fixed targets before original data-row access

The primary signed target is a **germination proportion** contrast, protected minus unprotected, comparing the two sowing stations in each experiment plot and averaging equal physical station-pair weights within species × site × sowing year. Sign tolerance is a predeclared ±0.025; the middle category is operationally near-zero, not statistical non-significance. First-summer establishment is secondary and must be derived from the documented monitoring subset (only the earliest germinated individual per position was monitored for some species), not fabricated from unmonitored seeds.

A genuine establishment event in a naturally absent patch contradicts a *strict impossibility of establishment* for that planted microsite and life stage. It does **not** prove that natural absence was caused by dispersal limitation; protection could be important and natural arrival was not measured. Zero observed success is **not** proof of habitat impossibility.

Primary units: sowing stations nested within experimental plots, species and forest patches. Highest geographically independent unit is a forest patch (ten total), **not** 61,000 individually independent seeds. Site-type is an observed natural species presence/absence designation, without detection model. Cage-induced microclimate is a competing explanation. Neither complete A/B/M mask identification nor full physiological niche or long-term population persistence is claimed.

The official scientific contract, estimand and fail-closed conditions were committed **before** reading original sowing outcome rows: [protocol](../validation/mediterranean_sowing_constraint_witness_v1/protocol.json).

## Source gate (this PR)

Run:

    python -m pytest -q tests/test_mediterranean_sowing_source_gate_v1.py
    python benchmarks/mediterranean_sowing_source_gate_v1.py --output-dir /tmp/eog_med_sowing

The gate retrieves only official Dryad JSON metadata and fixed source files, requires authoritative positive byte sizes and MD5/SHA256 digests, and checks exact bytes. Its reported source evidence contains only file headers, counts of zero response scores and file hashes; it does **not** inspect or summarize treatment outcome rows. It may legitimately return SOURCE_STOP even if GitHub Actions itself passes. An unverified mirror is never a substitute.

After successful source-byte verification, the next action is a separate frozen schema/eligibility and stage-response analysis with transparent nonidentification. No fourth EOG-WF endpoint is authorized; the published response and existing negative NutNet study remain unchanged.
