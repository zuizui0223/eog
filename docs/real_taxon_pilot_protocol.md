# Frozen real-taxon pilot protocol

This pilot tests whether the standalone EOG repository can execute the issue #3 rules on real GBIF occurrence data without changing taxa after results are inspected.

## Cohort

The six taxon-region pairs are fixed in `benchmarks/real_taxon_pilot_manifest.csv`. The pilot contains three plants and three animals and excludes Campanula. Taxon names and bounding boxes must not be replaced based on eligibility or EOG outcomes.

## Data and filters

- GBIF taxon identity is resolved with the species-match endpoint.
- Occurrences require coordinates and no flagged geospatial issue.
- Exact duplicate coordinates are removed.
- Records are deterministically thinned at 10 km.
- At most 240 thinned records are retained using evenly spaced deterministic indices.
- Environmental variables are frozen as CHELSA v2.1 bio1, bio4, bio12, and bio15.
- A pair is confirmatory-eligible only with at least 60 complete CHELSA rows after thinning.

## Metrics

Eligible pairs report span, continuity, raw gap strength, and the matched-size/matched-dimension Gaussian-null gap percentile established in issue #3. The percentile is a comparative reference score, not a probability of fragmentation.

## Stability

For each eligible pair, twenty 80% subsamples are evaluated. Outputs record span relative error, continuity absolute error, and gap-strength relative error against the full thinned matrix.

## Pilot gate

The gate tests pipeline feasibility rather than biological success:

1. every declaration produces a status row;
2. at least four of six pairs are technically eligible;
3. every eligible pair produces thinning-stability rows;
4. failed and ineligible pairs remain visible in artifacts.

Passing this gate permits freezing a larger 30–50 pair confirmatory manifest. It does not establish cross-taxon generality by itself.
