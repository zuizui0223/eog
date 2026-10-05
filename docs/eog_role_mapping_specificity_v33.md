# EOG v33 — role-mapping specificity audit

## Status

**FROZEN BEFORE ANY PLACEBO-MAPPING SCORE IS CALCULATED.**

v32 aligned each community by the identity that actually arrived first and found a very
large role-aligned history signal in the v28 microbiome. Because that response
transformation is itself indexed by the randomized history treatment, v33 asks whether
the biological history-to-identity mapping is specifically informative or whether
arbitrary treatment-dependent coordinate choices produce the same apparent gain.

This is an audit of v32 specificity, not a new priority-effects discovery.

## Primary question

> **Does the biologically correct mapping from arrival-history label to the corresponding
> ecological identity outperform arbitrary one-to-one mappings that use the same
> treatment-dependent response construction?**

## v28 microbiome — primary specificity test

Histories and response identities are the same five fungal names:

- Alternaria
- Aureobasidium
- Cladosporium
- Dioszegia
- Fusarium

Enumerate **all 5! = 120 bijections** from history labels to fungal response coordinates.

For each mapping:

1. select the mapped coordinate as the first role-aligned coordinate;
2. sort the remaining four abundance values descending;
3. preserve the exact five abundance values in every plant;
4. calculate Bray–Curtis distance;
5. calculate the same observed Genotype-aware partial R² used in v32.

The biologically correct mapping is the identity mapping:

history Alternaria -> coordinate Alternaria, etc.

### Frozen primary prediction

The correct biological mapping must be unusually strong among the complete 120-mapping
ensemble.

Primary criteria:

- its partial R² must exceed the median placebo-mapping partial R²;
- its exact mapping-specificity tail probability
  `p_map = #{mappings with R2 >= correct R2} / 120`
  must be **<= 0.05**.

Because the complete mapping space is enumerated, this is an exact finite comparison and
requires no Monte Carlo mapping sample.

## v30 grassland — descriptive specificity audit

Histories:

- F-first
- G-first
- L-first

Response identities:

- Forbs
- Grasses
- Legumes

Enumerate all **3! = 6 bijections**.

The correct biological mapping is:

- F-first -> Forbs
- G-first -> Grasses
- L-first -> Legumes.

The same role-aligned response construction and blocked partial R² are used.

With only six possible mappings, the minimum exact tail probability is 1/6; therefore
v30 mapping rank is descriptive and is not a binary confirmation gate.

## Why raw R² is the primary mapping statistic

v33 is not comparing different response dimensionalities or different model spaces.

Within each system every placebo mapping uses:

- the same experimental units;
- the same abundance values;
- the same number of dimensions;
- the same treatment-indexed coordinate-selection rule;
- the same distance;
- the same nuisance/block model.

Therefore the complete mapping ensemble directly controls the concern that
treatment-conditioned relabeling itself can inflate apparent separation.

The v32 null-calibrated E values remain the history-association evidence. v33 asks a
different question: whether the *biologically correct coordinate mapping* is specifically
better than arbitrary coordinate mappings under the same construction.

## Secondary diagnostics

For each system report:

- correct-mapping partial R²;
- median, minimum and maximum placebo-mapping partial R²;
- correct minus placebo median;
- exact rank of the correct mapping;
- exact upper-tail mapping probability;
- the five highest-scoring mappings for v28 and all six mappings for v30.

No alternate mapping statistic may replace the frozen primary statistic after scoring.

## Gates

Before accepting v33:

1. reproduce the v32 correct role-aligned partial R² for v28;
2. reproduce the v32 correct role-aligned partial R² for v30;
3. confirm every mapping preserves each row's exact abundance multiset;
4. enumerate exactly 120 unique v28 bijections and 6 unique v30 bijections.

## Exposure boundary

Known before freeze:

- all v28-v32 source data and results;
- the v32 correct role-aligned scores;
- the concern that the response construction depends on actual Treatment.

Not calculated before freeze:

- any incorrect-mapping role-aligned R²;
- correct-mapping rank among bijections;
- placebo-mapping median;
- mapping-specificity tail probability.

## Interpretation boundary

If the v28 correct mapping is exceptional among all bijections, v32 gains a strong
specificity control: its role-aligned gain cannot be explained merely by choosing *some*
Treatment-dependent coordinate.

If it is not exceptional, v32's biological role-symmetry interpretation must be
downgraded because arbitrary treatment-dependent response mappings perform similarly.

Do not call the mapping probability a causal randomization p-value. It is an exact
specificity comparison over a finite transformation ensemble.

## Claim boundary

Do not claim:

- direct causal identification of niche preemption or niche modification;
- that mapping specificity proves a mechanistic process;
- that arbitrary mappings are ecological null communities;
- universality from two systems.

The allowed conclusion is only whether the biologically correct first-arriver mapping is
specifically supported relative to all equally complex treatment-indexed placebo mappings.
