# EOG v38 — mechanistic ceiling after v37

## Status

**MECHANISTIC CEILING AUDIT. NO NEW DERIVED TARGET IS SCORED.**

The v28–v37 chain has localized a robust structural history signature in the microbiome:

- assembly history is retained strongly in community composition but weakly in aggregate
  rust state;
- microbiome history survives taxon-identity removal;
- Alternaria has the largest prospective history-level leverage on that identity-free
  architecture;
- the leverage is stronger in rank-1 dominance than in the normalized lower-rank tail;
- the direct Alternaria-versus-rest dominance contrast is positive across 11 of 12 host
  genotypes and is primarily genotype-shared.

v38 asks a different question:

> **Can the archived experiment identify why Alternaria-first communities develop stronger
> final dominance?**

The answer is **no**. The available source data support a structural storage result but do
not discriminate the relevant interaction mechanism.

## Source-paper reconciliation

Leopold & Busby (2020) already report two facts that are essential for interpreting the
EOG result correctly.

### Alternaria is generally abundant, not simply the strongest beneficiary of early arrival

The source paper states that:

- only three of the five early-arriving fungal species consistently benefited from
  pre-emptive colonization;
- Alternaria had the greatest relative abundance across treatments;
- Alternaria did benefit from early arrival, but its priority-effect magnitude was
  relatively low.

The authors therefore discuss at least two explanations:

1. Alternaria may have high intrinsic competitive ability;
2. Alternaria may occupy a relatively distinct niche.

They explicitly do not distinguish those alternatives.

This means the v34–v37 result must **not** be paraphrased as:

> Alternaria has the strongest priority effect.

The supported EOG statement is different:

> **Alternaria arrival history has the largest leverage on the identity-free dominance
> structure of the final community.**

A history can have large leverage on final dominance even when the focal taxon's own
early-arrival log-ratio is not the largest among colonists.

## Why the existing archive cannot identify mechanism

### 1. Amplicon data are compositional

The community data measure relative sequence abundance.

They do not provide total fungal load or absolute population size.

Therefore a larger final relative dominance value cannot distinguish among:

- increased absolute growth of the dominant fungus;
- reduced growth of competitors;
- changes in total community size;
- host-mediated shifts in multiple fungi simultaneously.

The source paper itself notes that quantitative microbial-abundance data are needed to
resolve these possibilities.

### 2. No direct pairwise interaction assay is archived

The repository contains:

- sample metadata;
- amplicon community tables;
- sequencing-bias calibration;
- rust measurements;
- source analysis code.

It does **not** contain a factorial pairwise competition matrix, fungal growth curves,
resource-consumption trajectories, inhibition-zone assays, or other direct interaction
measurements for the five focal early colonists.

Therefore the current archive cannot separate:

- niche pre-emption;
- niche modification;
- direct antagonism;
- facilitation;
- intrinsic growth-rate differences.

### 3. TP2 is not a valid temporal community trajectory

The source helper `code/Rfunctions.R` explicitly restricts community analysis to
Timepoint 1 because Timepoint 2 was sampled during the rust phase and the sequence data
were overwhelmed by rust reads.

Therefore TP2 cannot be used as an unbiased later community state to test temporal
persistence of the Alternaria dominance signature.

A TP1-versus-TP2 persistence analysis would confound community dynamics with pathogen-read
domination and is not a valid next EOG test.

### 4. Rust does not close the mechanism

The source paper reports that assembly history can affect rust disease independently of
microbiome composition at the time of pathogen exposure.

Thus rust severity does not provide a simple downstream readout of the abundance mechanism
that produced dominance.

## Correct interpretation after v37

The strongest supported microbiome result is now:

> **A randomized Alternaria arrival history leaves a broadly host-genotype-shared,
> identity-free signature of stronger final community dominance.**

This signature is:

- not the whole architecture-memory signal;
- not limited to one genotype;
- not equivalent to Alternaria having the largest species-specific priority-effect
  log-ratio;
- not sufficient to identify niche pre-emption, niche modification, intrinsic fitness or
  host-mediated interaction.

## What evidence would actually resolve the mechanism

At least one of the following is required.

### Absolute-abundance time series

Measure each focal fungus in absolute units before and after community assembly, such as:

- taxon-specific qPCR / ddPCR;
- spike-in calibrated sequencing;
- culture-based abundance where defensible.

This would separate focal growth from compositional displacement.

### Pairwise / reduced-community interaction experiment

For Alternaria and the other focal taxa, manipulate:

- arrival order;
- pair identity;
- host genotype;
- initial density.

This can test whether Alternaria suppresses competitors, simply grows faster, or changes
the host environment.

### Host-response measurements

If niche modification through the host is plausible, measure plant responses between the
first and second inoculations:

- defense signaling;
- leaf chemistry;
- immune markers;
- resource traits.

### Clean temporal community sampling

Collect community composition before pathogen inoculation at more than one time point,
with absolute abundance calibration.

## Program-level consequence

Do **not** continue generating increasingly fine transformations of the same TP1 relative-
abundance table.

The v28–v37 chain has already extracted the defensible structural result.

The next genuine biological advance requires new or independently archived process-level
evidence.

## Claim boundary

Retain:

> **Assembly history is stored unevenly across present ecological states and, within the
> v28 microbiome, Alternaria arrival history contributes a broadly genotype-shared,
> dominance-centered structural legacy.**

Do not claim:

- Alternaria has the strongest intrinsic priority effect;
- Alternaria is necessarily the dominant taxon in every Alternaria-history plant;
- niche pre-emption;
- niche modification;
- direct competition;
- host-mediated facilitation or inhibition;
- temporal persistence beyond the clean TP1 community measurement.

## Next action

The manuscript should stop the within-dataset derivation chain at v37.

Future work should be framed as a discriminating experiment:

> **Does Alternaria-first history increase dominance because Alternaria itself expands
> absolutely, because competitors are suppressed, or because the host environment is
> modified before later colonists arrive?**
