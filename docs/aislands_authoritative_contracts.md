# A-Islands authoritative pre-outcome contracts

The confirmatory A-Islands benchmark uses the earliest merged pre-outcome contracts as authoritative. Later experimental protocol files that conflicted with them have been removed before any species-level benchmark outcome was computed.

Authoritative order:

1. `validation/aislands_preoutcome_20260808/freeze_manifest.json` — source, 842-island survey universe, and 886 APC-native taxa.
2. `validation/aislands_model_contract_20260808/support_model_contract.json` — five CHELSA predictors (`bio01`, `bio05`, `bio06`, `bio12`, `bio15`), direct centroid extraction, deterministic L2 logistic regression with no class weighting, and the shared five-fold 5-degree spatial partition.
3. `validation/aislands_reachability_contract_20260808/reachability_contract.json` — the 12 predeclared island-chain scenarios and the conditional reachability concordance, conditioning on pointwise support and nearest-training-presence distance.
4. `validation/aislands_chelsa_20260808/climate_freeze_manifest.json` — exact direct-centroid CHELSA artifact, with accepted CSV SHA-256 `6ae7f4a78eea28f074ef3c3399368a4886b09d2d0714e723e957d0a99b524285`.

The A-Islands execution must use `src/eog/support_model.py`, `src/eog/island_reachability.py`, and `src/eog/conditional_reachability.py`. It must not substitute a taxon-stratified 10-fold split, class-balanced support model, k-nearest bridge protocol, or a different climate variable set.

This cleanup was made before any 886-taxon support, reachability, or held-out performance outcome was inspected. Future changes to the confirmatory contract require a separately labelled sensitivity analysis and cannot replace the primary result after outcomes are known.
