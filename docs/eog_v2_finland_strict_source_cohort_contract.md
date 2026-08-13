# EOG v2 SW Finland strict-source occurrence contract

## Status

**Prospective outcome-free redesign frozen after the original response-free source-reconstruction admission failed and before any released `outcome` value is accessed by EOG v2.**

This contract does not erase or reinterpret the original Finland admission failure. The original complement-source rule across all sourceful species failed its predeclared historical-count consistency gate (`R² = 0.9999649916830429 < 0.999999`) while island-universe, nearest-history, sourceful-species, and zero-source checks passed. That failed gate remains archived.

The redesign is deliberately narrower: it admits only species for which source identity is already exact from the released potential-target row structure and therefore requires **no source repair, deletion inference, or outcome-dependent choice**.

### Pre-outcome integrity correction

The first strict-bundle freeze exposed an internal contradiction before any `outcome` value was accessed: the initial 184-name file was copied from the response-free `exact_complement` status, but four of those taxa had decoded historical source count `0`. That contradicted the already-written fixed-source rule requiring a positive historical source count and would make source-conditioned EOG-R undefined. The correction removes exactly these four fixed-source-non-applicable taxa and changes no graph, predictor, fold, threshold, fit, inference, or promotion rule:

- `Epilobium adenocaulon`;
- `Epilobium ciliatum`;
- `Galium album`;
- `Senecio viscosus`.

The response-free audit still contains 184 `exact_complement` statuses; the prospective strict sourceful cohort is therefore 180 species. This correction was made solely from the already-frozen response-free audit and before outcome scoring.

## Immutable raw data and response firewall

Authoritative raw object:

- Dryad DOI `10.5061/dryad.ffbg79cr6`;
- file `colonization_select.csv`;
- byte size `129157803`;
- SHA-256 `72b631033ef36210ee19b151dc4f6569760262d68f70b9ce6de6c8a11afeb957`.

The Åbo Akademi-linked Zenodo mirror is accepted only because its downloaded bytes match this Dryad SHA-256 and size exactly. The semicolon delimiter and Dryad-documented `Limestone` Yes/No -> 1/0 representation normalization are syntax/schema handling only.

At the time this contract and cohort were frozen:

- `outcome` column existence had been checked;
- no `outcome` value had been parsed, counted, summarized, stratified, modeled, or used for species selection.

## Why the original complement source reconstruction failed globally

The released `Historical_total_log` values form an exact shared affine transform of integer `ln(historical_island_count + 1)` values. The response-free exact-consensus grid recovered:

- intercept `-3.0098005679308137`;
- slope `0.7981217334649451`;
- maximum integer decode error `2.5011104298755527e-12`;
- maximum released-value residual `5.551115123125783e-15`.

Among the 312 species with a released historical count:

- 184 species: potential-target complement count equals decoded historical island count exactly; 180 have a positive decoded historical count and 4 have count `0`;
- 3 species: source set could be uniquely repaired from count + nearest-distance constraints;
- 123 species: multiple source deletions satisfy the released response-free summaries;
- 2 species: nearest-distance constraints are inconsistent with the required count reduction.

The 4 zero-source exact complements are fixed-source non-applicable. The 3 uniquely repairable species are **not used** in this strict cohort. Ambiguous and inconsistent species are excluded. The redesign therefore does not infer any missing historical source identity.

Response-free audit provenance:

- workflow run `31687132743`;
- artifact ID `9175904550`;
- artifact digest `sha256:6ceffc22d6b97c26a0a656e3a8c4e14d9e345c6fb7377e6bfa151df5c7c78503`;
- source-identifiability fingerprint `06f38cb7a5d1321c5dde4072ee0c1329f52de05a55fed353909b342e3f4e2afd`.

## Frozen strict cohort rule

A species is admitted if and only if all following response-free conditions hold:

1. it occurs in the frozen raw species universe;
2. the released `Historical_total_log` is present and invariant within species;
3. the released historical total decodes to an integer island count on the exact shared affine `ln(count+1)` grid;
4. the decoded historical island count is greater than zero;
5. that decoded count equals exactly the number of islands in the 471-island universe that are absent from the species' released potential-target row set;
6. no inferred deletion or repaired historical source is required.

This rule yielded exactly **180 species** before outcome access.

The exact species list is frozen at:

`benchmarks/frozen/finland_strict_source_cohort/exact_complement_species.txt`

with SHA-256:

`e218f94e5facd4ed330a80b0fead0012b31fd5cb7b7b026f2ee0ff326277b2bc`.

After outcome access this list cannot be enlarged, reduced, taxonomically repaired, or replaced because of predictive performance.

## Source identity

For every strict-cohort species, historical sources are exactly:

`471 frozen islands - released potential-target islands for that species`.

No source is added or removed. Because the complement count equals the independently decoded released historical count, source cardinality is exact under the released 471-island design.

Before feature-bundle promotion, the same source sets must also retain the frozen nearest-history consistency gate (`R² >= 0.999999`) against `Dist_to_historical_log`. A failure is a non-estimable stop; the cohort rule is not relaxed.

## Landscape graph and predictors — unchanged

The strict cohort changes only response-free species eligibility. All island/network/model settings remain exactly those frozen for the original Finland occurrence path:

- 471-island universe;
- EUREF-FIN coordinates;
- geometry-only Gabriel adjacency;
- environmental transition support from the same frozen island habitat fields;
- `loss_support = 0.55`;
- `max_steps = 5`;
- same geography-only dynamic sensitivity;
- same five deterministic island folds;
- same L2 logistic penalty `1.0`;
- same minimum complete-row and fold eligibility rules.

Reference ladder remains:

- `R0`: local island/environmental covariates;
- `R1`: R0 + nearest historical source + historical source count;
- `R2`: R1 + multi-source pressure + minimum effective resistance;
- `C`: R2 + fixed-source dynamic EOG reachability.

No source expansion is allowed. Training/test labels never construct sources.

## Inference — unchanged

Primary species-level contrast remains:

`C - R2` held-out log loss,

with negative values favourable to EOG.

The already-frozen inference settings remain:

- species is the inferential unit;
- five frozen spatial island folds;
- exactly 10,000 species bootstrap resamples;
- seed `20260812`;
- Brier score secondary;
- geography-only dynamic reachability sensitivity remains non-promotional.

Dataset-level GO still requires all:

1. at least 100 response-free eligible strict-cohort species after complete-row/fold gates;
2. pooled R2 held-out log loss <= pooled R0 held-out log loss;
3. equal-weight mean species `(C - R2)` log-loss difference < 0;
4. bootstrap upper 95% bound < 0.

If the strong-reference condition fails, status is indeterminate reference failure. If the EOG contrast fails, retain null/adverse. No weaker reference or alternate cohort may replace the primary result after outcome access.

## Claim boundary

This is a prospective independent occurrence test on a response-free source-identifiable subset of the released Finland dataset. A favourable result would support incremental held-out information from frozen source-conditioned dynamic reachability beyond R2 **for this strict cohort**. It would not establish colonization probability, realized movement routes, universal superiority over SDMs, or validity for the 407 excluded/zero-source/undecodable/ambiguous species.

The original failed global Finland admission and every excluded-species reason remain part of the audit trail.
