# Mt Gibson phascogale fresh paired complementarity attempt

This directory freezes one fresh temporal test of EOG Layer B in the 70-site
annual camera survey of reintroduced red-tailed phascogales (*Phascogale
calura*) at Mt Gibson Wildlife Sanctuary. It is candidate-specific validation
infrastructure, not a new ecological operator and not an API/CLI change.

Dryad version `303436` contains six independently stored objects. Preflight uses
the official version redirect and tokenized file manifest, keeps signed URLs only
in memory, and downloads only `README.md`,
`Camera_survey_site_location_data.csv`, and
`Camera_survey_deployment_data.csv`. It verifies the physical
`Camera_survey_detection_data.csv` header with 27 one-byte Range requests and
stops at the first CR. No response row or value is opened. The ancillary
arboreal-capture response and the assembled whole-version ZIP remain unopened.

The endpoint is observed annual camera-detection reappearance: a deployed site
has no released detection date in campaign *t* and either remains undetected or
has at least one detection date in *t+1*. This is not latent occupancy, physical
immigration, parentage, or a reconstructed colonization history. All 70 sites
have response-independent deployment effort in every 2018–2024 campaign.

Managed releases occurred in 2017–2019. The frozen claim starts in 2020: the
2020→2021 and 2021→2022 transitions are calibration; 2022→2023 and 2023→2024
are held out and scored by target campaign. Published materials do not provide
split-specific observed transition counts, so preflight preserves
`uncertain_pre_response` and authorizes only an exact-count-first once-only run.
Count failure means zero model fits and zero heldout scores.

The primary contrast is a strong frozen random forest with campaign, UTM
geometry, survey effort, conventional source-distance exposure, and lagged
detection-day predictors versus the identical learner plus the unchanged
ten-column `symmetric_world_support_summary_v1` Layer-B block. Exact site IDs and
exact world IDs are never supervised features. Favorable, null, and adverse
results are all terminally acceptable.

Outcome access requires a second commit adding only
`OUTCOME_AUTHORIZED_ONCE.json`. That marker binds the already-green parent
commit, contract, runner, preflight fingerprint, and 16-key authorization
result. The outcome workflow performs one full response download, never retries,
and never redesigns after opening.
