# EOG v2 SW Finland strict-source independent occurrence result

## Frozen status

**Independent prospective occurrence validation complete — NO PROMOTION.**

The authoritative one-time response-capable workflow was run `31690500533` (run number 1, attempt 1). It completed successfully after the response-free feature freeze and scoring preflight had both passed. The result artifact is `9177201442` with digest `sha256:47231b1163046a468805383010d652c019b92edb92336d5b48393ff8c922b870`.

The first access to released `outcome` values occurred only in the explicitly marked scoring step. No cohort, graph, predictor, fold, fitting rule, bootstrap rule, or promotion threshold was changed after that access.

## Frozen response-free inputs

- authoritative raw SHA-256: `72b631033ef36210ee19b151dc4f6569760262d68f70b9ce6de6c8a11afeb957`;
- strict sourceful species: 180;
- response-free analysis rows: 74,700;
- feature-bundle fingerprint: `24590e53c511330e99992e4399b711b85ce160a54a5bbc01364790f30982301b`;
- response-free scoring-preflight fingerprint: `d9cd041d6893592b20389f56a560099123dedbbf2fda0795bc618f88efebdc91`.

The four zero-source exact-complement taxa were excluded before outcome access because fixed-source EOG-R is undefined for zero historical sources. The original global Finland source-reconstruction admission failure remains archived and is not reclassified.

## Held-out result

Pooled held-out log loss:

- R0: `0.25845732128037924`;
- R1: `0.2381955499852448`;
- R2: `0.237422158781551`;
- C = R2 + fixed-source EOG reachability: `0.2373256991040136`;
- C_geo: `0.23733676822841138`.

Predeclared contrasts:

- R2 − R0: `-0.021035162498828225` — strong-reference operational gate **PASS**;
- pooled C − R2: `-0.00009645967753740825`;
- equal-weight mean species C − R2: `-0.00013800642598677228` — directional mean gate **PASS**;
- median species C − R2: `-0.00007438036891028739`;
- 99/180 species favourable, 81/180 adverse;
- species-bootstrap 95% interval: `[-0.00028370978779246455, +0.000000014795433136458638]` — upper-bound gate **FAIL** because the upper limit is above zero.

The predeclared decision is therefore **`no_empirical_added_information`**, with `promotion_go = false`.

The result fingerprint is `97de0a30c197e8352589fd98f0da976c69d4761229d2ec70106975292182068e`. The archived `result.json` byte SHA-256 is `c2c7c6d2f42615b9e7c4e9bb223d984b7659b415718abdebbf1fd90b4851ce3c`.

## Interpretation boundary

The point estimate is weakly favourable, and the strong conventional R2 reference is operational, but the predeclared uncertainty gate is not passed. The near-zero positive bootstrap upper bound is not rounded down, reclassified, rescued with another cohort, or used to justify a weaker threshold. EOG v2 therefore does **not** obtain independent empirical occurrence promotion from this dataset.

This does not imply that source-conditioned dynamic reachability is meaningless. It means that, under this frozen independent benchmark and its strong reference, the incremental held-out occurrence information is too weak to satisfy the prospectively declared promotion rule.

The result does not estimate colonisation probability, realised movement, migration rate, or a historical route, and it does not support a claim that EOG generally outperforms SDMs or conventional connectivity models.

## Stop rule

The one-time scoring workflow is removed after this result is archived. The frozen result may be reproduced for audit from the immutable code/data identities, but it may not be rerun as a tuning loop. Any future occurrence validation must be a separately predeclared independent dataset or endpoint and must retain this NO-GO result visibly.
