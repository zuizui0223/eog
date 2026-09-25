# Data and code availability draft

## Data

The empirical validation uses the NSF National Ecological Observatory Network (NEON)
**Small mammal box trapping** data product, DP1.10072.001, RELEASE-2026. The NEON release
citation reports DOI **10.48443/A83H-TB34**.

The confirmatory programme used a fixed set of 16 NEON sites and a once-only authenticated
query. The repository does not redistribute the downloaded NEON response files. Instead,
it records the frozen query contract, source release, selected file checksums, response
consumption receipt, site-level terminal results and the immutable programme closure
needed to reproduce the analysis from the authoritative NEON source.

## Code

Analysis code, validation contracts, tests, frozen result records and deterministic
manuscript-asset builders are maintained in the public EOG repository:

https://github.com/zuizui0223/eog

The canonical files for this manuscript are under:

- src/eog/v2/world_survival_identifiability.py
- validation/world_survival_regime_v2/
- manuscript/world_survival_identifiability/

Before submission, this manuscript lane should be archived at a permanent release/DOI and
the exact archived identifier inserted here.

## Reproducibility boundary

Seven fixed NEON sites terminated after response consumption because target-positive rows
contained trap coordinates outside the frozen response-blind node registry. Those sites
are preserved as integrity stops and are not repaired or reassigned a biological regime.
The nine scored sites and all reported manuscript numbers are generated from the frozen
v2.3 response lock.
